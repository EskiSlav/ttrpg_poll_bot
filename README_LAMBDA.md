# Telegram Poll Bot - Lambda Version

Serverless Telegram bot that creates rating polls, deployed on AWS Lambda.

## Architecture

- **AWS Lambda**: Runs the bot code
- **API Gateway**: Receives webhook from Telegram
- **SSM Parameter Store**: Stores bot token securely
- **Serverless Framework**: Deployment and infrastructure management

## Prerequisites

1. Node.js and npm (for Serverless Framework)
2. AWS CLI configured with credentials
3. Python 3.11
4. Telegram bot token from [@BotFather](https://t.me/botfather)

## Setup

### 1. Install Serverless Framework

```bash
npm install -g serverless
npm install --save-dev serverless-python-requirements
```

### 2. Store Bot Token in SSM

```bash
aws ssm put-parameter \
  --name "/telegram/poll_bot/token" \
  --value "YOUR_BOT_TOKEN" \
  --type "SecureString" \
  --region eu-west-1
```

### 3. Deploy

```bash
# Install Python dependencies
pip install -r requirements.txt

# Deploy to AWS
serverless deploy --stage prod --region eu-west-1
```

After deployment, you'll get an API Gateway URL like:
```
https://xxxxxxxxxx.execute-api.eu-west-1.amazonaws.com/webhook
```

### 4. Set Webhook

```bash
# Set the webhook to your API Gateway URL
python lambda_handler.py https://xxxxxxxxxx.execute-api.eu-west-1.amazonaws.com/webhook
```

Or manually:
```bash
curl -X POST "https://api.telegram.org/bot<YOUR_TOKEN>/setWebhook" \
  -H "Content-Type: application/json" \
  -d '{"url":"https://xxxxxxxxxx.execute-api.eu-west-1.amazonaws.com/webhook"}'
```

## Usage

Same as before:
- `/poll <text>` - Create a poll
- `/rate <text>` - Create a poll
- `/start` - Show help

## Configuration

Edit `serverless.yml` to customize:
- `region`: AWS region
- `stage`: Deployment stage
- `memorySize`: Lambda memory allocation
- `custom.ssmParameter`: SSM parameter path

## Local Development

The original polling-based bot is still in [main.py](main.py) for local testing:

```bash
export TELEGRAM_BOT_TOKEN="your_token"
python main.py
```

## Logs

View Lambda logs:
```bash
serverless logs -f webhook --tail
```

## Cleanup

Remove all resources:
```bash
serverless remove
```

Don't forget to delete the SSM parameter:
```bash
aws ssm delete-parameter --name "/telegram/poll_bot/token"
```

## Cost

AWS Lambda free tier includes:
- 1M requests/month
- 400,000 GB-seconds of compute time/month

This bot should stay within free tier for moderate usage.
