# Self-Hosting Kodak

This guide walks you through running Kodak on your own computer. Your data stays completely local.

## What You'll Need

1. **Python 3.12+** — The programming language Kodak runs on
2. **A Discord Bot Token** — Free, takes 5 minutes to set up
3. **An Anthropic API Key** — Pay-per-use (~$0.01-0.02 per message)

## Step 1: Install Python

**Mac:**
```bash
# Check if you have Python
python3 --version

# If not installed, get it from python.org or use Homebrew:
brew install python
```

**Windows:**
1. Download from [python.org](https://www.python.org/downloads/)
2. **Important:** Check "Add Python to PATH" during installation

**Linux:**
```bash
sudo apt update && sudo apt install python3 python3-pip python3-venv
```

## Step 2: Create Your Discord Bot

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Click **"New Application"** → Name it "Kodak" (or whatever you want)
3. Go to **Bot** in the left sidebar
4. Click **"Reset Token"** → Copy the token (save it somewhere safe!)
5. Scroll down and enable **"Message Content Intent"** under Privileged Gateway Intents
6. Go to **OAuth2 → URL Generator** in the left sidebar
7. Under **Scopes**, check:
   - `bot`
   - `applications.commands`
8. Under **Bot Permissions**, check:
   - Send Messages
   - Embed Links
   - Attach Files
   - Read Message History
   - Use Slash Commands
9. Copy the generated URL at the bottom
10. Open that URL in your browser → Select your server → Authorize

Your bot is now in your server (but offline until you run the code).

## Step 3: Get Your Anthropic API Key

1. Go to [console.anthropic.com](https://console.anthropic.com/)
2. Sign up or log in
3. Go to **API Keys** → Create a new key
4. Copy the key (starts with `sk-ant-...`)

**Cost:** About $0.01-0.02 per conversation turn. A typical session might cost $0.10-0.50.

## Step 4: Download and Set Up Kodak

**Option A: With Git (recommended)**
```bash
git clone https://github.com/ericmagro/kodak.git
cd kodak
```

**Option B: Without Git**
1. Go to [github.com/ericmagro/kodak](https://github.com/ericmagro/kodak)
2. Click the green **"Code"** button → **"Download ZIP"**
3. Unzip it somewhere (e.g., your Documents folder)
4. Open a terminal and navigate to that folder:
   ```bash
   cd ~/Documents/kodak-main
   ```

## Step 5: Configure Your Tokens

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Open `.env` in any text editor and add your tokens:
   ```
   DISCORD_TOKEN=your_discord_bot_token_here
   ANTHROPIC_API_KEY=your_anthropic_api_key_here
   ```

3. Save the file.

## Step 6: Install Dependencies and Run

**Mac/Linux:**
```bash
# Create a virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the bot
cd src && python bot.py
```

**Windows (Command Prompt):**
```cmd
# Create a virtual environment
python -m venv venv

# Activate it
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the bot
cd src && python bot.py
```

**Windows (PowerShell):**
```powershell
# Create a virtual environment
python -m venv venv

# Activate it
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Run the bot
cd src && python bot.py
```

You should see:
```
Logged in as Kodak#1234
Syncing commands...
Ready!
```

Your bot is now online! DM it on Discord to start chatting.

## Keeping It Running

The bot only works while the terminal is open. Some options:

**Just close the laptop lid** — Most computers will keep running. Reopen terminal and run again if it stops.

**Run in background (Mac/Linux):**
```bash
nohup python bot.py > kodak.log 2>&1 &
```

**Run as a service (advanced):** Look into `systemd` (Linux) or `launchd` (Mac) for auto-start on boot.

## Stopping the Bot

Press `Ctrl+C` in the terminal where it's running.

## Rate Limiting (Optional)

By default, there's **no rate limit** — you're paying your own API costs, so you decide.

To add a limit, edit `.env`:
```
RATE_LIMIT_PER_HOUR=15
```

This limits each user to 15 messages per hour. Useful if you're hosting for others.

**Cost math:** At ~$0.02/message, 15 msgs/hour = $0.30/hour max per user.

## Updating Kodak

If you used Git:
```bash
cd kodak
git pull
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
cd src && python bot.py
```

If you downloaded the ZIP, download the new ZIP and replace the files (keep your `.env` file!).

## Troubleshooting

### "Command not found: python"
Try `python3` instead of `python`.

### "No module named discord"
Make sure you activated the virtual environment:
```bash
source venv/bin/activate  # Mac/Linux
venv\Scripts\activate     # Windows
```

### Bot is online but not responding
1. Make sure you enabled **Message Content Intent** in the Discord Developer Portal
2. Make sure you're DMing the bot or @mentioning it in a channel

### "Improper token passed"
Your Discord token is wrong. Go back to the Developer Portal, reset the token, and update `.env`.

### "Invalid API key"
Your Anthropic key is wrong. Check [console.anthropic.com](https://console.anthropic.com/) and update `.env`.

### Bot crashes with errors
Check that you have Python 3.12+:
```bash
python3 --version
```

## Your Data

Everything is stored locally in `kodak.db` (SQLite database).

- **Export your data:** Use `/export` in Discord
- **Delete everything:** Use `/clear` in Discord, or just delete `kodak.db`
- **Backup:** Copy `kodak.db` somewhere safe

Your beliefs never leave your computer.

## Questions?

Open an issue at [github.com/ericmagro/kodak/issues](https://github.com/ericmagro/kodak/issues)
