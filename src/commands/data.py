"""Data management commands (export/clear)."""

import io
import json
import logging
import discord
from discord import app_commands

from db import get_or_create_user, export_user_data, clear_all_user_data

logger = logging.getLogger('kodak')


async def register_data_commands(bot):
    """Register all data management commands with the bot."""

    @bot.tree.command(name="export", description="Download all your data")
    async def export_command(interaction: discord.Interaction):
        """Export all user data as JSON."""
        user_id = str(interaction.user.id)
        user = await get_or_create_user(user_id, username=interaction.user.name)

        await interaction.response.defer(ephemeral=True)

        try:
            data = await export_user_data(user_id)

            # Create JSON file
            json_data = json.dumps(data, indent=2, default=str)
            filename = f"kodak_export_{user_id}.json"

            file = discord.File(
                fp=io.BytesIO(json_data.encode('utf-8')),
                filename=filename
            )

            await interaction.followup.send(
                "**📦 Your Kodak Data Export**\n\n"
                "This file contains all your beliefs, sessions, summaries, and themes. "
                "Keep it safe—this is your complete journaling history!\n\n"
                "*Note: This doesn't include your actual conversation messages for privacy.*",
                file=file,
                ephemeral=True
            )

            logger.info(f"User {user_id} exported their data")

        except Exception as e:
            logger.error(f"Error exporting data for {user_id}: {e}")
            await interaction.followup.send(
                "❌ I had trouble creating your export. Try again in a moment.",
                ephemeral=True
            )

    @bot.tree.command(name="clear", description="Delete all your data")
    async def clear_command(interaction: discord.Interaction):
        """Delete all user data with confirmation."""
        user_id = str(interaction.user.id)
        user = await get_or_create_user(user_id, username=interaction.user.name)

        class ConfirmView(discord.ui.View):
            def __init__(self):
                super().__init__(timeout=120)

            @discord.ui.button(label="Yes, delete everything", style=discord.ButtonStyle.danger)
            async def confirm_clear(self, interaction: discord.Interaction, button: discord.ui.Button):
                await interaction.response.defer(ephemeral=True)

                try:
                    success = await clear_all_user_data(user_id)

                    if success:
                        await interaction.followup.send(
                            "✅ **All data deleted**\n\n"
                            "Your Kodak data has been permanently removed. "
                            "If you start journaling again, you'll begin with a fresh profile.\n\n"
                            "Thanks for using Kodak!",
                            ephemeral=True
                        )
                        logger.info(f"User {user_id} cleared all their data")
                    else:
                        await interaction.followup.send(
                            "❌ **Deletion failed**\n\n"
                            "I had trouble deleting your data. Please try again.",
                            ephemeral=True
                        )

                except Exception as e:
                    logger.error(f"Error clearing data for {user_id}: {e}")
                    await interaction.followup.send(
                        "❌ I had trouble deleting your data. Try again in a moment.",
                        ephemeral=True
                    )

            @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary)
            async def cancel_clear(self, interaction: discord.Interaction, button: discord.ui.Button):
                await interaction.response.send_message(
                    "Cancelled. Your data is safe and hasn't been deleted.",
                    ephemeral=True
                )

        warning_text = (
            "⚠️ **WARNING: This will permanently delete ALL your Kodak data**\n\n"
            "This includes:\n"
            "• All beliefs and themes\n"
            "• Journal sessions and summaries\n"
            "• Your value profile and history\n"
            "• All settings and preferences\n\n"
            "**This cannot be undone.** Export your data first if you want to keep a backup.\n\n"
            "Are you absolutely sure you want to continue?"
        )

        view = ConfirmView()
        await interaction.response.send_message(warning_text, view=view, ephemeral=True)