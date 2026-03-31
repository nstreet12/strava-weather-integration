AWS_PROFILE ?= default
AWS_REGION  ?= us-east-1
AWS_STACK_NAME ?= strava-weather
S3_BUCKET ?= $(AWS_STACK_NAME)-deploy-$(shell aws sts get-caller-identity --query Account --output text --profile $(AWS_PROFILE) 2>/dev/null)

.PHONY: install build deploy local test clean

install:
	python3 -m venv .venv
	.venv/bin/pip install --upgrade pip
	.venv/bin/pip install -r requirements.txt

build:
	sam build --use-container

deploy: build
	sam deploy \
		--stack-name $(AWS_STACK_NAME) \
		--region $(AWS_REGION) \
		--profile $(AWS_PROFILE) \
		--capabilities CAPABILITY_IAM \
		--resolve-s3 \
		--parameter-overrides \
			StravaClientId=$(strava_client_id) \
			StravaClientSecret=$(strava_client_secret) \
			StravaRefreshToken=$(strava_refresh_token) \
			AnthropicApiKey=$(ANTHROPIC_API_KEY)

local:
	sam local start-api --env-vars .env.json

test:
	.venv/bin/python -m pytest tests/ -v

clean:
	rm -rf .aws-sam/
	rm -rf build/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null; true
	find . -name "*.pyc" -delete
