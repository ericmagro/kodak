"""Theme and values-related commands."""

import io
import json
import logging
import discord
from discord import app_commands

from db import get_or_create_user, get_user_beliefs
from values import (
    get_user_value_profile, get_value_profile_history, generate_value_narrative,
    format_profile_comparison, export_themes_for_sharing, parse_exported_themes
)

logger = logging.getLogger('kodak')


async def get_source_beliefs_for_themes(user_id: str, profile, beliefs: list) -> str:
    """Get example beliefs that contributed to the user's top themes."""
    if not beliefs:
        return ""

    # Get top 2-3 themes
    top_values = profile.get_top_values(3)
    if not top_values or all(v.normalized_score == 0 for v in top_values):
        return ""

    # Filter for only significant themes (>0.1 score)
    significant_values = [v for v in top_values if v.normalized_score > 0.1]
    if not significant_values:
        return ""

    source_examples = []

    # For each significant theme, find 1-2 supporting beliefs
    for value in significant_values[:2]:  # Show source for top 2 themes
        value_name = value.value_name

        # Find beliefs that contributed to this theme
        matching_beliefs = []
        for belief in beliefs:
            # Check belief_values mapping for this belief
            if 'values' in belief and belief['values']:
                for belief_value in belief['values']:
                    if belief_value.get('value_name') == value_name and belief_value.get('weight', 0) > 0.5:
                        matching_beliefs.append(belief)
                        break

        # If we have matching beliefs, pick 1-2 good examples
        if matching_beliefs:
            # Sort by confidence and pick the most confident ones
            matching_beliefs.sort(key=lambda b: b.get('confidence', 0.5), reverse=True)

            examples = []
            for belief in matching_beliefs[:2]:  # Max 2 examples per theme
                statement = belief['statement']
                # Truncate long statements
                if len(statement) > 100:
                    statement = statement[:97] + "..."
                examples.append(f"*\"{statement}\"*")

            if examples:
                theme_label = value_name.replace('_', ' ').title()
                source_examples.append(f"**{theme_label}** theme based on things like:\n• " + "\n• ".join(examples))

    if source_examples:
        return "**What's behind these themes:**\n\n" + "\n\n".join(source_examples)

    return ""


async def register_themes_commands(bot):
    """Register all theme/values-related commands with the bot."""

    @bot.tree.command(name="themes", description="See patterns Kodak has noticed")
    async def themes_command(interaction: discord.Interaction):
        """Show user's current value themes."""
        user_id = str(interaction.user.id)
        user = await get_or_create_user(user_id, username=interaction.user.name)

        await interaction.response.defer(ephemeral=True)

        profile = await get_user_value_profile(user_id)
        beliefs = await get_user_beliefs(user_id, include_values=True)
        belief_count = len(beliefs)

        # Generate base narrative
        narrative = generate_value_narrative(profile, belief_count=belief_count)

        # Add source beliefs for top themes
        source_beliefs = await get_source_beliefs_for_themes(user_id, profile, beliefs)
        if source_beliefs:
            narrative += "\n\n" + source_beliefs

        await interaction.followup.send(narrative, ephemeral=True)
        logger.info(f"User {user_id} viewed their themes")

    @bot.tree.command(name="values", description="See patterns Kodak has noticed (same as /themes)")
    async def values_command(interaction: discord.Interaction):
        """Alias for themes command."""
        # Just redirect to the themes command logic
        user_id = str(interaction.user.id)
        user = await get_or_create_user(user_id, username=interaction.user.name)

        await interaction.response.defer(ephemeral=True)

        profile = await get_user_value_profile(user_id)
        beliefs = await get_user_beliefs(user_id, include_values=True)
        belief_count = len(beliefs)

        # Generate base narrative
        narrative = generate_value_narrative(profile, belief_count=belief_count)

        # Add source beliefs for top themes
        source_beliefs = await get_source_beliefs_for_themes(user_id, profile, beliefs)
        if source_beliefs:
            narrative += "\n\n" + source_beliefs

        await interaction.followup.send(narrative, ephemeral=True)
        logger.info(f"User {user_id} viewed their values")

    @bot.tree.command(name="themes-history", description="See how your themes have shifted")
    async def themes_history_command(interaction: discord.Interaction):
        """Show how themes have changed over time."""
        user_id = str(interaction.user.id)
        user = await get_or_create_user(user_id, username=interaction.user.name)

        try:
            history = await get_value_profile_history(user_id, days=30)

            if not history:
                await interaction.response.send_message(
                    "**No theme history yet** 📊\n\n"
                    "I haven't tracked your themes long enough to show changes over time. "
                    "Keep journaling and check back in a week or two!",
                    ephemeral=True
                )
                return

            # Find the most significant changes
            if len(history) < 2:
                await interaction.response.send_message(
                    "**Not enough data yet** 📊\n\n"
                    "I need at least two weeks of data to show how your themes are shifting. "
                    "Keep journaling and I'll start tracking changes!",
                    ephemeral=True
                )
                return

            # Compare first and last profiles
            first_profile = history[0]
            last_profile = history[-1]

            # Find significant changes (>10% difference)
            changes = []
            for value_name in first_profile.keys():
                if value_name in last_profile:
                    first_score = first_profile[value_name]
                    last_score = last_profile[value_name]
                    change = last_score - first_score

                    if abs(change) > 0.10:  # 10% threshold
                        direction = "↗️" if change > 0 else "↘️"
                        changes.append({
                            'value': value_name.title(),
                            'change': change,
                            'direction': direction,
                            'first': first_score,
                            'last': last_score
                        })

            # Sort by magnitude of change
            changes.sort(key=lambda x: abs(x['change']), reverse=True)

            if not changes:
                change_narrative = "*No recorded changes yet. This belief has remained stable.*\n"
            else:
                change_narrative = "**Significant shifts over the past month:**\n\n"
                for change in changes[:5]:  # Top 5 changes
                    change_narrative += f"{change['direction']} **{change['value']}**: "
                    change_narrative += f"{change['first']:.2f} → {change['last']:.2f} "
                    change_narrative += f"({change['change']:+.2f})\n"

            response = f"**📈 How Your Themes Have Shifted**\n\n{change_narrative}"

            if len(response) > 2000:
                response = response[:1997] + "..."

            await interaction.response.send_message(response, ephemeral=True)
            logger.info(f"User {user_id} viewed theme history")

        except Exception as e:
            logger.error(f"Error showing theme history for {user_id}: {e}")
            await interaction.response.send_message(
                "❌ I had trouble loading your theme history. Try again in a moment.",
                ephemeral=True
            )

    @bot.tree.command(name="values-history", description="See how themes shifted (same as /themes-history)")
    async def values_history_command(interaction: discord.Interaction):
        """Alias for themes-history command."""
        await themes_history_command(interaction)

    @bot.tree.command(name="share-themes", description="Export your themes to share with someone")
    async def share_themes_command(interaction: discord.Interaction):
        """Export themes as a shareable file."""
        user_id = str(interaction.user.id)
        user = await get_or_create_user(user_id, username=interaction.user.name)

        try:
            # Get current profile
            profile = await get_user_value_profile(user_id)

            if not profile or not any(profile.scores.values()):
                await interaction.response.send_message(
                    "**Not enough data yet** 📊\n\n"
                    "I need more journaling sessions to generate meaningful themes to share. "
                    "Try again after a few more conversations!",
                    ephemeral=True
                )
                return

            # Export themes
            display_name = interaction.user.display_name or interaction.user.name
            export_data = await export_themes_for_sharing(user_id, display_name)

            # Create file
            export_json = json.dumps(export_data, indent=2)
            filename = f"{display_name.replace(' ', '_').lower()}_themes.json"

            file = discord.File(
                fp=io.BytesIO(export_json.encode()),
                filename=filename
            )

            await interaction.response.send_message(
                "**🎁 Your themes, ready to share!**\n\n"
                "Send this file to someone you want to compare themes with. "
                "They can upload it using `/compare-file` to see how your values align.\n\n"
                "*This file contains only your value scores and some example beliefs you chose to share—no personal details or private thoughts.*",
                file=file,
                ephemeral=True
            )

            logger.info(f"User {user_id} exported themes for sharing")

        except Exception as e:
            logger.error(f"Error exporting themes for {user_id}: {e}")
            await interaction.response.send_message(
                "❌ I had trouble creating your export. Try again in a moment.",
                ephemeral=True
            )

    @bot.tree.command(name="share-values", description="Export themes to share (same as /share-themes)")
    async def share_values_command(interaction: discord.Interaction):
        """Alias for share-themes command."""
        await share_themes_command(interaction)

    @bot.tree.command(name="compare-file", description="Compare your themes with someone's shared file")
    async def compare_file_command(interaction: discord.Interaction, file: discord.Attachment):
        """Compare user's themes with an uploaded file."""
        user_id = str(interaction.user.id)
        user = await get_or_create_user(user_id, username=interaction.user.name)

        try:
            # Validate file
            if not file.filename.endswith('.json'):
                await interaction.response.send_message(
                    "❌ **Invalid file type**\n\n"
                    "Please upload a JSON file created by Kodak's `/share-themes` command.",
                    ephemeral=True
                )
                return

            if file.size > 1024 * 100:  # 100KB limit
                await interaction.response.send_message(
                    "❌ **File too large**\n\n"
                    "Theme files should be small JSON files (under 100KB).",
                    ephemeral=True
                )
                return

            # Download and parse file
            file_content = await file.read()
            try:
                other_data = json.loads(file_content.decode('utf-8'))
            except (json.JSONDecodeError, UnicodeDecodeError):
                await interaction.response.send_message(
                    "❌ **Invalid file format**\n\n"
                    "This doesn't appear to be a valid Kodak themes file.",
                    ephemeral=True
                )
                return

            # Parse and validate
            other_profile = parse_exported_themes(other_data)
            if not other_profile:
                await interaction.response.send_message(
                    "❌ **Invalid themes file**\n\n"
                    "This file doesn't contain valid Kodak theme data. "
                    "Make sure it was created with `/share-themes`.",
                    ephemeral=True
                )
                return

            # Get user's current profile
            user_profile = await get_user_value_profile(user_id)
            if not user_profile or not any(user_profile.scores.values()):
                await interaction.response.send_message(
                    "**You don't have enough theme data yet** 📊\n\n"
                    "I need more journaling sessions from you to make a meaningful comparison. "
                    "Try again after a few more conversations!",
                    ephemeral=True
                )
                return

            # Generate comparison
            comparison = format_profile_comparison(user_profile, other_profile)

            # Create embed
            embed = discord.Embed(
                title=f"🔍 Theme Comparison",
                description=comparison,
                color=0x5865F2
            )

            await interaction.response.send_message(embed=embed, ephemeral=True)
            logger.info(f"User {user_id} compared themes with {other_profile.display_name}")

        except Exception as e:
            logger.error(f"Error comparing themes for {user_id}: {e}")
            await interaction.response.send_message(
                "❌ I had trouble processing the comparison. Try again in a moment.",
                ephemeral=True
            )