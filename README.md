# DiscoAI

Bot for Discord that automatically reads messages from a channel and replies using the **Gemini** API.

Monitors a Discord channel through HTTP polling, builds conversation context, and generates automatic responses in informal Portuguese, mimicking a real group member.

## Features

- Reads messages in real time from a specific Discord channel
- Generates responses with the **Gemini 2.5 Flash Lite** model
- Maintains conversation context (last 10 messages)
- Detects replies and direct mentions
- Detects images attached to messages
- Automatic rotation between multiple Gemini API keys
- 3-hour cooldown when all keys hit rate limits, with a notice sent to the channel
- Ignores its own messages, specific users, and media-heavy messages
- Colorful structured logs using `rich`

## Requirements

- Python 3.11+
- pip
- A Discord user token (self-bot)
- One or more Gemini API keys from [Google AI Studio](https://aistudio.google.com/)

> **Warning:** This project uses the Discord HTTP API with a *user* token (self-bot), which violates the [Discord Terms of Service](https://discord.com/terms). Use at your own risk.

## Installation

1. Clone the repository:

```bash
git clone https://github.com/flazo0/DiscoAI.git
cd DiscoAI
```

2. Create a virtual environment (optional, recommended):

```bash
python -m venv .venv
.venv\Scripts\activate   # Windows
source .venv/bin/activate  # Linux/macOS
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Set up your environment variables:

```bash
cp .env.exemple .env
```

## Configuration

Edit the `.env` file:

```env
DISCORD_TOKEN=your_discord_token
CHANNEL_ID=channel_id
GUILD_ID=server_id
USERNAME=your_discord_username
GEMINI_API_KEYS=key1,key2,key3
```

| Variable | Description |
|---|---|
| `DISCORD_TOKEN` | Discord authentication token |
| `CHANNEL_ID` | ID of the channel to monitor |
| `GUILD_ID` | ID of the server containing the channel |
| `USERNAME` | Your Discord username (prevents the bot from replying to itself) |
| `GEMINI_API_KEYS` | One or more Gemini keys, comma-separated (for rotation) |

> **Security:** Never share your token or keys. The `.env` file is already covered by `.gitignore`.

## Usage

```bash
python RunPy.py
```

The bot will:

1. Fetch the most recent messages from the channel
2. Skip messages from itself, blocked users, or messages without text
3. Build the conversation context and generate a response with Gemini
4. Send the response as a reply to the original message
5. Wait a random interval (10-20s) before the next cycle

## Customization

- **Response tone:** edit the prompt inside `ask_gemini_from_context()` in `RunPy.py`
- **Ignored users:** add conditions in the `loop()` function
- **Rate limit messages:** edit the `RATE_LIMIT_MESSAGES` list

## Project Structure

```
DiscoAI/
│
├─ RunPy.py           # Main bot script
├─ requirements.txt   # Dependencies
├─ .env.exemple       # Configuration template
├─ .gitignore         # Files ignored by git
├─ LICENSE            # Apache 2.0 license
└─ README.md
```

## Contributing

Pull requests are welcome. Suggested improvements:

- Response style and personality
- Rate limit handling
- Polling loop optimization
- Migration to the Discord WebSocket (gateway) API

## License

Distributed under the **Apache 2.0** license. See the [LICENSE](LICENSE) file for details.
