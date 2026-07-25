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
- `/stats` - Open the club's Telegram Mini App to see your own rating stats
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

## Personal Stats Mini App (`/stats`)

Every `/rate` poll is non-anonymous, so Telegram sends this bot a `poll_answer` webhook
update whenever someone votes — the `webhook` function now records these (who rated
what, when) into two new DynamoDB tables managed by the `ttrpg_website2`/`aws_infra`
Terraform: `ttrpg_club_telegram_rating_polls` (which poll_id was rating which text) and
`ttrpg_club_telegram_rating_votes` (the actual votes). The "Подивитись відповідь" /
view-results option (index 0) is never stored as a rating.

The `ttrpg_website2` frontend has a standalone Mini App page (`/telegram`) that reads
Telegram's signed `initData` (proof of identity — no separate login) and calls a new
`POST /telegram/stats` endpoint on the club's own API to show a user their own rating
history. That endpoint needs `ssm:GetParameter` on this bot's token (to verify
`initData`'s signature) and read access to the votes table — both already wired into
`aws_infra`'s `lambda/ttrpg_club_api` Terraform.

**People who voted don't need to be registered on the club website at all** — stats are
keyed purely by Telegram user ID, independent of the website's own member accounts.

To make `/stats` actually open the Mini App, you need to register it with @BotFather
once (Telegram only allows `web_app` inline buttons in private chats, not this bot's
group chat — so `/stats` instead sends a plain URL button using a `t.me/<bot>/<app>`
deep link, which works everywhere):

1. Message [@BotFather](https://t.me/botfather): `/newapp`, pick this bot, give it a
   name/short name (e.g. `stats`), and when asked for the Web App URL, use your
   deployed site's `/telegram` page — e.g. `https://your-cloudfront-domain/telegram`.
2. Deploy with the resulting deep link:
   ```bash
   serverless deploy --stage prod --region eu-west-2 \
     --param="adminChatId=$ADMIN_CHAT_ID" \
     --param="signupRequestsStreamArn=$STREAM_ARN" \
     --param="miniAppDeepLink=https://t.me/your_bot/stats"
   ```

Until `miniAppDeepLink` is set, `/stats` replies with a "temporarily unavailable"
message instead of a broken button.

## Cost

AWS Lambda free tier includes:
- 1M requests/month
- 400,000 GB-seconds of compute time/month

This bot should stay within free tier for moderate usage.
