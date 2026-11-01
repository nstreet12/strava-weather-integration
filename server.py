"""
Standalone HTTP server entrypoint for the Strava weather integration.

This wraps the existing AWS-Lambda-style `lambda_handler(event, context)`
(see lambda_function.py) with a minimal stdlib http.server implementation,
so the exact same business logic (strava_helper.py, weather_helper.py) can
run as a long-lived process on a home server instead of inside AWS Lambda.

Strava calls:
  GET  /webhook?hub.challenge=...&hub.verify_token=...   (subscription verification)
  POST /webhook  (body: JSON event, e.g. {"object_id": ..., "aspect_type": "create", ...})

Both are translated into the same `event` dict shape the lambda_handler
expects: event['httpMethod'], event['queryStringParameters'], event['body'].
"""

import json
import logging
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

from lambda_function import lambda_handler

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("strava-weather-server")

PORT = int(os.environ.get("PORT", "8787"))
HOST = os.environ.get("HOST", "0.0.0.0")


class WebhookHandler(BaseHTTPRequestHandler):
    server_version = "StravaWeather/1.0"

    def _send_json_response(self, status_code, body_str):
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        encoded = body_str.encode("utf-8") if isinstance(body_str, str) else json.dumps(body_str).encode("utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def _dispatch(self, http_method, body_str):
        parsed = urlparse(self.path)
        if parsed.path != "/webhook":
            self._send_json_response(404, json.dumps({"error": "not found"}))
            return

        query_params = {k: v[0] for k, v in parse_qs(parsed.query).items()}

        event = {
            "httpMethod": http_method,
            "queryStringParameters": query_params,
            "body": body_str,
        }

        try:
            result = lambda_handler(event, None)
        except Exception as exc:  # noqa: BLE001 - surface as 500, keep service alive
            logger.exception("lambda_handler raised an exception")
            self._send_json_response(500, json.dumps({"error": str(exc)}))
            return

        if result is None:
            # Original lambda_handler falls through to an implicit `None`
            # return in some branches (unhandled aspect_type, etc). Treat
            # that as a benign "no-op, acknowledged" response.
            self._send_json_response(200, json.dumps({"status": "ignored"}))
            return

        status_code = result.get("statusCode", 200)
        body = result.get("body", "")
        self._send_json_response(status_code, body)

    def do_GET(self):
        self._dispatch("GET", "")

    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0) or 0)
        raw_body = self.rfile.read(content_length) if content_length else b""
        body_str = raw_body.decode("utf-8") if raw_body else "{}"
        self._dispatch("POST", body_str)

    def log_message(self, fmt, *args):
        logger.info("%s - %s", self.address_string(), fmt % args)


def main():
    server = ThreadingHTTPServer((HOST, PORT), WebhookHandler)
    logger.info(f"Starting strava-weather server on {HOST}:{PORT}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
