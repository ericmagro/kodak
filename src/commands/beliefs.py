"""Belief management commands."""

import logging
import discord
from discord import app_commands

from db import (
    get_or_create_user, get_user_beliefs, get_belief_by_id,
    update_belief_confidence, update_belief_importance,
    soft_delete_belief, restore_last_deleted_belief,
    get_belief_history, get_recent_changes, get_all_tensions
)

logger = logging.getLogger('kodak')


async def register_beliefs_commands(bot):
    """Register all belief-related commands with the bot."""

    @bot.tree.command(name="map", description="See your belief map")
    async def map_command(interaction: discord.Interaction):
        """Show beliefs organized by topic."""
        user_id = str(interaction.user.id)
        user = await get_or_create_user(user_id, username=interaction.user.name)

        try:
            beliefs = await get_user_beliefs(user_id)

            if not beliefs:
                await interaction.response.send_message(
                    "**No beliefs recorded yet** 🗺️\n\n"
                    "As you journal with me, I'll start noticing patterns in what you believe and organize them by topic. "
                    "Check back after a few sessions!",
                    ephemeral=True
                )
                return

            # Group by topics
            topic_groups = {}
            untagged = []

            for belief in beliefs:
                topics = belief.get('topics', [])
                if topics:
                    for topic in topics:
                        topic = topic.title()
                        if topic not in topic_groups:
                            topic_groups[topic] = []
                        topic_groups[topic].append(belief)
                else:
                    untagged.append(belief)

            # Build response
            response = "**🗺️ Your Belief Map**\n\n"

            # Show topic groups
            for topic, beliefs_in_topic in sorted(topic_groups.items()):
                response += f"**{topic}** ({len(beliefs_in_topic)})\n"
                for belief in beliefs_in_topic[:3]:  # Show first 3
                    response += f"• {belief['statement'][:80]}{'...' if len(belief['statement']) > 80 else ''}\n"
                if len(beliefs_in_topic) > 3:
                    response += f"  *...and {len(beliefs_in_topic) - 3} more*\n"
                response += "\n"

            # Show untagged if any
            if untagged:
                response += f"**Other** ({len(untagged)})\n"
                for belief in untagged[:3]:
                    response += f"• {belief['statement'][:80]}{'...' if len(belief['statement']) > 80 else ''}\n"
                if len(untagged) > 3:
                    response += f"  *...and {len(untagged) - 3} more*\n"

            response += f"\nUse `/beliefs` to see the full list with IDs."

            if len(response) > 2000:
                response = response[:1997] + "..."

            await interaction.response.send_message(response, ephemeral=True)
            logger.info(f"User {user_id} viewed belief map")

        except Exception as e:
            logger.error(f"Error showing belief map for {user_id}: {e}")
            await interaction.response.send_message(
                "❌ I had trouble loading your belief map. Try again in a moment.",
                ephemeral=True
            )

    @bot.tree.command(name="explore", description="Explore beliefs about a topic")
    @app_commands.describe(topic="The topic to explore (e.g., work, relationships, goals)")
    async def explore_command(interaction: discord.Interaction, topic: str):
        """Show all beliefs related to a specific topic."""
        user_id = str(interaction.user.id)
        user = await get_or_create_user(user_id, username=interaction.user.name)

        try:
            beliefs = await get_user_beliefs(user_id)

            if not beliefs:
                await interaction.response.send_message(
                    f"**No beliefs about '{topic}' yet** 🔍\n\n"
                    "I haven't recorded any beliefs on this topic. Keep journaling and I'll start noticing patterns!",
                    ephemeral=True
                )
                return

            # Filter by topic (case-insensitive)
            topic_lower = topic.lower()
            matching_beliefs = []

            for belief in beliefs:
                # Check if topic matches any of the belief's topics
                belief_topics = [t.lower() for t in belief.get('topics', [])]
                if any(topic_lower in bt or bt in topic_lower for bt in belief_topics):
                    matching_beliefs.append(belief)
                # Also check if topic appears in the belief statement
                elif topic_lower in belief['statement'].lower():
                    matching_beliefs.append(belief)

            if not matching_beliefs:
                await interaction.response.send_message(
                    f"**No beliefs about '{topic}' found** 🔍\n\n"
                    f"I don't have any beliefs related to '{topic}' yet. "
                    f"Try journaling about this topic, or use `/map` to see what topics I do have.",
                    ephemeral=True
                )
                return

            # Build response
            response = f"**🔍 Exploring: {topic.title()}** ({len(matching_beliefs)} beliefs)\n\n"

            for i, belief in enumerate(matching_beliefs[:10], 1):  # Show up to 10
                confidence = belief['confidence'] * 100 if belief['confidence'] else 50
                response += f"**{i}.** {belief['statement']}\n"
                response += f"   *Confidence: {confidence:.0f}% • ID: {belief['id'][:8]}*\n\n"

            if len(matching_beliefs) > 10:
                response += f"*...and {len(matching_beliefs) - 10} more. Use `/beliefs` to see all.*\n\n"

            response += f"Use `/belief <id>` to explore any belief in detail."

            if len(response) > 2000:
                response = response[:1997] + "..."

            await interaction.response.send_message(response, ephemeral=True)
            logger.info(f"User {user_id} explored topic: {topic}")

        except Exception as e:
            logger.error(f"Error exploring topic {topic} for {user_id}: {e}")
            await interaction.response.send_message(
                "❌ I had trouble exploring that topic. Try again in a moment.",
                ephemeral=True
            )

    @bot.tree.command(name="beliefs", description="List all your beliefs")
    async def beliefs_command(interaction: discord.Interaction):
        """Show paginated list of all beliefs."""
        user_id = str(interaction.user.id)
        user = await get_or_create_user(user_id, username=interaction.user.name)

        try:
            beliefs = await get_user_beliefs(user_id)

            if not beliefs:
                await interaction.response.send_message(
                    "**No beliefs recorded yet** 💭\n\n"
                    "I haven't extracted any beliefs from our conversations yet. "
                    "Keep journaling and I'll start noticing patterns in what you believe!",
                    ephemeral=True
                )
                return

            # Sort by most recent
            beliefs.sort(key=lambda x: x['first_expressed'], reverse=True)

            # Build response (first page)
            response = f"**💭 Your Beliefs** ({len(beliefs)} total)\n\n"

            for i, belief in enumerate(beliefs[:10], 1):  # First 10
                confidence = belief['confidence'] * 100 if belief['confidence'] else 50
                response += f"**{i}.** {belief['statement'][:100]}{'...' if len(belief['statement']) > 100 else ''}\n"
                response += f"   *Confidence: {confidence:.0f}% • ID: {belief['id'][:8]}*\n\n"

            if len(beliefs) > 10:
                response += f"*Showing first 10 of {len(beliefs)}. Use `/belief <id>` to explore specific beliefs.*"

            await interaction.response.send_message(response, ephemeral=True)
            logger.info(f"User {user_id} listed their beliefs")

        except Exception as e:
            logger.error(f"Error listing beliefs for {user_id}: {e}")
            await interaction.response.send_message(
                "❌ I had trouble loading your beliefs. Try again in a moment.",
                ephemeral=True
            )

    @bot.tree.command(name="belief", description="View a single belief in detail")
    @app_commands.describe(id="The belief ID (first 8 characters shown in other commands)")
    async def belief_command(interaction: discord.Interaction, id: str):
        """Show detailed view of a specific belief."""
        user_id = str(interaction.user.id)
        user = await get_or_create_user(user_id, username=interaction.user.name)

        try:
            belief = await get_belief_by_id(user_id, id)

            if not belief:
                await interaction.response.send_message(
                    f"❌ **Belief not found**\n\n"
                    f"No belief found with ID `{id}`. Use `/beliefs` to see your belief list with IDs.",
                    ephemeral=True
                )
                return

            # Build detailed view
            confidence = belief['confidence'] * 100 if belief['confidence'] else 50
            importance = belief.get('importance', 3)

            response = f"**💭 Belief Details**\n\n"
            response += f"**Statement:** {belief['statement']}\n\n"
            response += f"**Confidence:** {confidence:.0f}%\n"
            response += f"**Importance:** {'⭐' * importance} ({importance}/5)\n"
            response += f"**First expressed:** {belief['first_expressed'][:10]}\n"

            if belief.get('topics'):
                topics_text = ", ".join(belief['topics'])
                response += f"**Topics:** {topics_text}\n"

            if belief.get('context'):
                response += f"**Context:** {belief['context'][:200]}{'...' if len(belief['context']) > 200 else ''}\n"

            response += f"\n**ID:** `{belief['id'][:8]}`\n\n"
            response += f"Use `/confidence {belief['id'][:8]} <1-5>` to update confidence\n"
            response += f"Use `/mark {belief['id'][:8]} <1-5>` to update importance"

            await interaction.response.send_message(response, ephemeral=True)
            logger.info(f"User {user_id} viewed belief {belief['id'][:8]}")

        except Exception as e:
            logger.error(f"Error showing belief {id} for {user_id}: {e}")
            await interaction.response.send_message(
                "❌ I had trouble loading that belief. Try again in a moment.",
                ephemeral=True
            )

    @bot.tree.command(name="forget", description="Delete a belief")
    @app_commands.describe(id="The belief ID to delete")
    async def forget_command(interaction: discord.Interaction, id: str):
        """Delete a belief (with confirmation)."""
        user_id = str(interaction.user.id)
        user = await get_or_create_user(user_id, username=interaction.user.name)

        try:
            belief = await get_belief_by_id(user_id, id)

            if not belief:
                await interaction.response.send_message(
                    f"❌ **Belief not found**\n\n"
                    f"No belief found with ID `{id}`.",
                    ephemeral=True
                )
                return

            class ConfirmView(discord.ui.View):
                def __init__(self):
                    super().__init__(timeout=60)

                @discord.ui.button(label="Yes, delete it", style=discord.ButtonStyle.danger)
                async def confirm_delete(self, interaction: discord.Interaction, button: discord.ui.Button):
                    await soft_delete_belief(id, user_id)
                    await interaction.response.send_message(
                        f"✅ **Belief deleted**\n\n"
                        f"The belief has been removed. You can restore it with `/undo` if you change your mind.",
                        ephemeral=True
                    )
                    logger.info(f"User {user_id} deleted belief {id[:8]}")

                @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary)
                async def cancel_delete(self, interaction: discord.Interaction, button: discord.ui.Button):
                    await interaction.response.send_message("Cancelled. The belief wasn't deleted.", ephemeral=True)

            response = f"**Are you sure you want to delete this belief?**\n\n"
            response += f"*\"{belief['statement'][:150]}{'...' if len(belief['statement']) > 150 else ''}\"*\n\n"
            response += f"This will permanently remove it from your profile."

            view = ConfirmView()
            await interaction.response.send_message(response, view=view, ephemeral=True)

        except Exception as e:
            logger.error(f"Error deleting belief {id} for {user_id}: {e}")
            await interaction.response.send_message(
                "❌ I had trouble deleting that belief. Try again in a moment.",
                ephemeral=True
            )

    @bot.tree.command(name="undo", description="Restore the last forgotten belief")
    async def undo_command(interaction: discord.Interaction):
        """Restore the most recently deleted belief."""
        user_id = str(interaction.user.id)
        user = await get_or_create_user(user_id, username=interaction.user.name)

        try:
            restored = await restore_last_deleted_belief(user_id)

            if restored:
                await interaction.response.send_message(
                    f"✅ **Belief restored**\n\n"
                    f"*\"{restored['statement'][:150]}{'...' if len(restored['statement']) > 150 else ''}\"*\n\n"
                    f"The belief is back in your profile.",
                    ephemeral=True
                )
                logger.info(f"User {user_id} restored belief {restored['id'][:8]}")
            else:
                await interaction.response.send_message(
                    "**Nothing to restore** 💭\n\n"
                    "You haven't deleted any beliefs recently, so there's nothing to undo.",
                    ephemeral=True
                )

        except Exception as e:
            logger.error(f"Error restoring belief for {user_id}: {e}")
            await interaction.response.send_message(
                "❌ I had trouble restoring a belief. Try again in a moment.",
                ephemeral=True
            )

    @bot.tree.command(name="confidence", description="Update your confidence in a belief")
    @app_commands.describe(
        id="The belief ID",
        level="How confident you are (1=very unsure, 5=very confident)"
    )
    @app_commands.choices(level=[
        app_commands.Choice(name="1 - Very unsure", value=1),
        app_commands.Choice(name="2 - Somewhat unsure", value=2),
        app_commands.Choice(name="3 - Neutral", value=3),
        app_commands.Choice(name="4 - Somewhat confident", value=4),
        app_commands.Choice(name="5 - Very confident", value=5),
    ])
    async def confidence_command(interaction: discord.Interaction, id: str, level: int):
        """Update confidence level for a belief."""
        user_id = str(interaction.user.id)
        user = await get_or_create_user(user_id, username=interaction.user.name)

        try:
            belief = await get_belief_by_id(user_id, id)

            if not belief:
                await interaction.response.send_message(
                    f"❌ **Belief not found**\n\n"
                    f"No belief found with ID `{id}`.",
                    ephemeral=True
                )
                return

            # Convert to 0-1 scale
            confidence_score = level / 5.0

            await update_belief_confidence(id, user_id, confidence_score, trigger="user_adjustment")

            confidence_labels = {1: "very unsure", 2: "somewhat unsure", 3: "neutral", 4: "somewhat confident", 5: "very confident"}

            await interaction.response.send_message(
                f"✅ **Confidence updated**\n\n"
                f"*\"{belief['statement'][:100]}{'...' if len(belief['statement']) > 100 else ''}\"*\n\n"
                f"Your confidence is now: **{confidence_labels[level]}** ({level}/5)",
                ephemeral=True
            )
            logger.info(f"User {user_id} updated confidence for belief {id[:8]} to {level}")

        except Exception as e:
            logger.error(f"Error updating confidence for belief {id} for {user_id}: {e}")
            await interaction.response.send_message(
                "❌ I had trouble updating that belief. Try again in a moment.",
                ephemeral=True
            )

    @bot.tree.command(name="mark", description="Mark how important a belief is")
    @app_commands.describe(
        id="The belief ID",
        importance="How important this belief is to you (1=not important, 5=very important)"
    )
    @app_commands.choices(importance=[
        app_commands.Choice(name="1 - Not important", value=1),
        app_commands.Choice(name="2 - Somewhat important", value=2),
        app_commands.Choice(name="3 - Moderately important", value=3),
        app_commands.Choice(name="4 - Important", value=4),
        app_commands.Choice(name="5 - Very important", value=5),
    ])
    async def mark_command(interaction: discord.Interaction, id: str, importance: int):
        """Update importance level for a belief."""
        user_id = str(interaction.user.id)
        user = await get_or_create_user(user_id, username=interaction.user.name)

        try:
            belief = await get_belief_by_id(user_id, id)

            if not belief:
                await interaction.response.send_message(
                    f"❌ **Belief not found**\n\n"
                    f"No belief found with ID `{id}`.",
                    ephemeral=True
                )
                return

            await update_belief_importance(id, user_id, importance)

            importance_labels = {1: "not important", 2: "somewhat important", 3: "moderately important", 4: "important", 5: "very important"}

            await interaction.response.send_message(
                f"✅ **Importance updated**\n\n"
                f"*\"{belief['statement'][:100]}{'...' if len(belief['statement']) > 100 else ''}\"*\n\n"
                f"Importance is now: **{importance_labels[importance]}** ({'⭐' * importance})",
                ephemeral=True
            )
            logger.info(f"User {user_id} updated importance for belief {id[:8]} to {importance}")

        except Exception as e:
            logger.error(f"Error updating importance for belief {id} for {user_id}: {e}")
            await interaction.response.send_message(
                "❌ I had trouble updating that belief. Try again in a moment.",
                ephemeral=True
            )

    @bot.tree.command(name="core", description="Show your most important beliefs")
    async def core_command(interaction: discord.Interaction):
        """Show beliefs marked as most important."""
        user_id = str(interaction.user.id)
        user = await get_or_create_user(user_id, username=interaction.user.name)

        try:
            beliefs = await get_user_beliefs(user_id)

            if not beliefs:
                await interaction.response.send_message(
                    "**No beliefs recorded yet** 💭\n\n"
                    "I haven't extracted any beliefs from our conversations yet. "
                    "Keep journaling and I'll start identifying your core beliefs!",
                    ephemeral=True
                )
                return

            # Filter for important beliefs (4+ importance) and sort
            core_beliefs = [b for b in beliefs if b.get('importance', 3) >= 4]
            core_beliefs.sort(key=lambda x: (x.get('importance', 3), x.get('confidence', 0.5)), reverse=True)

            if not core_beliefs:
                await interaction.response.send_message(
                    "**No core beliefs identified yet** ⭐\n\n"
                    "You haven't marked any beliefs as highly important yet. "
                    "Use `/mark <id> 4` or `/mark <id> 5` to highlight your core beliefs, "
                    "or keep journaling and I'll start identifying patterns!",
                    ephemeral=True
                )
                return

            # Build response
            response = f"**⭐ Your Core Beliefs** ({len(core_beliefs)} beliefs)\n\n"

            for i, belief in enumerate(core_beliefs[:8], 1):  # Show up to 8
                importance = belief.get('importance', 3)
                confidence = belief['confidence'] * 100 if belief['confidence'] else 50
                response += f"**{i}.** {belief['statement']}\n"
                response += f"   *{'⭐' * importance} • {confidence:.0f}% confident • ID: {belief['id'][:8]}*\n\n"

            if len(core_beliefs) > 8:
                response += f"*...and {len(core_beliefs) - 8} more. Use `/beliefs` to see all.*"

            if len(response) > 2000:
                response = response[:1997] + "..."

            await interaction.response.send_message(response, ephemeral=True)
            logger.info(f"User {user_id} viewed core beliefs")

        except Exception as e:
            logger.error(f"Error showing core beliefs for {user_id}: {e}")
            await interaction.response.send_message(
                "❌ I had trouble loading your core beliefs. Try again in a moment.",
                ephemeral=True
            )

    @bot.tree.command(name="history", description="See how a belief has evolved over time")
    @app_commands.describe(id="The belief ID")
    async def history_command(interaction: discord.Interaction, id: str):
        """Show evolution history for a specific belief."""
        user_id = str(interaction.user.id)
        user = await get_or_create_user(user_id, username=interaction.user.name)

        try:
            belief = await get_belief_by_id(user_id, id)

            if not belief:
                await interaction.response.send_message(
                    f"❌ **Belief not found**\n\n"
                    f"No belief found with ID `{id}`.",
                    ephemeral=True
                )
                return

            history = await get_belief_history(belief['id'])

            response = f"**📈 Belief Evolution**\n\n"
            response += f"*\"{belief['statement']}\"*\n\n"

            if history:
                response += f"**Change History:**\n"
                for i, change in enumerate(history[:10], 1):  # Show up to 10 changes
                    date = change['timestamp'][:10] if change['timestamp'] else 'Unknown'

                    if change['old_confidence'] and change['new_confidence']:
                        old_conf = int(change['old_confidence'] * 100)
                        new_conf = int(change['new_confidence'] * 100)
                        response += f"**{date}:** Confidence {old_conf}% → {new_conf}%"
                        if change['trigger']:
                            response += f" ({change['trigger']})"
                        response += "\n"

                    if change['old_statement'] and change['new_statement']:
                        response += f"**{date}:** Updated statement"
                        if change['trigger']:
                            response += f" ({change['trigger']})"
                        response += f"\n   *Old:* {change['old_statement'][:100]}{'...' if len(change['old_statement']) > 100 else ''}\n"
                        response += f"   *New:* {change['new_statement'][:100]}{'...' if len(change['new_statement']) > 100 else ''}\n"

                if len(history) > 10:
                    response += f"\n*...and {len(history) - 10} earlier change(s)*"
            else:
                response += "*No recorded changes yet. This belief has remained stable.*\n"

            if len(response) > 2000:
                response = response[:1997] + "..."

            await interaction.response.send_message(response, ephemeral=True)
            logger.info(f"User {user_id} viewed history for belief {id[:8]}")

        except Exception as e:
            logger.error(f"Error showing belief history {id} for {user_id}: {e}")
            await interaction.response.send_message(
                "❌ I had trouble loading that belief's history. Try again in a moment.",
                ephemeral=True
            )

    @bot.tree.command(name="changes", description="See beliefs that have evolved recently")
    async def changes_command(interaction: discord.Interaction):
        """Show recently changed beliefs."""
        user_id = str(interaction.user.id)
        user = await get_or_create_user(user_id, username=interaction.user.name)

        try:
            changes = await get_recent_changes(user_id, days=30)

            if not changes:
                await interaction.response.send_message(
                    "**No recent changes** 📊\n\n"
                    "None of your beliefs have changed significantly in the past month. "
                    "This might mean your views are stable, or we need more conversation data!",
                    ephemeral=True
                )
                return

            response = f"**📊 Recent Belief Changes** ({len(changes)} in past month)\n\n"

            for i, change in enumerate(changes[:10], 1):  # Show up to 10
                date = change['timestamp'][:10] if change['timestamp'] else 'Unknown'
                response += f"**{i}.** {change['statement'][:80]}{'...' if len(change['statement']) > 80 else ''}\n"

                if change.get('confidence_change'):
                    old_conf = int((change.get('old_confidence', 0.5)) * 100)
                    new_conf = int((change.get('new_confidence', 0.5)) * 100)
                    response += f"   *{date}: Confidence {old_conf}% → {new_conf}%*\n"

                if change.get('statement_changed'):
                    response += f"   *{date}: Statement updated*\n"

                response += f"   *ID: {change['id'][:8]}*\n\n"

            if len(changes) > 10:
                response += f"*...and {len(changes) - 10} more changes*\n"

            response += f"\nUse `/history <id>` to see the full evolution of any belief."

            if len(response) > 2000:
                response = response[:1997] + "..."

            await interaction.response.send_message(response, ephemeral=True)
            logger.info(f"User {user_id} viewed recent belief changes")

        except Exception as e:
            logger.error(f"Error showing recent changes for {user_id}: {e}")
            await interaction.response.send_message(
                "❌ I had trouble loading recent changes. Try again in a moment.",
                ephemeral=True
            )

    @bot.tree.command(name="tensions", description="Show beliefs that might contradict each other")
    async def tensions_command(interaction: discord.Interaction):
        """Show potentially conflicting beliefs."""
        user_id = str(interaction.user.id)
        user = await get_or_create_user(user_id, username=interaction.user.name)

        try:
            tensions = await get_all_tensions(user_id)

            if not tensions:
                await interaction.response.send_message(
                    "**No tensions detected** ⚖️\n\n"
                    "I haven't found any obviously contradictory beliefs in your profile yet. "
                    "This could mean your beliefs are consistent, or I need more data to identify tensions!",
                    ephemeral=True
                )
                return

            response = f"**⚖️ Potential Tensions** ({len(tensions)} found)\n\n"
            response += "*These aren't necessarily problems—they might reflect the complexity of your thinking.*\n\n"

            for i, tension in enumerate(tensions[:5], 1):  # Show up to 5
                response += f"**{i}.** **Tension in {tension.get('topic', 'beliefs').title()}**\n"
                response += f"• {tension['belief1']['statement'][:100]}{'...' if len(tension['belief1']['statement']) > 100 else ''}\n"
                response += f"• {tension['belief2']['statement'][:100]}{'...' if len(tension['belief2']['statement']) > 100 else ''}\n"

                if tension.get('explanation'):
                    response += f"*{tension['explanation'][:150]}{'...' if len(tension['explanation']) > 150 else ''}*\n"

                response += f"*IDs: {tension['belief1']['id'][:8]}, {tension['belief2']['id'][:8]}*\n\n"

            if len(tensions) > 5:
                response += f"*...and {len(tensions) - 5} more potential tensions*\n"

            if len(response) > 2000:
                response = response[:1997] + "..."

            await interaction.response.send_message(response, ephemeral=True)
            logger.info(f"User {user_id} viewed belief tensions")

        except Exception as e:
            logger.error(f"Error finding tensions for {user_id}: {e}")
            await interaction.response.send_message(
                "❌ I had trouble analyzing belief tensions. Try again in a moment.",
                ephemeral=True
            )