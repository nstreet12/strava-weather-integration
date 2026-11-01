Strava Weather Integration
========================================

Description
-----------

This project integrates Strava activities with real-time weather data, enabling users to see weather conditions at the time of their activities. When a new activity is logged in Strava, the webhook handler is triggered, fetching weather data from the Open-Meteo API and appending it to the Strava activity's description.

<img width="533" alt="image" src="https://github.com/user-attachments/assets/a3e68430-c6ea-420e-928d-fab2fd22a8a0">

Current Deployment (nsserver / Tailscale Funnel)
-------------------------------------------------

As of November 2026, this project runs as a standalone Python service on a
home server (`nsserver`), not AWS Lambda. The original Lambda-style handler
(`lambda_function.py`, `strava_helper.py`, `weather_helper.py`) is unchanged;
a new thin entrypoint (`server.py`) wraps it with a plain-stdlib
`http.server` that translates real HTTP requests into the same `event` dict
shape `lambda_handler(event, context)` always expected
(`httpMethod`, `queryStringParameters`, `body`), and returns the handler's
`statusCode`/`body` as the HTTP response.

**Components**

-   **server.py**: Minimal stdlib HTTP server (`ThreadingHTTPServer`), listens on `/webhook` for Strava's GET (subscription verification / `hub.challenge`) and POST (activity events).
-   **systemd**: `strava-weather.service` runs `server.py` under a Python venv, `Restart=on-failure`, enabled at boot. Secrets (Strava client id/secret/refresh token) are supplied via `EnvironmentFile=` pointing at a gitignored `strava-weather.env` file — never committed.
-   **Tailscale Funnel**: Exposes the local port (8787) to the public internet over HTTPS so Strava's webhook can reach it, without opening router ports. `tailscale funnel 8787` (background mode) assigns a public `https://<node>.<tailnet>.ts.net/webhook` URL.
-   **Strava API**: Provides access to user activities; requires `activity:write` scope to PUT updated descriptions (not just `activity:read_all`).
-   **Open-Meteo API**: Supplies weather data.

**Setup on nsserver**

```bash
cd strava-weather-integration
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

# strava-weather.env (gitignored) — real secrets, loaded by systemd:
#   strava_client_id=...
#   strava_client_secret=...
#   strava_refresh_token=...   (must have activity:write scope)
#   PORT=8787
#   HOST=0.0.0.0

sudo cp strava-weather.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now strava-weather.service

# Expose publicly via Tailscale Funnel (requires Funnel enabled for the
# node/tailnet in the Tailscale admin console: https://login.tailscale.com/admin/acls)
sudo tailscale funnel --bg 8787

# Register the webhook with Strava once the Funnel URL is live:
curl -X POST https://www.strava.com/api/v3/push_subscriptions \
  -F client_id=<id> -F client_secret=<secret> \
  -F callback_url=https://<funnel-host>/webhook -F verify_token=STRAVA
```

Components (original / logic-level)
------------------------------------

-   **Compute**: Runs the Python function that is executed in response to event triggers (previously AWS Lambda behind API Gateway; now a systemd-managed process behind Tailscale Funnel).
-   **Strava API**: Provides access to user activities.
-   **Open-Meteo API**: Supplies weather data.

Functional Overview
-------------------

1.  **Event Trigger**:

    -   The process starts when a new activity is recorded in Strava, which triggers the webhook configured via Strava API.
2.  **Webhook Invocation**:

    -   Strava webhook events invoke the handler via the public Tailscale Funnel URL (previously via AWS API Gateway).
3.  **Data Fetching**:

    -   The handler extracts the activity details and queries the Open-Meteo API to fetch weather data for the time and location of the activity.
4.  **Data Processing**:

    -   The weather data is processed and formatted within the handler.
5.  **Post to Strava**:

    -   Finally, the handler PUTs the formatted weather data back onto the Strava activity's description.


Data Flow
---------

1.  **Activity Data**:

    -   Received from Strava containing details like activity ID, user ID, start time, and location.
2.  **Weather Data**:

    -   Contains weather conditions such as temperature, humidity, and wind speed at the time of the activity.
3.  **Processed Data**:

    -   Combines activity and weather data to enhance user experience on Strava.

Benefits
--------

-   **User Engagement**: Enhances user interaction with Strava by providing contextual weather information.
-   **Automation**: Automates the process of logging weather data without user intervention.
-   **Self-hosted & low-cost**: Runs on existing home-server hardware over a Tailscale Funnel tunnel instead of paid cloud infrastructure, with systemd handling restarts/boot-start the way AWS Lambda handled scaling/retries.

Further Development
-------------------

Potential areas for expansion include:

-   **Historical Weather Data**: Fetch historical weather data for past activities.
-   **User Preferences**: Allow users to customize the type of weather information they receive.
-   **Analytics**: Integrate more detailed analytics for users to track performance against weather conditions.
-   **AI-generated titles**: See the `feature-ai-title-generation` branch for an in-progress, not-yet-merged exploration of AI-generated activity titles (intentionally kept separate from this deployment).
