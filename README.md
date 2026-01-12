# Telegram Poll Bot

A simple Telegram bot that creates rating polls from any message.

## Features

- Receives any text message
- Creates a non-anonymous poll with rating options (1-10)
- Uses emojis for each rating level
- First option is "Подивитись відповідь"

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Get your bot token from [@BotFather](https://t.me/botfather)

3. Set your bot token as environment variable:
```bash
export TELEGRAM_BOT_TOKEN="your_bot_token_here"
```

Or edit [main.py](main.py) line 63 to replace `YOUR_BOT_TOKEN_HERE` with your actual token.

## Run

```bash
python3 main.py
```

## Usage

1. Start the bot with `/start` command
2. Send any message (e.g., "oblivion")
3. Bot will create a poll with that message as the question
4. Poll shows rating options from 1/10 to 10/10 with emojis

## Poll Options

- Подивитись відповідь
- 1 / 10 🤬
- 2 / 10 😡
- 3 / 10 🥴
- 4 / 10 😞
- 5 / 10 🤔
- 6 / 10 🙂
- 7 / 10 😀
- 8 / 10 ☺️
- 9 / 10 🤩
- 10 / 10 🌟🌟🌟

The poll is **not anonymous** - you can see who voted for what.
