"""Weekly/monthly/yearly summary generation for Kodak."""

import json
import logging
import pytz
from datetime import datetime, timedelta
from typing import Optional
import anthropic

from db import (
    get_sessions_in_range, get_beliefs_from_sessions, get_topics_frequency,
    get_user_value_profile, get_value_profile_at_date, store_summary,
    get_past_summaries, get_or_create_user
)
from values import ALL_VALUES

logger = logging.getLogger('kodak')

# Initialize Anthropic client
_client = None


def init_client(api_key: str) -> bool:
    """Initialize the Anthropic client. Returns True if successful."""
    global _client
    if _client is not None:
        return True  # Already initialized
    if not api_key:
        logger.error("No API key provided for summaries client")
        return False
    _client = anthropic.Anthropic(api_key=api_key)
    return True


def get_client():
    """Get the initialized client, raising if not available."""
    if _client is None:
        raise ValueError("Anthropic client not initialized. Call init_client first.")
    return _client


def get_user_timezone(user: dict) -> pytz.BaseTzInfo:
    """Get the user's timezone, defaulting to UTC."""
    tz_name = user.get('timezone') or 'UTC'
    try:
        return pytz.timezone(tz_name)
    except pytz.UnknownTimeZoneError:
        logger.warning(f"Unknown timezone '{tz_name}', using UTC")
        return pytz.UTC


def format_date_friendly(date_str: str) -> str:
    """Format ISO date string to friendly format like 'Jan 17'."""
    try:
        dt = datetime.fromisoformat(date_str)
        return dt.strftime("%b %-d")
    except (ValueError, TypeError):
        return date_str


def format_date_range(start_str: str, end_str: str) -> str:
    """Format a date range like 'Jan 17 – Jan 24'."""
    start = format_date_friendly(start_str)
    end = format_date_friendly(end_str)
    return f"{start} – {end}"


# ============================================
# DATA GATHERING
# ============================================

async def gather_week_data(user_id: str, end_date: datetime = None, user: dict = None) -> dict:
    """Gather all data needed for a weekly summary.

    Args:
        user_id: The user's ID
        end_date: End of the period (defaults to now in user's timezone)
        user: User dict with timezone info (fetched if not provided)
    """
    # Get user for timezone if not provided
    if user is None:
        user = await get_or_create_user(user_id)

    # Use user's timezone for date calculations
    tz = get_user_timezone(user)

    if end_date is None:
        end_date = datetime.now(tz)
    elif end_date.tzinfo is None:
        end_date = tz.localize(end_date)

    start_date = end_date - timedelta(days=7)

    # Format dates for queries
    start_str = start_date.isoformat()
    end_str = end_date.isoformat()

    # Get sessions
    sessions = await get_sessions_in_range(user_id, start_str, end_str)
    session_ids = [s['id'] for s in sessions]

    # Get beliefs from those sessions
    beliefs = await get_beliefs_from_sessions(user_id, session_ids)

    # Get topic frequency
    topics = await get_topics_frequency(beliefs)

    # Get current value profile
    current_values = await get_user_value_profile(user_id)

    # Get value profile from 7 days ago (for comparison)
    past_values = await get_value_profile_at_date(user_id, start_str)

    # Calculate value changes
    value_changes = {}
    if past_values and current_values:
        for value_name in ALL_VALUES:
            current_score = current_values.scores.get(value_name)
            past_score = past_values.get(value_name, 0)
            if current_score:
                change = current_score.normalized_score - past_score
                if abs(change) > 0.05:  # Only note significant changes (>5%)
                    value_changes[value_name] = {
                        'before': round(past_score, 2),
                        'after': round(current_score.normalized_score, 2),
                        'change': round(change, 2)
                    }

    # Check if this is the first summary
    past_summaries = await get_past_summaries(user_id, 'week', limit=1)
    is_first_summary = len(past_summaries) == 0

    return {
        'period_type': 'week',
        'period_start': start_date.date().isoformat(),
        'period_end': end_date.date().isoformat(),
        'session_count': len(sessions),
        'sessions': [
            {
                'started_at': s['started_at'],
                'message_count': s['message_count'],
                'beliefs_extracted': s['beliefs_extracted']
            }
            for s in sessions
        ],
        'belief_count': len(beliefs),
        'beliefs': [
            {
                'statement': b['statement'],
                'topics': b.get('topics', []),
                'values': [v['value_name'] for v in b.get('values', [])],
                'confidence': b['confidence']
            }
            for b in beliefs
        ],
        'topics': topics,
        'value_changes': value_changes,
        'is_first_summary': is_first_summary
    }


# ============================================
# NARRATIVE GENERATION
# ============================================

def generate_summary_prompt(data: dict) -> str:
    """Generate the prompt for Claude to create a summary narrative."""

    session_count = data['session_count']
    belief_count = data['belief_count']
    topics = data['topics']
    beliefs = data['beliefs']
    value_changes = data['value_changes']
    is_first = data['is_first_summary']

    # Handle quiet week
    if session_count == 0:
        return """Generate a brief, warm message for someone who didn't journal this week.
Don't guilt them. Acknowledge that some weeks are quieter.
Keep it to 1-2 sentences. End with something encouraging about next week."""

    # Build the prompt
    prompt_parts = []

    prompt_parts.append(f"""Generate a weekly summary for someone's journaling.

This week's data:
- Sessions completed: {session_count}
- Beliefs that emerged: {belief_count}
""")

    if topics:
        top_topics = list(topics.items())[:5]
        topics_str = ', '.join([f"{t} ({c}x)" for t, c in top_topics])
        prompt_parts.append(f"- Topics reflected on: {topics_str}")

    if beliefs:
        beliefs_str = '\n'.join([f'  - "{b["statement"]}"' for b in beliefs[:8]])
        prompt_parts.append(f"\nBeliefs that emerged:\n{beliefs_str}")

    if value_changes:
        changes_str = '\n'.join([
            f"  - {name}: {v['before']:.0%} → {v['after']:.0%} ({'+' if v['change'] > 0 else ''}{v['change']:.0%})"
            for name, v in value_changes.items()
        ])
        prompt_parts.append(f"\nValue shifts detected:\n{changes_str}")

    # Instructions
    if is_first:
        prompt_parts.append("""
This is their FIRST weekly summary. Make it feel like a milestone.
Frame it as "here's what we learned about you this week" rather than comparisons.""")
    else:
        prompt_parts.append("""
This is a returning user. You can reference changes and patterns.""")

    prompt_parts.append("""
Guidelines:
- Be warm but not sycophantic
- If there are clear patterns or themes, name them
- If value shifts happened, explain what might have driven them (tie to specific beliefs if possible)
- Don't manufacture insights that aren't there
- Keep it concise—aim for 3-5 short paragraphs max
- End with something that honors their reflection practice

Format:
- Start with a brief overview (1 sentence)
- Then the meat: themes, beliefs, value shifts
- End with a brief closing thought

Do NOT use bullet points. Write in flowing prose.""")

    return '\n'.join(prompt_parts)


def generate_highlights_prompt(data: dict) -> str:
    """Generate prompt for short, punchy highlights."""

    if data['session_count'] == 0:
        return None

    return f"""Based on this week's journaling data, generate 2-3 short, punchy highlights.
Each highlight should be 1 sentence max—something surprising, interesting, or worth noting.

Data:
- Sessions: {data['session_count']}
- Topics: {', '.join(list(data['topics'].keys())[:5]) if data['topics'] else 'none detected'}
- Beliefs emerged: {data['belief_count']}
- Value shifts: {', '.join(data['value_changes'].keys()) if data['value_changes'] else 'none significant'}

Examples of good highlights:
- "You mentioned your mom 4 times this week—more than anyone else."
- "Your Self-Direction score jumped 15%, driven by thoughts about career autonomy."
- "Work stress was the dominant theme, appearing in 3 of 4 sessions."

Return as a JSON array of strings. Just the array, no other text.
Example: ["Highlight one.", "Highlight two.", "Highlight three."]"""


async def generate_summary_narrative(data: dict) -> tuple[str, list[str]]:
    """Generate the summary narrative and highlights using Claude."""
    client = get_client()

    # Generate main narrative
    narrative_prompt = generate_summary_prompt(data)

    narrative_response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1000,
        messages=[{"role": "user", "content": narrative_prompt}]
    )
    narrative = narrative_response.content[0].text

    # Generate highlights (if not a quiet week)
    highlights = []
    highlights_prompt = generate_highlights_prompt(data)
    if highlights_prompt:
        try:
            highlights_response = get_client().messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=300,
                messages=[{"role": "user", "content": highlights_prompt}]
            )
            highlights_text = highlights_response.content[0].text.strip()
            # Parse JSON array
            if highlights_text.startswith('['):
                highlights = json.loads(highlights_text)
        except Exception as e:
            logger.warning(f"Failed to generate highlights: {e}")

    return narrative, highlights


# ============================================
# DUPLICATE CHECKING
# ============================================

async def get_existing_summary_for_period(user_id: str, period_type: str, period_start: str, period_end: str) -> Optional[dict]:
    """Check if a summary already exists for this exact period."""
    summaries = await get_past_summaries(user_id, period_type, limit=5)
    for s in summaries:
        if s['period_start'] == period_start and s['period_end'] == period_end:
            return s
    return None


# ============================================
# MAIN ENTRY POINT
# ============================================

async def create_weekly_summary(user_id: str, force_new: bool = False) -> dict:
    """Create a weekly summary for a user. Returns the summary data and narrative.

    Args:
        user_id: The user's ID
        force_new: If True, create new summary even if one exists for this period
    """
    # Get user for timezone
    user = await get_or_create_user(user_id)

    # Gather data (uses user's timezone)
    data = await gather_week_data(user_id, user=user)

    # Check for existing summary for this period (unless forcing new)
    if not force_new:
        existing = await get_existing_summary_for_period(
            user_id, 'week', data['period_start'], data['period_end']
        )
        if existing:
            # Return the existing summary with parsed highlights
            highlights = []
            if existing.get('highlights'):
                try:
                    highlights = json.loads(existing['highlights'])
                except (json.JSONDecodeError, TypeError):
                    pass
            return {
                'id': existing['id'],
                'period_type': 'week',
                'period_start': existing['period_start'],
                'period_end': existing['period_end'],
                'session_count': existing['session_count'],
                'belief_count': existing['belief_count'],
                'topics': data['topics'],  # Recalculated from current data
                'value_changes': data['value_changes'],
                'narrative': existing['narrative'],
                'highlights': highlights,
                'is_first_summary': False,
                'is_cached': True  # Indicate this was retrieved, not generated
            }

    # Generate narrative
    narrative, highlights = await generate_summary_narrative(data)

    # Store the summary
    summary_id = await store_summary(
        user_id=user_id,
        period_type='week',
        period_start=data['period_start'],
        period_end=data['period_end'],
        data_json=json.dumps(data),
        narrative=narrative,
        highlights=json.dumps(highlights),
        session_count=data['session_count'],
        belief_count=data['belief_count']
    )

    return {
        'id': summary_id,
        'period_type': 'week',
        'period_start': data['period_start'],
        'period_end': data['period_end'],
        'session_count': data['session_count'],
        'belief_count': data['belief_count'],
        'topics': data['topics'],
        'value_changes': data['value_changes'],
        'narrative': narrative,
        'highlights': highlights,
        'is_first_summary': data['is_first_summary'],
        'is_cached': False
    }


async def get_user_summaries(user_id: str, period_type: str = None, limit: int = 10) -> list[dict]:
    """Get past summaries for a user, formatted for display.

    Args:
        user_id: The user's ID
        period_type: Filter by 'week', 'month', or 'year' (None for all)
        limit: Maximum number of summaries to return
    """
    summaries = await get_past_summaries(user_id, period_type, limit)

    formatted = []
    for s in summaries:
        highlights = []
        if s.get('highlights'):
            try:
                highlights = json.loads(s['highlights'])
            except (json.JSONDecodeError, TypeError):
                pass

        formatted.append({
            'id': s['id'],
            'period_type': s['period_type'],
            'period_start': s['period_start'],
            'period_end': s['period_end'],
            'date_range': format_date_range(s['period_start'], s['period_end']),
            'session_count': s['session_count'],
            'belief_count': s['belief_count'],
            'narrative': s['narrative'],
            'highlights': highlights,
            'generated_at': s['generated_at']
        })

    return formatted
