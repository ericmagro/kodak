# Kodak

A Discord bot that helps you understand yourself through daily journaling.

Kodak is a reflective journaling companion. Each day at a time you choose, it checks in with a thoughtful prompt. Through natural conversation, it helps you explore what's on your mind—and over time, surfaces patterns in what you value.

## What It Does

- **Daily check-ins** at a time you choose (evening works best for most people)
- **Adaptive sessions** that follow your energy—quick check-ins or deep exploration
- **Extracts beliefs** from your reflections (you don't have to do anything special)
- **Derives values** using Schwartz's 10 Basic Human Values framework
- **Tracks change** — see how your values shift over weeks and months
- **Enables comparison** — share your value profile with friends to see how you align

## The Session Flow

When Kodak checks in, a typical session looks like:

1. **Opener** — A thoughtful prompt to get you reflecting
2. **Exploration** — Follow-up questions that go deeper (adapts to your response length)
3. **Closure** — A gentle wrap-up, sometimes surfacing beliefs it noticed

Sessions adapt: share a lot and Kodak will explore further; keep it brief and it wraps up quickly.

## Commands

### Scheduling
| Command | Description |
|---------|-------------|
| `/schedule [time]` | Set your daily check-in time |
| `/skip` | Skip today's check-in |
| `/pause` | Pause all check-ins |
| `/resume` | Resume check-ins |
| `/journal` | Start a session right now |
| `/timezone [tz]` | Set your timezone |

### Personality
| Command | Description |
|---------|-------------|
| `/setup` | Choose a personality preset |
| `/depth` | Set session depth (quick/standard/deep) |
| `/style` | View your personality dimensions |

### Beliefs
| Command | Description |
|---------|-------------|
| `/map` | View your belief map by topic |
| `/beliefs` | Raw list with IDs |
| `/belief [id]` | View one belief in detail |
| `/explore [topic]` | Dive into beliefs about a topic |
| `/core` | Show your most important beliefs |

### Edit Beliefs
| Command | Description |
|---------|-------------|
| `/confidence [id] [level]` | Update how certain you are |
| `/mark [id] [1-5]` | Set how important a belief is |
| `/forget [id]` | Delete a belief |
| `/undo` | Restore last deleted belief |

### History & Analysis
| Command | Description |
|---------|-------------|
| `/history [id]` | See how a belief has evolved |
| `/changes [days]` | See beliefs that changed recently |
| `/tensions` | Show potentially conflicting beliefs |

### Values
| Command | Description |
|---------|-------------|
| `/values` | See your value profile |
| `/values-history` | See how values shifted over time |
| `/share-values` | Export your values to share |
| `/compare-file` | Compare with someone's export |

### Privacy & Data
| Command | Description |
|---------|-------------|
| `/export` | Download all your data (JSON) |
| `/clear` | Delete everything |

## Personality Presets

Choose how Kodak shows up in your conversations:

- **The Philosopher** — Thoughtful, probing, asks "why"
- **The Best Friend** — Warm, honest, supportive
- **The Scientist** — Precise, analytical, evidence-focused
- **The Trickster** — Playful, irreverent, challenges assumptions
- **The Therapist** — Empathetic, safe, never pushes

## Values Framework

Kodak uses Schwartz's 10 Basic Human Values to understand what matters to you:

| Value | Description |
|-------|-------------|
| Universalism | Tolerance, social justice, equality |
| Benevolence | Helpfulness, honesty, loyalty to close others |
| Tradition | Respect for customs, humility |
| Conformity | Obedience, self-discipline, politeness |
| Security | Safety, stability, social order |
| Achievement | Success, competence, ambition |
| Power | Authority, wealth, recognition |
| Self-Direction | Creativity, freedom, independence |
| Stimulation | Excitement, novelty, challenge |
| Hedonism | Pleasure, enjoying life |

Your beliefs are tagged with relevant values, and over time Kodak builds a profile of what you prioritize.

## Run Your Own

Two options:

### Railway (Recommended)
Deploy to Railway for always-on hosting (~$5/month):
1. Fork this repo
2. Connect to Railway
3. Add a volume mounted at `/data`
4. Set environment variables: `DISCORD_TOKEN`, `ANTHROPIC_API_KEY`, `KODAK_DB_PATH=/data/kodak.db`

### Local
Run on your own computer (free, but only works while running):

```bash
git clone https://github.com/ericmagro/kodak.git
cd kodak
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your tokens
cd src && python bot.py
```

**[Full setup guide →](SETUP.md)**

## Cost

Each message costs ~$0.01-0.02 (Anthropic API). A typical daily session might cost $0.05-0.20.

## Privacy

- All data stored locally in `kodak.db` on your computer
- Journal entries never leave your machine
- Value exports only include what you choose to share
- `/pause` to chat without tracking
- `/export` to download your data
- `/clear` to delete everything

## Design Philosophy

Kodak is designed to be a genuine companion, not a sycophant. It won't validate everything you say—it'll engage honestly, notice contradictions, and sometimes disagree.

This is intentional. Research shows sycophantic AI makes people more certain and less open. Kodak aims for the opposite: helping you understand yourself more clearly, including the parts that are messy or contradictory.

## License

MIT

## Credits

Built with [discord.py](https://discordpy.readthedocs.io/) and [Anthropic Claude](https://anthropic.com).
