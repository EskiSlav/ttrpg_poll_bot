#!/usr/bin/env python3
"""
Telegram Poll Bot
Sends a rating poll in response to any message
"""

import logging
from telegram import Update, Poll
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

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
        is_anonymous=False,  # Poll is not anonymous
        allows_multiple_answers=False
    )
    
    logger.info(f"Poll created by {update.effective_user.username}: {poll_question}")


def main() -> None:
    """Start the bot."""
    # Get bot token from environment variable or replace with your token
    import os
    import asyncio
    
    TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', 'YOUR_BOT_TOKEN_HERE')
    
    if TOKEN == 'YOUR_BOT_TOKEN_HERE':
        logger.error("Please set TELEGRAM_BOT_TOKEN environment variable or update the script with your token")
        return
    
    # Create the Application
    application = Application.builder().token(TOKEN).build()
    
    # Register handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("poll", create_poll))
    application.add_handler(CommandHandler("rate", create_poll))
    
    # Start the Bot
    logger.info("Bot is starting...")
    
    # Fix for Python 3.14 - create and set event loop manually
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        application.run_polling(allowed_updates=Update.ALL_TYPES)
    finally:
        loop.close()


if __name__ == '__main__':
    main()