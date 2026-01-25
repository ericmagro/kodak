"""Journal and session management commands."""

import logging
import discord
from discord import app_commands
from datetime import datetime

from db import get_or_create_user, update_user
from handlers.sessions import start_journal_session, handle_onboarding_complete
from onboarding import OnboardingFlow
from personality import PRESETS, PRESET_ORDER
from session import get_active_session
from scheduler import parse_time_input

logger = logging.getLogger('kodak')


async def register_journal_commands(bot):
    """Register all journal-related commands with the bot."""

    @bot.tree.command(name="schedule", description="Set your daily check-in time")
    @app_commands.describe(time="Time in HH:MM format (24hr), like 20:00 for 8 PM")
    async def schedule_command(interaction: discord.Interaction, time: str):
        """Set or update daily check-in time."""
        user_id = str(interaction.user.id)
        user = await get_or_create_user(user_id, username=interaction.user.name)

        try:
            parsed_time = parse_time_input(time)
            await update_user(user_id, prompt_time=parsed_time)

            await interaction.response.send_message(
                f"✅ Daily check-in set for **{parsed_time}**.\n"
                f"I'll send you a journaling prompt every day at this time.\n\n"
                f"Use `/pause` to pause check-ins or `/skip` to skip just today.",
                ephemeral=True
            )
            logger.info(f"User {user_id} set prompt time to {parsed_time}")
        except ValueError as e:
            await interaction.response.send_message(
                f"❌ Invalid time format. Use HH:MM (24-hour), like:\n"
                f"• `08:30` for 8:30 AM\n"
                f"• `20:00` for 8:00 PM\n\n"
                f"Error: {str(e)}",
                ephemeral=True
            )

    @bot.tree.command(name="skip", description="Skip today's check-in")
    async def skip_command(interaction: discord.Interaction):
        """Skip today's scheduled prompt."""
        user_id = str(interaction.user.id)
        user = await get_or_create_user(user_id, username=interaction.user.name)

        await update_user(user_id, last_prompt_sent=datetime.now().isoformat())

        await interaction.response.send_message(
            "✅ **Skipped today's check-in.**\n"
            "I won't send a prompt today. Tomorrow's check-in will happen as normal.\n\n"
            "*Need a longer break? Use `/pause` to pause all check-ins.*",
            ephemeral=True
        )
        logger.info(f"User {user_id} skipped today's prompt")

    @bot.tree.command(name="journal", description="Start a journaling session now")
    async def journal_command(interaction: discord.Interaction):
        """Start a journaling session immediately."""
        user_id = str(interaction.user.id)
        user = await get_or_create_user(user_id, username=interaction.user.name)

        # Check if they've completed onboarding
        if not user.get('onboarding_complete'):
            await interaction.response.send_message(
                "👋 **Welcome to Kodak!**\n\n"
                "Let's get you set up first. I'll ask you a few quick questions to personalize your experience.",
                ephemeral=True
            )

            # Start onboarding flow
            flow = OnboardingFlow(user_id, on_complete=handle_onboarding_complete)
            await flow.start(interaction)
            return

        # Check for active session
        if get_active_session(user_id):
            await interaction.response.send_message(
                "You already have an active session running. Just keep talking to me!",
                ephemeral=True
            )
            return

        await interaction.response.send_message(
            "Starting a journaling session...",
            ephemeral=True
        )

        # Start session
        try:
            dm_channel = await interaction.user.create_dm()
            await start_journal_session(dm_channel, user, prompt_type='user_initiated')
        except Exception as e:
            logger.error(f"Failed to start journal session for {user_id}: {e}")
            await interaction.followup.send(
                "❌ I had trouble starting your session. Try again in a moment.",
                ephemeral=True
            )

    @bot.tree.command(name="setup", description="Change your personality preference")
    async def setup_command(interaction: discord.Interaction):
        """Show personality selection."""
        user_id = str(interaction.user.id)

        class PersonalitySelect(discord.ui.Select):
            def __init__(self):
                options = [
                    discord.SelectOption(
                        label=PRESETS[key].name,
                        value=key,
                        description=PRESETS[key].description[:100]
                    )
                    for key in PRESET_ORDER
                ]
                super().__init__(placeholder="Choose a personality...", options=options)

            async def callback(self, interaction: discord.Interaction):
                selected = self.values[0]
                preset = PRESETS[selected]
                await update_user(user_id, personality_preset=selected)
                await interaction.response.send_message(
                    content=f"Updated to **{preset.name}**!\n\n*{preset.journaling_style}*",
                    ephemeral=True
                )
                logger.info(f"User {user_id} changed personality to {selected}")

        class PersonalityView(discord.ui.View):
            def __init__(self):
                super().__init__(timeout=60)
                self.add_item(PersonalitySelect())

        await interaction.response.send_message(
            "Choose a personality that fits how you like to reflect:",
            view=PersonalityView(),
            ephemeral=True
        )

    @bot.tree.command(name="depth", description="Set session depth preference")
    @app_commands.describe(level="How deep you want sessions to go")
    @app_commands.choices(level=[
        app_commands.Choice(name="Quick (2-3 exchanges)", value="quick"),
        app_commands.Choice(name="Standard (4-6 exchanges)", value="standard"),
        app_commands.Choice(name="Deep (6+ exchanges)", value="deep"),
    ])
    async def depth_command(interaction: discord.Interaction, level: str):
        """Set session depth preference."""
        user_id = str(interaction.user.id)

        descriptions = {
            "quick": "Quick sessions (2-3 exchanges) - Perfect for busy days",
            "standard": "Standard sessions (4-6 exchanges) - Balanced exploration",
            "deep": "Deep sessions (6+ exchanges) - Thorough reflection"
        }

        await update_user(user_id, prompt_depth=level)

        await interaction.response.send_message(
            f"✅ **Session depth set to {level}.**\n\n"
            f"{descriptions[level]}\n\n"
            f"You can change this anytime with `/depth`.",
            ephemeral=True
        )
        logger.info(f"User {user_id} set depth to {level}")

    @bot.tree.command(name="pause", description="Pause daily check-ins")
    async def pause_command(interaction: discord.Interaction):
        """Pause daily check-ins."""
        user_id = str(interaction.user.id)
        await update_user(user_id, tracking_paused=1)

        await interaction.response.send_message(
            "⏸️ **Daily check-ins paused.**\n\n"
            "I won't send any scheduled prompts until you use `/resume`.\n\n"
            "*You can still start sessions manually with `/journal`.*",
            ephemeral=True
        )
        logger.info(f"User {user_id} paused check-ins")

    @bot.tree.command(name="resume", description="Resume daily check-ins")
    async def resume_command(interaction: discord.Interaction):
        """Resume daily check-ins."""
        user_id = str(interaction.user.id)
        user = await get_or_create_user(user_id, username=interaction.user.name)

        await update_user(user_id, tracking_paused=0)

        prompt_time = user.get('prompt_time', 'not set')
        message = f"▶️ **Daily check-ins resumed!**\n\n"

        if prompt_time != 'not set':
            message += f"I'll send your next prompt at {prompt_time}."
        else:
            message += "Use `/schedule` to set your check-in time."

        await interaction.response.send_message(message, ephemeral=True)
        logger.info(f"User {user_id} resumed check-ins")