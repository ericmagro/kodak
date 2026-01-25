"""Summary-related commands."""

import logging
import discord
from discord import app_commands
import anthropic

from db import get_or_create_user
from summaries import create_weekly_summary, get_past_summaries, format_date_range

logger = logging.getLogger('kodak')


async def register_summaries_commands(bot):
    """Register all summary-related commands with the bot."""

    @bot.tree.command(name="summary", description="Get a summary of your journaling")
    @app_commands.describe(period="The time period to summarize")
    @app_commands.choices(period=[
        app_commands.Choice(name="This week", value="week"),
    ])
    async def summary_command(interaction: discord.Interaction, period: str = "week"):
        """Generate a summary for the specified period."""
        user_id = str(interaction.user.id)
        user = await get_or_create_user(user_id, username=interaction.user.name)

        if period != "week":
            await interaction.response.send_message(
                "❌ Only weekly summaries are available right now. Monthly summaries coming soon!",
                ephemeral=True
            )
            return

        await interaction.response.defer(ephemeral=True)

        try:
            summary = await create_weekly_summary(user_id)

            # Create embed
            embed = discord.Embed(
                title="📊 Your Weekly Summary",
                description=summary['narrative'],
                color=0x5865F2
            )

            # Add highlights if they exist
            if summary.get('highlights'):
                highlights_text = "\n".join([f"• {h}" for h in summary['highlights']])
                embed.add_field(name="Key Insights", value=highlights_text, inline=False)

            # Add stats
            date_range = format_date_range(summary['period_start'], summary['period_end'])
            stats = f"{summary['session_count']} sessions"
            if summary['belief_count'] > 0:
                stats += f" · {summary['belief_count']} beliefs emerged"
            embed.set_footer(text=f"{date_range} · {stats}")

            await interaction.followup.send(embed=embed, ephemeral=True)
            logger.info(f"User {user_id} generated weekly summary")

        except anthropic.APITimeoutError:
            logger.error("LLM request timed out during summary generation")
            await interaction.followup.send(
                "❌ **Summary timed out**\n\n"
                "The summary is taking too long to generate. This usually happens when there's a lot of data to process. "
                "Try again in a moment.",
                ephemeral=True
            )
        except anthropic.APIError as e:
            logger.error(f"LLM API error during summary: {e}")
            await interaction.followup.send(
                "❌ **Summary failed**\n\n"
                "I'm having trouble generating your summary right now. Please try again in a moment.",
                ephemeral=True
            )
        except Exception as e:
            logger.error(f"Error generating summary for {user_id}: {e}")
            await interaction.followup.send(
                "❌ I had trouble generating your summary. Try again in a moment.",
                ephemeral=True
            )

    @bot.tree.command(name="summaries", description="View your past summaries")
    async def summaries_command(interaction: discord.Interaction):
        """Show list of past summaries."""
        user_id = str(interaction.user.id)
        user = await get_or_create_user(user_id, username=interaction.user.name)

        try:
            summaries = await get_past_summaries(user_id, 'week', limit=10)

            if not summaries:
                await interaction.response.send_message(
                    "**No summaries yet** 📊\n\n"
                    "You don't have any weekly summaries yet. Use `/summary week` to generate your first one!",
                    ephemeral=True
                )
                return

            # Create embed
            embed = discord.Embed(
                title="📊 Your Past Summaries",
                description=f"Here are your recent weekly summaries:",
                color=0x5865F2
            )

            for s in summaries[:5]:  # Show last 5
                # Truncate narrative for preview
                preview = s['narrative'][:200] + "..." if len(s['narrative']) > 200 else s['narrative']

                field_name = f"{s['date_range']} ({s['session_count']} sessions)"
                embed.add_field(name=field_name, value=preview, inline=False)

            embed.set_footer(text="Use /summary week to generate a new summary")

            await interaction.response.send_message(embed=embed, ephemeral=True)
            logger.info(f"User {user_id} viewed past summaries")

        except Exception as e:
            logger.error(f"Error showing summaries for {user_id}: {e}")
            await interaction.response.send_message(
                "❌ I had trouble loading your summaries. Try again in a moment.",
                ephemeral=True
            )