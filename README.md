# Kodak

A Discord bot that notices what you keep coming back to.

Most people can't articulate what they actually care about. Ask them and you get generic answers: "family, honesty, success." Kodak surfaces what you *really* keep returning to—by paying attention over time.

**What makes it different:**
- **Just talk naturally** — Kodak notices patterns in what you share
- **Surfaces themes over time** — See what you keep coming back to across weeks and months
- **Honest, not sycophantic** — Kodak will notice contradictions and push back on your ideas
- **Your data, your control** — Self-hosted, open source, exportable

## What a Session Looks Like

```
Kodak: What's been sitting with you today?

You: Work stuff. My manager announced a reorg and I might
     have to move teams. I'm not even sure I'm upset about
     it but I can't stop thinking about it.

Kodak: What is it about the uncertainty that's hard to let go of?

You: I think it's that I finally felt like I knew what I was
     doing. Now I might have to start over proving myself again.

Kodak: That's interesting—it sounds less about the team and
       more about losing a sense of competence you'd built up.
       Is that fair?

You: Yeah, actually. I hadn't thought of it that way.
```

Sessions adapt to your energy. Share a lot and Kodak goes deeper. Keep it brief and it wraps up quickly.

## Core Features

| Feature | What it does |
|---------|--------------|
| **Daily check-ins** | Thoughtful prompts at a time you choose |
| **Pattern recognition** | Notices themes from natural conversation, shows supporting quotes and confidence levels |
| **Weekly summaries** | What you kept coming back to, shifts in emphasis |
| **Milestone celebrations** | Encouraging messages at 5, 15, 20, 50 sessions |
| **Comparison** | Share your themes with someone, explore where you align and differ |
| **Personality presets** | Choose your conversational style (philosopher, therapist, trickster, etc.) |

## Privacy

- **Stored locally** — All your data lives in a local SQLite database you control
- **Processed by Anthropic** — Conversations are sent to Claude for responses (see [Anthropic's privacy policy](https://www.anthropic.com/privacy))
- `/export` to download everything as JSON
- `/clear` to delete all your data
- `/pause` to chat without belief tracking

## Commands

### Getting Started
| Command | Description |
|---------|-------------|
| `/journal` | Start a session right now |
| `/schedule [time]` | Set your daily check-in time |
| `/themes` | See patterns Kodak has noticed, with quotes from your conversations |
| `/summary week` | Get your weekly digest |
| `/help` | See all commands |

### Beliefs
| Command | Description |
|---------|-------------|
| `/map` | View beliefs organized by topic |
| `/beliefs` | List all beliefs with IDs |
| `/belief [id]` | View one belief in detail |
| `/explore [topic]` | Dive into a specific topic |
| `/core` | Show your most important beliefs |
| `/tensions` | Find potentially conflicting beliefs |
| `/history [id]` | See how a belief has evolved over time |
| `/changes` | See beliefs that have changed recently |
| `/confidence [id] [1-5]` | Update your confidence in a belief |
| `/mark [id] [1-5]` | Mark how important a belief is to you |
| `/forget [id]` | Delete a belief you no longer hold |
| `/undo` | Restore the last forgotten belief |

### Themes & Summaries
| Command | Description |
|---------|-------------|
| `/themes` (or `/values`) | See patterns Kodak has noticed |
| `/themes-history` (or `/values-history`) | See how your themes have shifted |
| `/summary week` | Weekly digest with patterns and insights |
| `/summaries` | View past summaries |
| `/share-themes` (or `/share-values`) | Export your themes to share |
| `/compare-file` | Compare with someone's export |

### Scheduling & Preferences
| Command | Description |
|---------|-------------|
| `/schedule [time]` | Set daily check-in time |
| `/timezone [tz]` | Set your timezone |
| `/skip` | Skip today's check-in |
| `/pause` / `/resume` | Pause or resume check-ins |
| `/setup` | Choose a personality preset |
| `/style` | Fine-tune personality dimensions |
| `/depth` | Set session depth (quick/standard/deep) |

### Data Management
| Command | Description |
|---------|-------------|
| `/export` | Download all your data (JSON) |
| `/clear` | Delete everything |

## Personality Presets

Choose how Kodak shows up:

- **The Philosopher** — Probing, asks "why," examines assumptions
- **The Best Friend** — Warm, honest, supportive
- **The Scientist** — Precise, analytical, evidence-focused
- **The Trickster** — Playful, irreverent, challenges you
- **The Therapist** — Gentle, safe, never pushes

## How It Works

Kodak pays attention to your conversations over time and surfaces patterns:

- **Themes** you keep returning to (accomplishment, connection, freedom, security, etc.)
- **Shifts** in what you emphasize week to week
- **Tensions** where your stated beliefs might contradict each other

Think of it as a curious friend who occasionally says "hey, have you noticed you keep talking about X?"

## Run Your Own

### Railway (Recommended)
Always-on cloud hosting (~$5/month):
1. Fork this repo
2. Connect to Railway
3. Add a volume mounted at `/data`
4. Set environment variables: `DISCORD_TOKEN`, `ANTHROPIC_API_KEY`, `KODAK_DB_PATH=/data/kodak.db`

### Local
Free, but only runs while your computer is on:
```bash
git clone https://github.com/ericmagro/kodak.git
cd kodak
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # Add your tokens
cd src && python bot.py
```

**[Full setup guide →](SETUP.md)**

## Cost

Each message costs ~$0.01-0.02 (Anthropic API). A typical daily session runs $0.05-0.20.

## Design Philosophy

Kodak is designed to be a curious thinking partner, not a yes-man.

Most AI assistants validate everything you say. This feels good but doesn't help you grow. Kodak engages honestly—noticing patterns, questioning assumptions, sometimes pointing out contradictions.

The goal isn't to tell you who you are. It's to help you notice what you keep coming back to, and whether that serves you.

## License

MIT

## Credits

Built with [discord.py](https://discordpy.readthedocs.io/) and [Anthropic Claude](https://anthropic.com).
