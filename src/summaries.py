"""Weekly/monthly/yearly summary generation for Kodak."""

import json
import logging
from datetime import datetime, timedelta
from typing import Optional
import anthropic

from db import (
    get_sessions_in_range, get_beliefs_from_sessions, get_topics_frequency,
    get_user_value_profile, get_value_profile_at_date, store_summary,
    get_past_summaries
)
from values import ALL_VALUES

logger = logging.getLogger('kodak')

# Initialize Anthropic client
client = None


def init_client(api_key: str):
    """Initialize the Anthropic client."""
    global client
    client = anthropic.Anthropic(api_key=api_key)


# ============================================
# DATA GATHERING
# ============================================

async def gather_week_data(user_id: str, end_date: datetime = None) -> dict:
    """Gather all data needed for a weekly summary."""
    if end_date is None:
        end_date = datetime.now()

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
    if not client:
        raise ValueError("Anthropic client not initialized. Call init_client first.")

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
            highlights_response = client.messages.create(
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
# MAIN ENTRY POINT
# ============================================

async def create_weekly_summary(user_id: str) -> dict:
    """Create a weekly summary for a user. Returns the summary data and narrative."""

    # Gather data
    data = await gather_week_data(user_id)

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
        'is_first_summary': data['is_first_summary']
    }
