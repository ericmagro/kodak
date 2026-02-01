"""Prompt templates for Kodak v2 journaling sessions."""

import random
from typing import Optional

# ============================================
# OPENER POOLS (7-10 per personality)
# ============================================

OPENER_POOLS = {
    "philosopher": [
        "What occupied your mind today?",
        "What's something from today that deserves more thought?",
        "Any moments today that made you pause?",
        "What assumptions did today challenge?",
        "What's sitting with you from today?",
        "Anything today that surprised you about yourself?",
        "What would you want to remember from today?",
    ],
    "best_friend": [
        "Hey! How was today?",
        "What's the vibe tonight?",
        "Anything good happen today?",
        "How you doing?",
        "What's on your mind?",
        "Tell me about your day.",
        "Any highlights? Or lowlights?",
        "What's the headline from today?",
    ],
    "scientist": [
        "What happened today that's worth examining?",
        "What data did today generate?",
        "Any observations from today?",
        "What would you want to document from today?",
        "What patterns did you notice today?",
        "Anything today that warrants analysis?",
        "What's the most notable event from today?",
    ],
    "trickster": [
        "Survive another day in the simulation?",
        "What chaos did today bring?",
        "Any good stories from today?",
        "What's the most absurd thing that happened today?",
        "Did the universe mess with you today?",
        "Any plot twists today?",
        "What would today's episode be titled?",
        "How'd the NPCs treat you today?",
    ],
    "therapist": [
        "How are you feeling this evening?",
        "How was today for you?",
        "What's present for you right now?",
        "How are you arriving tonight?",
        "What are you carrying from today?",
        "How's your heart tonight?",
        "What does today feel like?",
    ],
}

def get_opener(personality: str, last_opener: str = None) -> str:
    """Get a random opener for the personality, avoiding the last one used.

    Args:
        personality: The personality preset key
        last_opener: The last opener used (from DB), to avoid repetition
    """
    pool = OPENER_POOLS.get(personality, OPENER_POOLS["best_friend"])

    # Filter out last used opener
    available = [o for o in pool if o != last_opener] if last_opener else pool
    if not available:
        available = pool

    return random.choice(available)


# ============================================
# PROBE TEMPLATES (contextual, by personality)
# ============================================

PROBE_TEMPLATES = {
    "philosopher": [
        "What does that reveal about what matters to you?",
        "What's the assumption underneath that?",
        "Why do you think that bothered you?",
        "What would it mean if the opposite were true?",
        "What's the deeper question here?",
        "What does that say about what you value?",
        "Is there a tension there worth exploring?",
    ],
    "best_friend": [
        "Ugh, that sounds frustrating. What was the worst part?",
        "Wait, tell me more about that.",
        "How'd that make you feel?",
        "That's a lot. What's the piece that sticks with you most?",
        "What did you want to happen instead?",
        "That's real. What are you gonna do about it?",
        "How are you feeling about it now?",
    ],
    "scientist": [
        "What specifically triggered that reaction?",
        "What happened right before that?",
        "Can you walk me through the sequence?",
        "What evidence led you to that conclusion?",
        "What's the specific thing that's bothering you?",
        "What variables were at play there?",
        "What would you do differently next time?",
    ],
    "trickster": [
        "Classic. What's the pettiest thought you had about it?",
        "On a scale from 'mildly annoyed' to 'plotting revenge,' where are we?",
        "What would chaos goblin you do about this?",
        "What's the version of this story you'd tell at a bar?",
        "Is this a 'vent and forget' or a 'this actually matters' situation?",
        "What's the most unhinged response you considered?",
        "What would main character you do here?",
    ],
    "therapist": [
        "It sounds like that really landed. How are you sitting with it?",
        "What's that bringing up for you?",
        "Where do you feel that in your body?",
        "What would you want someone to understand about this?",
        "What do you need right now?",
        "How does that connect to how you're feeling overall?",
        "What would it look like to be gentle with yourself here?",
    ],
}


def get_probe_templates(personality: str) -> list[str]:
    """Get probe templates for a personality."""
    return PROBE_TEMPLATES.get(personality, PROBE_TEMPLATES["best_friend"])


# ============================================
# ANCHOR PROMPTS (focus on one concrete thing)
# ============================================

ANCHOR_PROMPTS = {
    "philosopher": [
        "Let's focus on that. What specifically happened?",
        "Tell me more about that moment.",
        "What made that stand out?",
    ],
    "best_friend": [
        "Okay, back up — tell me the whole thing.",
        "Wait, I need more context. What happened?",
        "Start from the beginning.",
    ],
    "scientist": [
        "Let's examine that more closely. What were the specifics?",
        "Walk me through that event.",
        "What exactly occurred?",
    ],
    "trickster": [
        "Okay I need the full story.",
        "Spill. What actually happened?",
        "Give me the details.",
    ],
    "therapist": [
        "Let's stay with that. Can you tell me more?",
        "I'd like to understand that better. What happened?",
        "That seems important. What was that like?",
    ],
}


def get_anchor_prompt(personality: str) -> str:
    """Get an anchor prompt for a personality."""
    prompts = ANCHOR_PROMPTS.get(personality, ANCHOR_PROMPTS["best_friend"])
    return random.choice(prompts)


# ============================================
# CLOSURE TEMPLATES
# ============================================

CLOSURE_TEMPLATES = {
    "philosopher": {
        "base": "Interesting threads today. Let them sit.",
        "with_theme": "Interesting threads today around {theme}. Let them sit.",
        "first_session": "Good first reflection. We'll keep building on this.",
        "short_session": "Sometimes brief is enough. See you tomorrow.",
    },
    "best_friend": {
        "base": "Thanks for catching up. Talk tomorrow?",
        "with_theme": "Thanks for sharing about {theme}. Talk tomorrow?",
        "first_session": "That was a good first chat. See you tomorrow!",
        "short_session": "All good. Catch you tomorrow.",
    },
    "scientist": {
        "base": "Good data point. We'll see what patterns emerge.",
        "with_theme": "Good data on {theme}. We'll see what patterns emerge.",
        "first_session": "First entry logged. The data will get more interesting over time.",
        "short_session": "Entry recorded. See you tomorrow.",
    },
    "trickster": {
        "base": "Alright, go touch grass. See you tomorrow.",
        "with_theme": "Alright, enough about {theme}. Go touch grass.",
        "first_session": "Not bad for a first session. Try not to do anything too unhinged before tomorrow.",
        "short_session": "Short and sweet. Peace.",
    },
    "therapist": {
        "base": "Take care of yourself tonight. I'm here when you need me.",
        "with_theme": "Be gentle with yourself around {theme}. I'm here when you need me.",
        "first_session": "Thank you for sharing. This is a safe space, always.",
        "short_session": "That's okay. Rest well. I'm here tomorrow.",
    },
}


def get_closure(
    personality: str,
    theme: Optional[str] = None,
    is_first_session: bool = False,
    is_short_session: bool = False
) -> str:
    """Get a closure message for the personality and context."""
    templates = CLOSURE_TEMPLATES.get(personality, CLOSURE_TEMPLATES["best_friend"])

    if is_first_session:
        return templates["first_session"]
    if is_short_session:
        return templates["short_session"]
    if theme:
        return templates["with_theme"].format(theme=theme)
    return templates["base"]


# ============================================
# DEPTH TRANSITION PROMPTS
# ============================================

DEPTH_CHECK_PROMPTS = {
    "philosopher": "Want to go deeper on this, or leave it there?",
    "best_friend": "Want to keep going, or is that enough for tonight?",
    "scientist": "Should we analyze this further, or move on?",
    "trickster": "Want to keep digging, or call it?",
    "therapist": "Would you like to explore this more, or does it feel complete?",
}


def get_depth_check(personality: str) -> str:
    """Get a prompt to check if user wants to continue."""
    return DEPTH_CHECK_PROMPTS.get(personality, DEPTH_CHECK_PROMPTS["best_friend"])


# ============================================
# FIRST SESSION FRAMING
# ============================================

FIRST_SESSION_FRAMING = {
    "philosopher": "Just tell me whatever comes to mind. There's no right way to do this.",
    "best_friend": "Just say whatever — there's literally no wrong answer here.",
    "scientist": "Just share what happened. We're just collecting initial data.",
    "trickster": "No pressure. Just say whatever weird thing pops into your head.",
    "therapist": "Take your time. Whatever you share is welcome here.",
}


def get_first_session_framing(personality: str) -> str:
    """Get framing text for first session."""
    return FIRST_SESSION_FRAMING.get(personality, FIRST_SESSION_FRAMING["best_friend"])


# ============================================
# RE-ENGAGEMENT PROMPTS (2+ weeks absent)
# ============================================

REENGAGEMENT_PROMPTS = {
    "philosopher": "Hey, it's been a while. No pressure — want to catch up, or just pick up fresh?",
    "best_friend": "Hey stranger! No worries about being away. Want to catch up, or just start fresh?",
    "scientist": "It's been some time. Would you like to resume where we left off, or start a new data set?",
    "trickster": "Look who's back! No guilt trips here. Want to pretend nothing happened, or actually talk about it?",
    "therapist": "Welcome back. There's no pressure to explain. Would you like to talk about what's been happening, or just be present tonight?",
}


def get_reengagement_prompt(personality: str) -> str:
    """Get re-engagement prompt for returning user."""
    return REENGAGEMENT_PROMPTS.get(personality, REENGAGEMENT_PROMPTS["best_friend"])


# ============================================
# EXTRACTION VISIBILITY TEMPLATES
# ============================================

EXTRACTION_TEMPLATES = {
    "philosopher": "I noticed something worth remembering:\n*\"{belief}\"*",
    "best_friend": "Something you said stuck with me:\n*\"{belief}\"*",
    "scientist": "Logging this observation:\n*\"{belief}\"*",
    "trickster": "This was interesting:\n*\"{belief}\"*",
    "therapist": "I heard something meaningful:\n*\"{belief}\"*",
}


def format_extraction_note(personality: str, belief: str) -> str:
    """Format an extraction note for session close."""
    template = EXTRACTION_TEMPLATES.get(personality, EXTRACTION_TEMPLATES["best_friend"])
    return template.format(belief=belief)


# ============================================
# RESPONSE DEPTH INFERENCE
# ============================================

def infer_response_depth(message: str) -> str:
    """
    Infer user's engagement depth from response.

    Returns: 'minimal', 'short', 'medium', 'long'
    """
    words = len(message.split())

    if words <= 3:
        return 'minimal'
    elif words < 20:
        return 'short'
    elif words < 100:
        return 'medium'
    else:
        return 'long'


def should_probe_more(
    response_depth: str,
    exchange_count: int,
    depth_setting: str
) -> bool:
    """
    Determine if we should continue probing.

    Args:
        response_depth: 'minimal', 'short', 'medium', 'long'
        exchange_count: Number of exchanges so far
        depth_setting: 'quick', 'standard', 'deep'

    Returns:
        True if we should probe more, False if we should close
    """
    # Depth setting ceilings
    max_exchanges = {
        'quick': 3,
        'standard': 6,
        'deep': 10
    }

    max_ex = max_exchanges.get(depth_setting, 6)

    # Hit the ceiling
    if exchange_count >= max_ex:
        return False

    # Minimal response: one gentle follow-up max
    if response_depth == 'minimal':
        return exchange_count < 2

    # Short response: fewer probes
    if response_depth == 'short':
        return exchange_count < min(3, max_ex)

    # Medium: standard flow
    if response_depth == 'medium':
        return exchange_count < max_ex

    # Long: follow their energy
    return exchange_count < max_ex


# ============================================
# SOFT CLOSE (PRE_CLOSE STAGE)
# ============================================

# Pool of soft close questions (5-7 per personality, like OPENER_POOLS)
SOFT_CLOSE_QUESTION_POOLS = {
    "philosopher": [
        "Anything else sitting with you tonight?",
        "Any other threads worth pulling?",
        "Anything else you want to sit with?",
        "Is there more here, or is that the shape of it?",
        "Any questions still forming?",
    ],
    "best_friend": [
        "Alright, anything else you need to get off your chest?",
        "That it, or is there more?",
        "Anything else you wanna get out?",
        "That everything, or is there more?",
        "Anything else before I let you go?",
    ],
    "scientist": [
        "Any other observations to log?",
        "Anything else worth recording?",
        "Any other data points?",
        "That complete the picture, or is there more?",
        "Anything else for the record?",
    ],
    "trickster": [
        "Cool. That the whole episode, or is there a post-credits scene?",
        "Alright. Anything else rattling around in there?",
        "That's good chaos for one day. Anything else before you go?",
        "Should I let you go be a person now, or is there more?",
        "Plot points logged. Anything else for the record?",
    ],
    "therapist": [
        "Is there anything else you'd like to share?",
        "Anything else coming up for you?",
        "Is there more you want to explore, or does this feel complete?",
        "Anything else you'd like to put words to?",
        "Is there anything else present for you tonight?",
    ],
}

# Fallback acknowledgments if LLM validation fails
FALLBACK_ACKNOWLEDGMENTS = {
    "philosopher": ["That's a lot to sit with.", "Worth reflecting on.", "Some threads to follow."],
    "best_friend": ["That's real.", "I hear you.", "That's a lot.", "Got it."],
    "scientist": ["Noted.", "Good data point.", "Logged.", "Recorded."],
    "trickster": ["Fair.", "That tracks.", "Solid.", "Checks out."],
    "therapist": ["Thank you for sharing that.", "I appreciate you sharing.", "That took trust to share."],
}


def get_soft_close_question(personality: str, last_question: str = None) -> str:
    """Get a soft close question for a personality, avoiding the last one used.

    Args:
        personality: The personality preset key
        last_question: The last question used, to avoid repetition
    """
    pool = SOFT_CLOSE_QUESTION_POOLS.get(personality, SOFT_CLOSE_QUESTION_POOLS["best_friend"])

    # Filter out last used question
    available = [q for q in pool if q != last_question] if last_question else pool
    if not available:
        available = pool

    return random.choice(available)


def get_fallback_acknowledgment(personality: str) -> str:
    """Get a fallback acknowledgment for a personality."""
    acks = FALLBACK_ACKNOWLEDGMENTS.get(personality, FALLBACK_ACKNOWLEDGMENTS["best_friend"])
    return random.choice(acks)


def validate_acknowledgment(text: str) -> bool:
    """
    Validate that an LLM-generated acknowledgment follows constraints.

    Returns True if valid, False if should use fallback.
    """
    # Must be short (roughly 1 sentence, under 100 chars)
    if len(text) > 100:
        return False

    # No questions
    if '?' in text:
        return False

    text_lower = text.lower()

    # No evaluative language
    evaluative_words = [
        'great', 'amazing', 'wonderful', 'terrible', 'hard', 'difficult',
        'important', 'interesting', 'exciting', 'tough', 'rough',
        'sounds like you', 'seems like you', 'you seem', 'you sound',
        'struggling', 'stressed', 'overwhelmed', 'proud', 'happy', 'sad'
    ]
    for word in evaluative_words:
        if word in text_lower:
            return False

    # No advice
    advice_patterns = ['you should', 'you could', 'try to', 'maybe you', 'have you considered']
    for pattern in advice_patterns:
        if pattern in text_lower:
            return False

    return True
