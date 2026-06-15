# Telegram Banking Chatbot

A Python-based Telegram chatbot that simulates core digital banking workflows. This repository is presented as a technical assessment and portfolio project, with a focus on conversational UX, simple authentication, SQLite persistence, Docker support, and an optional OpenAI integration for general banking questions.

## Overview

The bot lets a demo user authenticate with a PIN, check their account balance, review recent transactions, and simulate a personal loan. It also detects common banking intents from natural language messages and can use OpenAI to answer general questions about banking products when `OPENAI_API_KEY` is configured.

## Features

- PIN-based demo authentication.
- Balance lookup backed by SQLite.
- Recent transaction history.
- Personal loan simulation with a dynamic interest-rate adjustment based on user interactions.
- Natural language intent detection for balance, transactions, and loans.
- Optional OpenAI-powered responses for general banking questions.
- Docker-ready runtime.
- Environment-based configuration with no secrets committed to the repository.

## Tech Stack

- Python 3.10
- python-telegram-bot 20.6
- OpenAI Python SDK 1.14.3
- python-dotenv
- SQLite
- Docker

## Architecture

```text
.
|-- main.py          # Telegram bot handlers, authentication flow, and command routing
|-- ai.py            # Intent detection and optional OpenAI integration
|-- db.py            # SQLite schema and data-access functions
|-- logic.py         # Loan calculation and currency formatting
|-- data/            # Runtime SQLite database location
|-- Dockerfile       # Container image definition
`-- requirements.txt # Python dependencies
```

Runtime data is stored in `data/banco.db`. The database file is generated automatically when the bot starts and is intentionally ignored by Git.

## Environment Variables

Create a `.env` file based on `.env.example`.

```env
TELEGRAM_TOKEN=your_telegram_bot_token_here
OPENAI_API_KEY=your_openai_api_key_here
```

| Variable | Required | Description |
| --- | --- | --- |
| `TELEGRAM_TOKEN` | Yes | Telegram Bot API token generated with BotFather. The app stops with a clear error if this value is missing. |
| `OPENAI_API_KEY` | No | Enables general banking Q&A through OpenAI. If omitted, the bot still runs and returns a controlled message for general AI questions. |

## Local Setup

1. Clone the repository.

```bash
git clone <repository-url>
cd python-banking-chatbot
```

2. Create and activate a virtual environment.

```bash
python -m venv .venv
.venv\Scripts\activate
```

On macOS or Linux:

```bash
python -m venv .venv
source .venv/bin/activate
```

3. Install dependencies.

```bash
pip install -r requirements.txt
```

4. Configure environment variables.

```bash
copy .env.example .env
```

On macOS or Linux:

```bash
cp .env.example .env
```

Then edit `.env` and set `TELEGRAM_TOKEN`. `OPENAI_API_KEY` is optional.

5. Run the bot.

```bash
python main.py
```

## Docker Setup

Build the image:

```bash
docker build -t telegram-banking-chatbot .
```

Run the container with your `.env` file and a mounted data directory:

```bash
docker run --rm --name telegram-banking-chatbot --env-file .env -v ${PWD}/data:/app/data telegram-banking-chatbot
```

On Windows PowerShell, use:

```powershell
docker run --rm --name telegram-banking-chatbot --env-file .env -v ${PWD}/data:/app/data telegram-banking-chatbot
```

## Available Commands

- `/start` - Start or restart the bot and begin authentication.
- `/saldo` - Show the current account balance.
- `/movimientos` - Show recent account transactions.
- `/prestamo` - Start the personal loan simulation flow.
- `/cancelar` - Cancel the active loan simulation flow.
- `/ayuda` - Show help and example questions.

The bot also understands natural language messages such as:

- "Cuanto tengo en mi cuenta?"
- "Mostrame los ultimos movimientos"
- "Necesito un prestamo"
- "Que tarjetas ofrecen?"

## Default Demo PIN

The default demo PIN is:

```text
1234
```

When a new Telegram user starts the bot, the app creates a local demo profile with simulated initial movements and a starting balance derived from those movements.
