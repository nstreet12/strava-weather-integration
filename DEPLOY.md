# Deployment Guide

## Prerequisites

- [AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/install-cliv2.html) configured with appropriate credentials
- [AWS SAM CLI](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html)
- [Docker](https://docs.docker.com/get-docker/) (required for `sam build --use-container`)
- Python 3.11+
- A Strava API application ([create one here](https://www.strava.com/settings/api))
- An Anthropic API key ([get one here](https://console.anthropic.com/))

## Getting Your Credentials

### Strava Credentials

1. Go to https://www.strava.com/settings/api and create an application
2. Note your **Client ID** and **Client Secret**
3. Get a refresh token with `activity:write` scope:
   - Authorize via: `https://www.strava.com/oauth/authorize?client_id=YOUR_CLIENT_ID&response_type=code&redirect_uri=http://localhost&approval_prompt=force&scope=activity:write`
   - Exchange the returned `code` for tokens:
     ```
     curl -X POST https://www.strava.com/oauth/token \
       -d client_id=YOUR_CLIENT_ID \
       -d client_secret=YOUR_CLIENT_SECRET \
       -d code=YOUR_CODE \
       -d grant_type=authorization_code
     ```
   - Save the `refresh_token` from the response

### Anthropic API Key

1. Go to https://console.anthropic.com/
2. Create an API key under **API Keys**

## Deployment Steps

### 1. Install local dependencies

```bash
make install
```

### 2. Set environment variables

Copy `.env.example` to `.env` and fill in your values (for local reference only — never commit `.env`):

```bash
cp .env.example .env
```

### 3. Build the deployment package

```bash
make build
```

### 4. Deploy to AWS

```bash
make deploy \
  strava_client_id=YOUR_CLIENT_ID \
  strava_client_secret=YOUR_CLIENT_SECRET \
  strava_refresh_token=YOUR_REFRESH_TOKEN \
  ANTHROPIC_API_KEY=YOUR_ANTHROPIC_KEY
```

Or export them as shell variables first:

```bash
export strava_client_id=YOUR_CLIENT_ID
export strava_client_secret=YOUR_CLIENT_SECRET
export strava_refresh_token=YOUR_REFRESH_TOKEN
export ANTHROPIC_API_KEY=YOUR_ANTHROPIC_KEY
make deploy
```

After deployment, the output will include your **WebhookUrl**. Copy it — you'll need it in the next step.

### 5. Register the Strava Webhook

Replace `YOUR_WEBHOOK_URL`, `YOUR_CLIENT_ID`, and `YOUR_CLIENT_SECRET`:

```bash
curl -X POST https://www.strava.com/api/v3/push_subscriptions \
  -F client_id=YOUR_CLIENT_ID \
  -F client_secret=YOUR_CLIENT_SECRET \
  -F callback_url=YOUR_WEBHOOK_URL \
  -F verify_token=STRAVA
```

Strava will send a GET request to verify your endpoint — the Lambda handles this automatically.

## Local Testing

For local testing, create a `.env.json` file:

```json
{
  "StravaWeatherFunction": {
    "strava_client_id": "YOUR_CLIENT_ID",
    "strava_client_secret": "YOUR_CLIENT_SECRET",
    "strava_refresh_token": "YOUR_REFRESH_TOKEN",
    "ANTHROPIC_API_KEY": "YOUR_ANTHROPIC_KEY"
  }
}
```

Then run:

```bash
make local
```

## Redeployment

After code changes, just run `make deploy` again with your credentials. SAM will update the existing stack in-place.

## Cleanup

To delete the stack and all AWS resources:

```bash
aws cloudformation delete-stack --stack-name strava-weather --profile YOUR_PROFILE
```

## Troubleshooting

- **Lambda timeout**: The default timeout is 30 seconds. If Claude API calls are slow, increase `Timeout` in `template.yaml`.
- **Missing credentials**: Check CloudWatch Logs (`/aws/lambda/strava-weather-StravaWeatherFunction-*`) for environment variable errors.
- **Webhook not firing**: Verify your Strava subscription is active: `GET https://www.strava.com/api/v3/push_subscriptions?client_id=X&client_secret=Y`
