# Hosting Kodak

Two options for running Kodak:

1. **Railway (Recommended)** — Cloud hosting, always on, ~$5/month
2. **Local** — Run on your own computer, completely free

---

## Option 1: Railway (Cloud)

Railway keeps your bot running 24/7 without keeping your computer on.

### Prerequisites
- A Discord Bot Token ([setup instructions](#step-2-create-your-discord-bot))
- An Anthropic API Key ([setup instructions](#step-3-get-your-anthropic-api-key))
- A Railway account ([railway.app](https://railway.app))

### Deploy to Railway

1. **Create project:** New Project → Deploy from GitHub → Select your fork of `kodak`

2. **Add a volume** (for persistent database):
   - Click "New" → "Volume"
   - Mount path: `/data`

3. **Set environment variables** (Settings → Variables):
   ```
   DISCORD_TOKEN=your_discord_bot_token
   ANTHROPIC_API_KEY=your_anthropic_api_key
   KODAK_DB_PATH=/data/kodak.db
   ```

4. **Deploy** — Railway auto-deploys from your repo

5. **Verify** — Check logs for "Logged in as Kodak#1234"

Your bot is now running 24/7. Railway will restart it automatically if it crashes.

**Cost:** ~$5/month for the hobby plan (includes enough hours for a Discord bot).

---

## Option 2: Local (Your Computer)

Run Kodak on your own machine. Your data is stored locally (conversations are sent to Anthropic's API for processing).

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
10. Open that URL in your browser → Select a server → Authorize

**Don't have a server?** Create one in Discord: click the **+** button in your server list → "Create My Own" → "For me and my friends". Name it anything. This is just to let you DM the bot.

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

Your bot is now online!

## Step 7: Start Chatting

1. Open Discord and go to the server where you invited your bot
2. Find the bot in the member list (right sidebar) — it should show as online
3. Click on the bot's name → Click **"Message"**
4. This opens a DM — just say hi!

The bot will guide you through a quick setup, then you can start chatting. Your beliefs and data are stored locally in `kodak.db`.

## Keeping It Running

The bot only works while the terminal is open. For daily check-ins to work reliably, you'll want to run it as a background service that starts automatically.

### Quick Background Run (Mac/Linux)

```bash
cd /path/to/kodak/src
nohup python bot.py > ../kodak.log 2>&1 &
```

Check the log with `tail -f ../kodak.log`. To stop: `pkill -f "python bot.py"`.

### Auto-Start on macOS (launchd)

1. Create a plist file:
```bash
nano ~/Library/LaunchAgents/com.kodak.bot.plist
```

2. Add this content (replace paths with your actual paths):
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.kodak.bot</string>
    <key>ProgramArguments</key>
    <array>
        <string>/Users/YOURUSERNAME/kodak/venv/bin/python</string>
        <string>/Users/YOURUSERNAME/kodak/src/bot.py</string>
    </array>
    <key>WorkingDirectory</key>
    <string>/Users/YOURUSERNAME/kodak/src</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/Users/YOURUSERNAME/kodak/kodak.log</string>
    <key>StandardErrorPath</key>
    <string>/Users/YOURUSERNAME/kodak/kodak.log</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/usr/local/bin:/usr/bin:/bin</string>
    </dict>
</dict>
</plist>
```

3. Load the service:
```bash
launchctl load ~/Library/LaunchAgents/com.kodak.bot.plist
```

4. Manage it:
```bash
# Check status
launchctl list | grep kodak

# Stop
launchctl unload ~/Library/LaunchAgents/com.kodak.bot.plist

# Restart
launchctl unload ~/Library/LaunchAgents/com.kodak.bot.plist
launchctl load ~/Library/LaunchAgents/com.kodak.bot.plist
```

### Auto-Start on Linux (systemd)

1. Create a service file:
```bash
sudo nano /etc/systemd/system/kodak.service
```

2. Add this content (replace paths and username):
```ini
[Unit]
Description=Kodak Discord Bot
After=network.target

[Service]
Type=simple
User=YOURUSERNAME
WorkingDirectory=/home/YOURUSERNAME/kodak/src
ExecStart=/home/YOURUSERNAME/kodak/venv/bin/python bot.py
Restart=always
RestartSec=10
StandardOutput=append:/home/YOURUSERNAME/kodak/kodak.log
StandardError=append:/home/YOURUSERNAME/kodak/kodak.log

[Install]
WantedBy=multi-user.target
```

3. Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable kodak
sudo systemctl start kodak
```

4. Manage it:
```bash
# Check status
sudo systemctl status kodak

# View logs
journalctl -u kodak -f

# Restart
sudo systemctl restart kodak

# Stop
sudo systemctl stop kodak
```

### Auto-Start on Windows (Task Scheduler)

1. Open **Task Scheduler** (search for it in Start menu)

2. Click **Create Basic Task**
   - Name: `Kodak Bot`
   - Trigger: **When I log on**
   - Action: **Start a program**

3. For the program settings:
   - Program: `C:\Users\YOURUSERNAME\kodak\venv\Scripts\pythonw.exe`
   - Arguments: `bot.py`
   - Start in: `C:\Users\YOURUSERNAME\kodak\src`

4. Click **Finish**, then find the task, right-click → **Properties**:
   - Check "Run whether user is logged on or not"
   - Check "Run with highest privileges"

5. To see output, modify the task to run a batch file instead:

   Create `run_kodak.bat` in your kodak folder:
   ```batch
   @echo off
   cd /d C:\Users\YOURUSERNAME\kodak\src
   C:\Users\YOURUSERNAME\kodak\venv\Scripts\python.exe bot.py >> ..\kodak.log 2>&1
   ```

   Then point Task Scheduler to this batch file.

### Important: .env File Loading

The bot uses `python-dotenv` to load environment variables from the `.env` file. For auto-start to work:

- The `WorkingDirectory` in your service config must point to the `src/` folder (or the folder containing `.env`)
- Alternatively, copy `.env` to `/Users/YOURUSERNAME/kodak/src/.env`
- Or set environment variables directly in the service config (less recommended for security)

If the bot fails to start via auto-start but works manually, check that the `.env` file is accessible from the working directory.

### Verify It's Working

After setting up auto-start:
1. Reboot your computer
2. Check Discord — the bot should come online within a minute
3. Check the log file for any errors
4. If the bot doesn't start, check the log for "DISCORD_TOKEN not found" or similar errors

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

## Custom Database Location (Optional)

By default, the database is stored as `kodak.db` in the project folder. To use a different location:

```
KODAK_DB_PATH=/path/to/your/kodak.db
```

Useful if you want to store data on a different drive or a persistent volume.

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

Your stored data never leaves your computer (though conversations are processed via Anthropic's API).

## Questions?

Open an issue at [github.com/ericmagro/kodak/issues](https://github.com/ericmagro/kodak/issues)
