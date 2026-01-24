# Kodak

A Discord bot that maps your belief network through engaging conversation.

Kodak has natural, curious conversations with you—and along the way, builds a map of what you believe and why. Think of it like a mirror for your mind.

## What It Does

- **Extracts beliefs** from natural conversation (you don't have to do anything special)
- **Tracks confidence levels** based on how certain you sound
- **Finds connections** between your beliefs over time
- **Lets you explore** your belief map with `/map` and `/explore [topic]`
- **Respects privacy** — all data is per-user, you can pause, export, or delete anytime

## Reading Your Belief Map

### Confidence Indicators

Each belief shows a confidence level based on how certain you sounded:

```
[●●●●●] 100% — Very certain ("I absolutely believe...")
[●●●●○]  80% — Confident ("I think...", stated directly)
[●●●○○]  60% — Moderate ("I feel like...", "probably...")
[●●○○○]  40% — Tentative ("maybe...", "I'm not sure but...")
[●○○○○]  20% — Uncertain ("I guess...", implied beliefs)
```

### The Map View

When you run `/map`, you'll see beliefs grouped by topic:

```
──────────────────────────────
  CAREER
──────────────────────────────
  [●●●●○] Your belief statement here...
```

Use `/explore [topic]` to dive deeper into any topic, or `/beliefs` to see the raw list with IDs.

## Commands

| Command | Description |
|---------|-------------|
| `/help` | See all commands |
| `/map` | View your belief map |
| `/explore [topic]` | Dive into beliefs about a topic |
| `/beliefs` | Raw list with IDs |
| `/belief [id]` | View one belief with its connections |
| `/setup` | Choose a personality preset |
| `/style` | Fine-tune personality (warmth, playfulness, etc.) |
| `/forget [id]` | Delete a belief (use `last` for most recent) |
| `/pause` | Pause belief tracking |
| `/resume` | Resume tracking |
| `/export` | Download all your data as JSON |
| `/clear` | Delete everything |

## Personality Presets

- 🏛️ **The Philosopher** — Thoughtful and probing
- 💛 **The Best Friend** — Warm and fun
- 🔬 **The Scientist** — Precise and analytical
- 🃏 **The Trickster** — Playful and irreverent
- 🌿 **The Therapist** — Empathetic and safe

## Deploy Your Own

### Prerequisites

- Python 3.12+
- Discord Bot Token ([create one here](https://discord.com/developers/applications))
- Anthropic API Key ([get one here](https://console.anthropic.com/))

### Local Development

```bash
git clone https://github.com/ericmagro/kodak.git
cd kodak
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Add your tokens
cp .env.example .env
# Edit .env with your tokens

# Run
cd src && python bot.py
```

### Deploy to Railway

1. Fork this repo
2. Create a new project on [Railway](https://railway.app)
3. Connect your GitHub repo
4. Add environment variables:
   - `DISCORD_TOKEN`
   - `ANTHROPIC_API_KEY`
5. Deploy

### Discord Bot Setup

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Create New Application → name it "Kodak"
3. Go to Bot → Reset Token → Copy it
4. Enable **Message Content Intent** under Privileged Gateway Intents
5. Go to OAuth2 → URL Generator
   - Scopes: `bot`, `applications.commands`
   - Permissions: Send Messages, Embed Links, Attach Files, Read Message History, Use Slash Commands
6. Use the generated URL to invite the bot to your server

## Cost Considerations

Kodak uses the Anthropic API for:
- Generating responses (1 call per message)
- Extracting beliefs (1 call per message, runs in parallel)
- Summarizing beliefs (1 call per `/map` or `/explore`)

Rough estimate: ~$0.01-0.02 per conversation turn using Claude Sonnet.

## How to Use

**DMs (recommended for belief mapping):**
- Just DM the bot directly
- Private conversations, better for deep exploration
- Your beliefs stay completely private

**Channels:**
- @mention the bot to chat
- Good for casual group discussions
- Beliefs are still extracted per-user

## Privacy

- All belief data is stored per-user
- Only you can see your beliefs (commands are ephemeral)
- Command responses disappear after a while (use `/export` to save)
- Use `/pause` to chat without tracking
- Use `/export` to download your data
- Use `/clear` to delete everything

## License

MIT

## Credits

Built with [discord.py](https://discordpy.readthedocs.io/) and [Anthropic Claude](https://anthropic.com).
