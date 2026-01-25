# Kodak

A Discord bot for daily journaling that pays attention.

Each day at a time you choose, Kodak checks in with a question. You talk. Over weeks and months, it notices what you keep coming back to—and where your words and actions don't line up.

No blank page, no habit to build. Just answer when it asks.

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

## What Makes It Different

- **Conversation, not questionnaires** — Values emerge from what you keep bringing up, not how you answer a survey
- **Catches contradictions** — Kodak notices when what you say and what you do don't line up
- **Honest, not sycophantic** — Pushes back on your ideas instead of validating everything
- **Portable and shareable** — Export your patterns, compare with others, take your data anywhere
- **Self-hosted and open source** — No accounts, no company storing your data

## Three Months Later

```
Kodak: You've said work-life balance matters to you, but
       the last six sessions have all been about work stress
       you haven't done anything about. What's actually
       going on there?

You: ...that's uncomfortably accurate.
```

This is the payoff. Kodak tracks what you keep returning to—and where your actions don't match your words. A bot that just validated everything you said would miss this. It would reflect your self-image back at you instead of showing you something true.

## Comparison

Export your patterns. Share them with a friend. See where you align and where you see the world differently.

This isn't a compatibility score. It's a starting point for real conversation: "I keep coming back to security, you keep coming back to freedom. What does that mean for us?"

Your values data is yours. Share it on your terms, with who you choose.

## Core Features

| Feature | What it does |
|---------|--------------|
| **Daily check-ins** | Thoughtful prompts at a time you choose |
| **Pattern recognition** | Notices themes from natural conversation, shows supporting quotes and confidence levels |
| **Weekly summaries** | What you kept coming back to, shifts in emphasis |
| **Tension detection** | Surfaces contradictions between what you say and what you do |
| **Personality presets** | Choose your conversational style (philosopher, therapist, trickster, etc.) |

## Privacy

Your conversations are processed by Anthropic's Claude API to generate responses and extract patterns. See [Anthropic's privacy policy](https://www.anthropic.com/privacy) for how they handle data.

Everything else stays with you:
- All your data lives in a local SQLite database you control
- There are no Kodak servers—nothing is stored anywhere except your machine (or your own Railway instance)
- `/export` downloads everything as JSON
- `/clear` deletes all your data
- `/pause` lets you chat without pattern tracking

## The Bigger Picture

Your values data should belong to you—not locked in a dating app, not harvested by a social network.

Old OkCupid had the right idea: match people on values, not just photos. But they used questionnaires (easy to game) and controlled the data (you couldn't take it with you). Then they killed most of it anyway.

Kodak is an attempt at something different. Extract what you actually care about through honest conversation. Own that data. Share it on your terms. Today, that means comparing with friends who also use Kodak. Eventually, maybe finding others who see the world like you do—without an algorithm deciding who you get to meet.

[Read more about where this is going →](VISION.md)

## Design Philosophy

Questionnaires capture who you think you are. Conversation captures who you actually are.

Most AI assistants are yes-men. They validate everything you say. This feels good but produces garbage data—if a bot just reflects your self-image back at you, the "values" it extracts are just self-flattery.

Kodak is designed to be a thinking partner, not a cheerleader. It notices patterns, questions assumptions, and points out contradictions. That's not rudeness—it's respect.

The honesty isn't a feature. It's what makes the whole thing work.

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

## License

MIT

## Credits

Built with [discord.py](https://discordpy.readthedocs.io/) and [Anthropic Claude](https://anthropic.com).
