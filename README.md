# Kodak

A Discord bot that maps your belief network through engaging conversation.

Kodak has natural, curious conversations with you—and along the way, builds a map of what you believe and why. Think of it like a mirror for your mind.

## What It Does

- **Extracts beliefs** from natural conversation (you don't have to do anything special)
- **Tracks confidence levels** based on how certain you sound
- **Lets you mark importance** — distinguish core beliefs from passing thoughts
- **Finds connections** between your beliefs over time
- **Lets you explore** your belief map with `/map` and `/explore [topic]`
- **Lets you share** — create snapshots of your beliefs to discuss with others
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

### Importance Indicators

Mark how important each belief is to you with `/mark`:

```
★★★★★ Core (5)       — Foundational to who you are
★★★★☆ High (4)       — Very important, rarely changes
★★★☆☆ Medium (3)     — Significant but flexible (default)
★★☆☆☆ Low (2)        — Opinions you hold loosely
★☆☆☆☆ Peripheral (1) — Passing thoughts, trivia
```

Use `/core` to see only your most important beliefs (★★★★+).

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
| `/beliefs` | Raw list with IDs and importance |
| `/belief [id]` | View one belief with its connections |
| `/core` | Show only important beliefs (★★★★+) |
| `/tensions` | Show beliefs that might contradict each other |
| `/history [id]` | See how a belief has evolved over time |
| `/changes` | See beliefs that changed recently |
| `/mark [id] [1-5]` | Set how important a belief is |
| `/confidence [id] [1-5]` | Update how certain you are in a belief |
| `/share` | Create shareable snapshot of your beliefs |
| `/share-export` | Export shareable beliefs as file |
| `/compare-file` | Compare with someone's exported file |
| `/bridging` | See your bridging score |
| `/privacy` | Control which beliefs are shareable |
| `/setup` | Choose a personality preset |
| `/style` | Fine-tune personality (warmth, directness, playfulness, formality) |
| `/forget [id]` | Delete a belief (use `last` for most recent) |
| `/pause` | Pause belief tracking |
| `/resume` | Resume tracking |
| `/export` | Download all your data as JSON |
| `/backup` | Download database backup file |
| `/clear` | Delete everything |

## Personality Presets

- 🏛️ **The Philosopher** — Thoughtful and probing
- 💛 **The Best Friend** — Warm and honest
- 🔬 **The Scientist** — Precise and analytical
- 🃏 **The Trickster** — Playful and irreverent
- 🌿 **The Therapist** — Empathetic and safe

## Design Philosophy: Honest Engagement

Kodak is designed to be warm but never sycophantic. This is intentional.

Many AI chatbots default to excessive validation ("That's a great point!", "What a fascinating perspective!"). We deliberately designed against this. Research shows sycophantic AI makes users *more confident they're right* even when wrong, and *less open* to other viewpoints.

Kodak takes a different approach, inspired by:
- **Adam Grant's "disagreeable givers"** — people who challenge because they care
- **Kim Scott's Radical Candor** — care personally AND challenge directly
- **Carl Rogers** — genuineness is essential alongside warmth

What this means:
- The bot accepts *you* fully, while questioning your *ideas* freely
- If something seems contradictory, it'll say so
- If it disagrees, it'll share why
- It won't praise just to be nice

This makes conversations more real and the belief map more accurate.

## Run Your Own

Kodak is designed to run locally on your computer. Your data stays on your machine, and you control everything.

**You'll need:**
- Python 3.12+
- A Discord bot token (free)
- An Anthropic API key (~$0.01-0.02 per message)

**Quick start:**
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

Step-by-step instructions for Discord bot creation, API keys, Windows/Mac/Linux, and troubleshooting.

## Cost

Each message costs ~$0.01-0.02 (Anthropic API). A good conversation session might cost $0.10-0.50.

## Privacy

- All data stored locally in `kodak.db` on your computer
- Only you can see your beliefs
- `/pause` to chat without tracking
- `/export` to download your data
- `/clear` to delete everything

Your beliefs never leave your machine.

## Where This Is Going

Right now, Kodak maps your beliefs through conversation. But the vision is bigger:

**Coming soon:**
- **Compatibility matching** — Find people who share your values, or who disagree in interesting ways
- **Web visualization** — See your beliefs as an interactive graph, not just text
- **Obsidian/Roam export** — Take your belief network into your second brain
- **Scheduled check-ins** — Track how your thinking evolves over months and years

**Longer term:**
- Community belief mapping — What does a group actually think?
- Bridge-building tools — Find common ground across divides
- Deliberation support — Help groups have productive disagreements

The goal: technology that helps us understand ourselves and each other, instead of just confirming what we already believe.

See the full [roadmap and vision](DESIGN.md#roadmap).

## License

MIT

## Credits

Built with [discord.py](https://discordpy.readthedocs.io/) and [Anthropic Claude](https://anthropic.com).
