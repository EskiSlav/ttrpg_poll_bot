#!/usr/bin/env python3
"""
Telegram Poll Bot - Lambda Handler
Simple implementation using Telegram Bot API directly
"""

import json
import logging
import os
import boto3
import requests

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


class User:
    def __init__(self, user: dict) -> None:
        self.id: int = user.get('id')
        self.is_bot: bool = user.get('is_bot', False)
        self.first_name: str = user.get('first_name', '')
        self.last_name: str = user.get('last_name', '')
        self.username: str = user.get('username', '')
        self.language_code: str = user.get('language_code', '')

    def __repr__(self) -> str:
        return str(self.__dict__)


class Chat:
    def __init__(self, chat: dict) -> None:
        self.id: int = chat.get('id')
        self.first_name: str = chat.get('first_name', '')
        self.last_name: str = chat.get('last_name', '')
        self.username: str = chat.get('username', '')
        self.type: str = chat.get('type', '')

    def __repr__(self) -> str:
        return str(self.__dict__)


class Message:
    def __init__(self, message: dict) -> None:
        self.from_user = User(message.get('from', {}))
        self.chat = Chat(message.get('chat', {}))
        self.date: int = message.get('date')
        self.text: str = message.get('text', '')
        self.entities: list = message.get('entities', [])

    def get_command(self) -> str:
        """Extract command from message if present."""
        if self.entities and self.entities[0].get('type') == 'bot_command':
            return self.text.split()[0]
        return ''

    def get_command_args(self) -> str:
        """Get text after command."""
        if self.get_command():
            parts = self.text.split(maxsplit=1)
            return parts[1] if len(parts) > 1 else ''
        return ''

    def __repr__(self) -> str:
        return str(self.__dict__)


class Update:
    def __init__(self, update: dict) -> None:
        self.update_id = update.get('update_id')
        self.message = Message(update.get('message', {})) if 'message' in update else None

    def __repr__(self) -> str:
        return str(self.__dict__)


class Bot:
    """Simple Telegram Bot API client."""
    
    def __init__(self, token: str = None) -> None:
        if token is None:
            token = self._get_token_from_ssm()
        
        self.token = token
        self.session = requests.Session()
        self.api_url = f'https://api.telegram.org/bot{self.token}/'

    @staticmethod
    def _get_token_from_ssm() -> str:
        """Fetch bot token from SSM Parameter Store."""
        ssm = boto3.client('ssm', region_name=os.environ.get('AWS_REGION', 'eu-west-2'))
        parameter_name = os.environ.get('TELEGRAM_TOKEN_SSM_PARAMETER', '/telegram/poll_bot/token')
        
        try:
            response = ssm.get_parameter(Name=parameter_name, WithDecryption=True)
            token = response['Parameter']['Value']
            logger.info(f"Successfully retrieved token from SSM: {parameter_name}")
            return token
        except Exception as e:
            logger.error(f"Failed to get SSM parameter {parameter_name}: {e}")
            raise

    def send_message(self, chat_id: int, text: str) -> int:
        """Send text message to chat."""
        url = self.api_url + 'sendMessage'
        json_data = {
            'chat_id': chat_id,
            'text': text,
        }
        logger.debug(f'Sending message: {json_data}')
        response = self.session.post(url=url, json=json_data)
        logger.info(f'Sent message to {chat_id}')
        logger.debug(f'{response.status_code=} {response.text=}')
        
        return response.status_code

    def send_poll(
        self, 
        chat_id: int, 
        question: str, 
        options: list,
        is_anonymous: bool = False,
        allows_multiple_answers: bool = False
    ) -> int:
        """Send poll to chat."""
        url = self.api_url + 'sendPoll'
        json_data = {
            'chat_id': chat_id,
            'question': question,
            'options': options,
            'is_anonymous': is_anonymous,
            'allows_multiple_answers': allows_multiple_answers,
        }
        logger.debug(f'Sending poll: {json_data}')
        response = self.session.post(url=url, json=json_data)
        logger.info(f'Sent poll to {chat_id}: {question}')
        logger.debug(f'{response.status_code=} {response.text=}')
        
        return response.status_code


def handle_start_command(bot: Bot, update: Update):
    """Handle /start command."""
    bot.send_message(
        update.message.chat.id,
        'Привіт! Використовуйте /poll <текст> або /rate <текст> щоб створити опитування.'
    )


def handle_poll_command(bot: Bot, update: Update):
    """Handle /poll and /rate commands."""
    args = update.message.get_command_args()
    
    if not args:
        bot.send_message(
            update.message.chat.id,
            'Будь ласка, додайте текст після команди. Наприклад: /poll oblivion'
        )
        return
    
    # Create poll question
    poll_question = f"Оцінка ({args})"
    
    # Send poll
    bot.send_poll(
        chat_id=update.message.chat.id,
        question=poll_question,
        options=POLL_OPTIONS,
        is_anonymous=False,
        allows_multiple_answers=False
    )
    
    logger.info(f"Poll created by {update.message.from_user.username}: {poll_question}")


def update_handler(update: Update):
    """Process incoming update."""
    if not update.message:
        logger.warning("Update without message received")
        return
    
    bot = Bot()
    command = update.message.get_command()
    
    logger.info(f"Received command: {command} from user {update.message.from_user.username}")
    
    if command == '/start':
        handle_start_command(bot, update)
    elif command in ['/poll', '/rate']:
        handle_poll_command(bot, update)
    else:
        # Unknown command or regular message - ignore
        logger.debug(f"Ignoring message: {update.message.text}")


def lambda_handler(event, context):
    """AWS Lambda handler function."""
    logger.info(f"Received event: {json.dumps(event)}")
    
    # Handle webhook verification (optional)
    if event.get('httpMethod') == 'GET':
        return {
            'statusCode': 200,
            'body': json.dumps({'status': 'Bot is running'})
        }
    
    try:
        update = Update(json.loads(event['body']))
        update_handler(update)
    except Exception as e:
        logger.error(f"Error processing update: {e}", exc_info=True)
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
    
    return {
        'statusCode': 200,
        'body': json.dumps({'status': 'ok'})
    }


# For setting webhook (run locally)
if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python lambda_handler.py <webhook_url>")
        sys.exit(1)
    
    webhook_url = sys.argv[1]
    bot = Bot()
    
    # Set webhook
    url = bot.api_url + 'setWebhook'
    response = bot.session.post(url=url, json={'url': webhook_url})
    print(f"Webhook set: {response.status_code} - {response.text}")
    
    # Get webhook info
    url = bot.api_url + 'getWebhookInfo'
    response = bot.session.get(url=url)
    print(f"Webhook info: {response.text}")
