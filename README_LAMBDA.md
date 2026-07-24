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

- `/poll <text>` - Create a rating poll (1-10)
- `/rate <text>` - Create a rating poll (1-10)
- `/bool <question>` - Create a Yes/No poll
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

## Club Signup Notifications (`notifySignup`)

A second function, `notifySignup`, is triggered directly by the `ttrpg_club_signup_requests`
DynamoDB Stream from the separate `ttrpg_website`/`aws_infra` project — it posts a message
to `ADMIN_CHAT_ID` whenever someone submits a new club membership request. It reuses this
bot's existing token (same SSM parameter, `Bot.send_message`), so no second bot is needed.

Deploy it (in addition to the token in SSM) by passing two extra params:

```bash
# Your own numeric Telegram chat ID — see README.md's normal getUpdates instructions,
# or message the bot and check the chat.id there.
ADMIN_CHAT_ID=123456789

# From the aws_infra repo: cd dynamodb/ttrpg_club_signup_requests && terraform output -raw dynamodb_table_stream_arn
STREAM_ARN=arn:aws:dynamodb:eu-west-2:...:table/ttrpg_club_signup_requests/stream/...

serverless deploy --stage prod --region eu-west-2 \
  --param="adminChatId=$ADMIN_CHAT_ID" \
  --param="signupRequestsStreamArn=$STREAM_ARN"
```

If the club's `ttrpg_club_signup_requests` table is ever recreated, its stream ARN changes
and you'll need to redeploy with the new value.

## Cost

AWS Lambda free tier includes:
- 1M requests/month
- 400,000 GB-seconds of compute time/month

This bot should stay within free tier for moderate usage.
