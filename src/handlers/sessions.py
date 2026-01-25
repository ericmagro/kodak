"""Session management and lifecycle handlers."""

import uuid
import asyncio
import logging
import discord
from datetime import datetime, timedelta

from structured_logging import log_session_event, log_user_action, log_error_with_context

from session import SessionState, SessionStage, create_session, end_session, get_active_session, determine_next_stage
from db import (
    get_or_create_user, update_user,
    create_session as db_create_session, end_session as db_end_session,
    update_session, get_completed_session_count
)
from prompts import get_opener, get_first_session_framing, get_closure
from personality import build_session_system_prompt
from extractor import extract_beliefs_and_values
from client import create_message
import anthropic
from values import update_user_value_profile, create_value_snapshot

logger = logging.getLogger('kodak')


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

    # Get and send opener (pass last used from DB to avoid repeats)
    opener = get_opener(personality, last_opener=user.get('last_opener'))
    session.opener_used = opener

    # Persist the opener so it survives restarts
    await update_user(user_id, last_opener=opener)

    # Add first session framing if needed
    if is_first:
        framing = get_first_session_framing(personality)
        message = f"{opener}\n\n*{framing}*"
    else:
        message = opener

    await channel.send(message)

    log_session_event(
        logger, "session_started", session_id, user_id,
        prompt_type=prompt_type, is_first_session=is_first, personality=personality
    )
    return session


async def process_session_message(
    channel: discord.DMChannel,
    user: dict,
    message_content: str
) -> None:
    """Process a user's message during an active session."""
    user_id = user['user_id']

    # Get active session
    session = get_active_session(user_id)
    if not session:
        logger.warning(f"No active session for user {user_id}")
        await channel.send("I don't think we have an active session. Use `/journal` to start one!")
        return

    # Process the message and update state
    depth = 'short' if len(message_content) < 50 else 'long' if len(message_content) > 200 else 'medium'
    session.add_user_message(message_content, depth)

    # Update database
    await update_session(session.session_id, message_count=session.exchange_count)

    # Extract beliefs from this message (async, doesn't block response)
    try:
        # Get existing beliefs for context
        from db import get_user_beliefs
        existing_beliefs = await get_user_beliefs(user_id, limit=20)

        # Extract with conversation context
        extraction_result = await extract_beliefs_and_values(
            message=message_content,
            conversation_context=session.messages,
            existing_beliefs=existing_beliefs
        )

        if extraction_result.beliefs:
            # Convert ExtractedBelief objects to dicts for session storage
            belief_dicts = [
                {
                    'statement': b.statement,
                    'themes': b.themes,
                    'confidence': b.confidence
                }
                for b in extraction_result.beliefs
            ]
            session.extracted_beliefs.extend(belief_dicts)
            logger.info(f"Extracted {len(belief_dicts)} beliefs from user {user_id}")
    except Exception as e:
        logger.error(f"Belief extraction failed for user {user_id}: {e}")

    # Determine next stage
    next_stage = determine_next_stage(session)
    session.stage = next_stage

    # Check if we should close
    if next_stage == SessionStage.CLOSE:
        await close_session(channel, user, session)
        return

    # Generate response using LLM
    try:
        bot_response = await generate_session_response(session, message_content)
        await channel.send(bot_response)
        logger.info(f"Sent response to user {user_id} in session {session.session_id}")

    except anthropic.APITimeoutError:
        logger.error("LLM request timed out during session response")
        await channel.send("Sorry, I'm taking too long to think. Let me try to respond more quickly...")
        # Try with a shorter prompt
        try:
            fallback_response = await generate_session_response(session, message_content, fallback=True)
            await channel.send(fallback_response)
        except Exception as e:
            logger.error(f"Fallback response also failed: {e}")
            await channel.send("I'm having trouble responding right now. Let's continue this conversation later.")
    except anthropic.APIError as e:
        logger.error(f"LLM API error: {e}")
        await channel.send("I'm having trouble thinking right now. Can you try again in a moment?")
    except Exception as e:
        logger.error(f"Unexpected error in session response: {e}")
        await channel.send("I hear you. Tell me more about that.")


async def generate_session_response(session: SessionState, user_message: str, fallback: bool = False) -> str:
    """Generate a contextual response using the LLM."""
    if fallback:
        # Simple fallback for timeouts
        return "I hear you. Tell me more about that."

    # Build system prompt
    system_prompt = build_session_system_prompt(
        preset_key=session.personality,
        session_stage=session.stage.value,
        depth_setting=session.depth_setting,
        is_first_session=session.is_first_session,
        exchange_count=session.exchange_count
    )

    # Add stage instruction
    stage_instructions = {
        SessionStage.OPENER: "Ask a follow-up question to understand what's on their mind.",
        SessionStage.ANCHOR: "Help them focus on one specific thing. Ask them to elaborate on the most interesting part.",
        SessionStage.PROBE: "Go deeper. Ask why this matters or what makes it significant.",
        SessionStage.CONNECT: "Help them connect this to broader patterns or values.",
        SessionStage.CLOSE: "Begin to wrap up thoughtfully."
    }

    instruction = stage_instructions.get(session.stage, "Continue the conversation naturally.")
    full_system = f"{system_prompt}\n\n{instruction}"

    # Build conversation history from session messages
    messages = session.get_recent_context(6)  # Get last 6 messages (3 exchanges)

    # Add current message
    messages.append({"role": "user", "content": user_message})

    try:
        response = await create_message(
            messages=messages,
            system=full_system,
            max_tokens=300 if not fallback else 100
        )

        # Store bot's response in session
        session.add_bot_message(response)

        return response

    except Exception as e:
        logger.error(f"Error generating session response: {e}")
        return "I hear you. Tell me more about that."


async def should_prompt_weekly_summary(user_id: str, user: dict = None) -> bool:
    """Check if user should be prompted for a weekly summary."""
    from summaries import gather_week_data, get_past_summaries

    if user is None:
        user = await get_or_create_user(user_id)

    # Check if already prompted recently (within last 3 days)
    last_prompt = user.get('last_weekly_summary_prompt')
    if last_prompt:
        try:
            last_prompt_time = datetime.fromisoformat(last_prompt)
            if datetime.now() - last_prompt_time < timedelta(days=3):
                return False
        except ValueError:
            pass  # Ignore invalid timestamps

    # Get this week's data
    try:
        week_data = await gather_week_data(user_id, user=user)

        # Need at least 5 sessions this week
        if week_data['session_count'] < 5:
            return False

        # Check if they already have a summary for this week
        current_week_start = week_data['period_start']
        existing_summaries = await get_past_summaries(user_id, 'week', limit=5)

        for summary in existing_summaries:
            if summary['period_start'] == current_week_start:
                return False  # Already has a summary for this week

        return True

    except Exception as e:
        logger.error(f"Error checking weekly summary eligibility for {user_id}: {e}")
        return False


async def send_weekly_summary_prompt(channel: discord.DMChannel, user_id: str):
    """Send a prompt asking if user wants to see their weekly summary."""

    class WeeklySummaryView(discord.ui.View):
        def __init__(self):
            super().__init__(timeout=300)  # 5 minute timeout

        @discord.ui.button(label="Yes, show me!", style=discord.ButtonStyle.primary, emoji="📊")
        async def show_summary(self, interaction: discord.Interaction, button: discord.ui.Button):
            await interaction.response.defer()

            # Import here to avoid circular imports
            from summaries import create_weekly_summary

            try:
                summary = await create_weekly_summary(user_id)

                # Create embed for summary
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
                from summaries import format_date_range
                date_range = format_date_range(summary['period_start'], summary['period_end'])
                stats = f"{summary['session_count']} sessions"
                if summary['belief_count'] > 0:
                    stats += f" · {summary['belief_count']} beliefs emerged"
                embed.set_footer(text=f"{date_range} · {stats}")

                await interaction.followup.send(embed=embed)
                logger.info(f"Sent weekly summary to user {user_id} via prompt")

            except Exception as e:
                logger.error(f"Error generating weekly summary for {user_id}: {e}")
                await interaction.followup.send("Sorry, I had trouble generating your summary. Try using `/summary week` instead.")

            self.stop()

        @discord.ui.button(label="Maybe later", style=discord.ButtonStyle.secondary)
        async def maybe_later(self, interaction: discord.Interaction, button: discord.ui.Button):
            await interaction.response.send_message("No worries! Use `/summary week` whenever you're ready.", ephemeral=True)
            self.stop()

    message = (
        "**You've been busy this week!** 📈\n\n"
        "You've had 5+ journaling sessions—want to see what patterns emerged? "
        "I can generate a summary of your week's themes and insights."
    )

    view = WeeklySummaryView()
    await channel.send(message, view=view)

    # Update last prompt time
    await update_user(user_id, last_weekly_summary_prompt=datetime.now().isoformat())
    logger.info(f"Sent weekly summary prompt to user {user_id}")


async def check_and_send_milestone_message(channel: discord.DMChannel, user_id: str, session_count: int):
    """Check if user hit a milestone and send appropriate celebratory message."""
    milestones = [
        (5, "**You've completed 5 sessions!** 🎉\n\nYou've finished the \"getting to know you\" phase. I'm starting to see patterns in what matters to you. Keep going—the more we talk, the clearer your themes become."),
        (15, "**Something exciting is happening** ✨\n\nWith 15 sessions under your belt, your themes are really starting to emerge. This is where things get interesting—I can see what you consistently return to in your thoughts. Use `/themes` to explore what's surfacing."),
        (20, "**Your themes are crystallizing** 💎\n\nAfter 20 sessions, clear patterns have emerged in what you value and think about. This is the first real payoff moment—you're seeing yourself more clearly than before. Try `/themes` to see what's standing out."),
        (50, "**Your themes are stable** 🌟\n\nWith 50 sessions completed, you've built a solid foundation of self-understanding. Your core themes are well-established now. Consider using `/share-themes` to explore how your values compare with someone close to you.")
    ]

    for milestone_count, message in milestones:
        if session_count == milestone_count:
            # Send milestone message with a delay to feel natural
            await asyncio.sleep(2)
            await channel.send(message)
            logger.info(f"Sent milestone message for session #{milestone_count} to user {user_id}")
            break


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

    # Generate same-session insight (if enough data)
    from values import generate_session_insight
    session_insight = generate_session_insight(session.extracted_beliefs)
    if session_insight and not session.is_first_session:
        closure_parts.append(session_insight)

    # Show extracted beliefs (if any and not first session)
    if session.extracted_beliefs and not session.is_first_session:
        # Show up to 2 most recent beliefs
        beliefs_to_show = session.extracted_beliefs[-2:]
        statements = [b['statement'] for b in beliefs_to_show]
        if len(statements) == 1:
            closure_parts.append(f"Something worth remembering:\n*\"{statements[0]}\"*")
        else:
            closure_parts.append("A couple things worth remembering:")
            for s in statements:
                closure_parts.append(f"*\"{s}\"*")

    closure_parts.append(closure)

    await channel.send("\n\n".join(closure_parts))

    # Update value profile
    try:
        await update_user_value_profile(user_id)
        logger.info(f"Updated value profile for user {user_id}")

        # Create value snapshot for tracking changes over time
        await create_value_snapshot(user_id)
        logger.info(f"Created value snapshot for user {user_id}")
    except Exception as e:
        logger.error(f"Failed to update value profile/snapshot: {e}")

    # End in-memory session
    end_session(user_id)

    # Update database
    await db_end_session(session.session_id)

    # Mark first session complete if applicable
    if session.is_first_session:
        await update_user(user_id, first_session_complete=1)

    # Check for milestones
    try:
        session_count = await get_completed_session_count(user_id)
        await check_and_send_milestone_message(channel, user_id, session_count)
    except Exception as e:
        logger.error(f"Failed to check/send milestone message: {e}")

    # Check if user should be prompted for weekly summary
    try:
        if await should_prompt_weekly_summary(user_id, user):
            # Send prompt after a brief delay
            await asyncio.sleep(3)
            await send_weekly_summary_prompt(channel, user_id)
    except Exception as e:
        logger.error(f"Failed to check/send weekly summary prompt: {e}")

    log_session_event(
        logger, "session_closed", session.session_id, user_id,
        exchange_count=session.exchange_count,
        beliefs_extracted=len(session.extracted_beliefs),
        session_duration_exchanges=session.exchange_count
    )


async def send_scheduled_prompt(user: dict):
    """Send a scheduled daily prompt to a user."""
    try:
        # This would need to import the bot instance from the main module
        # For now, keeping this as a placeholder that can be called from main bot
        pass
    except Exception as e:
        logger.error(f"Failed to send scheduled prompt to {user['user_id']}: {e}")


async def send_catch_up_prompt(user: dict, hours_late: int):
    """Send a catch-up prompt for a missed scheduled prompt."""
    try:
        # This would need to import the bot instance from the main module
        # For now, keeping this as a placeholder that can be called from main bot
        pass
    except Exception as e:
        logger.error(f"Failed to send catch-up prompt to {user['user_id']}: {e}")


async def send_reengagement_prompt(user: dict):
    """Send a reengagement prompt to inactive users."""
    try:
        # This would need to import the bot instance from the main module
        # For now, keeping this as a placeholder that can be called from main bot
        pass
    except Exception as e:
        logger.error(f"Failed to send reengagement prompt to {user['user_id']}: {e}")


async def handle_onboarding_complete(
    user_id: str,
    personality: str,
    time: str,
    start_now: bool = False
):
    """Complete the onboarding process for a user."""
    await update_user(
        user_id,
        onboarding_complete=1,
        personality_preset=personality,
        prompt_time=time,
        last_active=datetime.now().isoformat()
    )

    logger.info(f"User {user_id} completed onboarding: {personality}, {time}")

    # Start first session if requested
    if start_now:
        # This would need access to the bot and channel
        # Implementation would be moved to main bot module
        pass