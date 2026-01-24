"""Kodak Discord Bot - Main entry point."""

import os
import json
import asyncio
import random
import time
import uuid
import logging
from datetime import datetime
from collections import defaultdict
import discord
from discord import app_commands, ui
from discord.ext import commands
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger('kodak')

from db import (
    init_db, get_or_create_user, update_user_personality,
    add_belief, get_user_beliefs, get_beliefs_by_topic,
    soft_delete_belief, restore_belief, add_conversation_message, get_recent_conversation,
    get_all_topics, complete_onboarding, set_tracking_paused,
    increment_message_count, reset_message_count, get_recent_beliefs,
    clear_all_user_data, export_user_data, add_belief_relation,
    get_belief_relations, get_belief_relations_inverse, get_all_tensions,
    set_belief_importance, get_beliefs_by_importance,
    get_belief_history, get_recent_changes, update_belief_confidence,
    create_comparison_request, get_pending_requests, respond_to_comparison,
    get_comparison_request, get_shareable_beliefs, get_accepted_comparison,
    store_comparison_result, get_bridging_score,
    set_belief_visibility, set_topic_visibility, get_visibility_breakdown
)
from extractor import extract_beliefs, generate_response, find_belief_relations, summarize_beliefs, calculate_belief_similarity
from personality import (
    build_system_prompt, list_presets, get_preset, PRESETS,
    CONVERSATION_STARTERS, RETURNING_PROMPTS
)

load_dotenv()

# Bot setup
intents = discord.Intents.default()
intents.message_content = True
intents.dm_messages = True

bot = commands.Bot(command_prefix="!", intents=intents)

# How many messages before showing a belief summary
MESSAGES_BEFORE_SUMMARY = 8

# Rate limiting: messages per user per hour (0 = unlimited)
# Default is unlimited; set RATE_LIMIT_PER_HOUR env var to limit
RATE_LIMIT_PER_HOUR = int(os.getenv("RATE_LIMIT_PER_HOUR", "0"))

# Track message timestamps per user for rate limiting
user_message_times: dict[str, list[float]] = defaultdict(list)
_last_cleanup_time: float = 0.0
_CLEANUP_INTERVAL: float = 3600.0  # Clean up inactive users every hour

# Track last deleted belief per user for /undo functionality
last_deleted_belief: dict[str, dict] = {}


def _cleanup_inactive_users():
    """Remove users with no recent messages from rate limit tracking."""
    global _last_cleanup_time
    now = time.time()
    hour_ago = now - 3600

    # Find and remove inactive users
    inactive_users = [
        user_id for user_id, timestamps in user_message_times.items()
        if not timestamps or max(timestamps) < hour_ago
    ]
    for user_id in inactive_users:
        del user_message_times[user_id]

    _last_cleanup_time = now


def check_rate_limit(user_id: str) -> tuple[bool, int]:
    """
    Check if user is rate limited.
    Returns (is_allowed, seconds_until_reset).
    """
    global _last_cleanup_time

    if RATE_LIMIT_PER_HOUR <= 0:
        return True, 0

    now = time.time()
    hour_ago = now - 3600

    # Periodic cleanup of inactive users
    if now - _last_cleanup_time > _CLEANUP_INTERVAL:
        _cleanup_inactive_users()

    # Clean old timestamps and keep only last hour
    user_message_times[user_id] = [
        t for t in user_message_times[user_id] if t > hour_ago
    ]

    if len(user_message_times[user_id]) >= RATE_LIMIT_PER_HOUR:
        # Calculate when oldest message will expire
        oldest = min(user_message_times[user_id])
        seconds_until_reset = int(oldest + 3600 - now) + 1
        return False, seconds_until_reset

    # Record this message
    user_message_times[user_id].append(now)
    return True, 0


def confidence_bar(confidence: float) -> str:
    """Generate a visual confidence bar (●○) from 0.0-1.0 confidence value."""
    filled = round(confidence * 5)  # Use round() not int() for accurate display
    return "●" * filled + "○" * (5 - filled)


def importance_stars(level: int) -> str:
    """Generate visual importance stars (★☆) from 1-5 importance level."""
    level = max(1, min(5, level))  # Clamp to valid range
    return "★" * level + "☆" * (5 - level)


# === Autocomplete Functions ===

async def belief_autocomplete(
    interaction: discord.Interaction,
    current: str
) -> list[app_commands.Choice[str]]:
    """Autocomplete for belief IDs - shows statement preview."""
    beliefs = await get_user_beliefs(str(interaction.user.id))

    choices = []
    # Always offer "last" as first option
    if "last".startswith(current.lower()) or not current:
        choices.append(app_commands.Choice(name="last (most recent belief)", value="last"))

    for b in beliefs[:24]:  # Discord limit is 25 choices
        belief_id = b['id'][:8]
        statement = b['statement'][:60]
        if len(b['statement']) > 60:
            statement += "..."

        # Filter by current input
        if current.lower() in belief_id.lower() or current.lower() in b['statement'].lower():
            # Format: "abc123 - Statement preview..."
            display = f"{belief_id} - {statement}"
            if len(display) > 100:  # Discord name limit
                display = display[:97] + "..."
            choices.append(app_commands.Choice(name=display, value=belief_id))

        if len(choices) >= 25:
            break

    return choices[:25]


async def topic_autocomplete(
    interaction: discord.Interaction,
    current: str
) -> list[app_commands.Choice[str]]:
    """Autocomplete for topic names."""
    topics = await get_all_topics(str(interaction.user.id))

    choices = []
    for topic in topics:
        if current.lower() in topic.lower() or not current:
            choices.append(app_commands.Choice(name=topic, value=topic))
        if len(choices) >= 25:
            break

    return choices


# === Onboarding Views ===

class PersonalitySelect(ui.Select):
    """Dropdown for selecting personality preset."""

    def __init__(self):
        options = [
            discord.SelectOption(
                label=preset["name"],
                value=key,
                description=preset["description"][:100],
                emoji=preset["emoji"]
            )
            for key, preset in PRESETS.items()
        ]
        super().__init__(
            placeholder="Choose a personality...",
            options=options,
            min_values=1,
            max_values=1
        )

    async def callback(self, interaction: discord.Interaction):
        preset_key = self.values[0]
        preset = PRESETS[preset_key]

        # Save personality
        await update_user_personality(
            str(interaction.user.id),
            warmth=preset["warmth"],
            playfulness=preset["playfulness"],
            directness=preset["directness"],
            formality=preset["formality"]
        )

        # Show example
        example = preset["example_exchange"]
        embed = discord.Embed(
            title=f"{preset['emoji']} {preset['name']}",
            description=preset["description"],
            color=discord.Color.blue()
        )
        embed.add_field(
            name="Here's how I'd respond:",
            value=f"**You:** {example['user']}\n**Kodak:** {example['bot']}",
            inline=False
        )

        # Show extraction mode selection
        view = ExtractionModeView()
        await interaction.response.edit_message(
            content=None,
            embed=embed,
            view=view
        )


class PersonalitySelectView(ui.View):
    """View containing personality dropdown."""

    def __init__(self):
        super().__init__(timeout=300)
        self.add_item(PersonalitySelect())


class ExtractionModeView(ui.View):
    """View for selecting extraction mode."""

    def __init__(self):
        super().__init__(timeout=300)

    @ui.button(label="Active", style=discord.ButtonStyle.primary, emoji="🎯")
    async def active_mode(self, interaction: discord.Interaction, button: ui.Button):
        await self._set_mode(interaction, "active")

    @ui.button(label="Chill", style=discord.ButtonStyle.secondary, emoji="🌊")
    async def passive_mode(self, interaction: discord.Interaction, button: ui.Button):
        await self._set_mode(interaction, "passive")

    async def _set_mode(self, interaction: discord.Interaction, mode: str):
        await update_user_personality(str(interaction.user.id), extraction_mode=mode)
        await complete_onboarding(str(interaction.user.id))

        mode_desc = {
            "active": "I'll ask follow-up questions to understand you better.",
            "passive": "I'll mostly listen and let things emerge naturally."
        }

        # Show conversation starters
        starters = random.sample(CONVERSATION_STARTERS, 3)
        starter_text = "\n".join([f"{s['emoji']} *\"{s['prompt']}\"*" for s in starters])

        embed = discord.Embed(
            title="You're all set!",
            description=f"**Mode:** {mode.title()} — {mode_desc[mode]}\n\n"
                       f"Ready when you are. Here are some ways to start:\n\n{starter_text}\n\n"
                       f"Or just say whatever's on your mind.",
            color=discord.Color.green()
        )
        embed.set_footer(text="Tip: Use /help anytime to see what I can do.")

        await interaction.response.edit_message(embed=embed, view=None)


class ConfirmClearView(ui.View):
    """Confirmation view for clearing all data."""

    def __init__(self):
        super().__init__(timeout=60)

    @ui.button(label="Yes, delete everything", style=discord.ButtonStyle.danger)
    async def confirm(self, interaction: discord.Interaction, button: ui.Button):
        await clear_all_user_data(str(interaction.user.id))
        await interaction.response.edit_message(
            content="All your data has been deleted. If you message me again, we'll start fresh.",
            view=None
        )

    @ui.button(label="Cancel", style=discord.ButtonStyle.secondary)
    async def cancel(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.edit_message(
            content="Cancelled. Your data is safe.",
            view=None
        )


class ShareExportView(ui.View):
    """View for confirming shareable belief export."""

    def __init__(self, export_data: dict, filename: str):
        super().__init__(timeout=300)  # 5 minute timeout
        self.export_data = export_data
        self.filename = filename

    @ui.button(label="Download Export", style=discord.ButtonStyle.primary, emoji="📥")
    async def download(self, interaction: discord.Interaction, button: ui.Button):
        json_str = json.dumps(self.export_data, indent=2)
        file = discord.File(
            fp=__import__('io').BytesIO(json_str.encode()),
            filename=self.filename
        )
        await interaction.response.send_message(
            "Here's your export file. Send this to someone for comparison.",
            file=file,
            ephemeral=True
        )

    @ui.button(label="Cancel", style=discord.ButtonStyle.secondary)
    async def cancel(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.edit_message(
            content="Export cancelled.",
            embed=None,
            view=None
        )


class ComparisonRequestView(ui.View):
    """View for accepting/declining comparison requests."""

    def __init__(self, request_id: str, requester_id: str, requester_name: str):
        super().__init__(timeout=86400)  # 24 hour timeout
        self.request_id = request_id
        self.requester_id = requester_id
        self.requester_name = requester_name

    @ui.button(label="Accept", style=discord.ButtonStyle.success, emoji="✓")
    async def accept(self, interaction: discord.Interaction, button: ui.Button):
        success = await respond_to_comparison(
            self.request_id,
            str(interaction.user.id),
            accept=True
        )

        if success:
            await interaction.response.edit_message(
                content=f"Accepted! Calculating comparison with {self.requester_name}...",
                view=None
            )

            # Calculate and show comparison to both users
            await show_comparison_results(
                interaction,
                self.requester_id,
                str(interaction.user.id),
                self.requester_name,
                interaction.user.display_name,
                self.request_id
            )
        else:
            await interaction.response.edit_message(
                content="Something went wrong. The request may have expired.",
                view=None
            )

    @ui.button(label="Decline", style=discord.ButtonStyle.secondary, emoji="✗")
    async def decline(self, interaction: discord.Interaction, button: ui.Button):
        await respond_to_comparison(
            self.request_id,
            str(interaction.user.id),
            accept=False
        )
        await interaction.response.edit_message(
            content=f"Declined comparison request from {self.requester_name}.",
            view=None
        )


async def show_comparison_results(
    interaction: discord.Interaction,
    user_a_id: str,
    user_b_id: str,
    user_a_name: str,
    user_b_name: str,
    request_id: str = None
):
    """Calculate and display comparison results to both users."""
    # Get shareable beliefs for both users
    beliefs_a = await get_shareable_beliefs(user_a_id)
    beliefs_b = await get_shareable_beliefs(user_b_id)

    if not beliefs_a or not beliefs_b:
        await interaction.followup.send(
            "One or both users don't have enough shareable beliefs for comparison.",
            ephemeral=True
        )
        return

    # Calculate similarity
    comparison = await calculate_belief_similarity(beliefs_a, beliefs_b)

    # Store comparison results for bridging score
    if request_id:
        # Identify bridging beliefs (agreements despite differences)
        bridging_beliefs = []
        if comparison['overall_similarity'] < 0.5:
            for ag in comparison.get('agreements', []):
                # Safely get belief IDs (may be missing in imported files)
                belief_a = ag.get('belief_a', {})
                belief_b = ag.get('belief_b', {})
                id_a = belief_a.get('id')
                id_b = belief_b.get('id')

                # Only add if both beliefs have valid IDs
                if id_a and id_b:
                    # Add bridging belief for user A
                    bridging_beliefs.append({
                        'belief_id': id_a,
                        'matched_id': id_b,
                        'user_id': user_a_id
                    })
                    # Add bridging belief for user B
                    bridging_beliefs.append({
                        'belief_id': id_b,
                        'matched_id': id_a,
                        'user_id': user_b_id
                    })

        await store_comparison_result(
            request_id=request_id,
            user_a_id=user_a_id,
            user_b_id=user_b_id,
            overall_similarity=comparison['overall_similarity'],
            core_similarity=comparison['core_similarity'],
            agreement_count=len(comparison.get('agreements', [])),
            difference_count=len(comparison.get('differences', [])),
            bridging_beliefs=bridging_beliefs
        )

    # Build result embed
    overall_pct = int(comparison['overall_similarity'] * 100)
    core_pct = int(comparison['core_similarity'] * 100)

    embed = discord.Embed(
        title=f"🔄 Belief Comparison: {user_a_name} ↔ {user_b_name}",
        color=discord.Color.blue()
    )

    # Overall scores
    overall_bar = "█" * (overall_pct // 10) + "░" * (10 - overall_pct // 10)
    core_bar = "█" * (core_pct // 10) + "░" * (10 - core_pct // 10)

    embed.add_field(
        name="Similarity Scores",
        value=f"**Overall:** [{overall_bar}] {overall_pct}%\n"
              f"**Core beliefs:** [{core_bar}] {core_pct}%",
        inline=False
    )

    # Summary
    if comparison.get('summary'):
        embed.add_field(
            name="Summary",
            value=comparison['summary'],
            inline=False
        )

    # Agreements
    if comparison['agreements']:
        agreement_text = ""
        for ag in comparison['agreements'][:3]:
            stmt_a = ag['belief_a']['statement'][:50]
            stmt_b = ag['belief_b']['statement'][:50]
            if len(ag['belief_a']['statement']) > 50:
                stmt_a += "..."
            agreement_text += f"🤝 *\"{stmt_a}\"*\n"
            if ag.get('note'):
                agreement_text += f"   {ag['note']}\n"
        embed.add_field(
            name=f"Agreements ({len(comparison['agreements'])} found)",
            value=agreement_text or "None found",
            inline=False
        )

    # Differences
    if comparison['differences']:
        diff_text = ""
        for df in comparison['differences'][:3]:
            stmt_a = df['belief_a']['statement'][:40]
            stmt_b = df['belief_b']['statement'][:40]
            if len(df['belief_a']['statement']) > 40:
                stmt_a += "..."
            if len(df['belief_b']['statement']) > 40:
                stmt_b += "..."
            diff_text += f"⚡ *\"{stmt_a}\"* vs *\"{stmt_b}\"*\n"
            if df.get('note'):
                diff_text += f"   {df['note']}\n"
        embed.add_field(
            name=f"Interesting Differences ({len(comparison['differences'])} found)",
            value=diff_text or "None found",
            inline=False
        )

    embed.set_footer(text="Only shareable beliefs were compared. Use /bridging to see your bridging score.")

    # Send to the user who triggered this (the one who accepted)
    await interaction.followup.send(embed=embed)

    # Try to DM the requester too
    try:
        requester = await bot.fetch_user(int(user_a_id))
        await requester.send(embed=embed)
    except discord.errors.Forbidden:
        pass  # Can't DM them


# === Bot Events ===

@bot.event
async def on_ready():
    """Called when bot is ready."""
    await init_db()
    logger.info(f"Bot started as {bot.user} (ID: {bot.user.id})")

    # Sync slash commands
    try:
        synced = await bot.tree.sync()
        logger.info(f"Synced {len(synced)} slash commands")
    except Exception as e:
        logger.error(f"Failed to sync commands: {e}")


@bot.event
async def on_message(message: discord.Message):
    """Handle incoming messages."""
    # Ignore own messages
    if message.author == bot.user:
        return

    # Ignore messages that are slash commands
    if message.content.startswith("/"):
        return

    # Check if this is a DM or if bot is mentioned in a channel
    is_dm = isinstance(message.channel, discord.DMChannel)
    is_mentioned = bot.user in message.mentions

    # Only respond in DMs or when mentioned
    if not is_dm and not is_mentioned:
        return

    context = "DM" if is_dm else f"channel:{message.channel.id}"
    logger.info(f"Message from user:{message.author.id} in {context}")

    # Check rate limit
    is_allowed, wait_seconds = check_rate_limit(str(message.author.id))
    if not is_allowed:
        logger.info(f"Rate limited user:{message.author.id} (wait {wait_seconds}s)")
        minutes = wait_seconds // 60
        await message.reply(
            f"You've hit the rate limit ({RATE_LIMIT_PER_HOUR} messages/hour). "
            f"Try again in {minutes + 1} minute{'s' if minutes > 0 else ''}.",
            mention_author=False
        )
        return

    # Remove the mention from the message content
    content = message.content.replace(f"<@{bot.user.id}>", "").strip()

    # Get or create user
    user = await get_or_create_user(
        str(message.author.id),
        message.author.name
    )

    # Check for natural language commands
    lower_content = content.lower()
    if any(phrase in lower_content for phrase in ["show me my map", "show my map", "what do i believe", "my beliefs"]):
        await handle_map_request(message, user)
        return
    if any(phrase in lower_content for phrase in ["pause tracking", "stop tracking", "don't track"]):
        await set_tracking_paused(str(message.author.id), True)
        await message.reply("Got it, I've paused belief tracking. We can still chat—I just won't be taking notes. Say 'resume tracking' whenever you're ready.", mention_author=False)
        return
    if any(phrase in lower_content for phrase in ["resume tracking", "start tracking"]):
        await set_tracking_paused(str(message.author.id), False)
        await message.reply("Tracking resumed! I'll start mapping our conversations again.", mention_author=False)
        return

    # Handle empty content after mention
    if not content:
        if not user.get("onboarding_complete"):
            await send_onboarding(message)
        else:
            starters = random.sample(CONVERSATION_STARTERS, 3)
            starter_text = "\n".join([f"{s['emoji']} *\"{s['prompt']}\"*" for s in starters])
            await message.reply(
                f"{random.choice(RETURNING_PROMPTS)}\n\n{starter_text}",
                mention_author=False
            )
        return

    # Check if user needs onboarding
    if not user.get("onboarding_complete"):
        await send_onboarding(message)
        return

    async with message.channel.typing():
        # Get conversation history
        history = await get_recent_conversation(str(message.author.id))

        # Get existing beliefs for context
        existing_beliefs = await get_user_beliefs(str(message.author.id))

        # Build system prompt
        system_prompt = build_system_prompt(
            user_settings=user,
            existing_beliefs=existing_beliefs,
            is_dm=is_dm
        )

        # Store user message
        await add_conversation_message(
            str(message.author.id),
            "user",
            content,
            str(message.channel.id),
            str(message.id)
        )

        # Extract beliefs from the message (runs in parallel with response generation)
        # Skip if tracking is paused
        extraction_task = None
        if not user.get("tracking_paused"):
            extraction_task = asyncio.create_task(
                extract_beliefs(content, history, existing_beliefs)
            )

        # Generate response
        response = await generate_response(content, system_prompt, history)

        # Store assistant message
        await add_conversation_message(
            str(message.author.id),
            "assistant",
            response
        )

        # Process extraction results
        new_beliefs = []
        if extraction_task:
            extraction_result = await extraction_task
            belief_count = len(extraction_result.get("beliefs", []))
            if belief_count > 0:
                logger.info(f"Extracted {belief_count} belief(s) from user:{message.author.id}")

            for belief_data in extraction_result.get("beliefs", []):
                new_belief = await add_belief(
                    user_id=str(message.author.id),
                    statement=belief_data["statement"],
                    confidence=belief_data.get("confidence", 0.5),
                    source_type=belief_data.get("source_type"),
                    context=content[:200],
                    message_id=str(message.id),
                    channel_id=str(message.channel.id),
                    topics=belief_data.get("topics", [])
                )
                new_beliefs.append(new_belief)

                # Find and store relations to existing beliefs
                relations = await find_belief_relations(new_belief, existing_beliefs)
                for rel in relations:
                    await add_belief_relation(
                        source_id=new_belief["id"],
                        target_id=rel["target_id"],
                        relation_type=rel["relation_type"],
                        strength=rel.get("strength", 0.5)
                    )

        # Send response
        await message.reply(response, mention_author=False)

        # Check if we should show a belief summary
        if not user.get("tracking_paused"):
            msg_count = await increment_message_count(str(message.author.id))
            if msg_count >= MESSAGES_BEFORE_SUMMARY and new_beliefs:
                await send_belief_summary(message, str(message.author.id))


async def send_onboarding(message: discord.Message):
    """Send the onboarding flow to a new user."""
    embed = discord.Embed(
        title="Hey! I'm Kodak.",
        description=(
            "I'm here to have great conversations with you—and along the way, "
            "I'll help you build a map of what you believe and why.\n\n"
            "Think of it like a mirror for your mind. Everything stays private "
            "to you, and you can delete anything anytime.\n\n"
            "**First, how would you like me to show up?**"
        ),
        color=discord.Color.blue()
    )
    embed.set_footer(text="🔒 Your beliefs stay private. Use /forget or /clear anytime.")

    view = PersonalitySelectView()
    await message.reply(embed=embed, view=view, mention_author=False)


async def send_belief_summary(message: discord.Message, user_id: str):
    """Send a summary of recently captured beliefs."""
    recent_beliefs = await get_recent_beliefs(user_id, limit=5)

    if not recent_beliefs:
        return

    await reset_message_count(user_id)

    belief_lines = []
    for i, b in enumerate(recent_beliefs[:3], 1):
        belief_lines.append(f"{i}. {b['statement']}")

    embed = discord.Embed(
        title="📸 Quick snapshot",
        description=(
            "Here's what I've picked up from our recent chat:\n\n"
            + "\n".join(belief_lines)
            + "\n\n*Anything off? Use `/forget` or just tell me.*"
        ),
        color=discord.Color.light_grey()
    )

    await message.channel.send(embed=embed)


async def handle_map_request(message: discord.Message, user: dict):
    """Handle natural language map request."""
    beliefs = await get_user_beliefs(str(message.author.id))

    if not beliefs:
        await message.reply(
            "No beliefs mapped yet. Let's chat and I'll start building your map!",
            mention_author=False
        )
        return

    topics = await get_all_topics(str(message.author.id))
    summary = await summarize_beliefs(beliefs)

    response = f"**Your Belief Map**\n\n"
    response += f"*{len(beliefs)} beliefs across {len(topics)} topics*\n\n"
    response += summary
    response += f"\n\n**Topics:** {', '.join(topics) if topics else 'None yet'}"

    if len(response) > 2000:
        response = response[:1997] + "..."

    await message.reply(response, mention_author=False)


# === Slash Commands ===

@bot.tree.command(name="help", description="Learn what Kodak can do")
async def help_command(interaction: discord.Interaction):
    """Show help information."""
    embed = discord.Embed(
        title="Kodak Commands",
        description="I map your beliefs through conversation. Here's what I can do:",
        color=discord.Color.blue()
    )

    embed.add_field(
        name="🗺️ Explore Your Map",
        value=(
            "`/map` — See your belief map summarized\n"
            "`/explore [topic]` — Dive into beliefs about something\n"
            "`/beliefs` — Raw list with IDs and importance\n"
            "`/belief [id]` — View one belief with connections\n"
            "`/core` — Show only your most important beliefs\n"
            "`/tensions` — Show beliefs that might contradict\n"
            "`/history [id]` — See how a belief has evolved\n"
            "`/changes` — See beliefs that changed recently"
        ),
        inline=False
    )

    embed.add_field(
        name="⭐ Importance & Confidence",
        value=(
            "`/mark [id] [1-5]` — Set how important a belief is\n"
            "`/confidence [id] [1-5]` — Update how certain you are\n"
            "*1=peripheral/uncertain, 5=core/certain*"
        ),
        inline=False
    )

    embed.add_field(
        name="📤 Share & Compare",
        value=(
            "`/share` — Create shareable snapshot (view in Discord)\n"
            "`/share-export` — Export shareable beliefs as file\n"
            "`/compare-file` — Compare with someone's exported file\n"
            "`/bridging` — See your bridging score\n"
            "`/privacy` — Control which beliefs are shareable"
        ),
        inline=False
    )

    embed.add_field(
        name="🎭 Customize Me",
        value=(
            "`/setup` — Choose a personality preset\n"
            "`/style` — Fine-tune personality dimensions"
        ),
        inline=False
    )

    embed.add_field(
        name="🔒 Privacy & Control",
        value=(
            "`/forget [id]` — Remove a specific belief\n"
            "`/undo` — Restore the last forgotten belief\n"
            "`/pause` — Pause belief tracking\n"
            "`/resume` — Resume belief tracking\n"
            "`/export` — Download all your data\n"
            "`/backup` — Download database backup\n"
            "`/clear` — Delete everything"
        ),
        inline=False
    )

    embed.add_field(
        name="📊 Reading Confidence",
        value=(
            "`[●●●●●]` Certain — `[●●●○○]` Moderate — `[●○○○○]` Tentative"
        ),
        inline=False
    )

    embed.set_footer(text="Command responses are private and disappear after a while. Use /export to save.")

    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(name="setup", description="Choose a personality preset")
async def setup_command(interaction: discord.Interaction):
    """Configure the bot's personality with preview."""
    embed = discord.Embed(
        title="Choose a Personality",
        description="Each personality has a different style. Pick one to see an example.",
        color=discord.Color.blue()
    )

    view = PersonalitySelectView()
    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


@bot.tree.command(name="map", description="See your belief map")
async def map_command(interaction: discord.Interaction):
    """Show the user's belief map."""
    await interaction.response.defer(ephemeral=True)

    beliefs = await get_user_beliefs(str(interaction.user.id))

    if not beliefs:
        await interaction.followup.send(
            "No beliefs mapped yet. Start chatting with me to build your map!",
            ephemeral=True
        )
        return

    topics = await get_all_topics(str(interaction.user.id))
    summary = await summarize_beliefs(beliefs)

    # Build ASCII-style visualization
    response = f"**Your Belief Map**\n"
    response += f"*{len(beliefs)} beliefs across {len(topics)} topics*\n\n"

    # Group beliefs by topic for visualization
    if topics:
        response += "```\n"
        for topic in topics[:5]:  # Limit to 5 topics
            topic_beliefs = await get_beliefs_by_topic(str(interaction.user.id), topic)
            response += f"{'─' * 40}\n"
            response += f"  {topic.upper()}\n"
            response += f"{'─' * 40}\n"
            for b in topic_beliefs[:2]:  # Limit to 2 beliefs per topic for space
                conf = confidence_bar(b.get('confidence', 0.5))
                response += f"  [{conf}] {b['statement']}\n"
            response += "\n"
        response += "```\n"

    response += f"\n{summary}"
    response += f"\n\nUse `/explore [topic]` to dive deeper."

    if len(response) > 2000:
        response = response[:1997] + "..."

    await interaction.followup.send(response, ephemeral=True)


@bot.tree.command(name="explore", description="Explore beliefs about a topic")
@app_commands.describe(topic="The topic to explore")
@app_commands.autocomplete(topic=topic_autocomplete)
async def explore_command(interaction: discord.Interaction, topic: str):
    """Explore beliefs about a specific topic."""
    await interaction.response.defer(ephemeral=True)

    beliefs = await get_beliefs_by_topic(str(interaction.user.id), topic.lower())

    if not beliefs:
        all_beliefs = await get_user_beliefs(str(interaction.user.id))
        beliefs = [
            b for b in all_beliefs
            if topic.lower() in b["statement"].lower()
            or topic.lower() in " ".join(b.get("topics", []))
        ]

    if not beliefs:
        topics = await get_all_topics(str(interaction.user.id))

        if not topics:
            await interaction.followup.send(
                f"No beliefs found about '{topic}'.\n\n"
                "You don't have any topics mapped yet. Keep chatting and I'll build your map!",
                ephemeral=True
            )
            return

        # Find similar topics (partial matches)
        search_lower = topic.lower()
        similar = [t for t in topics if search_lower in t or t in search_lower]

        # Also check topic synonyms for related concepts
        from db import TOPIC_SYNONYMS
        # Find canonical form if searched term is a synonym
        canonical = TOPIC_SYNONYMS.get(search_lower)
        if canonical and canonical in topics and canonical not in similar:
            similar.append(canonical)
        # Find synonyms that map to the same canonical as existing topics
        for t in topics:
            if TOPIC_SYNONYMS.get(search_lower) == t or TOPIC_SYNONYMS.get(t) == search_lower:
                if t not in similar:
                    similar.append(t)

        response = f"No beliefs found about '{topic}'.\n\n"

        if similar:
            response += "**Similar topics you have:**\n"
            for t in similar[:5]:
                response += f"• `/explore {t}`\n"
            response += "\n"

        # Show other topics if there's room
        other_topics = [t for t in topics if t not in similar][:8]
        if other_topics:
            response += f"**Other topics:** {', '.join(other_topics)}"

        await interaction.followup.send(response, ephemeral=True)
        return

    summary = await summarize_beliefs(beliefs, topic)
    response = f"**Beliefs about: {topic}**\n\n{summary}"

    if len(response) > 2000:
        response = response[:1997] + "..."

    await interaction.followup.send(response, ephemeral=True)


@bot.tree.command(name="beliefs", description="List your beliefs (raw)")
async def beliefs_command(interaction: discord.Interaction):
    """List all beliefs in raw format."""
    await interaction.response.defer(ephemeral=True)

    beliefs = await get_user_beliefs(str(interaction.user.id))

    if not beliefs:
        await interaction.followup.send("No beliefs mapped yet.", ephemeral=True)
        return

    lines = []
    for b in beliefs[:20]:
        conf = confidence_bar(b.get('confidence', 0.5))
        imp = importance_stars(b.get('importance', 3))
        topics = ", ".join(b.get("topics", []))
        topic_str = f" *({topics})*" if topics else ""
        lines.append(f"`{b['id'][:8]}` {imp} [{conf}] {b['statement']}{topic_str}")

    response = "**Your Beliefs:**\n"
    response += "*★=importance, ●=confidence*\n\n"
    response += "\n\n".join(lines)

    if len(beliefs) > 20:
        response += f"\n\n*...and {len(beliefs) - 20} more*"

    response += f"\n\n*Use `/mark [id] [1-5]` to set importance. `/core` for important beliefs only.*"

    if len(response) > 2000:
        response = response[:1997] + "..."

    await interaction.followup.send(response, ephemeral=True)


@bot.tree.command(name="belief", description="View a single belief in detail")
@app_commands.describe(belief_id="The belief ID (first 8 characters)")
@app_commands.autocomplete(belief_id=belief_autocomplete)
async def belief_command(interaction: discord.Interaction, belief_id: str):
    """View a single belief with its relations."""
    await interaction.response.defer(ephemeral=True)

    beliefs = await get_user_beliefs(str(interaction.user.id))
    matching = [b for b in beliefs if b["id"].startswith(belief_id)]

    if not matching:
        await interaction.followup.send(
            f"No belief found starting with `{belief_id}`. Use `/beliefs` to see IDs.",
            ephemeral=True
        )
        return

    if len(matching) > 1:
        await interaction.followup.send(
            f"Multiple beliefs match `{belief_id}`. Please be more specific.",
            ephemeral=True
        )
        return

    belief = matching[0]

    # Get relations in both directions
    outgoing_relations = await get_belief_relations(belief["id"])
    incoming_relations = await get_belief_relations_inverse(belief["id"])

    # Build indicators
    conf = confidence_bar(belief.get('confidence', 0.5))
    imp = importance_stars(belief.get('importance', 3))
    topics = ", ".join(belief.get("topics", [])) or "none"

    response = f"**{belief['statement']}**\n\n"
    response += f"Confidence: [{conf}] {int(belief.get('confidence', 0.5) * 100)}%\n"
    response += f"Importance: {imp}\n"
    response += f"Source: {belief.get('source_type', 'unknown')}\n"
    response += f"Topics: {topics}\n"
    response += f"ID: `{belief['id'][:8]}`\n"

    # Group relations by type
    foundations = [r for r in outgoing_relations if r["relation_type"] in ("assumes", "derives_from")]
    supports = [r for r in outgoing_relations if r["relation_type"] == "supports"]
    tensions = [r for r in outgoing_relations if r["relation_type"] == "contradicts"]
    related = [r for r in outgoing_relations if r["relation_type"] == "relates_to"]

    # Beliefs that depend on this one (from incoming)
    supported_by_this = [r for r in incoming_relations if r["relation_type"] in ("assumes", "derives_from")]

    has_connections = foundations or supports or tensions or related or supported_by_this

    if has_connections:
        response += "\n"

        if foundations:
            response += "```\n┌─ FOUNDATIONS (this belief assumes):\n"
            for r in foundations:
                stmt = r.get("target_statement", "")[:50]
                if len(r.get("target_statement", "")) > 50:
                    stmt += "..."
                response += f"│  • {stmt}\n"
            response += "```\n"

        if supports:
            response += "```\n├─ SUPPORTS:\n"
            for r in supports:
                stmt = r.get("target_statement", "")[:50]
                if len(r.get("target_statement", "")) > 50:
                    stmt += "..."
                response += f"│  • {stmt}\n"
            response += "```\n"

        if supported_by_this:
            response += "```\n├─ SUPPORTS THIS (beliefs built on this one):\n"
            for r in supported_by_this:
                stmt = r.get("source_statement", "")[:50]
                if len(r.get("source_statement", "")) > 50:
                    stmt += "..."
                response += f"│  • {stmt}\n"
            response += "```\n"

        if tensions:
            response += "```\n├─ ⚡ TENSIONS:\n"
            for r in tensions:
                stmt = r.get("target_statement", "")[:50]
                if len(r.get("target_statement", "")) > 50:
                    stmt += "..."
                response += f"│  • {stmt}\n"
            response += "│  (You hold both — worth exploring?)\n"
            response += "```\n"

        if related:
            response += "```\n└─ RELATED:\n"
            for r in related[:3]:  # Limit related to avoid clutter
                stmt = r.get("target_statement", "")[:50]
                if len(r.get("target_statement", "")) > 50:
                    stmt += "..."
                response += f"   • {stmt}\n"
            response += "```\n"
    else:
        response += "\n*No connections to other beliefs yet.*\n"

    response += f"\n`/mark {belief['id'][:8]} [1-5]` to change importance"
    response += f" • `/forget {belief['id'][:8]}` to remove"

    if len(response) > 2000:
        response = response[:1997] + "..."

    await interaction.followup.send(response, ephemeral=True)


@bot.tree.command(name="forget", description="Delete a belief from your map")
@app_commands.describe(belief_id="The belief ID (first 8 characters) or 'last' for most recent")
@app_commands.autocomplete(belief_id=belief_autocomplete)
async def forget_command(interaction: discord.Interaction, belief_id: str):
    """Delete a belief."""
    await interaction.response.defer(ephemeral=True)

    if belief_id.lower() == "last":
        recent = await get_recent_beliefs(str(interaction.user.id), limit=1)
        if not recent:
            await interaction.followup.send("No beliefs to forget.", ephemeral=True)
            return
        belief = recent[0]
    else:
        beliefs = await get_user_beliefs(str(interaction.user.id))
        matching = [b for b in beliefs if b["id"].startswith(belief_id)]

        if not matching:
            await interaction.followup.send(
                f"No belief found starting with `{belief_id}`. Use `/beliefs` to see IDs.",
                ephemeral=True
            )
            return

        if len(matching) > 1:
            await interaction.followup.send(
                f"Multiple beliefs match `{belief_id}`. Please be more specific.",
                ephemeral=True
            )
            return

        belief = matching[0]

    success = await soft_delete_belief(belief["id"], str(interaction.user.id))

    if success:
        # Store for potential undo
        last_deleted_belief[str(interaction.user.id)] = belief
        logger.info(f"Belief forgotten by user:{interaction.user.id} - {belief['id'][:8]}")

        await interaction.followup.send(
            f"Forgotten: *{belief['statement']}*\n\n"
            f"*Changed your mind? Use `/undo` to restore it.*",
            ephemeral=True
        )
    else:
        await interaction.followup.send("Hmm, couldn't delete that one.", ephemeral=True)


@bot.tree.command(name="undo", description="Restore the last forgotten belief")
async def undo_command(interaction: discord.Interaction):
    """Restore the most recently forgotten belief."""
    user_id = str(interaction.user.id)

    if user_id not in last_deleted_belief:
        await interaction.response.send_message(
            "Nothing to undo. Use `/forget` first to delete a belief.",
            ephemeral=True
        )
        return

    belief = last_deleted_belief[user_id]
    success = await restore_belief(belief["id"], user_id)

    if success:
        # Clear from undo buffer
        del last_deleted_belief[user_id]
        logger.info(f"Belief restored by user:{user_id} - {belief['id'][:8]}")

        await interaction.response.send_message(
            f"Restored: *{belief['statement']}*",
            ephemeral=True
        )
    else:
        # Might have been permanently deleted or already restored
        del last_deleted_belief[user_id]
        await interaction.response.send_message(
            "Couldn't restore that belief. It may have already been restored or permanently deleted.",
            ephemeral=True
        )


@bot.tree.command(name="confidence", description="Update how confident you are in a belief")
@app_commands.describe(
    belief_id="The belief ID (first 8 characters)",
    level="1 (very uncertain) to 5 (very certain)"
)
@app_commands.autocomplete(belief_id=belief_autocomplete)
async def confidence_command(interaction: discord.Interaction, belief_id: str, level: int):
    """Update confidence and record evolution."""
    if level < 1 or level > 5:
        await interaction.response.send_message(
            "Confidence level must be between 1 and 5.",
            ephemeral=True
        )
        return

    beliefs = await get_user_beliefs(str(interaction.user.id))
    matching = [b for b in beliefs if b["id"].startswith(belief_id)]

    if not matching:
        await interaction.response.send_message(
            f"No belief found starting with `{belief_id}`. Use `/beliefs` to see IDs.",
            ephemeral=True
        )
        return

    if len(matching) > 1:
        await interaction.response.send_message(
            f"Multiple beliefs match `{belief_id}`. Please be more specific.",
            ephemeral=True
        )
        return

    belief = matching[0]
    new_confidence = level / 5.0  # Convert 1-5 to 0.0-1.0

    old_conf_pct = int(belief.get('confidence', 0.5) * 100)
    new_conf_pct = int(new_confidence * 100)

    success = await update_belief_confidence(
        belief["id"],
        str(interaction.user.id),
        new_confidence,
        trigger="Manual update via /confidence"
    )

    if success:
        direction = "↑" if new_conf_pct > old_conf_pct else "↓" if new_conf_pct < old_conf_pct else "="
        conf_bar = "●" * level + "○" * (5 - level)

        confidence_labels = {
            1: "Very uncertain",
            2: "Somewhat uncertain",
            3: "Moderate",
            4: "Fairly confident",
            5: "Very certain"
        }

        await interaction.response.send_message(
            f"Updated confidence: {old_conf_pct}% {direction} {new_conf_pct}% [{conf_bar}]\n"
            f"**{confidence_labels[level]}**\n\n"
            f"*{belief['statement'][:80]}{'...' if len(belief['statement']) > 80 else ''}*\n\n"
            f"Use `/history {belief['id'][:8]}` to see this belief's evolution.",
            ephemeral=True
        )
    else:
        await interaction.response.send_message("Couldn't update that belief.", ephemeral=True)


@bot.tree.command(name="mark", description="Set how important a belief is to you")
@app_commands.describe(
    belief_id="The belief ID (first 8 characters)",
    importance="1 (peripheral) to 5 (core)"
)
@app_commands.autocomplete(belief_id=belief_autocomplete)
async def mark_command(interaction: discord.Interaction, belief_id: str, importance: int):
    """Mark a belief's importance level."""
    if importance < 1 or importance > 5:
        await interaction.response.send_message(
            "Importance must be between 1 and 5.",
            ephemeral=True
        )
        return

    beliefs = await get_user_beliefs(str(interaction.user.id))
    matching = [b for b in beliefs if b["id"].startswith(belief_id)]

    if not matching:
        await interaction.response.send_message(
            f"No belief found starting with `{belief_id}`. Use `/beliefs` to see IDs.",
            ephemeral=True
        )
        return

    if len(matching) > 1:
        await interaction.response.send_message(
            f"Multiple beliefs match `{belief_id}`. Please be more specific.",
            ephemeral=True
        )
        return

    belief = matching[0]
    success = await set_belief_importance(belief["id"], str(interaction.user.id), importance)

    if success:
        importance_labels = {
            1: "Peripheral — passing thought",
            2: "Low — hold loosely",
            3: "Medium — significant but flexible",
            4: "High — very important",
            5: "Core — foundational to who you are"
        }
        stars = importance_stars(importance)
        await interaction.response.send_message(
            f"Marked as **{importance_labels[importance]}** ({stars}):\n"
            f"*{belief['statement']}*",
            ephemeral=True
        )
    else:
        await interaction.response.send_message("Couldn't update that belief.", ephemeral=True)


@bot.tree.command(name="core", description="Show only your most important beliefs")
async def core_command(interaction: discord.Interaction):
    """Show beliefs marked as high importance (4-5)."""
    await interaction.response.defer(ephemeral=True)

    beliefs = await get_beliefs_by_importance(str(interaction.user.id), min_importance=4)

    if not beliefs:
        await interaction.followup.send(
            "No core beliefs marked yet.\n"
            "Use `/mark [id] 4` or `/mark [id] 5` to mark important beliefs.",
            ephemeral=True
        )
        return

    lines = []
    for b in beliefs[:15]:
        conf = confidence_bar(b.get('confidence', 0.5))
        imp = importance_stars(b.get('importance', 3))
        lines.append(f"{imp} [{conf}] {b['statement']}")

    response = "**Your Core Beliefs (★★★★+):**\n\n"
    response += "\n\n".join(lines)

    if len(beliefs) > 15:
        response += f"\n\n*...and {len(beliefs) - 15} more*"

    await interaction.followup.send(response, ephemeral=True)


@bot.tree.command(name="tensions", description="Show beliefs that might contradict each other")
async def tensions_command(interaction: discord.Interaction):
    """Show all contradicting belief pairs."""
    await interaction.response.defer(ephemeral=True)

    tensions = await get_all_tensions(str(interaction.user.id))

    if not tensions:
        await interaction.followup.send(
            "No tensions found in your belief map.\n\n"
            "This could mean your beliefs are consistent, or I haven't "
            "detected any contradictions yet. Keep chatting and I'll "
            "notice if something doesn't quite fit together.",
            ephemeral=True
        )
        return

    response = "**⚡ Tensions in Your Belief Map**\n\n"
    response += "*These beliefs might be in tension with each other. "
    response += "That's not necessarily bad — exploring contradictions can lead to deeper understanding.*\n\n"

    for i, t in enumerate(tensions[:5], 1):
        src_imp = importance_stars(t.get('source_importance', 3))
        tgt_imp = importance_stars(t.get('target_importance', 3))

        src_stmt = t['source_statement'][:70]
        if len(t['source_statement']) > 70:
            src_stmt += "..."

        tgt_stmt = t['target_statement'][:70]
        if len(t['target_statement']) > 70:
            tgt_stmt += "..."

        response += f"**Tension {i}:**\n"
        response += f"```\n"
        response += f"{src_imp} \"{src_stmt}\"\n"
        response += f"      ⚡ vs ⚡\n"
        response += f"{tgt_imp} \"{tgt_stmt}\"\n"
        response += f"```\n"

    if len(tensions) > 5:
        response += f"\n*...and {len(tensions) - 5} more tension(s)*\n"

    response += "\n*Want to explore a tension? Just ask me about it.*"

    if len(response) > 2000:
        response = response[:1997] + "..."

    await interaction.followup.send(response, ephemeral=True)


@bot.tree.command(name="history", description="See how a belief has evolved over time")
@app_commands.describe(belief_id="The belief ID (first 8 characters)")
@app_commands.autocomplete(belief_id=belief_autocomplete)
async def history_command(interaction: discord.Interaction, belief_id: str):
    """Show the evolution history of a specific belief."""
    await interaction.response.defer(ephemeral=True)

    beliefs = await get_user_beliefs(str(interaction.user.id))
    matching = [b for b in beliefs if b["id"].startswith(belief_id)]

    if not matching:
        await interaction.followup.send(
            f"No belief found starting with `{belief_id}`. Use `/beliefs` to see IDs.",
            ephemeral=True
        )
        return

    if len(matching) > 1:
        await interaction.followup.send(
            f"Multiple beliefs match `{belief_id}`. Please be more specific.",
            ephemeral=True
        )
        return

    belief = matching[0]
    history = await get_belief_history(belief["id"])

    # Current state
    conf = confidence_bar(belief.get('confidence', 0.5))
    imp = importance_stars(belief.get('importance', 3))

    response = f"**Evolution of Belief:**\n"
    response += f"*\"{belief['statement']}\"*\n\n"

    response += f"**Current state:** [{conf}] {int(belief.get('confidence', 0.5) * 100)}% confidence, {imp} importance\n"
    response += f"**First expressed:** {belief.get('first_expressed', 'unknown')[:10]}\n\n"

    if history:
        response += "**Changes:**\n```\n"
        for i, h in enumerate(history[:10]):
            timestamp = h.get('timestamp', '')[:10]

            if h.get('old_confidence') and h.get('new_confidence'):
                old_pct = int(h['old_confidence'] * 100)
                new_pct = int(h['new_confidence'] * 100)
                direction = "↑" if new_pct > old_pct else "↓"
                response += f"📅 {timestamp} — Confidence {old_pct}% {direction} {new_pct}%\n"

            if h.get('old_statement') and h.get('new_statement'):
                response += f"📅 {timestamp} — Wording changed\n"
                response += f"   From: \"{h['old_statement'][:40]}...\"\n"
                response += f"   To:   \"{h['new_statement'][:40]}...\"\n"

            if h.get('trigger'):
                response += f"   Trigger: {h['trigger'][:50]}\n"

            response += "\n"
        response += "```"

        if len(history) > 10:
            response += f"\n*...and {len(history) - 10} earlier change(s)*"
    else:
        response += "*No recorded changes yet. This belief has remained stable.*\n"
        response += "\n*As you chat and your views evolve, I'll track the changes here.*"

    if len(response) > 2000:
        response = response[:1997] + "..."

    await interaction.followup.send(response, ephemeral=True)


@bot.tree.command(name="changes", description="See beliefs that have evolved recently")
@app_commands.describe(days="Number of days to look back (default: 30)")
async def changes_command(interaction: discord.Interaction, days: int = 30):
    """Show beliefs that have changed recently."""
    await interaction.response.defer(ephemeral=True)

    if days < 1 or days > 365:
        await interaction.followup.send("Days must be between 1 and 365.", ephemeral=True)
        return

    changes = await get_recent_changes(str(interaction.user.id), days)

    if not changes:
        await interaction.followup.send(
            f"No belief changes recorded in the last {days} days.\n\n"
            "As you chat and your views evolve, I'll track the changes here.",
            ephemeral=True
        )
        return

    # Group by belief
    belief_changes = {}
    for c in changes:
        bid = c['belief_id']
        if bid not in belief_changes:
            belief_changes[bid] = {
                'statement': c['current_statement'],
                'current_confidence': c['current_confidence'],
                'importance': c.get('importance', 3),
                'changes': []
            }
        belief_changes[bid]['changes'].append(c)

    response = f"**🔄 Belief Changes (last {days} days)**\n\n"

    for i, (bid, data) in enumerate(list(belief_changes.items())[:5]):
        stmt = data['statement'][:60]
        if len(data['statement']) > 60:
            stmt += "..."

        imp = importance_stars(data['importance'])
        response += f"**{i+1}. {stmt}**\n"
        response += f"   {imp} | {len(data['changes'])} change(s)\n"

        # Show most recent change
        latest = data['changes'][0]
        if latest.get('old_confidence') and latest.get('new_confidence'):
            old_pct = int(latest['old_confidence'] * 100)
            new_pct = int(latest['new_confidence'] * 100)
            direction = "↑" if new_pct > old_pct else "↓"
            response += f"   Latest: {old_pct}% {direction} {new_pct}%\n"

        response += f"   `/history {bid[:8]}` for full evolution\n\n"

    if len(belief_changes) > 5:
        response += f"*...and {len(belief_changes) - 5} more belief(s) changed*\n"

    response += "\n*Your beliefs are living ideas. Change is growth.*"

    if len(response) > 2000:
        response = response[:1997] + "..."

    await interaction.followup.send(response, ephemeral=True)


@bot.tree.command(name="share", description="Create a shareable snapshot of your beliefs")
@app_commands.describe(
    topic="Share beliefs about a specific topic (optional)",
    core_only="Only share important beliefs (4-5 stars)"
)
@app_commands.autocomplete(topic=topic_autocomplete)
async def share_command(
    interaction: discord.Interaction,
    topic: str = None,
    core_only: bool = False
):
    """Generate a shareable belief snapshot."""
    await interaction.response.defer(ephemeral=True)

    if topic:
        beliefs = await get_beliefs_by_topic(str(interaction.user.id), topic)
        title = f"Beliefs: {topic.upper()}"
    elif core_only:
        beliefs = await get_beliefs_by_importance(str(interaction.user.id), min_importance=4)
        title = "Core Beliefs"
    else:
        beliefs = await get_user_beliefs(str(interaction.user.id))
        title = "Belief Snapshot"

    if not beliefs:
        await interaction.followup.send(
            "No beliefs to share." + (" Try a different topic." if topic else ""),
            ephemeral=True
        )
        return

    # Build the shareable embed
    embed = discord.Embed(
        title=f"🧠 {interaction.user.display_name}'s {title}",
        color=discord.Color.blue()
    )

    # Group by topic if not filtering by topic
    if not topic and len(beliefs) > 5:
        # Show top beliefs by importance
        sorted_beliefs = sorted(beliefs, key=lambda b: b.get('importance', 3), reverse=True)[:8]
        belief_lines = []
        for b in sorted_beliefs:
            imp = importance_stars(b.get('importance', 3))
            conf = confidence_bar(b.get('confidence', 0.5))
            statement = b['statement'][:80] + "..." if len(b['statement']) > 80 else b['statement']
            belief_lines.append(f"{imp} [{conf}] {statement}")
        embed.description = "\n".join(belief_lines)
        if len(beliefs) > 8:
            embed.set_footer(text=f"Showing top 8 of {len(beliefs)} beliefs")
    else:
        belief_lines = []
        for b in beliefs[:10]:
            imp = importance_stars(b.get('importance', 3))
            conf = confidence_bar(b.get('confidence', 0.5))
            statement = b['statement'][:80] + "..." if len(b['statement']) > 80 else b['statement']
            belief_lines.append(f"{imp} [{conf}] {statement}")
        embed.description = "\n".join(belief_lines)
        if len(beliefs) > 10:
            embed.set_footer(text=f"Showing 10 of {len(beliefs)} beliefs")

    # Also create text version for copying
    text_version = f"**{interaction.user.display_name}'s {title}**\n"
    text_version += "```\n"
    for b in (beliefs[:10] if len(beliefs) > 10 else beliefs):
        imp = importance_stars(b.get('importance', 3))
        conf = confidence_bar(b.get('confidence', 0.5))
        statement = b['statement'][:60] + "..." if len(b['statement']) > 60 else b['statement']
        text_version += f"{imp} [{conf}] {statement}\n"
    text_version += "```"
    text_version += "\n*Mapped with Kodak*"

    # Show preview
    await interaction.followup.send(
        "**Preview of your shareable snapshot:**",
        embed=embed,
        ephemeral=True
    )

    # Send text version as copyable
    await interaction.followup.send(
        "**Copy-paste version:**\n" + text_version +
        "\n\n*To post this publicly, copy the text above and paste in any channel.*",
        ephemeral=True
    )


@bot.tree.command(name="compare", description="Compare your beliefs with another user")
@app_commands.describe(user="The user to compare with")
async def compare_command(interaction: discord.Interaction, user: discord.User):
    """Request a belief comparison with another user."""
    if user.id == interaction.user.id:
        await interaction.response.send_message(
            "You can't compare with yourself! Use `/tensions` to find internal contradictions.",
            ephemeral=True
        )
        return

    if user.bot:
        await interaction.response.send_message(
            "Can't compare beliefs with a bot.",
            ephemeral=True
        )
        return

    # Check if they have beliefs to share
    my_beliefs = await get_shareable_beliefs(str(interaction.user.id))
    if not my_beliefs:
        await interaction.response.send_message(
            "You don't have any shareable beliefs yet. Chat with me first to build your belief map!",
            ephemeral=True
        )
        return

    # Check if there's already an accepted comparison
    existing = await get_accepted_comparison(str(interaction.user.id), str(user.id))
    if existing:
        await interaction.response.send_message(
            f"You already have an active comparison with {user.display_name}. "
            f"Use `/compare-view {user.display_name}` to see it again.",
            ephemeral=True
        )
        return

    # Create the request
    result = await create_comparison_request(str(interaction.user.id), str(user.id))

    if result["status"] == "already_pending":
        await interaction.response.send_message(
            f"You already have a pending request to {user.display_name}. Waiting for their response.",
            ephemeral=True
        )
        return

    # Try to DM the target user
    try:
        embed = discord.Embed(
            title="🔄 Belief Comparison Request",
            description=f"*Kodak maps what you believe through conversation.*\n\n"
                       f"**{interaction.user.display_name}** wants to compare belief maps with you.\n\n"
                       f"If you accept, you'll both see:\n"
                       f"• Where you agree\n"
                       f"• Where you differ\n"
                       f"• A similarity score\n\n"
                       f"Only beliefs marked 'shareable' are visible (use `/privacy` to control this).",
            color=discord.Color.blue()
        )
        embed.set_footer(text="New to Kodak? Just DM me to start mapping your beliefs.")

        view = ComparisonRequestView(
            result["id"],
            str(interaction.user.id),
            interaction.user.display_name
        )

        await user.send(embed=embed, view=view)

        await interaction.response.send_message(
            f"📤 Comparison request sent to {user.display_name}!\n"
            f"They'll need to accept before you can see results.",
            ephemeral=True
        )

    except discord.errors.Forbidden:
        await interaction.response.send_message(
            f"Couldn't send request to {user.display_name} — they may have DMs disabled.",
            ephemeral=True
        )


@bot.tree.command(name="requests", description="See pending comparison requests")
async def requests_command(interaction: discord.Interaction):
    """Show pending comparison requests."""
    requests = await get_pending_requests(str(interaction.user.id))

    if not requests:
        await interaction.response.send_message(
            "No pending comparison requests.\n"
            "Use `/compare @user` to request a comparison with someone.",
            ephemeral=True
        )
        return

    embed = discord.Embed(
        title="📥 Pending Comparison Requests",
        color=discord.Color.blue()
    )

    for req in requests[:5]:
        requester_name = req.get('requester_username', 'Unknown')
        requested_at = req.get('requested_at', '')[:10]
        embed.add_field(
            name=f"From: {requester_name}",
            value=f"Requested: {requested_at}\n"
                  f"Use buttons below to respond",
            inline=False
        )

    # Add view with buttons for the first request
    if requests:
        first_req = requests[0]
        view = ComparisonRequestView(
            first_req['id'],
            first_req['requester_id'],
            first_req.get('requester_username', 'Unknown')
        )
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
    else:
        await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(name="bridging", description="See your bridging score — how well you connect across differences")
async def bridging_command(interaction: discord.Interaction):
    """Show the user's bridging score and bridging beliefs."""
    await interaction.response.defer(ephemeral=True)

    bridging = await get_bridging_score(str(interaction.user.id))

    if bridging['comparisons_count'] == 0:
        await interaction.followup.send(
            "**🌉 Your Bridging Profile**\n\n"
            "No comparisons yet! Your bridging score is calculated from "
            "how often you find common ground with people who are different from you.\n\n"
            "Use `/compare @user` to start comparing beliefs with others.",
            ephemeral=True
        )
        return

    score_pct = int(bridging['score'] * 100)
    score_bar = "█" * (score_pct // 10) + "░" * (10 - score_pct // 10)

    # Interpret the score
    if score_pct >= 70:
        interpretation = "You're a natural bridge-builder. You find common ground even with people who think differently."
    elif score_pct >= 40:
        interpretation = "You can connect across differences when you try. Keep exploring different perspectives."
    else:
        interpretation = "You tend to connect with people similar to you. Try comparing with people who seem different!"

    response = f"**🌉 Your Bridging Profile**\n\n"
    response += f"**Bridging Score:** [{score_bar}] {score_pct}%\n\n"
    response += f"*{interpretation}*\n\n"

    response += f"**Stats:**\n"
    response += f"• Comparisons completed: {bridging['comparisons_count']}\n"
    response += f"• Found common ground despite differences: {bridging['bridging_comparisons']} times\n"
    response += f"• Total bridging agreements: {bridging['total_bridging_agreements']}\n"

    # Show bridging beliefs if any
    if bridging['bridging_beliefs']:
        response += f"\n**Your Bridging Beliefs** (shared with people who differ from you):\n"
        for bb in bridging['bridging_beliefs'][:5]:
            imp = importance_stars(bb.get('importance', 3))
            stmt = bb['statement'][:50]
            if len(bb['statement']) > 50:
                stmt += "..."
            response += f"• {imp} *\"{stmt}\"*\n"

    response += "\n*High bridging scores indicate you can appreciate ideas across divides — valuable for productive dialogue.*"

    if len(response) > 2000:
        response = response[:1997] + "..."

    await interaction.followup.send(response, ephemeral=True)


@bot.tree.command(name="privacy", description="Control which beliefs are shareable")
@app_commands.describe(
    belief_id="Belief ID to change (optional)",
    visibility="Visibility level: public, shareable, private, hidden",
    topic="Set visibility for all beliefs with this topic (optional)"
)
@app_commands.autocomplete(belief_id=belief_autocomplete, topic=topic_autocomplete)
async def privacy_command(
    interaction: discord.Interaction,
    belief_id: str = None,
    visibility: str = None,
    topic: str = None
):
    """View or change belief visibility settings."""
    user_id = str(interaction.user.id)

    # If no arguments, show breakdown
    if not belief_id and not visibility and not topic:
        breakdown = await get_visibility_breakdown(user_id)
        total = sum(breakdown.values())

        response = "**🔒 Your Belief Privacy Settings**\n\n"
        response += f"**PUBLIC** (anyone can see): {breakdown['public']} beliefs\n"
        response += f"**SHAREABLE** (shared in comparisons): {breakdown['shareable']} beliefs\n"
        response += f"**PRIVATE** (only you): {breakdown['private']} beliefs\n"
        response += f"**HIDDEN** (excluded from everything): {breakdown['hidden']} beliefs\n"
        response += f"\n*Total: {total} beliefs*\n\n"

        response += "**Usage:**\n"
        response += "`/privacy [belief_id] [visibility]` — change one belief\n"
        response += "`/privacy topic:[topic] [visibility]` — change all beliefs on a topic\n"
        response += "\n*When you `/share-export`, only public/shareable beliefs are included.*"

        await interaction.response.send_message(response, ephemeral=True)
        return

    # Validate visibility if provided
    valid_levels = ('public', 'shareable', 'private', 'hidden')
    if visibility and visibility.lower() not in valid_levels:
        await interaction.response.send_message(
            f"Invalid visibility. Choose: {', '.join(valid_levels)}",
            ephemeral=True
        )
        return

    visibility = visibility.lower() if visibility else None

    # Set topic visibility
    if topic and visibility:
        count = await set_topic_visibility(user_id, topic, visibility)
        if count > 0:
            await interaction.response.send_message(
                f"Updated {count} belief(s) about '{topic}' to **{visibility}**.",
                ephemeral=True
            )
        else:
            await interaction.response.send_message(
                f"No beliefs found with topic '{topic}'.",
                ephemeral=True
            )
        return

    # Set individual belief visibility
    if belief_id and visibility:
        beliefs = await get_user_beliefs(user_id)
        matching = [b for b in beliefs if b["id"].startswith(belief_id)]

        if not matching:
            await interaction.response.send_message(
                f"No belief found starting with `{belief_id}`.",
                ephemeral=True
            )
            return

        if len(matching) > 1:
            await interaction.response.send_message(
                f"Multiple beliefs match `{belief_id}`. Be more specific.",
                ephemeral=True
            )
            return

        belief = matching[0]
        success = await set_belief_visibility(belief["id"], user_id, visibility)

        if success:
            stmt = belief['statement'][:50]
            if len(belief['statement']) > 50:
                stmt += "..."
            await interaction.response.send_message(
                f"Updated to **{visibility}**:\n*\"{stmt}\"*",
                ephemeral=True
            )
        else:
            await interaction.response.send_message("Couldn't update that belief.", ephemeral=True)
        return

    # Missing required params
    await interaction.response.send_message(
        "Please provide both a belief_id (or topic) and visibility level.\n"
        "Example: `/privacy abc123 private` or `/privacy topic:politics private`",
        ephemeral=True
    )


@bot.tree.command(name="share-export", description="Export only shareable beliefs (for comparison)")
@app_commands.describe(topic="Only export beliefs about this topic (optional)")
@app_commands.autocomplete(topic=topic_autocomplete)
async def share_export_command(interaction: discord.Interaction, topic: str = None):
    """Export shareable beliefs as JSON for sharing with others."""
    await interaction.response.defer(ephemeral=True)

    beliefs = await get_shareable_beliefs(str(interaction.user.id))

    if topic:
        beliefs = [b for b in beliefs if topic.lower() in [t.lower() for t in b.get('topics', [])]]

    if not beliefs:
        await interaction.followup.send(
            "No shareable beliefs to export." +
            (f" (filtered by topic: {topic})" if topic else "") +
            "\n\nUse `/privacy` to mark beliefs as shareable.",
            ephemeral=True
        )
        return

    # Build export data (simplified for sharing)
    export_data = {
        "username": interaction.user.display_name,
        "exported_at": datetime.now().isoformat(),
        "belief_count": len(beliefs),
        "topic_filter": topic,
        "beliefs": [
            {
                "id": b["id"],
                "statement": b["statement"],
                "confidence": b.get("confidence", 0.5),
                "importance": b.get("importance", 3),
                "topics": b.get("topics", []),
                "source_type": b.get("source_type")
            }
            for b in beliefs
        ]
    }

    # Build preview embed
    embed = discord.Embed(
        title="📤 Export Preview",
        description=f"**{len(beliefs)} belief(s)** will be included" +
                    (f" (topic: {topic})" if topic else ""),
        color=discord.Color.blue()
    )

    # Show preview of beliefs that will be exported
    preview_lines = []
    for b in beliefs[:8]:
        stmt = b['statement'][:50]
        if len(b['statement']) > 50:
            stmt += "..."
        imp = importance_stars(b.get('importance', 3))
        preview_lines.append(f"{imp} {stmt}")

    embed.add_field(
        name="Beliefs to export:",
        value="\n".join(preview_lines) if preview_lines else "None",
        inline=False
    )

    if len(beliefs) > 8:
        embed.set_footer(text=f"...and {len(beliefs) - 8} more")

    embed.add_field(
        name="⚠️ Privacy reminder",
        value="Only 'public' and 'shareable' beliefs are included.\n"
              "Use `/privacy` to adjust visibility before exporting.",
        inline=False
    )

    # Create view with download button
    filename = f"kodak_shareable_{interaction.user.id}.json"
    view = ShareExportView(export_data, filename)

    await interaction.followup.send(
        embed=embed,
        view=view,
        ephemeral=True
    )


@bot.tree.command(name="compare-file", description="Compare your beliefs with someone's exported file")
@app_commands.describe(file="The JSON file from someone's /share-export")
async def compare_file_command(interaction: discord.Interaction, file: discord.Attachment):
    """Compare local beliefs with an imported file."""
    await interaction.response.defer(ephemeral=True)

    # Validate file
    if not file.filename.endswith('.json'):
        await interaction.followup.send(
            "Please attach a JSON file from `/share-export`.",
            ephemeral=True
        )
        return

    if file.size > 1_000_000:  # 1MB limit
        await interaction.followup.send(
            "File too large. Maximum size is 1MB.",
            ephemeral=True
        )
        return

    # Download and parse
    try:
        content = await file.read()
        imported_data = json.loads(content.decode('utf-8'))
    except discord.HTTPException:
        await interaction.followup.send(
            "Couldn't download that file. Please try again.",
            ephemeral=True
        )
        return
    except (json.JSONDecodeError, UnicodeDecodeError):
        await interaction.followup.send(
            "Couldn't parse that file. Make sure it's from `/share-export`.",
            ephemeral=True
        )
        return

    # Validate structure
    if 'beliefs' not in imported_data or not isinstance(imported_data['beliefs'], list):
        await interaction.followup.send(
            "Invalid file format. Make sure it's from `/share-export`.",
            ephemeral=True
        )
        return

    imported_beliefs = imported_data['beliefs']
    imported_username = imported_data.get('username', 'Unknown')

    # Validate each belief has required fields
    valid_beliefs = []
    for belief in imported_beliefs:
        if isinstance(belief, dict) and 'statement' in belief:
            # Ensure required fields exist with defaults
            valid_beliefs.append({
                'id': belief.get('id', str(uuid.uuid4())),
                'statement': belief['statement'],
                'confidence': belief.get('confidence', 0.5),
                'importance': belief.get('importance', 3),
                'topics': belief.get('topics', []),
                'source_type': belief.get('source_type')
            })

    if not valid_beliefs:
        await interaction.followup.send(
            "No valid beliefs found in file. Each belief needs at least a 'statement' field.",
            ephemeral=True
        )
        return

    imported_beliefs = valid_beliefs

    if not imported_beliefs:
        await interaction.followup.send(
            "The imported file has no beliefs.",
            ephemeral=True
        )
        return

    # Get local shareable beliefs
    my_beliefs = await get_shareable_beliefs(str(interaction.user.id))

    if not my_beliefs:
        await interaction.followup.send(
            "You don't have any shareable beliefs yet. Chat with me first!",
            ephemeral=True
        )
        return

    # Calculate similarity
    comparison = await calculate_belief_similarity(my_beliefs, imported_beliefs)

    # Build result embed
    overall_pct = int(comparison['overall_similarity'] * 100)
    core_pct = int(comparison['core_similarity'] * 100)

    embed = discord.Embed(
        title=f"🔄 Belief Comparison: You ↔ {imported_username}",
        color=discord.Color.blue()
    )

    embed.add_field(
        name="📊 Similarity",
        value=f"**Overall:** {overall_pct}%\n**Core beliefs:** {core_pct}%",
        inline=True
    )

    embed.add_field(
        name="📈 Belief Counts",
        value=f"**Yours:** {len(my_beliefs)}\n**Theirs:** {len(imported_beliefs)}",
        inline=True
    )

    if comparison.get('summary'):
        embed.add_field(
            name="Summary",
            value=comparison['summary'],
            inline=False
        )

    # Agreements
    if comparison['agreements']:
        agreement_text = ""
        for ag in comparison['agreements'][:3]:
            stmt = ag['belief_a']['statement'][:60]
            if len(ag['belief_a']['statement']) > 60:
                stmt += "..."
            agreement_text += f"🤝 *\"{stmt}\"*\n"
        embed.add_field(
            name=f"Agreements ({len(comparison['agreements'])})",
            value=agreement_text or "None",
            inline=False
        )

    # Differences
    if comparison['differences']:
        diff_text = ""
        for df in comparison['differences'][:3]:
            stmt_a = df['belief_a']['statement'][:35]
            stmt_b = df['belief_b']['statement'][:35]
            diff_text += f"⚡ *\"{stmt_a}...\"* vs *\"{stmt_b}...\"*\n"
        embed.add_field(
            name=f"Differences ({len(comparison['differences'])})",
            value=diff_text or "None",
            inline=False
        )

    embed.set_footer(text=f"Compared with file from {imported_username}")

    await interaction.followup.send(embed=embed, ephemeral=True)


@bot.tree.command(name="pause", description="Pause belief tracking")
async def pause_command(interaction: discord.Interaction):
    """Pause belief tracking."""
    await set_tracking_paused(str(interaction.user.id), True)
    await interaction.response.send_message(
        "Belief tracking paused. We can still chat—I just won't be taking notes.\n"
        "Use `/resume` whenever you're ready to start mapping again.",
        ephemeral=True
    )


@bot.tree.command(name="resume", description="Resume belief tracking")
async def resume_command(interaction: discord.Interaction):
    """Resume belief tracking."""
    await set_tracking_paused(str(interaction.user.id), False)
    await interaction.response.send_message(
        "Tracking resumed! I'll start mapping our conversations again.",
        ephemeral=True
    )


@bot.tree.command(name="export", description="Download all your data")
async def export_command(interaction: discord.Interaction):
    """Export all user data as JSON."""
    await interaction.response.defer(ephemeral=True)

    data = await export_user_data(str(interaction.user.id))

    # Create a file
    json_str = json.dumps(data, indent=2, default=str)

    if len(json_str) > 8_000_000:  # Discord file size limit
        await interaction.followup.send(
            "Your data is too large to export directly. Please contact support.",
            ephemeral=True
        )
        return

    file = discord.File(
        fp=__import__('io').BytesIO(json_str.encode()),
        filename=f"kodak_export_{interaction.user.id}.json"
    )

    await interaction.followup.send(
        "Here's all your data. This includes your beliefs, conversation history, and settings.",
        file=file,
        ephemeral=True
    )


@bot.tree.command(name="clear", description="Delete all your data")
async def clear_command(interaction: discord.Interaction):
    """Delete all user data with confirmation."""
    embed = discord.Embed(
        title="Are you sure?",
        description=(
            "This will permanently delete:\n"
            "• All your beliefs\n"
            "• Your conversation history\n"
            "• Your personality settings\n\n"
            "This cannot be undone."
        ),
        color=discord.Color.red()
    )

    view = ConfirmClearView()
    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


@bot.tree.command(name="style", description="Fine-tune personality dimensions")
@app_commands.describe(
    warmth="1 (analytical) to 5 (warm)",
    directness="1 (gentle) to 5 (blunt)",
    playfulness="1 (serious) to 5 (playful)",
    formality="1 (casual) to 5 (formal)"
)
async def style_command(
    interaction: discord.Interaction,
    warmth: int = None,
    directness: int = None,
    playfulness: int = None,
    formality: int = None
):
    """Fine-tune personality dimensions."""
    for name, val in [("warmth", warmth), ("directness", directness),
                      ("playfulness", playfulness), ("formality", formality)]:
        if val is not None and (val < 1 or val > 5):
            await interaction.response.send_message(
                f"{name} must be between 1 and 5.",
                ephemeral=True
            )
            return

    await get_or_create_user(str(interaction.user.id), interaction.user.name)
    user = await update_user_personality(
        str(interaction.user.id),
        warmth=warmth,
        directness=directness,
        playfulness=playfulness,
        formality=formality
    )

    # Visual representation
    def bar(val):
        return "█" * val + "░" * (5 - val)

    await interaction.response.send_message(
        f"**Your Style:**\n"
        f"```\n"
        f"Warmth:      [{bar(user['warmth'])}] {user['warmth']}/5\n"
        f"Directness:  [{bar(user['directness'])}] {user['directness']}/5\n"
        f"Playfulness: [{bar(user['playfulness'])}] {user['playfulness']}/5\n"
        f"Formality:   [{bar(user['formality'])}] {user['formality']}/5\n"
        f"```",
        ephemeral=True
    )


@bot.tree.command(name="backup", description="Download a backup of the database")
async def backup_command(interaction: discord.Interaction):
    """Send the database file as a backup."""
    await interaction.response.defer(ephemeral=True)

    from db import DB_PATH
    import shutil
    from io import BytesIO

    if not DB_PATH.exists():
        await interaction.followup.send(
            "No database found to backup.",
            ephemeral=True
        )
        return

    # Read the database file
    try:
        with open(DB_PATH, 'rb') as f:
            db_content = f.read()

        # Check file size (Discord limit is 25MB for most servers)
        if len(db_content) > 25_000_000:
            await interaction.followup.send(
                "Database is too large to send via Discord (>25MB).\n"
                f"You can find it at: `{DB_PATH}`",
                ephemeral=True
            )
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file = discord.File(
            fp=BytesIO(db_content),
            filename=f"kodak_backup_{timestamp}.db"
        )

        await interaction.followup.send(
            f"**📦 Database Backup**\n"
            f"Size: {len(db_content) / 1024:.1f} KB\n"
            f"To restore: replace `{DB_PATH.name}` with this file.",
            file=file,
            ephemeral=True
        )

    except Exception as e:
        await interaction.followup.send(
            f"Couldn't create backup: {e}",
            ephemeral=True
        )


def main():
    """Run the bot."""
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        print("Error: DISCORD_TOKEN not found in environment")
        return

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: ANTHROPIC_API_KEY not found in environment")
        return

    bot.run(token)


if __name__ == "__main__":
    main()
