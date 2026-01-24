"""Kodak v2.0 - Reflective Journaling Companion."""

import os
import logging
import uuid
import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv
from datetime import datetime

from db import (
    init_db, get_or_create_user, update_user,
    get_users_for_prompt, get_users_with_missed_prompts,
    get_users_needing_reengagement, mark_prompt_sent,
    create_session as db_create_session, get_active_session as db_get_active_session,
    end_session as db_end_session, update_session,
    get_user_value_profile, get_value_snapshot, update_user_value_profile,
    add_belief, add_belief_values, get_user_beliefs, get_belief,
    get_all_topics, get_beliefs_by_topic, get_important_beliefs,
    update_belief_confidence, update_belief_importance,
    soft_delete_belief, restore_belief, get_last_deleted_belief,
    get_belief_history, get_recent_changes, get_all_tensions,
    export_user_data, clear_all_user_data
)
from scheduler import JournalScheduler, parse_time_input, format_time_display
from values import (
    generate_value_narrative, generate_value_change_narrative,
    export_to_json, parse_import_data, generate_comparison_with_import_narrative,
    ALL_VALUES, VALUE_DEFINITIONS
)
from extractor import (
    extract_beliefs_and_values, extract_from_session,
    format_beliefs_for_close, ExtractedBelief
)
from prompts import (
    get_opener, get_closure, get_reengagement_prompt, get_first_session_framing,
    infer_response_depth, should_probe_more
)
from personality import (
    PRESETS, PRESET_ORDER, get_preset, build_session_system_prompt
)
from session import (
    SessionState, SessionStage, get_active_session, create_session,
    end_session, has_active_session, determine_next_stage, get_stage_instruction
)
from onboarding import OnboardingFlow, get_onboarding_state, clear_onboarding_state

# Load environment
load_dotenv()

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(name)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger('kodak')

# Discord setup
intents = discord.Intents.default()
intents.message_content = True
intents.dm_messages = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Scheduler instance (initialized on ready)
scheduler: JournalScheduler = None

# Anthropic client for LLM responses
anthropic_client = None


def get_anthropic_client():
    """Lazy-load Anthropic client."""
    global anthropic_client
    if anthropic_client is None:
        import anthropic
        anthropic_client = anthropic.Anthropic()
    return anthropic_client


# ============================================
# SESSION MANAGEMENT
# ============================================

async def start_journal_session(
    channel: discord.DMChannel,
    user: dict,
    prompt_type: str = 'scheduled'
) -> SessionState:
    """
    Start a new journaling session for a user.

    Args:
        channel: The DM channel
        user: The user dict from database
        prompt_type: 'scheduled', 'user_initiated', 'catch_up', 'first'
    """
    user_id = user['user_id']
    personality = user.get('personality_preset', 'best_friend')
    depth = user.get('prompt_depth', 'standard')
    is_first = not user.get('first_session_complete', False)

    # Create session ID
    session_id = str(uuid.uuid4())

    # Create in-memory session state
    session = create_session(
        session_id=session_id,
        user_id=user_id,
        personality=personality,
        depth_setting=depth,
        is_first_session=is_first
    )

    # Persist to database
    await db_create_session(
        session_id=session_id,
        user_id=user_id,
        prompt_type=prompt_type if not is_first else 'first'
    )

    # Get and send opener
    opener = get_opener(personality, user_id)
    session.opener_used = opener

    # Add first session framing if needed
    if is_first:
        framing = get_first_session_framing(personality)
        message = f"{opener}\n\n*{framing}*"
    else:
        message = opener

    await channel.send(message)
    session.add_bot_message(opener)
    session.stage = SessionStage.ANCHOR  # Move to anchor after opener

    logger.info(f"Started {prompt_type} session {session_id} for user {user_id}")
    return session


async def process_session_message(
    channel: discord.DMChannel,
    user: dict,
    message_content: str
) -> None:
    """
    Process a message within an active session.

    This is the core conversation loop.
    """
    user_id = user['user_id']
    session = get_active_session(user_id)

    if not session:
        logger.warning(f"No active session for user {user_id}")
        return

    # Infer response depth
    depth = infer_response_depth(message_content)
    session.add_user_message(message_content, depth)

    # Update database
    await update_session(session.session_id, message_count=session.exchange_count)

    # Extract beliefs from this message (async, doesn't block response)
    try:
        existing_beliefs = await get_user_beliefs(user_id, limit=20)
        extraction = await extract_beliefs_and_values(
            message=message_content,
            conversation_context=session.get_recent_context(6),
            existing_beliefs=existing_beliefs
        )

        # Store extracted beliefs
        for belief in extraction.beliefs:
            stored_belief = await add_belief(
                user_id=user_id,
                statement=belief.statement,
                confidence=belief.confidence,
                source_type=belief.source_type,
                session_id=session.session_id,
                topics=belief.topics
            )

            # Add value mappings
            if belief.values:
                await add_belief_values(
                    belief_id=stored_belief['id'],
                    values=[(v.name, v.weight, v.mapping_confidence) for v in belief.values]
                )

            # Track for session close display
            session.extracted_beliefs.append(belief.statement)

        if extraction.beliefs:
            logger.info(f"Extracted {len(extraction.beliefs)} beliefs from user {user_id}")

    except Exception as e:
        logger.error(f"Extraction error: {e}")

    # Determine next stage
    next_stage = determine_next_stage(session)
    session.stage = next_stage

    # Check if we should close
    if next_stage == SessionStage.CLOSE:
        await close_session(channel, user, session)
        return

    # Generate response using LLM
    response = await generate_session_response(session, message_content)

    if response:
        await channel.send(response)
        session.add_bot_message(response)


async def generate_session_response(session: SessionState, user_message: str) -> str:
    """Generate a response using the LLM."""
    try:
        client = get_anthropic_client()

        # Build system prompt
        system = build_session_system_prompt(
            preset_key=session.personality,
            session_stage=session.stage.value,
            depth_setting=session.depth_setting,
            is_first_session=session.is_first_session,
            exchange_count=session.exchange_count
        )

        # Add stage instruction
        stage_instruction = get_stage_instruction(session)
        system += f"\n\nCurrent instruction: {stage_instruction}"

        # Build messages from session history
        messages = []
        for msg in session.get_recent_context(6):
            messages.append({
                'role': msg['role'],
                'content': msg['content']
            })

        # Add current message if not already in history
        if not messages or messages[-1]['content'] != user_message:
            messages.append({'role': 'user', 'content': user_message})

        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=300,
            system=system,
            messages=messages
        )

        return response.content[0].text

    except Exception as e:
        logger.error(f"Error generating response: {e}")
        # Fallback to a simple response
        return "I hear you. Tell me more about that."


async def close_session(
    channel: discord.DMChannel,
    user: dict,
    session: SessionState
) -> None:
    """Close a session with appropriate closure message."""
    user_id = user['user_id']
    personality = session.personality

    # Build closure message
    closure_parts = []

    # Get base closure
    closure = get_closure(
        personality=personality,
        theme=session.theme_identified,
        is_first_session=session.is_first_session,
        is_short_session=session.exchange_count <= 2
    )

    # Show extracted beliefs (if any and not first session)
    if session.extracted_beliefs and not session.is_first_session:
        # Show up to 2 most recent beliefs
        beliefs_to_show = session.extracted_beliefs[-2:]
        if len(beliefs_to_show) == 1:
            closure_parts.append(f"Something worth remembering:\n*\"{beliefs_to_show[0]}\"*")
        else:
            closure_parts.append("A couple things worth remembering:")
            for b in beliefs_to_show:
                closure_parts.append(f"*\"{b}\"*")

    closure_parts.append(closure)

    await channel.send("\n\n".join(closure_parts))

    # Update value profile
    try:
        await update_user_value_profile(user_id)
        logger.info(f"Updated value profile for user {user_id}")
    except Exception as e:
        logger.error(f"Failed to update value profile: {e}")

    # End in-memory session
    end_session(user_id)

    # Update database
    await db_end_session(session.session_id)

    # Mark first session complete if applicable
    if session.is_first_session:
        await update_user(user_id, first_session_complete=1)

    logger.info(f"Closed session {session.session_id} for user {user_id} ({session.exchange_count} exchanges, {len(session.extracted_beliefs)} beliefs)")


# ============================================
# PROMPT SENDING FUNCTIONS
# ============================================

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

    except discord.Forbidden:
        logger.warning(f"Cannot DM user {user['user_id']} - DMs may be disabled")
    except Exception as e:
        logger.error(f"Error sending prompt to {user['user_id']}: {e}")


async def send_catch_up_prompt(user: dict, hours_late: int):
    """Send a catch-up prompt for a missed scheduled time."""
    try:
        discord_user = await bot.fetch_user(int(user['user_id']))
        if not discord_user:
            return

        personality = user.get('personality_preset', 'best_friend')

        if hours_late < 2:
            message = "Hey! Just missed our usual time — want to reflect on your day now?"
        else:
            message = (
                "Hey, I noticed we missed our check-in earlier. "
                "No worries — want to catch up now, or wait until tomorrow?"
            )

        dm_channel = await discord_user.create_dm()
        await dm_channel.send(message)
        logger.info(f"Sent catch-up prompt to {user['user_id']} ({hours_late}h late)")

    except discord.Forbidden:
        logger.warning(f"Cannot DM user {user['user_id']}")
    except Exception as e:
        logger.error(f"Error sending catch-up to {user['user_id']}: {e}")


async def send_reengagement_prompt(user: dict):
    """Send a re-engagement message to a user who's been away."""
    try:
        discord_user = await bot.fetch_user(int(user['user_id']))
        if not discord_user:
            return

        personality = user.get('personality_preset', 'best_friend')
        message = get_reengagement_prompt(personality)

        dm_channel = await discord_user.create_dm()
        await dm_channel.send(message)
        logger.info(f"Sent re-engagement to {user['user_id']}")

    except discord.Forbidden:
        logger.warning(f"Cannot DM user {user['user_id']}")
    except Exception as e:
        logger.error(f"Error sending re-engagement to {user['user_id']}: {e}")


# ============================================
# ONBOARDING
# ============================================

async def handle_onboarding_complete(
    channel: discord.DMChannel,
    user_id: str,
    personality: str,
    time: str,
    start_now: bool
):
    """Handle completion of onboarding flow."""
    # Update user in database
    await update_user(
        user_id,
        personality_preset=personality,
        prompt_time=time,
        onboarding_complete=1
    )

    user = await get_or_create_user(user_id)

    if start_now:
        await start_journal_session(channel, user, prompt_type='first')

    logger.info(f"User {user_id} completed onboarding: {personality}, {time}")


# ============================================
# BOT EVENTS
# ============================================

@bot.event
async def on_ready():
    """Bot startup."""
    global scheduler

    logger.info(f"Kodak v2 logged in as {bot.user}")

    # Initialize database
    await init_db()
    logger.info("Database initialized")

    # Initialize and start scheduler
    scheduler = JournalScheduler(
        get_users_for_prompt=get_users_for_prompt,
        get_users_with_missed_prompts=get_users_with_missed_prompts,
        get_users_needing_reengagement=get_users_needing_reengagement,
        send_scheduled_prompt=send_scheduled_prompt,
        send_catch_up_prompt=send_catch_up_prompt,
        send_reengagement_prompt=send_reengagement_prompt,
        mark_prompt_sent=mark_prompt_sent
    )
    await scheduler.start()
    logger.info("Scheduler started")

    # Sync commands
    try:
        synced = await bot.tree.sync()
        logger.info(f"Synced {len(synced)} commands")
    except Exception as e:
        logger.error(f"Failed to sync commands: {e}")


@bot.event
async def on_message(message: discord.Message):
    """Handle incoming messages."""
    # Ignore bot's own messages
    if message.author == bot.user:
        return

    # Only handle DMs for v2
    if not isinstance(message.channel, discord.DMChannel):
        return

    user_id = str(message.author.id)

    # Get or create user
    user = await get_or_create_user(user_id, message.author.name)

    # Update last active
    await update_user(user_id, last_active=datetime.now().isoformat())

    # Check if user needs onboarding
    if not user.get('onboarding_complete'):
        # Check if already in onboarding flow
        state = get_onboarding_state(user_id)
        if state.selected_personality is None:
            # Start onboarding
            flow = OnboardingFlow(
                channel=message.channel,
                user_id=user_id,
                on_complete=lambda p, t, s: handle_onboarding_complete(
                    message.channel, user_id, p, t, s
                )
            )
            await flow.start()
        else:
            # Already in onboarding, remind them
            await message.channel.send(
                "Let's finish setting you up first! Use the buttons above to continue."
            )
        return

    # Check for active session
    if has_active_session(user_id):
        await process_session_message(message.channel, user, message.content)
    else:
        # No active session - start one (user-initiated)
        await start_journal_session(message.channel, user, prompt_type='user_initiated')
        # Process their message as the first response
        if has_active_session(user_id):
            await process_session_message(message.channel, user, message.content)


# ============================================
# COMMANDS
# ============================================

@bot.tree.command(name="schedule", description="Set your daily check-in time")
@app_commands.describe(time="Time for daily prompt (e.g., 8pm, 20:00)")
async def schedule_command(interaction: discord.Interaction, time: str):
    """Set the user's daily prompt time."""
    parsed = parse_time_input(time)

    if not parsed:
        await interaction.response.send_message(
            f"Couldn't understand '{time}'. Try something like '8pm' or '20:00'.",
            ephemeral=True
        )
        return

    user_id = str(interaction.user.id)
    await update_user(user_id, prompt_time=parsed)

    display_time = format_time_display(parsed)
    await interaction.response.send_message(
        f"Got it! I'll check in with you at **{display_time}** each day.\n\n"
        f"Use `/schedule` again to change the time, or `/skip` to skip a day.",
        ephemeral=True
    )
    logger.info(f"User {user_id} set schedule to {parsed}")


@bot.tree.command(name="skip", description="Skip today's check-in")
async def skip_command(interaction: discord.Interaction):
    """Skip today's prompt."""
    user_id = str(interaction.user.id)

    # Mark today's prompt as "sent" so scheduler won't send it
    await mark_prompt_sent(user_id)

    await interaction.response.send_message(
        "No problem, I'll skip today. See you tomorrow!",
        ephemeral=True
    )
    logger.info(f"User {user_id} skipped today's prompt")


@bot.tree.command(name="journal", description="Start a journaling session now")
async def journal_command(interaction: discord.Interaction):
    """Start an off-schedule journaling session."""
    user_id = str(interaction.user.id)

    # Check if already in a session
    if has_active_session(user_id):
        await interaction.response.send_message(
            "You're already in a session! Just keep chatting.",
            ephemeral=True
        )
        return

    user = await get_or_create_user(user_id, interaction.user.name)

    if not user.get('onboarding_complete'):
        await interaction.response.send_message(
            "Let's get you set up first! Send me any message to start onboarding.",
            ephemeral=True
        )
        return

    await interaction.response.send_message("Starting a session...", ephemeral=True)

    dm_channel = await interaction.user.create_dm()
    await start_journal_session(dm_channel, user, prompt_type='user_initiated')


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

        async def callback(self, select_interaction: discord.Interaction):
            selected = self.values[0]
            preset = PRESETS[selected]
            await update_user(user_id, personality_preset=selected)
            await select_interaction.response.edit_message(
                content=f"Updated to **{preset.name}**!\n\n*{preset.journaling_style}*",
                view=None
            )
            logger.info(f"User {user_id} changed personality to {selected}")

    class SetupView(discord.ui.View):
        def __init__(self):
            super().__init__(timeout=120)
            self.add_item(PersonalitySelect())

    await interaction.response.send_message(
        "**How should I show up?**\n\n"
        "Choose a personality that fits how you like to reflect:",
        view=SetupView(),
        ephemeral=True
    )


@bot.tree.command(name="depth", description="Set session depth preference")
@app_commands.describe(level="How deep should sessions go?")
@app_commands.choices(level=[
    app_commands.Choice(name="Quick (2-3 exchanges)", value="quick"),
    app_commands.Choice(name="Standard (4-6 exchanges)", value="standard"),
    app_commands.Choice(name="Deep (8+ exchanges)", value="deep"),
])
async def depth_command(interaction: discord.Interaction, level: str):
    """Set the user's depth preference."""
    user_id = str(interaction.user.id)
    await update_user(user_id, prompt_depth=level)

    descriptions = {
        'quick': "Quick check-ins, 2-3 exchanges",
        'standard': "Standard depth, 4-6 exchanges",
        'deep': "Deep exploration, follow your energy"
    }

    await interaction.response.send_message(
        f"Set to **{level}**: {descriptions[level]}.\n\n"
        f"I'll still adapt based on how much you share.",
        ephemeral=True
    )
    logger.info(f"User {user_id} set depth to {level}")


@bot.tree.command(name="values", description="See your value profile")
async def values_command(interaction: discord.Interaction):
    """Display the user's value profile."""
    await interaction.response.defer(ephemeral=True)

    user_id = str(interaction.user.id)
    profile = await get_user_value_profile(user_id)
    narrative = generate_value_narrative(profile)

    await interaction.followup.send(narrative, ephemeral=True)


@bot.tree.command(name="values-history", description="See how your values have changed")
async def values_history_command(interaction: discord.Interaction):
    """Show value changes over time."""
    await interaction.response.defer(ephemeral=True)

    user_id = str(interaction.user.id)

    # Get current and historical profiles
    current_profile = await get_user_value_profile(user_id)
    month_ago_profile = await get_value_snapshot(user_id, days_ago=30)

    if not month_ago_profile:
        await interaction.followup.send(
            "Not enough history yet to show changes.\n\n"
            "Keep journaling — after a month I'll be able to show how your values are shifting.",
            ephemeral=True
        )
        return

    # Generate change narrative
    change_narrative = generate_value_change_narrative(
        current_profile=current_profile,
        previous_profile=month_ago_profile,
        period_description="the past month"
    )

    if not change_narrative:
        await interaction.followup.send(
            "Your values have been pretty stable over the past month.\n\n"
            "No major shifts in what you emphasize.",
            ephemeral=True
        )
        return

    await interaction.followup.send(change_narrative, ephemeral=True)


# ============================================
# VALUE SHARING COMMANDS
# ============================================

class ShareValuesView(discord.ui.View):
    """Privacy selection UI for sharing values."""

    def __init__(self, user_id: str, profile, beliefs: list[dict]):
        super().__init__(timeout=300)
        self.user_id = user_id
        self.profile = profile
        self.beliefs = beliefs

        # Default: include all values, no beliefs
        self.included_values = set(ALL_VALUES)
        self.included_beliefs = set()
        self.display_name = "Anonymous"

    @discord.ui.button(label="Include all values", style=discord.ButtonStyle.primary, row=0)
    async def include_all_values(self, interaction: discord.Interaction, button: discord.ui.Button):
        if str(interaction.user.id) != self.user_id:
            await interaction.response.send_message("This isn't your export!", ephemeral=True)
            return
        self.included_values = set(ALL_VALUES)
        await interaction.response.send_message(
            f"All 10 values will be included.",
            ephemeral=True
        )

    @discord.ui.button(label="Only top values", style=discord.ButtonStyle.secondary, row=0)
    async def only_top_values(self, interaction: discord.Interaction, button: discord.ui.Button):
        if str(interaction.user.id) != self.user_id:
            await interaction.response.send_message("This isn't your export!", ephemeral=True)
            return
        top = self.profile.get_top_values(5)
        self.included_values = {v.value_name for v in top if v.normalized_score > 0.3}
        names = [VALUE_DEFINITIONS[v]["name"] for v in self.included_values]
        await interaction.response.send_message(
            f"Will include: {', '.join(names)}",
            ephemeral=True
        )

    @discord.ui.button(label="Add sample beliefs", style=discord.ButtonStyle.secondary, row=1)
    async def add_beliefs(self, interaction: discord.Interaction, button: discord.ui.Button):
        if str(interaction.user.id) != self.user_id:
            await interaction.response.send_message("This isn't your export!", ephemeral=True)
            return
        # Include top 3 most confident beliefs
        sorted_beliefs = sorted(self.beliefs, key=lambda b: b.get('confidence', 0), reverse=True)
        self.included_beliefs = {b['statement'] for b in sorted_beliefs[:3]}
        await interaction.response.send_message(
            f"Will include {len(self.included_beliefs)} sample beliefs.",
            ephemeral=True
        )

    @discord.ui.button(label="No beliefs", style=discord.ButtonStyle.secondary, row=1)
    async def no_beliefs(self, interaction: discord.Interaction, button: discord.ui.Button):
        if str(interaction.user.id) != self.user_id:
            await interaction.response.send_message("This isn't your export!", ephemeral=True)
            return
        self.included_beliefs = set()
        await interaction.response.send_message(
            "No beliefs will be included.",
            ephemeral=True
        )

    @discord.ui.button(label="Generate file", style=discord.ButtonStyle.success, row=2)
    async def generate_file(self, interaction: discord.Interaction, button: discord.ui.Button):
        if str(interaction.user.id) != self.user_id:
            await interaction.response.send_message("This isn't your export!", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)

        # Generate export
        json_str = export_to_json(
            profile=self.profile,
            display_name=self.display_name,
            included_values=list(self.included_values),
            included_beliefs=list(self.included_beliefs)
        )

        import io
        file = discord.File(
            io.BytesIO(json_str.encode()),
            filename=f"kodak-values-{self.user_id[:8]}.json"
        )

        await interaction.followup.send(
            f"Here's your value profile! Share this file with someone who uses Kodak.\n"
            f"They can use `/compare-file` to see how your values align.",
            file=file,
            ephemeral=True
        )

        self.stop()


class NameInputModal(discord.ui.Modal, title="Set Display Name"):
    """Modal for entering display name."""

    name_input = discord.ui.TextInput(
        label="How should you appear in the export?",
        placeholder="Your name or nickname",
        default="Anonymous",
        required=True,
        max_length=50
    )

    def __init__(self, view: ShareValuesView):
        super().__init__()
        self.view = view

    async def on_submit(self, interaction: discord.Interaction):
        self.view.display_name = self.name_input.value
        await interaction.response.send_message(
            f"Display name set to **{self.view.display_name}**",
            ephemeral=True
        )


@bot.tree.command(name="share-values", description="Export your value profile to share")
async def share_values_command(interaction: discord.Interaction):
    """Export value profile as shareable JSON with privacy controls."""
    await interaction.response.defer(ephemeral=True)

    user_id = str(interaction.user.id)
    profile = await get_user_value_profile(user_id)
    beliefs = await get_user_beliefs(user_id, limit=20)

    # Check if user has enough data
    top_values = profile.get_top_values(3)
    if not top_values or all(v.normalized_score == 0 for v in top_values):
        await interaction.followup.send(
            "You don't have enough data to share yet.\n\n"
            "Keep journaling and I'll build your value profile over time.",
            ephemeral=True
        )
        return

    view = ShareValuesView(user_id, profile, beliefs)

    # Add name input button
    name_button = discord.ui.Button(label="Set display name", style=discord.ButtonStyle.secondary, row=2)
    async def name_callback(button_interaction: discord.Interaction):
        if str(button_interaction.user.id) != user_id:
            await button_interaction.response.send_message("This isn't your export!", ephemeral=True)
            return
        await button_interaction.response.send_modal(NameInputModal(view))
    name_button.callback = name_callback
    view.add_item(name_button)

    # Show current top values
    top_names = [f"**{v.display_name}** ({v.normalized_score:.0%})" for v in top_values[:3] if v.normalized_score > 0.2]

    await interaction.followup.send(
        "**Share Your Values**\n\n"
        f"Your top values: {', '.join(top_names)}\n\n"
        "Choose what to include in your export:\n"
        "• **Values** — your normalized scores (default: all 10)\n"
        "• **Beliefs** — sample statements that shaped your values (optional)\n"
        "• **Display name** — how you appear to the recipient\n\n"
        "Then click **Generate file** to create your shareable profile.",
        view=view,
        ephemeral=True
    )
    logger.info(f"User {user_id} started share-values flow")


@bot.tree.command(name="compare-file", description="Compare your values with someone's shared file")
async def compare_file_command(interaction: discord.Interaction, file: discord.Attachment):
    """Load and compare a shared value profile."""
    await interaction.response.defer(ephemeral=True)

    user_id = str(interaction.user.id)

    # Validate file
    if not file.filename.endswith('.json'):
        await interaction.followup.send(
            "Please attach a `.json` file exported from Kodak.",
            ephemeral=True
        )
        return

    if file.size > 100000:  # 100KB max
        await interaction.followup.send(
            "File too large. Kodak export files should be small.",
            ephemeral=True
        )
        return

    try:
        # Download and parse file
        content = await file.read()
        json_str = content.decode('utf-8')

        imported = parse_import_data(json_str)
        if not imported:
            await interaction.followup.send(
                "Couldn't read that file. Make sure it's a Kodak value export.\n\n"
                "Ask your friend to use `/share-values` to create a valid export.",
                ephemeral=True
            )
            return

        # Get user's profile for comparison
        your_profile = await get_user_value_profile(user_id)

        # Check if user has data
        top_values = your_profile.get_top_values(3)
        if not top_values or all(v.normalized_score == 0 for v in top_values):
            await interaction.followup.send(
                "You need to build your own value profile first before comparing.\n\n"
                "Keep journaling and then try again!",
                ephemeral=True
            )
            return

        # Generate comparison
        comparison_text = generate_comparison_with_import_narrative(your_profile, imported)

        await interaction.followup.send(comparison_text, ephemeral=True)
        logger.info(f"User {user_id} compared values with {imported.display_name}")

    except Exception as e:
        logger.error(f"Error in compare-file: {e}")
        await interaction.followup.send(
            "Something went wrong reading that file. Make sure it's a valid Kodak export.",
            ephemeral=True
        )


@bot.tree.command(name="pause", description="Pause daily check-ins")
async def pause_command(interaction: discord.Interaction):
    """Pause scheduled prompts."""
    user_id = str(interaction.user.id)
    await update_user(user_id, tracking_paused=1)

    await interaction.response.send_message(
        "Paused. I won't send check-ins until you `/resume`.\n"
        "You can still message me anytime.",
        ephemeral=True
    )
    logger.info(f"User {user_id} paused prompts")


@bot.tree.command(name="resume", description="Resume daily check-ins")
async def resume_command(interaction: discord.Interaction):
    """Resume scheduled prompts."""
    user_id = str(interaction.user.id)
    user = await update_user(user_id, tracking_paused=0)

    prompt_time = user.get('prompt_time')
    if prompt_time:
        display_time = format_time_display(prompt_time)
        await interaction.response.send_message(
            f"Resumed! I'll check in at **{display_time}**.",
            ephemeral=True
        )
    else:
        await interaction.response.send_message(
            "Resumed! Use `/schedule` to set your check-in time.",
            ephemeral=True
        )
    logger.info(f"User {user_id} resumed prompts")


@bot.tree.command(name="export", description="Download all your data")
async def export_command(interaction: discord.Interaction):
    """Export user data as JSON."""
    await interaction.response.defer(ephemeral=True)

    user_id = str(interaction.user.id)
    data = await export_user_data(user_id)

    import json
    import io

    json_str = json.dumps(data, indent=2, default=str)
    file = discord.File(
        io.BytesIO(json_str.encode()),
        filename=f"kodak-export-{user_id[:8]}.json"
    )

    await interaction.followup.send(
        "Here's all your data:",
        file=file,
        ephemeral=True
    )
    logger.info(f"User {user_id} exported data")


@bot.tree.command(name="clear", description="Delete all your data")
async def clear_command(interaction: discord.Interaction):
    """Delete all user data (with confirmation)."""

    class ConfirmClear(discord.ui.View):
        def __init__(self):
            super().__init__(timeout=60)

        @discord.ui.button(label="Yes, delete everything", style=discord.ButtonStyle.danger)
        async def confirm(self, button_interaction: discord.Interaction, button: discord.ui.Button):
            await clear_all_user_data(str(interaction.user.id))
            await button_interaction.response.edit_message(
                content="All your data has been deleted.",
                view=None
            )
            logger.info(f"User {interaction.user.id} cleared all data")

        @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary)
        async def cancel(self, button_interaction: discord.Interaction, button: discord.ui.Button):
            await button_interaction.response.edit_message(
                content="Cancelled. Your data is safe.",
                view=None
            )

    await interaction.response.send_message(
        "**Are you sure?**\n\n"
        "This will permanently delete:\n"
        "- All your journal sessions\n"
        "- All extracted beliefs\n"
        "- Your value profile\n"
        "- All conversation history\n\n"
        "This cannot be undone.",
        view=ConfirmClear(),
        ephemeral=True
    )


# ============================================
# BELIEF MANAGEMENT COMMANDS
# ============================================

def confidence_bar(confidence: float) -> str:
    """Create a visual confidence bar."""
    filled = int(confidence * 5)
    return "●" * filled + "○" * (5 - filled)


@bot.tree.command(name="map", description="See your belief map")
async def map_command(interaction: discord.Interaction):
    """Show the user's belief map grouped by topic."""
    await interaction.response.defer(ephemeral=True)

    user_id = str(interaction.user.id)
    beliefs = await get_user_beliefs(user_id)

    if not beliefs:
        await interaction.followup.send(
            "No beliefs mapped yet. Keep journaling and I'll extract patterns from what you share!",
            ephemeral=True
        )
        return

    topics = await get_all_topics(user_id)

    response = f"**Your Belief Map**\n"
    response += f"*{len(beliefs)} beliefs across {len(topics)} topics*\n\n"

    if topics:
        for topic in topics[:6]:
            topic_beliefs = await get_beliefs_by_topic(user_id, topic)
            response += f"**{topic.title()}**\n"
            for b in topic_beliefs[:3]:
                conf = confidence_bar(b.get('confidence', 0.5))
                stmt = b['statement'][:60] + "..." if len(b['statement']) > 60 else b['statement']
                response += f"  [{conf}] {stmt}\n"
            response += "\n"

    response += f"Use `/explore [topic]` to dive deeper, or `/beliefs` for the full list."

    if len(response) > 2000:
        response = response[:1997] + "..."

    await interaction.followup.send(response, ephemeral=True)


@bot.tree.command(name="explore", description="Explore beliefs about a topic")
@app_commands.describe(topic="The topic to explore")
async def explore_command(interaction: discord.Interaction, topic: str):
    """Explore beliefs about a specific topic."""
    await interaction.response.defer(ephemeral=True)

    user_id = str(interaction.user.id)
    beliefs = await get_beliefs_by_topic(user_id, topic.lower())

    if not beliefs:
        # Try searching in statements
        all_beliefs = await get_user_beliefs(user_id)
        beliefs = [
            b for b in all_beliefs
            if topic.lower() in b["statement"].lower()
            or topic.lower() in " ".join(b.get("topics", []))
        ]

    if not beliefs:
        topics = await get_all_topics(user_id)
        if topics:
            await interaction.followup.send(
                f"No beliefs found about '{topic}'.\n\n"
                f"**Topics you have:** {', '.join(topics[:10])}",
                ephemeral=True
            )
        else:
            await interaction.followup.send(
                f"No beliefs found about '{topic}'.\n\n"
                "Keep journaling to build your map!",
                ephemeral=True
            )
        return

    response = f"**Beliefs about: {topic}**\n\n"
    for b in beliefs[:10]:
        conf = confidence_bar(b.get('confidence', 0.5))
        response += f"[{conf}] {b['statement']}\n"
        response += f"  `ID: {b['id'][:8]}`\n\n"

    if len(response) > 2000:
        response = response[:1997] + "..."

    await interaction.followup.send(response, ephemeral=True)


@bot.tree.command(name="beliefs", description="List all your beliefs")
async def beliefs_command(interaction: discord.Interaction):
    """List all beliefs in raw format."""
    await interaction.response.defer(ephemeral=True)

    user_id = str(interaction.user.id)
    beliefs = await get_user_beliefs(user_id)

    if not beliefs:
        await interaction.followup.send(
            "No beliefs recorded yet. Keep journaling!",
            ephemeral=True
        )
        return

    response = f"**Your Beliefs** ({len(beliefs)} total)\n\n"
    for b in beliefs[:15]:
        conf = confidence_bar(b.get('confidence', 0.5))
        imp = "⭐" if b.get('importance', 3) >= 4 else ""
        response += f"[{conf}]{imp} {b['statement']}\n"
        response += f"  `{b['id'][:8]}` · {', '.join(b.get('topics', []))}\n\n"

    if len(beliefs) > 15:
        response += f"*...and {len(beliefs) - 15} more. Use `/explore [topic]` to filter.*"

    if len(response) > 2000:
        response = response[:1997] + "..."

    await interaction.followup.send(response, ephemeral=True)


@bot.tree.command(name="belief", description="View a single belief in detail")
@app_commands.describe(belief_id="The belief ID (first 8 characters)")
async def belief_command(interaction: discord.Interaction, belief_id: str):
    """View details of a single belief."""
    await interaction.response.defer(ephemeral=True)

    user_id = str(interaction.user.id)

    # Find belief by partial ID
    all_beliefs = await get_user_beliefs(user_id, include_deleted=False)
    belief = next((b for b in all_beliefs if b['id'].startswith(belief_id)), None)

    if not belief:
        await interaction.followup.send(
            f"Couldn't find a belief starting with `{belief_id}`.\n"
            "Use `/beliefs` to see your beliefs with their IDs.",
            ephemeral=True
        )
        return

    conf = confidence_bar(belief.get('confidence', 0.5))
    imp = belief.get('importance', 3)
    imp_stars = "⭐" * imp

    response = f"**Belief Detail**\n\n"
    response += f"> {belief['statement']}\n\n"
    response += f"**Confidence:** [{conf}] {belief.get('confidence', 0.5):.0%}\n"
    response += f"**Importance:** {imp_stars} ({imp}/5)\n"
    response += f"**Topics:** {', '.join(belief.get('topics', ['none']))}\n"
    response += f"**Source:** {belief.get('source_type', 'unknown')}\n"
    response += f"**First expressed:** {belief.get('first_expressed', 'unknown')[:10]}\n"
    response += f"\n`ID: {belief['id']}`"

    await interaction.followup.send(response, ephemeral=True)


@bot.tree.command(name="forget", description="Delete a belief")
@app_commands.describe(belief_id="The belief ID to delete")
async def forget_command(interaction: discord.Interaction, belief_id: str):
    """Delete a belief from the map."""
    user_id = str(interaction.user.id)

    # Find belief by partial ID
    all_beliefs = await get_user_beliefs(user_id)
    belief = next((b for b in all_beliefs if b['id'].startswith(belief_id)), None)

    if not belief:
        await interaction.response.send_message(
            f"Couldn't find a belief starting with `{belief_id}`.",
            ephemeral=True
        )
        return

    success = await soft_delete_belief(belief['id'], user_id)

    if success:
        await interaction.response.send_message(
            f"Forgotten: *\"{belief['statement'][:50]}...\"*\n\n"
            "Use `/undo` to restore it.",
            ephemeral=True
        )
        logger.info(f"User {user_id} forgot belief {belief['id']}")
    else:
        await interaction.response.send_message(
            "Couldn't delete that belief.",
            ephemeral=True
        )


@bot.tree.command(name="undo", description="Restore the last forgotten belief")
async def undo_command(interaction: discord.Interaction):
    """Restore the most recently deleted belief."""
    user_id = str(interaction.user.id)

    deleted = await get_last_deleted_belief(user_id)

    if not deleted:
        await interaction.response.send_message(
            "Nothing to undo.",
            ephemeral=True
        )
        return

    success = await restore_belief(deleted['id'], user_id)

    if success:
        await interaction.response.send_message(
            f"Restored: *\"{deleted['statement'][:50]}...\"*",
            ephemeral=True
        )
        logger.info(f"User {user_id} restored belief {deleted['id']}")
    else:
        await interaction.response.send_message(
            "Couldn't restore the belief.",
            ephemeral=True
        )


@bot.tree.command(name="confidence", description="Update your confidence in a belief")
@app_commands.describe(
    belief_id="The belief ID",
    level="New confidence level"
)
@app_commands.choices(level=[
    app_commands.Choice(name="Very uncertain (20%)", value="0.2"),
    app_commands.Choice(name="Somewhat uncertain (40%)", value="0.4"),
    app_commands.Choice(name="Neutral (60%)", value="0.6"),
    app_commands.Choice(name="Fairly confident (80%)", value="0.8"),
    app_commands.Choice(name="Very confident (100%)", value="1.0"),
])
async def confidence_command(interaction: discord.Interaction, belief_id: str, level: str):
    """Update confidence in a belief."""
    user_id = str(interaction.user.id)
    new_confidence = float(level)

    # Find belief by partial ID
    all_beliefs = await get_user_beliefs(user_id)
    belief = next((b for b in all_beliefs if b['id'].startswith(belief_id)), None)

    if not belief:
        await interaction.response.send_message(
            f"Couldn't find a belief starting with `{belief_id}`.",
            ephemeral=True
        )
        return

    success = await update_belief_confidence(belief['id'], user_id, new_confidence)

    if success:
        conf = confidence_bar(new_confidence)
        await interaction.response.send_message(
            f"Updated confidence to [{conf}] {new_confidence:.0%}\n\n"
            f"*\"{belief['statement'][:60]}...\"*",
            ephemeral=True
        )
    else:
        await interaction.response.send_message(
            "Couldn't update confidence.",
            ephemeral=True
        )


@bot.tree.command(name="mark", description="Mark how important a belief is")
@app_commands.describe(
    belief_id="The belief ID",
    importance="How important is this belief to you?"
)
@app_commands.choices(importance=[
    app_commands.Choice(name="⭐ Minor", value=1),
    app_commands.Choice(name="⭐⭐ Somewhat", value=2),
    app_commands.Choice(name="⭐⭐⭐ Moderate", value=3),
    app_commands.Choice(name="⭐⭐⭐⭐ Important", value=4),
    app_commands.Choice(name="⭐⭐⭐⭐⭐ Core belief", value=5),
])
async def mark_command(interaction: discord.Interaction, belief_id: str, importance: int):
    """Set importance of a belief."""
    user_id = str(interaction.user.id)

    # Find belief by partial ID
    all_beliefs = await get_user_beliefs(user_id)
    belief = next((b for b in all_beliefs if b['id'].startswith(belief_id)), None)

    if not belief:
        await interaction.response.send_message(
            f"Couldn't find a belief starting with `{belief_id}`.",
            ephemeral=True
        )
        return

    success = await update_belief_importance(belief['id'], user_id, importance)

    if success:
        stars = "⭐" * importance
        await interaction.response.send_message(
            f"Marked as {stars}\n\n"
            f"*\"{belief['statement'][:60]}...\"*",
            ephemeral=True
        )
    else:
        await interaction.response.send_message(
            "Couldn't update importance.",
            ephemeral=True
        )


@bot.tree.command(name="core", description="Show your most important beliefs")
async def core_command(interaction: discord.Interaction):
    """Show beliefs marked as important."""
    await interaction.response.defer(ephemeral=True)

    user_id = str(interaction.user.id)
    beliefs = await get_important_beliefs(user_id, min_importance=4)

    if not beliefs:
        await interaction.followup.send(
            "No core beliefs marked yet.\n\n"
            "Use `/mark [id] [importance]` to mark beliefs that matter most to you.",
            ephemeral=True
        )
        return

    response = "**Your Core Beliefs**\n\n"
    for b in beliefs[:10]:
        stars = "⭐" * b.get('importance', 4)
        response += f"{stars} {b['statement']}\n\n"

    await interaction.followup.send(response, ephemeral=True)


@bot.tree.command(name="style", description="Fine-tune personality dimensions")
async def style_command(interaction: discord.Interaction):
    """Show current personality dimensions."""
    user_id = str(interaction.user.id)
    user = await get_or_create_user(user_id)

    preset = user.get('personality_preset', 'best_friend')
    warmth = user.get('warmth', 3)
    directness = user.get('directness', 3)
    playfulness = user.get('playfulness', 3)
    formality = user.get('formality', 3)

    def dim_bar(val):
        return "█" * val + "░" * (5 - val)

    response = (
        f"**Your Style** (preset: {preset})\n\n"
        f"Warmth:      [{dim_bar(warmth)}] {warmth}/5\n"
        f"Directness:  [{dim_bar(directness)}] {directness}/5\n"
        f"Playfulness: [{dim_bar(playfulness)}] {playfulness}/5\n"
        f"Formality:   [{dim_bar(formality)}] {formality}/5\n\n"
        f"Use `/setup` to change personality preset."
    )

    await interaction.response.send_message(response, ephemeral=True)


@bot.tree.command(name="timezone", description="Set your timezone")
@app_commands.describe(tz="Your timezone (e.g., America/New_York, Europe/London)")
async def timezone_command(interaction: discord.Interaction, tz: str):
    """Set user's timezone."""
    user_id = str(interaction.user.id)

    # Basic validation
    common_timezones = [
        'America/New_York', 'America/Chicago', 'America/Denver', 'America/Los_Angeles',
        'Europe/London', 'Europe/Paris', 'Europe/Berlin',
        'Asia/Tokyo', 'Asia/Shanghai', 'Asia/Singapore',
        'Australia/Sydney', 'Pacific/Auckland', 'UTC'
    ]

    # Accept common abbreviations
    tz_map = {
        'est': 'America/New_York', 'edt': 'America/New_York',
        'cst': 'America/Chicago', 'cdt': 'America/Chicago',
        'mst': 'America/Denver', 'mdt': 'America/Denver',
        'pst': 'America/Los_Angeles', 'pdt': 'America/Los_Angeles',
        'gmt': 'Europe/London', 'bst': 'Europe/London',
        'utc': 'UTC'
    }

    resolved_tz = tz_map.get(tz.lower(), tz)

    await update_user(user_id, timezone=resolved_tz)

    await interaction.response.send_message(
        f"Timezone set to **{resolved_tz}**.\n\n"
        "Your scheduled prompts will use this timezone.",
        ephemeral=True
    )
    logger.info(f"User {user_id} set timezone to {resolved_tz}")


@bot.tree.command(name="history", description="See how a belief has evolved over time")
@app_commands.describe(belief_id="The belief ID (first 8 characters)")
async def history_command(interaction: discord.Interaction, belief_id: str):
    """Show the evolution history of a specific belief."""
    await interaction.response.defer(ephemeral=True)

    user_id = str(interaction.user.id)
    all_beliefs = await get_user_beliefs(user_id)
    belief = next((b for b in all_beliefs if b['id'].startswith(belief_id)), None)

    if not belief:
        await interaction.followup.send(
            f"No belief found starting with `{belief_id}`. Use `/beliefs` to see IDs.",
            ephemeral=True
        )
        return

    history = await get_belief_history(belief['id'])

    # Current state
    conf = confidence_bar(belief.get('confidence', 0.5))
    imp = "⭐" * belief.get('importance', 3)

    response = f"**Evolution of Belief:**\n"
    response += f"*\"{belief['statement']}\"*\n\n"
    response += f"**Current state:** [{conf}] {int(belief.get('confidence', 0.5) * 100)}% confidence, {imp}\n"
    response += f"**First expressed:** {belief.get('first_expressed', 'unknown')[:10]}\n\n"

    if history:
        response += "**Changes:**\n```\n"
        for h in history[:10]:
            timestamp = h.get('timestamp', '')[:10]

            if h.get('old_confidence') is not None and h.get('new_confidence') is not None:
                old_pct = int(h['old_confidence'] * 100)
                new_pct = int(h['new_confidence'] * 100)
                direction = "↑" if new_pct > old_pct else "↓"
                response += f"{timestamp} — Confidence {old_pct}% {direction} {new_pct}%\n"

            if h.get('old_statement') and h.get('new_statement'):
                response += f"{timestamp} — Wording changed\n"
                response += f"  From: \"{h['old_statement'][:40]}...\"\n"
                response += f"  To:   \"{h['new_statement'][:40]}...\"\n"

            if h.get('trigger'):
                response += f"  Trigger: {h['trigger'][:50]}\n"

            response += "\n"
        response += "```"

        if len(history) > 10:
            response += f"\n*...and {len(history) - 10} earlier change(s)*"
    else:
        response += "*No recorded changes yet. This belief has remained stable.*\n"

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

    user_id = str(interaction.user.id)
    changes = await get_recent_changes(user_id, days)

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
                'importance': c['importance'],
                'changes': []
            }
        belief_changes[bid]['changes'].append(c)

    response = f"**Belief Changes** (last {days} days)\n\n"

    for bid, data in list(belief_changes.items())[:5]:
        stmt = data['statement'][:50]
        if len(data['statement']) > 50:
            stmt += "..."

        response += f"**{stmt}**\n"
        for ch in data['changes'][:3]:
            ts = ch.get('timestamp', '')[:10]
            if ch.get('old_confidence') is not None and ch.get('new_confidence') is not None:
                old_pct = int(ch['old_confidence'] * 100)
                new_pct = int(ch['new_confidence'] * 100)
                direction = "↑" if new_pct > old_pct else "↓"
                response += f"  {ts}: {old_pct}% {direction} {new_pct}%\n"
        response += f"  `{bid[:8]}`\n\n"

    if len(belief_changes) > 5:
        response += f"*...and {len(belief_changes) - 5} more beliefs with changes*"

    if len(response) > 2000:
        response = response[:1997] + "..."

    await interaction.followup.send(response, ephemeral=True)


@bot.tree.command(name="tensions", description="Show beliefs that might contradict each other")
async def tensions_command(interaction: discord.Interaction):
    """Show all contradicting belief pairs."""
    await interaction.response.defer(ephemeral=True)

    user_id = str(interaction.user.id)
    tensions = await get_all_tensions(user_id)

    if not tensions:
        await interaction.followup.send(
            "No tensions found in your belief map.\n\n"
            "This could mean your beliefs are consistent, or I haven't "
            "detected any contradictions yet. Keep journaling and I'll "
            "notice if something doesn't quite fit together.",
            ephemeral=True
        )
        return

    response = "**Tensions in Your Belief Map**\n\n"
    response += "*These beliefs might be in tension with each other. "
    response += "Exploring contradictions can lead to deeper understanding.*\n\n"

    for i, t in enumerate(tensions[:5], 1):
        src_imp = "⭐" * t.get('source_importance', 3)
        tgt_imp = "⭐" * t.get('target_importance', 3)

        src_stmt = t['source_statement'][:60]
        if len(t['source_statement']) > 60:
            src_stmt += "..."

        tgt_stmt = t['target_statement'][:60]
        if len(t['target_statement']) > 60:
            tgt_stmt += "..."

        response += f"**Tension {i}:**\n"
        response += f"{src_imp} *\"{src_stmt}\"*\n"
        response += f"  vs\n"
        response += f"{tgt_imp} *\"{tgt_stmt}\"*\n\n"

    if len(tensions) > 5:
        response += f"\n*...and {len(tensions) - 5} more tension(s)*"

    if len(response) > 2000:
        response = response[:1997] + "..."

    await interaction.followup.send(response, ephemeral=True)


@bot.tree.command(name="help", description="Show available commands")
async def help_command(interaction: discord.Interaction):
    """Show help information."""
    embed = discord.Embed(
        title="Kodak Commands",
        description="Reflective journaling companion",
        color=0x7289da
    )

    embed.add_field(
        name="📅 Scheduling",
        value=(
            "`/schedule [time]` — Set daily check-in time\n"
            "`/skip` — Skip today's check-in\n"
            "`/pause` — Pause all check-ins\n"
            "`/resume` — Resume check-ins\n"
            "`/journal` — Start a session now\n"
            "`/timezone [tz]` — Set your timezone"
        ),
        inline=False
    )

    embed.add_field(
        name="🎭 Personality",
        value=(
            "`/setup` — Change personality preference\n"
            "`/depth` — Set session depth (quick/standard/deep)\n"
            "`/style` — View your personality dimensions"
        ),
        inline=False
    )

    embed.add_field(
        name="📋 Beliefs",
        value=(
            "`/map` — See your belief map by topic\n"
            "`/beliefs` — List all your beliefs\n"
            "`/belief [id]` — View a belief in detail\n"
            "`/explore [topic]` — Explore beliefs about a topic\n"
            "`/core` — Show your most important beliefs"
        ),
        inline=False
    )

    embed.add_field(
        name="✏️ Edit Beliefs",
        value=(
            "`/confidence [id] [level]` — Update belief confidence\n"
            "`/mark [id] [importance]` — Set belief importance\n"
            "`/forget [id]` — Delete a belief\n"
            "`/undo` — Restore last deleted belief"
        ),
        inline=False
    )

    embed.add_field(
        name="📊 History & Analysis",
        value=(
            "`/history [id]` — See how a belief evolved\n"
            "`/changes [days]` — See recent belief changes\n"
            "`/tensions` — Show potentially conflicting beliefs"
        ),
        inline=False
    )

    embed.add_field(
        name="🎯 Values",
        value=(
            "`/values` — See your value profile\n"
            "`/values-history` — See how values changed over time\n"
            "`/share-values` — Export your values to share\n"
            "`/compare-file` — Compare with someone's export"
        ),
        inline=False
    )

    embed.add_field(
        name="🔒 Privacy & Data",
        value=(
            "`/export` — Download all your data (JSON)\n"
            "`/clear` — Delete everything"
        ),
        inline=False
    )

    embed.set_footer(text="Just message me anytime to start journaling")

    await interaction.response.send_message(embed=embed, ephemeral=True)


# ============================================
# RUN
# ============================================

def main():
    """Run the bot."""
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        logger.error("DISCORD_TOKEN not found in environment")
        return

    logger.info("Starting Kodak v2...")
    bot.run(token)


if __name__ == "__main__":
    main()
