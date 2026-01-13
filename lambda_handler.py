#!/usr/bin/env python3
"""
Telegram Poll Bot - Lambda Handler
Runs as AWS Lambda function with webhook
"""

import json
import logging
import os
import boto3
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, ContextTypes

# Setup logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Poll options
POLL_OPTIONS = [
    "Подивитись відповідь",
    "1 / 10 🤬",
    "2 / 10 😡",
    "3 / 10 🥴",
    "4 / 10 😞",
    "5 / 10 🤔",
    "6 / 10 🙂",
    "7 / 10 😀",
    "8 / 10 ☺️",
    "9 / 10 🤩",
    "10 / 10 🌟🌟🌟"
]

# Cache for bot token and application state
_bot_token = None
_application = None
_initialized = False


def get_bot_token():
    """Fetch bot token from SSM Parameter Store."""
    global _bot_token
    
    if _bot_token:
        return _bot_token
    
    ssm = boto3.client('ssm', region_name=os.environ.get('AWS_REGION', 'eu-west-2'))
    parameter_name = os.environ.get('TELEGRAM_TOKEN_SSM_PARAMETER', '/telegram/poll_bot/token')
    
    try:
        response = ssm.get_parameter(Name=parameter_name, WithDecryption=True)
        _bot_token = response['Parameter']['Value']
        logger.info(f"Successfully retrieved token from SSM: {parameter_name}")
        return _bot_token
    except Exception as e:
        logger.error(f"Failed to get SSM parameter {parameter_name}: {e}")
        raise


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    await update.message.reply_text(
        'Привіт! Використовуйте /poll <текст> або /rate <текст> щоб створити опитування.'
    )


async def create_poll(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Create a poll from /poll or /rate command."""
    # Get text after the command
    if not context.args:
        await update.message.reply_text(
            'Будь ласка, додайте текст після команди. Наприклад: /poll oblivion'
        )
        return
    
    # Join all arguments to create the poll question
    poll_question = "Оцінка (" + ' '.join(context.args) + ")"
    
    # Send poll to the chat (not as a reply)
    await context.bot.send_poll(
        chat_id=update.effective_chat.id,
        question=poll_question,
        options=POLL_OPTIONS,
        is_anonymous=False,
        allows_multiple_answers=False
    )
    
    logger.info(f"Poll created by {update.effective_user.username}: {poll_question}")


def get_application():
    """Get or create the Application instance."""
    global _application
    
    if _application:
        return _application
    
    token = get_bot_token()
    
    # Create application
    _application = Application.builder().token(token).build()
    
    # Register handlers
    _application.add_handler(CommandHandler("start", start))
    _application.add_handler(CommandHandler("poll", create_poll))
    _application.add_handler(CommandHandler("rate", create_poll))
    
    return _application


async def process_update(event):
    """Process incoming webhook update."""
    global _initialized
    
    try:
        application = get_application()
        
        # Initialize application only once
        if not _initialized:
            await application.initialize()
            await application.start()
            _initialized = True
        
        # Parse update from webhook
        update = Update.de_json(json.loads(event['body']), application.bot)
        
        # Process the update
        await application.process_update(update)
        
        return {
            'statusCode': 200,
            'body': json.dumps({'status': 'ok'})
        }
    except Exception as e:
        logger.error(f"Error processing update: {e}", exc_info=True)
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }


def lambda_handler(event, context):
    """AWS Lambda handler function."""
    import asyncio
    
    logger.info(f"Received event: {json.dumps(event)}")
    
    # Handle webhook verification (optional)
    if event.get('httpMethod') == 'GET':
        return {
            'statusCode': 200,
            'body': json.dumps({'status': 'Bot is running'})
        }
    
    # Process webhook update
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        response = loop.run_until_complete(process_update(event))
        return response
    finally:
        loop.close()


# For setting webhook (run locally)
if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python lambda_handler.py <webhook_url>")
        sys.exit(1)
    
    webhook_url = sys.argv[1]
    token = get_bot_token()
    bot = Bot(token=token)
    
    import asyncio
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        result = loop.run_until_complete(bot.set_webhook(url=webhook_url))
        print(f"Webhook set: {result}")
        
        webhook_info = loop.run_until_complete(bot.get_webhook_info())
        print(f"Webhook info: {webhook_info}")
    finally:
        loop.close()
