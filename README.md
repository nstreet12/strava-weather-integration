Strava Weather Integration
========================================

When you log a new activity in Strava, this project automatically updates it with an AI-generated title and the weather conditions at the time and location of your activity.

<img width="533" alt="image" src="https://github.com/user-attachments/assets/a3e68430-c6ea-420e-928d-fab2fd22a8a0">

How It Works
------------

1. You finish an activity and save it in Strava
2. Strava fires a webhook to an API Gateway endpoint
3. A Lambda function fetches the full activity details from the Strava API
4. Weather conditions at the activity's start time and location are fetched from the Open-Meteo API
5. Claude generates a creative, context-aware title based on the activity type, effort, and weather
6. The Lambda updates the Strava activity — setting the new title and appending weather to the description

Infrastructure
--------------

- **AWS Lambda** — runs the Python handler on each Strava webhook event
- **API Gateway** — exposes the `/webhook` endpoint that Strava calls
- **AWS SAM** — manages all infrastructure as code (`template.yaml`)
- **Strava API** — source of activity data; receives the final update
- **Open-Meteo API** — provides historical weather data (no API key required)
- **Anthropic Claude API** — generates the activity title

Project Structure
-----------------

```
strava-weather-integration/
├── src/
│   ├── lambda_function.py    # Webhook handler and main orchestration
│   ├── strava_helper.py      # Strava API calls (fetch activity, update activity)
│   ├── weather_helper.py     # Open-Meteo weather data fetching
│   └── ai_title_helper.py    # Claude API title generation
├── tests/                    # Unit tests
├── .env.example              # Environment variable template
├── DEPLOY.md                 # Step-by-step deployment guide
├── Makefile                  # Build and deploy automation
├── requirements.txt          # Python dependencies
└── template.yaml             # AWS SAM infrastructure template
```

Deployment
----------

See [DEPLOY.md](DEPLOY.md) for full instructions. The short version:

```bash
make install
make build
make deploy \
  strava_client_id=YOUR_ID \
  strava_client_secret=YOUR_SECRET \
  strava_refresh_token=YOUR_TOKEN \
  ANTHROPIC_API_KEY=YOUR_KEY
```

After deploying, register the output `WebhookUrl` with Strava:

```bash
curl -X POST https://www.strava.com/api/v3/push_subscriptions \
  -F client_id=YOUR_ID \
  -F client_secret=YOUR_SECRET \
  -F callback_url=YOUR_WEBHOOK_URL \
  -F verify_token=STRAVA
```

Required Environment Variables
-------------------------------

| Variable | Description |
|---|---|
| `strava_client_id` | Strava OAuth client ID |
| `strava_client_secret` | Strava OAuth client secret |
| `strava_refresh_token` | Strava refresh token (requires `activity:write` scope) |
| `ANTHROPIC_API_KEY` | Anthropic API key for Claude |
