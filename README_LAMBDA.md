# Telegram Poll Bot - Lambda Version

Telegram bot that creates rating polls, deployed on AWS Lambda.

## Architecture

- **AWS Lambda**: Runs the bot code (3 functions: `webhook`, `notifySignup`, `notifyFeedback`)
- **API Gateway (HTTP API v2)**: Receives the webhook from Telegram
- **SSM Parameter Store**: Stores the bot token securely
- **Terraform** (`aws_infra/lambda/ttrpg_poll_bot`): Owns all of the above — the
  functions, the API, the shared IAM role, and the two DynamoDB Stream event source
  mappings. This repo only ever ships *code*, via `build.sh` + `aws lambda
  update-function-code` (by hand or via GitHub Actions) — no CloudFormation, no
  Serverless Framework. Matches exactly how `ttrpg_website2`'s backend deploys.

## Prerequisites

1. Python 3.14 + pip
2. AWS CLI configured with credentials
3. Telegram bot token from [@BotFather](https://t.me/botfather)
4. Terraform (only needed when the *infrastructure* changes — not for routine code pushes)

## Setup

### 1. Store Bot Token in SSM

```bash
aws ssm put-parameter \
  --name "/telegram/poll_bot/token" \
  --value "YOUR_BOT_TOKEN" \
  --type "SecureString" \
  --region eu-west-2
```

### 2. Apply the Terraform

From `aws_infra/lambda/ttrpg_poll_bot`:

```bash
cd ../../../ttrpg_poll_bot && ./build.sh   # produces build/, which Terraform's source_path reads
cd -
terraform init
terraform apply -var="admin_chat_id=<your numeric chat id>"
```

(If you're migrating from an existing Serverless Framework deployment rather than
starting fresh, see `import-from-serverless.sh` in that same directory — it imports the
already-running Lambda/API Gateway/IAM role/event source mappings into this Terraform
module with zero downtime, instead of recreating them.)

`terraform output webhook_url` gives you the API Gateway URL.

### 3. Set Webhook

```bash
python lambda_handler.py "$(terraform output -raw webhook_url)"
```

Or manually:
```bash
curl -X POST "https://api.telegram.org/bot<YOUR_TOKEN>/setWebhook" \
  -H "Content-Type: application/json" \
  -d '{"url":"<webhook_url from above>"}'
```

### Routine code changes

Once the infrastructure above exists, day-to-day changes to `lambda_handler.py` don't
need Terraform at all — either push to `main` (see GitHub Actions Deployment below) or,
locally:

```bash
./build.sh
cd build && zip -r ../function.zip . -x "__pycache__/*" && cd ..
aws lambda update-function-code --function-name telegram-poll-bot-prod-webhook --zip-file fileb://function.zip
aws lambda update-function-code --function-name telegram-poll-bot-prod-notifySignup --zip-file fileb://function.zip
aws lambda update-function-code --function-name telegram-poll-bot-prod-notifyFeedback --zip-file fileb://function.zip
# ...and the dev stage, if you've applied it (see "Dev Stage" below):
aws lambda update-function-code --function-name telegram-poll-bot-dev-webhook --zip-file fileb://function.zip
aws lambda update-function-code --function-name telegram-poll-bot-dev-notifySignup --zip-file fileb://function.zip
aws lambda update-function-code --function-name telegram-poll-bot-dev-notifyFeedback --zip-file fileb://function.zip
```

## Usage

- `/poll <text>` - Create a rating poll (1-10); also sends a "Leave Feedback" Mini App link
- `/rate <text>` - Create a rating poll (1-10); also sends a "Leave Feedback" Mini App link
- `/bool <question>` - Create a Yes/No poll
- `/stats` - Open the club's Telegram Mini App to see your own rating stats and game history
- `/start` - Show help

## Configuration

Edit `aws_infra/lambda/ttrpg_poll_bot/variables.tf` (region, `admin_chat_id`,
`mini_app_deep_link`) or `main.tf` (memory, timeout, environment variables) — these now
live in Terraform, not `serverless.yml` (removed as part of the Terraform migration).

## Local Development

The original polling-based bot is still in [main.py](main.py) for local testing:

```bash
export TELEGRAM_BOT_TOKEN="your_token"
python main.py
```

## Logs

```bash
aws logs tail /aws/lambda/telegram-poll-bot-prod-webhook --follow
```

## Cleanup

```bash
cd aws_infra/lambda/ttrpg_poll_bot && terraform destroy
```

Don't forget to delete the SSM parameter:
```bash
aws ssm delete-parameter --name "/telegram/poll_bot/token"
```

## Dev Stage (isolated test bot)

Alongside the real (`-prod-`) functions, the Terraform also creates a fully isolated
`-dev-` copy of all 3 functions — same code, own IAM role, own Telegram bot token, and
the (currently empty) `dynamodb/ttrpg_club/prod` tables instead of the real
`dynamodb/ttrpg_club/dev` ones the live bot uses. **A dev/test bot can never read or
write real club data.** It's reached at a different path on the *same* API Gateway
(`/dev/webhook` instead of `/webhook`) rather than a separate API — HTTP API v2's
Lambda-proxy integrations are fixed per route, not swappable per stage, so a distinct
route is what actually gets you a second, independently-routable webhook URL on one
host.

Setup, one time:

1. Create a second bot via [@BotFather](https://t.me/botfather) (`/newbot`) and store its
   token under a different SSM parameter name:
   ```bash
   aws ssm put-parameter --name "/telegram/poll_bot_dev/token" --value "YOUR_DEV_BOT_TOKEN" --type "SecureString" --region eu-west-2
   ```
2. `terraform apply` (optionally passing `-var="dev_admin_chat_id=..."` if you want dev
   signup notifications to go to a different chat than prod's `admin_chat_id`).
3. `terraform output webhook_dev_url` → register it as the dev bot's webhook:
   ```bash
   curl -X POST "https://api.telegram.org/bot<DEV_BOT_TOKEN>/setWebhook" -H "Content-Type: application/json" -d '{"url":"<webhook_dev_url>"}'
   ```
4. For the dev Mini App (stats/feedback pages), apply
   `aws_infra/s3_cloudfront/ttrpg_club_frontend_dev` (a separate S3 bucket + CloudFront
   distribution, so a dev frontend build never overwrites the real site), build/sync the
   frontend to it, register a second Mini App with @BotFather pointing at that dev
   CloudFront domain, and set `-var="mini_app_deep_link_dev=https://t.me/<dev_bot>/<app>"`.

Routine code pushes update both stages together (see the GitHub Actions section above,
and the manual command list right below "Routine code changes") — since the code is
identical, there's no separate dev build/deploy step.

## Club Signup Notifications (`notifySignup`)

A second function, `notifySignup`, is triggered directly by the `ttrpg_club_signup_requests`
DynamoDB Stream from the separate `ttrpg_website2`/`aws_infra` project — it posts a message
to `ADMIN_CHAT_ID` whenever someone submits a new club membership request. It reuses this
bot's existing token (same SSM parameter, `Bot.send_message`), so no second bot is needed.

The stream ARN needs no manual wiring — `aws_infra`'s Terraform for
`ttrpg_club_signup_requests` publishes it to the SSM parameter
`/ttrpg_club/signup_requests_stream_arn`, which `lambda/ttrpg_poll_bot`'s Terraform reads
directly via a `data "aws_ssm_parameter"` block. Just make sure that table's Terraform
has been applied at least once before applying this one.

## Personal Stats Mini App (`/stats`)

Every `/rate` poll is non-anonymous, so Telegram sends this bot a `poll_answer` webhook
update whenever someone votes — the `webhook` function now records these (who rated
what, when) into two new DynamoDB tables managed by the `ttrpg_website2`/`aws_infra`
Terraform: `ttrpg_club_telegram_rating_polls` (which poll_id was rating which text, plus
who created it — see below) and `ttrpg_club_telegram_rating_votes` (the actual votes).
The "Подивитись відповідь" / view-results option (index 0) is never stored as a rating —
and neither is a **retracted** vote: if someone taps their selection again to deselect it,
or switches to "view results" after having voted, Telegram sends a `poll_answer` with
that new state, and the bot deletes any previously stored rating for them. This matters
because it's how "My Games Played" (below) decides who actually played a session.

Each poll's item also remembers who ran it (`creatorUserId` etc., captured from the
`/rate` command's sender) — that's the session's GM for stats purposes, and who gets
DMed detailed feedback (see the next section).

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
2. Apply with the resulting deep link:
   ```bash
   terraform apply \
     -var="admin_chat_id=$ADMIN_CHAT_ID" \
     -var="mini_app_deep_link=https://t.me/your_bot/stats"
   ```

Until `mini_app_deep_link` is set, `/stats` replies with a "temporarily unavailable"
message instead of a broken button.

The Mini App also has three navigation buttons under `/stats` — **My Games Played**,
**My Games Conducted**, **All Games** — each date-range filterable and drilling down
into a per-session voter breakdown. These read from the same two tables above (plus a
`creatorUserId-index` GSI on the polls table for "conducted") via new `POST
/telegram/games/*` endpoints on the club API — no bot changes needed for this part.

## Session Feedback (`?startapp=feedback_<pollId>`)

Alongside the quick 1-10 poll, every `/rate` also sends a second message with a
**"📝 Залишити фідбек"** button — a `t.me/<bot>/<app>?startapp=feedback_<pollId>` deep
link that opens the Mini App straight to that session's detailed feedback form (four
1-10 questions — adventure/story, table, GM, self — plus optional free text). This is
deliberately separate from the quick poll vote: it's a private, mostly-anonymous channel
for the GM, not part of the public rating/player-list bookkeeping above.

Feedback submissions are stored in a third new table, `ttrpg_club_telegram_feedback`
(also in `aws_infra`'s Terraform). Delivery to the GM works the same way as
`notifySignup`: a DynamoDB Stream on that table triggers this repo's `notifyFeedback`
function (`lambda_handler.notify_new_feedback`), which DMs the GM (looked up via the
poll's `creatorUserId`) with the feedback content — revealing the submitter's identity
only if they checked "reveal" in the form, otherwise the DM just says "Анонімно".

**Note**: a Telegram bot can only DM a user who has already started a private chat with
it at least once — if the GM never has, the DM silently fails (logged as a warning, not
an error) rather than crashing. If GMs report not receiving feedback, the fix is usually
just having them send `/start` to the bot in a private chat once.

Like the signup notifications above, this table's stream ARN needs no manual wiring —
`aws_infra`'s Terraform for `ttrpg_club_telegram_feedback` publishes it to the SSM
parameter `/ttrpg_club/telegram_feedback_stream_arn`, which `lambda/ttrpg_poll_bot`'s
Terraform reads directly. Just make sure that table's Terraform has been applied at
least once first.

## GitHub Actions Deployment

Pushing to `main` deploys automatically via `.github/workflows/deploy.yml` (or trigger it
by hand from the Actions tab — it also has `workflow_dispatch`): build the Python
package, zip it, and `aws lambda update-function-code` on all 3 functions — the same
OIDC pattern and the same "just push code" shape `ttrpg_website2`'s backend pipeline
uses (no CloudFormation/Serverless involved, so no `SERVERLESS_ACCESS_KEY` or similar is
needed here). One-time setup:

1. **Apply the infrastructure first** — `aws_infra/lambda/ttrpg_poll_bot` (see Setup
   above) — CI only ever updates code on functions that already exist.
2. **Apply the deploy role's Terraform** — `aws_infra/iam/github_actions_ttrpg_poll_bot`.
   A role dedicated to this repo (reuses the OIDC provider `ttrpg_website2`'s pipeline
   already created, but doesn't share its role). `terraform output deploy_role_arn`
   afterward gives you the value for the next step. If `AssumeRoleWithWebIdentity` fails
   with a `sub` claim mismatch, see that module's `variables.tf` comment — the same
   "immutable IDs" issue hit during `ttrpg_website2`'s setup can recur here since it's a
   different GitHub account.
3. **In this repo's GitHub Settings → Secrets and variables → Actions**, set secret
   `AWS_DEPLOY_ROLE_ARN` to the ARN from step 2.

This role is intentionally narrow — just `lambda:UpdateFunctionCode` +
`GetFunctionConfiguration` on this project's 3 functions, matching the website's own CI
role. All the broader stack-management permissions a CloudFormation-driven deploy would
have needed are gone now that Terraform owns the infrastructure directly.

## Cost

AWS Lambda free tier includes:
- 1M requests/month
- 400,000 GB-seconds of compute time/month

This bot should stay within free tier for moderate usage.
