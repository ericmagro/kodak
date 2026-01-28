"""User settings and preferences commands."""

import logging
import discord
from discord import app_commands
import pytz

from db import get_or_create_user, update_user
from personality import get_dimensions_for_preset

logger = logging.getLogger('kodak')


async def register_settings_commands(bot):
    """Register all settings-related commands with the bot."""

    @bot.tree.command(name="style", description="Fine-tune personality dimensions")
    async def style_command(interaction: discord.Interaction):
        """Show current personality dimensions."""
        user_id = str(interaction.user.id)
        user = await get_or_create_user(user_id, username=interaction.user.name)

        preset = user.get('personality_preset', 'best_friend')
        dimensions = get_dimensions_for_preset(preset)

        response = (
            f"**Your Style** (preset: {preset})\n\n"
            f"**Warmth:** {dimensions.warmth}/5 ({'🔥' * dimensions.warmth})\n"
            f"**Directness:** {dimensions.directness}/5 ({'💬' * dimensions.directness})\n"
            f"**Playfulness:** {dimensions.playfulness}/5 ({'🎭' * dimensions.playfulness})\n"
            f"**Formality:** {dimensions.formality}/5 ({'👔' * dimensions.formality})\n\n"
            f"Use `/setup` to change personality preset."
        )

        await interaction.response.send_message(response, ephemeral=True)
        logger.info(f"User {user_id} viewed their style settings")

    @bot.tree.command(name="timezone", description="Set your timezone")
    @app_commands.describe(timezone="Your timezone (e.g., America/New_York, Europe/London)")
    async def timezone_command(interaction: discord.Interaction, timezone: str):
        """Set user's timezone."""
        user_id = str(interaction.user.id)
        user = await get_or_create_user(user_id, username=interaction.user.name)

        try:
            # Validate timezone
            tz = pytz.timezone(timezone)

            await update_user(user_id, timezone=timezone)

            await interaction.response.send_message(
                f"✅ **Timezone set to {timezone}**\n\n"
                f"Your daily check-ins and summaries will now use this timezone.\n\n"
                f"*Having trouble? Try common timezones like:*\n"
                f"• `America/New_York`\n"
                f"• `America/Los_Angeles`\n"
                f"• `Europe/London`\n"
                f"• `Asia/Tokyo`",
                ephemeral=True
            )
            logger.info(f"User {user_id} set timezone to {timezone}")

        except pytz.exceptions.UnknownTimeZoneError:
            await interaction.response.send_message(
                f"❌ **Unknown timezone: {timezone}**\n\n"
                f"Please use a valid timezone identifier. Common examples:\n"
                f"• `America/New_York` (Eastern Time)\n"
                f"• `America/Los_Angeles` (Pacific Time)\n"
                f"• `Europe/London` (GMT/BST)\n"
                f"• `Asia/Tokyo` (JST)\n"
                f"• `Australia/Sydney` (AEST)\n\n"
                f"Find your timezone at: https://en.wikipedia.org/wiki/List_of_tz_database_time_zones",
                ephemeral=True
            )
        except Exception as e:
            logger.error(f"Error setting timezone for {user_id}: {e}")
            if interaction.response.is_done():
                await interaction.followup.send(
                    "❌ I had trouble updating your timezone. Try again in a moment.",
                    ephemeral=True
                )
            else:
                await interaction.response.send_message(
                    "❌ I had trouble updating your timezone. Try again in a moment.",
                    ephemeral=True
                )