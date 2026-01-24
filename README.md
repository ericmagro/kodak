# Kodak

A Discord bot that reveals what you actually value—through daily conversation.

Most people can't articulate their values. Ask them and you get generic answers: "family, honesty, success." Kodak surfaces what you *really* prioritize by extracting beliefs from your reflections and mapping them to a validated psychological framework.

**What makes it different:**
- **Automatic belief extraction** — Just talk naturally; Kodak identifies the beliefs underneath
- **Real psychological framework** — Uses [Schwartz's 10 Basic Human Values](https://en.wikipedia.org/wiki/Theory_of_Basic_Human_Values), used in cross-cultural research worldwide
- **Tracks change over time** — See how your values shift across weeks and months
- **Honest, not sycophantic** — Kodak will notice contradictions and push back on your ideas

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
| **Belief extraction** | Surfaces what you believe from natural conversation |
| **Value profiling** | Maps beliefs to Schwartz's 10 values |
| **Weekly summaries** | Patterns, themes, and value shifts from your week |
| **Value comparison** | Share your profile to see how you align with others |
| **Personality presets** | Choose your conversational style (philosopher, therapist, trickster, etc.) |

## Privacy First

- All data stored locally—journal entries never leave your machine
- `/export` to download everything as JSON
- `/clear` to delete all your data
- `/pause` to chat without belief tracking

## Commands

### Getting Started
| Command | Description |
|---------|-------------|
| `/journal` | Start a session right now |
| `/schedule [time]` | Set your daily check-in time |
| `/values` | See your value profile |
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

### Values & Summaries
| Command | Description |
|---------|-------------|
| `/values` | See your current value profile |
| `/values-history` | See how values shifted over time |
| `/summary week` | Weekly digest with patterns and insights |
| `/summaries` | View past summaries |
| `/share-values` | Export your values to share |
| `/compare-file` | Compare with someone's export |

### Scheduling & Preferences
| Command | Description |
|---------|-------------|
| `/schedule [time]` | Set daily check-in time |
| `/timezone [tz]` | Set your timezone |
| `/skip` | Skip today's check-in |
| `/pause` / `/resume` | Pause or resume check-ins |
| `/setup` | Choose a personality preset |
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

## The Values Framework

Kodak uses Schwartz's 10 Basic Human Values—a research-backed framework used in psychology worldwide:

| Value | What it means |
|-------|---------------|
| Self-Direction | Independence, creativity, freedom |
| Stimulation | Excitement, novelty, challenge |
| Hedonism | Pleasure, enjoying life |
| Achievement | Success, competence, ambition |
| Power | Authority, wealth, social status |
| Security | Safety, stability, order |
| Conformity | Obedience, self-discipline |
| Tradition | Respect for customs, humility |
| Benevolence | Helping those close to you |
| Universalism | Tolerance, social justice for all |

Your beliefs are automatically tagged with relevant values. Over time, this builds a profile of what you actually prioritize—not what you think you should value.

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

Kodak is designed to be a genuine thinking partner, not a yes-man.

Most AI assistants validate everything you say. This feels good but doesn't help you grow. Kodak engages honestly—noticing contradictions, questioning assumptions, sometimes disagreeing.

The goal isn't to make you feel good about what you believe. It's to help you see what you *actually* believe, and whether those beliefs serve you.

## License

MIT

## Credits

Built with [discord.py](https://discordpy.readthedocs.io/) and [Anthropic Claude](https://anthropic.com).
