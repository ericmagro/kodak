"""Kodak v2.0 - Reflective Journaling Companion (Refactored)."""

import os
import logging
import asyncio
import discord
from discord.ext import commands
from dotenv import load_dotenv
from datetime import datetime, timedelta

# Database and core imports
from db import init_db, get_or_create_user, update_user
from session import get_active_session

# Handler imports
from handlers.sessions import (
    start_journal_session, process_session_message, handle_onboarding_complete
)

# Command modules
from commands.journal import register_journal_commands
from commands.themes import register_themes_commands
from commands.beliefs import register_beliefs_commands
from commands.summaries import register_summaries_commands
from commands.data import register_data_commands
from commands.settings import register_settings_commands
from commands.help import register_help_commands

# Scheduler
from scheduler import SchedulerManager

# Health server
from health_server import start_health_server

# Load environment
load_dotenv()

# Logging setup
from structured_logging import setup_structured_logging, log_user_action, log_session_event, log_error_with_context

# Use JSON logging in production, human-readable in development
enable_json = os.getenv('KODAK_JSON_LOGS', 'false').lower() == 'true'
log_level = os.getenv('KODAK_LOG_LEVEL', 'INFO')
logger = setup_structured_logging(level=log_level, enable_json=enable_json)

# Bot setup
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)
bot.remove_command('help')  # Remove default help to use our custom one

# Global instances
scheduler = None
health_server = None


@bot.event
async def on_ready():
    """Bot startup sequence."""
    global scheduler, health_server

    logger.info(f'Logged in as {bot.user}')

    try:
        # Start health check server
        port = int(os.getenv('PORT', '8080'))
        health_server = await start_health_server(port)

        # Initialize database
        await init_db()

        # Register all command modules
        await register_journal_commands(bot)
        await register_themes_commands(bot)
        await register_beliefs_commands(bot)
        await register_summaries_commands(bot)
        await register_data_commands(bot)
        await register_settings_commands(bot)
        await register_help_commands(bot)

        # Sync commands
        logger.info("Syncing commands...")
        await bot.tree.sync()
        logger.info("Commands synced successfully")

        # Start scheduler
        scheduler = SchedulerManager(bot, send_scheduled_prompt, send_catch_up_prompt, send_reengagement_prompt)
        await scheduler.start()

        logger.info("Ready!")

    except Exception as e:
        logger.error(f"Startup failed: {e}")


@bot.event
async def on_message(message: discord.Message):
    """Handle incoming messages."""
    # Ignore bot messages and non-DM messages
    if message.author.bot or not isinstance(message.channel, discord.DMChannel):
        return

    user_id = str(message.author.id)
    user = await get_or_create_user(user_id, username=message.author.name)

    # Update last active time
    await update_user(user_id, last_active=datetime.now().isoformat())

    # Log user message (without content for privacy)
    log_user_action(logger, "message_received", user_id, has_active_session=bool(get_active_session(user_id)))

    # Check if user has an active session
    if get_active_session(user_id):
        # Process as part of ongoing session
        await process_session_message(message.channel, user, message.content)
    else:
        # No active session - send guidance
        if not user.get('onboarding_complete'):
            await message.channel.send(
                "👋 **Welcome to Kodak!** I'm your personal journaling companion.\n\n"
                "I notice this is your first time here. Use `/journal` to get started, "
                "and I'll walk you through a quick setup!"
            )
        else:
            await message.channel.send(
                "Hi! I don't have an active session with you right now. "
                "Use `/journal` to start a new journaling session, or try `/help` to see what I can do."
            )


async def send_scheduled_prompt(user: dict):
    """Send a scheduled daily prompt to a user."""
    try:
        discord_user = await bot.fetch_user(int(user['user_id']))
        if not discord_user:
            logger.warning(f"Could not find Discord user {user['user_id']}")
            return

        dm_channel = await discord_user.create_dm()
        await start_journal_session(dm_channel, user, prompt_type='scheduled')
        logger.info(f"Sent scheduled prompt to {user['user_id']}")

    except Exception as e:
        logger.error(f"Failed to send scheduled prompt to {user['user_id']}: {e}")


async def send_catch_up_prompt(user: dict, hours_late: int):
    """Send a catch-up prompt for a missed scheduled prompt."""
    try:
        from prompts import get_reengagement_prompt

        discord_user = await bot.fetch_user(int(user['user_id']))
        if not discord_user:
            logger.warning(f"Could not find Discord user {user['user_id']}")
            return

        dm_channel = await discord_user.create_dm()

        # Send catch-up message first
        personality = user.get('personality_preset', 'best_friend')
        catch_up_messages = {
            "best_friend": f"Hey! I tried to check in with you {hours_late} hours ago. No worries if you were busy—want to catch up now?",
            "philosopher": f"I attempted to reach you {hours_late} hours ago. Shall we examine what's been occupying your thoughts?",
            "scientist": f"Scheduled prompt was {hours_late} hours overdue. Are you available to proceed with data collection now?",
            "trickster": f"I've been waiting {hours_late} hours! Did you forget about me, or are you just playing hard to get?",
            "therapist": f"I understand you might have been busy {hours_late} hours ago. Would you like to talk now? No pressure."
        }

        message = catch_up_messages.get(personality, catch_up_messages["best_friend"])
        await dm_channel.send(message)

        # Start session if they want to continue
        await start_journal_session(dm_channel, user, prompt_type='catch_up')
        logger.info(f"Sent catch-up prompt to {user['user_id']} ({hours_late}h late)")

    except Exception as e:
        logger.error(f"Failed to send catch-up prompt to {user['user_id']}: {e}")


async def send_reengagement_prompt(user: dict):
    """Send a reengagement prompt to inactive users."""
    try:
        from prompts import get_reengagement_prompt

        discord_user = await bot.fetch_user(int(user['user_id']))
        if not discord_user:
            logger.warning(f"Could not find Discord user {user['user_id']}")
            return

        dm_channel = await discord_user.create_dm()

        personality = user.get('personality_preset', 'best_friend')
        message = get_reengagement_prompt(personality)

        await dm_channel.send(message)
        logger.info(f"Sent reengagement prompt to {user['user_id']}")

    except Exception as e:
        logger.error(f"Failed to send reengagement prompt to {user['user_id']}: {e}")


async def main():
    """Main entry point."""
    token = os.getenv('DISCORD_TOKEN')
    if not token:
        logger.error("DISCORD_TOKEN not found in environment variables")
        return

    try:
        await bot.start(token)
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, shutting down...")
    except Exception as e:
        logger.error(f"Bot error: {e}")
    finally:
        if scheduler:
            await scheduler.stop()
        if health_server:
            await health_server.cleanup()
        await bot.close()


if __name__ == "__main__":
    asyncio.run(main())