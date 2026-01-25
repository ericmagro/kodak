"""Help and information commands."""

import logging
import discord
from discord import app_commands

from db import get_or_create_user

logger = logging.getLogger('kodak')


async def register_help_commands(bot):
    """Register all help-related commands with the bot."""

    @bot.tree.command(name="help", description="Show available commands")
    async def help_command(interaction: discord.Interaction):
        """Show tiered help with essential commands first."""
        user_id = str(interaction.user.id)
        user = await get_or_create_user(user_id, username=interaction.user.name)

        class ExpandHelpView(discord.ui.View):
            def __init__(self):
                super().__init__(timeout=300)

            @discord.ui.button(label="See all commands", style=discord.ButtonStyle.secondary, emoji="📖")
            async def show_all_commands(self, interaction: discord.Interaction, button: discord.ui.Button):
                full_help = """**📖 All Commands**

**🗓️ Scheduling**
`/schedule` — Set daily check-in time
`/skip` — Skip today's check-in
`/pause` / `/resume` — Pause/resume check-ins
`/timezone` — Set your timezone

**💭 Journaling**
`/journal` — Start a session now
`/setup` — Choose personality preset
`/style` — View personality dimensions
`/depth` — Set session depth

**🎨 Themes & Values**
`/themes` — See your patterns
`/themes-history` — How themes shifted
`/share-themes` — Export to share
`/compare-file` — Compare with someone

**🧠 Beliefs**
`/map` — Belief map by topic
`/beliefs` — List all beliefs
`/belief` — View belief details
`/explore` — Explore by topic
`/core` — Most important beliefs
`/history` — How belief evolved
`/changes` — Recent belief changes
`/tensions` — Conflicting beliefs
`/confidence` — Update confidence
`/mark` — Mark importance
`/forget` / `/undo` — Delete/restore

**📊 Summaries**
`/summary week` — Weekly digest
`/summaries` — View past summaries

**💾 Data**
`/export` — Download all data
`/clear` — Delete everything

Need help with a specific command? Just ask me about it!"""

                await interaction.response.send_message(full_help, ephemeral=True)

        essential_help = """**🌟 Essential Commands**

**Get Started**
`/journal` — Start journaling now
`/schedule 20:00` — Set daily check-in time
`/themes` — See what patterns I've noticed

**Explore Your Mind**
`/beliefs` — List all your beliefs
`/map` — See beliefs organized by topic
`/summary week` — Get your weekly insights

**Settings**
`/setup` — Choose personality style
`/pause` — Pause check-ins temporarily
`/export` — Download all your data

*Need more? Click below for the full command list.*"""

        view = ExpandHelpView()
        await interaction.response.send_message(essential_help, view=view, ephemeral=True)
        logger.info(f"User {user_id} viewed help")