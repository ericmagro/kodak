# Self-Hosting Kodak on a VPS

Run Kodak on your own server with full data privacy and automated backups.

**Why self-host?**
- Your data is encrypted — even the hosting provider can't read it
- Full control over your data
- Automated encrypted backups
- No vendor lock-in

---

## Overview

| Component | Choice | Cost |
|-----------|--------|------|
| VPS | DigitalOcean | $4-6/mo |
| Encryption | gocryptfs | Free |
| Backups | Local Mac → Backblaze | Free (uses existing backup) |
| Monitoring | UptimeRobot | Free |

**Time required:** ~45 minutes for initial setup, then hands-off (except rare reboots).

---

## Part 1: Get a VPS

### DigitalOcean

1. Go to [digitalocean.com](https://www.digitalocean.com/) and sign up
2. Enable **2FA** on your account (Account → Security)
3. Click **Create** → **Droplets**
4. Settings:
   - **Region**: Pick closest to you (e.g., SFO for West Coast, NYC for East Coast)
   - **Image**: Ubuntu 24.04 LTS
   - **Size**: Basic → Regular → $4-6/mo (512MB-1GB RAM is enough)
   - **Authentication**: SSH Key (see below)
   - **Hostname**: `kodak`
5. Click **Create Droplet**

### SSH Key Setup

If you don't have an SSH key:

```bash
ssh-keygen -t ed25519 -C "your@email.com"
```

Add a passphrase when prompted (important for security).

Get your public key:

```bash
cat ~/.ssh/id_ed25519.pub
```

Paste this into DigitalOcean when creating the droplet.

---

## Part 2: Initial Server Setup

SSH into your server:

```bash
ssh root@YOUR_SERVER_IP
```

Run these commands:

```bash
# Update system
apt update && apt upgrade -y

# Install required packages
apt install -y python3 python3-pip python3-venv git ufw sqlite3 gocryptfs

# Create non-root user
useradd -m -s /bin/bash kodak

# Set up firewall
ufw allow OpenSSH
ufw --force enable

# Enable gocryptfs for all users
echo "user_allow_other" >> /etc/fuse.conf
```

---

## Part 3: Set Up Encryption

Create encrypted directories:

```bash
mkdir -p /home/kodak/kodak-encrypted
mkdir -p /home/kodak/kodak-decrypted
```

Initialize encryption (save the password AND master key in your password manager):

```bash
gocryptfs -init /home/kodak/kodak-encrypted
```

Mount the encrypted folder:

```bash
gocryptfs -allow_other /home/kodak/kodak-encrypted /home/kodak/kodak-decrypted
```

---

## Part 4: Install Kodak

Switch to kodak user:

```bash
su - kodak
```

Install the bot:

```bash
git clone https://github.com/ericmagro/kodak.git
cd kodak
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Create .env file in the encrypted directory:

```bash
cat > /home/kodak/kodak-decrypted/.env << 'EOF'
DISCORD_TOKEN=your_discord_bot_token
ANTHROPIC_API_KEY=your_anthropic_api_key
EOF
chmod 600 /home/kodak/kodak-decrypted/.env
```

Create symlink so bot can find it:

```bash
ln -s /home/kodak/kodak-decrypted/.env /home/kodak/kodak/.env
```

Exit back to root:

```bash
exit
```

Set permissions:

```bash
chown -R kodak:kodak /home/kodak/kodak-encrypted /home/kodak/kodak-decrypted
```

---

## Part 5: Set Up Service

Create the systemd service:

```bash
cat > /etc/systemd/system/kodak.service << 'EOF'
[Unit]
Description=Kodak Discord Bot
After=network.target

[Service]
Type=simple
User=kodak
WorkingDirectory=/home/kodak/kodak/src
ExecStart=/home/kodak/kodak/venv/bin/python bot.py
Environment=KODAK_DB_PATH=/home/kodak/kodak-decrypted/kodak.db
Restart=always
RestartSec=10
StandardOutput=append:/home/kodak/kodak/kodak.log
StandardError=append:/home/kodak/kodak/kodak.log

[Install]
WantedBy=multi-user.target
EOF
```

**Important:** Do NOT enable auto-start (the encrypted folder must be unlocked first):

```bash
systemctl daemon-reload
systemctl start kodak
```

Create unlock script for after reboots:

```bash
cat > /home/kodak/unlock.sh << 'EOF'
#!/bin/bash
echo "Mounting encrypted folder..."
gocryptfs -allow_other /home/kodak/kodak-encrypted /home/kodak/kodak-decrypted
echo "Starting Kodak..."
systemctl start kodak
systemctl status kodak
EOF
chmod +x /home/kodak/unlock.sh
```

---

## Part 6: Automated Backups

On your **local Mac**, create a backup script:

```bash
cat > ~/Documents/c/kodak/backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR=~/Documents/c/kodak/backups
SERVER_IP=YOUR_SERVER_IP
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

mkdir -p "$BACKUP_DIR"

# Backup the encrypted folder (not the decrypted view)
scp -r root@$SERVER_IP:/home/kodak/kodak-encrypted "$BACKUP_DIR/kodak-encrypted_$TIMESTAMP"

# Keep only last 30 backups
ls -dt "$BACKUP_DIR"/kodak-encrypted_* 2>/dev/null | tail -n +31 | xargs rm -rf 2>/dev/null

echo "Backup complete: kodak-encrypted_$TIMESTAMP"
EOF
chmod +x ~/Documents/c/kodak/backup.sh
```

Replace `YOUR_SERVER_IP` with your actual IP.

Schedule daily backups (runs at 10 AM):

```bash
crontab -e
```

Add this line:

```
0 10 * * * ~/Documents/c/kodak/backup.sh >> ~/Documents/c/kodak/backups/backup.log 2>&1
```

Your Mac's existing Backblaze backup will sync these encrypted files automatically.

---

## Part 7: Monitoring

1. Sign up at [uptimerobot.com](https://uptimerobot.com/) (free)
2. Add New Monitor:
   - Type: HTTP(s)
   - URL: `http://YOUR_SERVER_IP:8080/health`
   - Interval: 5 minutes
3. Add your email as an alert contact

You'll get notified if the bot goes down.

---

## After a Reboot

Reboots are rare (~2-3 times per year). When one happens:

1. You'll get an email from UptimeRobot
2. SSH into your server:
   ```bash
   ssh root@YOUR_SERVER_IP
   ```
3. Run the unlock script:
   ```bash
   /home/kodak/unlock.sh
   ```
4. Enter your gocryptfs password
5. Bot is back online

---

## Quick Reference

| Task | Command |
|------|---------|
| SSH into server | `ssh root@YOUR_SERVER_IP` |
| Unlock after reboot | `/home/kodak/unlock.sh` |
| Check bot status | `systemctl status kodak` |
| View logs | `tail -50 /home/kodak/kodak/kodak.log` |
| Restart bot | `systemctl restart kodak` |
| Manual backup | `~/Documents/c/kodak/backup.sh` |
| Change gocryptfs password | `gocryptfs -passwd /home/kodak/kodak-encrypted` |

---

## Security Summary

| Layer | Protection |
|-------|------------|
| SSH access | Key-based + passphrase |
| DigitalOcean account | 2FA enabled |
| Database at rest | gocryptfs (AES-256) |
| Backups | Encrypted (gocryptfs) |
| Data in transit | SSH/SCP encryption |

Your data is encrypted on disk at all times. Even DigitalOcean cannot read it. The only way to access your journal entries is with your gocryptfs password.

---

## Restoring from Backup

If you need to restore:

1. Copy a backup folder to the server:
   ```bash
   scp -r ~/Documents/c/kodak/backups/kodak-encrypted_TIMESTAMP root@YOUR_SERVER_IP:/home/kodak/kodak-encrypted-restore
   ```

2. On the server, mount it:
   ```bash
   mkdir -p /home/kodak/restore-test
   gocryptfs /home/kodak/kodak-encrypted-restore /home/kodak/restore-test
   ```

3. Enter your password — your data is restored.

---

## Cost Breakdown

| Item | Monthly Cost |
|------|--------------|
| DigitalOcean Droplet | $4-6 |
| Backblaze (via Mac backup) | $0 (existing) |
| UptimeRobot | $0 (free tier) |
| Anthropic API | ~$5-15 (usage) |
| **Total** | **~$10-25/mo** |
