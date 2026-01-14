# Telegram Poll Bot

A simple Telegram bot that creates rating polls from any message.

## Features

- `/poll` or `/rate` commands create rating polls (1-10)
- `/bool` command creates Yes/No polls
- All polls are non-anonymous
- Rating polls use emojis for each level
- First option in rating polls is "Подивитись відповідь"

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

### Rating Polls

1. Use `/poll <text>` or `/rate <text>`
2. Example: `/poll oblivion`
3. Bot creates a poll with rating options 1-10

### Yes/No Polls

1. Use `/bool <question>`
2. Example: `/bool Це правда?`
3. Bot creates a poll with "Так" and "Ні" options

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
