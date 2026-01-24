"""Kodak Discord Bot - Main entry point."""

import os
import json
import asyncio
import random
import time
from collections import defaultdict
import discord
from discord import app_commands, ui
from discord.ext import commands
from dotenv import load_dotenv

from db import (
    init_db, get_or_create_user, update_user_personality,
    add_belief, get_user_beliefs, get_beliefs_by_topic,
    soft_delete_belief, add_conversation_message, get_recent_conversation,
    get_all_topics, complete_onboarding, set_tracking_paused,
    increment_message_count, reset_message_count, get_recent_beliefs,
    clear_all_user_data, export_user_data, add_belief_relation,
    get_belief_relations
)
from extractor import extract_beliefs, generate_response, find_belief_relations, summarize_beliefs
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


def check_rate_limit(user_id: str) -> tuple[bool, int]:
    """
    Check if user is rate limited.
    Returns (is_allowed, seconds_until_reset).
    """
    if RATE_LIMIT_PER_HOUR <= 0:
        return True, 0

    now = time.time()
    hour_ago = now - 3600

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


# === Bot Events ===

@bot.event
async def on_ready():
    """Called when bot is ready."""
    await init_db()
    print(f"Kodak is online as {bot.user}")

    # Sync slash commands
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(f"Failed to sync commands: {e}")


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

    # Check rate limit
    is_allowed, wait_seconds = check_rate_limit(str(message.author.id))
    if not is_allowed:
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
            "`/beliefs` — Raw list with IDs\n"
            "`/belief [id]` — View one belief with connections"
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
            "`/pause` — Pause belief tracking\n"
            "`/resume` — Resume belief tracking\n"
            "`/export` — Download all your data\n"
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
                conf = "●" * int(b.get('confidence', 0.5) * 5) + "○" * (5 - int(b.get('confidence', 0.5) * 5))
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
        suggestion = ""
        if topics:
            suggestion = f"\n\nTopics I know about: {', '.join(topics[:10])}"
        await interaction.followup.send(
            f"No beliefs found about '{topic}'.{suggestion}",
            ephemeral=True
        )
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
    for b in beliefs[:20]:  # Reduced to fit more content per belief
        conf = "●" * int(b.get('confidence', 0.5) * 5) + "○" * (5 - int(b.get('confidence', 0.5) * 5))
        topics = ", ".join(b.get("topics", []))
        topic_str = f" *({topics})*" if topics else ""
        lines.append(f"`{b['id'][:8]}` [{conf}] {b['statement']}{topic_str}")

    response = "**Your Beliefs:**\n"
    response += "*Confidence: ●=certain, ○=uncertain*\n\n"
    response += "\n\n".join(lines)  # Double newline for readability

    if len(beliefs) > 20:
        response += f"\n\n*...and {len(beliefs) - 20} more*"

    response += f"\n\n*Use `/belief [id]` to see connections and details.*"

    if len(response) > 2000:
        response = response[:1997] + "..."

    await interaction.followup.send(response, ephemeral=True)


@bot.tree.command(name="belief", description="View a single belief in detail")
@app_commands.describe(belief_id="The belief ID (first 8 characters)")
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
    relations = await get_belief_relations(belief["id"])

    # Build response
    conf = "●" * int(belief.get('confidence', 0.5) * 5) + "○" * (5 - int(belief.get('confidence', 0.5) * 5))
    topics = ", ".join(belief.get("topics", [])) or "none"

    response = f"**Belief:** {belief['statement']}\n\n"
    response += f"**Confidence:** [{conf}] ({int(belief.get('confidence', 0.5) * 100)}%)\n"
    response += f"**Source:** {belief.get('source_type', 'unknown')}\n"
    response += f"**Topics:** {topics}\n"
    response += f"**ID:** `{belief['id'][:8]}`\n"

    if relations:
        response += f"\n**Connections:**\n"
        relation_labels = {
            "supports": "⬆️ Supports",
            "contradicts": "⚡ Contradicts",
            "assumes": "📌 Assumes",
            "derives_from": "➡️ Derives from",
            "relates_to": "🔗 Related to"
        }
        for rel in relations:
            label = relation_labels.get(rel["relation_type"], rel["relation_type"])
            target_stmt = rel.get("target_statement", "")[:60]
            if len(rel.get("target_statement", "")) > 60:
                target_stmt += "..."
            response += f"{label}: *{target_stmt}*\n"
    else:
        response += f"\n*No connections to other beliefs yet.*"

    response += f"\n\nUse `/forget {belief['id'][:8]}` to remove this belief."

    await interaction.followup.send(response, ephemeral=True)


@bot.tree.command(name="forget", description="Delete a belief from your map")
@app_commands.describe(belief_id="The belief ID (first 8 characters) or 'last' for most recent")
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
        await interaction.followup.send(
            f"Forgotten: *{belief['statement']}*",
            ephemeral=True
        )
    else:
        await interaction.followup.send("Hmm, couldn't delete that one.", ephemeral=True)


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
