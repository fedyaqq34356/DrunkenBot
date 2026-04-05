# 🍺 DrunkenBot

> *A Telegram chatbot that talks like a drunk 45-year-old man at a bar. Short, rude, philosophical, and unexpectedly real.*

---

## What is this?

**DrunkenBot** is an AI-powered Telegram bot with a very specific personality: a heavily intoxicated middle-aged Russian man. He swears constantly, loses his train of thought, occasionally drops unexpected wisdom, and never pretends to be an AI.

Built with `aiogram` and `g4f` (GPT4Free), it runs fully for free — no paid API keys required.

---

## Features

- 🤬 **Authentic drunk persona** — rude, chaotic, slurred speech, heavy Russian profanity
- 🧠 **Persistent memory** — remembers conversation history per user (stored as JSON)
- 🎨 **AI image generation** — `/image <prompt>` generates images with a drunken commentary
- 🔄 **Session reset** — `/reset` to wipe memory and start fresh
- 📋 **Rotating logs** — structured logging with file rotation
- ⚡ **Async** — fully async with `aiogram` and `aiohttp`

---

## Commands

| Command | Description |
|---|---|
| `/start` | Wake the drunk up. Start a new conversation. |
| `/reset` | He forgets you. Clean slate. |
| `/image <prompt>` | Ask him to draw something. Results vary. |
| *any text* | Just talk to him. He'll respond. Somehow. |

---

## Tech Stack

- **Python 3.11+**
- **aiogram 3** — Telegram Bot framework
- **g4f (GPT4Free)** — Free AI completions & image generation
- **aiohttp** — Async HTTP
- **python-dotenv** — Environment config

---

## Installation

```bash
# Clone the repo
git clone https://github.com/yourusername/drunkenbot.git
cd drunkenbot

# Install dependencies
pip install -r requirements.txt

# Create .env file
echo 'BOT_TOKEN = your_telegram_bot_token_here' > .env

# Run
python main.py
```

---

## Configuration

Create a `.env` file in the project root:

```env
BOT_TOKEN = your_telegram_bot_token_here
```

Get your token from [@BotFather](https://t.me/BotFather) on Telegram.

---

## Running as a systemd service

```ini
[Unit]
Description=DrunkenBot
After=network.target

[Service]
WorkingDirectory=/path/to/drunkenbot
ExecStart=/usr/bin/python3 main.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
systemctl enable drunkenbot
systemctl start drunkenbot
```

---

## Project Structure

```
drunkenbot/
├── main.py          # Bot entry point, handlers
├── ai.py            # AI generation logic (text + images)
├── config.py        # Environment config
├── logger.py        # Logging setup
├── requirements.txt
├── .env             # Your token (never commit this)
└── history/         # Per-user conversation history (auto-created)
```

---

## License

GNU GENERAL PUBLIC LICENSE

---

*Made with ❤️ and a little too much vodka*

*If you found this useful or it made you laugh — please consider giving it a ⭐ star on GitHub. It means a lot!*