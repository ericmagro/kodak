"""Session state management for Kodak v2 journaling."""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional
from enum import Enum

logger = logging.getLogger('kodak')

# Session timeout: sessions expire after 2 hours of inactivity
SESSION_TIMEOUT_MINUTES = 120


class SessionStage(Enum):
    """Stages of a journaling session."""
    OPENER = "opener"
    ANCHOR = "anchor"
    PROBE = "probe"
    CONNECT = "connect"
    CLOSE = "close"
    ENDED = "ended"


@dataclass
class SessionState:
    """
    Tracks the state of an active journaling session.

    This is the in-memory state; persisted data is in the database.
    """
    session_id: str
    user_id: str
    personality: str
    depth_setting: str  # quick/standard/deep

    stage: SessionStage = SessionStage.OPENER
    exchange_count: int = 0
    is_first_session: bool = False

    # Track what we've shown/done
    opener_used: Optional[str] = None
    last_response_depth: str = "medium"  # minimal/short/medium/long
    theme_identified: Optional[str] = None
    pattern_surfaced_this_session: bool = False

    # Extracted beliefs (to show at close)
    # Each entry: {'statement': str, 'themes': list[str]}
    extracted_beliefs: list[dict] = field(default_factory=list)

    # Message history for this session
    messages: list[dict] = field(default_factory=list)

    # Timeout tracking
    created_at: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)

    def is_expired(self) -> bool:
        """Check if session has timed out."""
        timeout = timedelta(minutes=SESSION_TIMEOUT_MINUTES)
        return datetime.now() - self.last_activity > timeout

    def touch(self):
        """Update last activity timestamp."""
        self.last_activity = datetime.now()

    def add_user_message(self, content: str, depth: str):
        """Record a user message."""
        self.messages.append({
            'role': 'user',
            'content': content,
            'timestamp': datetime.now().isoformat()
        })
        self.last_response_depth = depth
        self.exchange_count += 1
        self.touch()  # Update activity timestamp

    def add_bot_message(self, content: str):
        """Record a bot message."""
        self.messages.append({
            'role': 'assistant',
            'content': content,
            'timestamp': datetime.now().isoformat()
        })

    def get_recent_context(self, n: int = 4) -> list[dict]:
        """Get the last N messages for context."""
        return self.messages[-n:] if self.messages else []


# In-memory session store
_active_sessions: dict[str, SessionState] = {}


def get_active_session(user_id: str) -> Optional[SessionState]:
    """Get the active session for a user, if any. Returns None if session is expired."""
    session = _active_sessions.get(user_id)
    if session and session.is_expired():
        logger.info(f"Session {session.session_id} expired for user {user_id}")
        _active_sessions.pop(user_id, None)
        return None
    return session


def create_session(
    session_id: str,
    user_id: str,
    personality: str,
    depth_setting: str,
    is_first_session: bool = False
) -> SessionState:
    """Create and store a new session."""
    session = SessionState(
        session_id=session_id,
        user_id=user_id,
        personality=personality,
        depth_setting=depth_setting,
        is_first_session=is_first_session
    )
    _active_sessions[user_id] = session
    logger.info(f"Created session {session_id} for user {user_id}")
    return session


def end_session(user_id: str) -> Optional[SessionState]:
    """End and remove a session, returning it for final processing."""
    session = _active_sessions.pop(user_id, None)
    if session:
        session.stage = SessionStage.ENDED
        logger.info(f"Ended session {session.session_id} for user {user_id}")
    return session


def has_active_session(user_id: str) -> bool:
    """Check if user has an active (non-expired) session."""
    return get_active_session(user_id) is not None


def cleanup_expired_sessions() -> int:
    """Remove all expired sessions. Returns number of sessions cleaned up."""
    expired = [
        user_id for user_id, session in _active_sessions.items()
        if session.is_expired()
    ]
    for user_id in expired:
        session = _active_sessions.pop(user_id, None)
        if session:
            logger.info(f"Cleaned up expired session {session.session_id} for user {user_id}")
    return len(expired)


# ============================================
# SESSION FLOW LOGIC
# ============================================

def determine_next_stage(session: SessionState) -> SessionStage:
    """
    Determine what stage to move to based on session state.

    This implements the adaptive depth logic from the design doc.
    """
    current = session.stage
    depth = session.last_response_depth
    exchanges = session.exchange_count
    setting = session.depth_setting
    is_first = session.is_first_session

    # Depth ceilings
    max_exchanges = {
        'quick': 3,
        'standard': 6,
        'deep': 10
    }
    ceiling = max_exchanges.get(setting, 6)

    # First session: max 4 exchanges
    if is_first:
        ceiling = min(ceiling, 4)

    # Already at or past ceiling
    if exchanges >= ceiling:
        return SessionStage.CLOSE

    # Stage transitions based on current stage and response depth
    if current == SessionStage.OPENER:
        # After opener, move to anchor
        return SessionStage.ANCHOR

    if current == SessionStage.ANCHOR:
        # After anchoring, start probing
        return SessionStage.PROBE

    if current == SessionStage.PROBE:
        # Minimal response: one follow-up then close
        if depth == 'minimal' and exchanges >= 2:
            return SessionStage.CLOSE

        # Short response: fewer probes
        if depth == 'short' and exchanges >= 3:
            return SessionStage.CLOSE

        # Check if we should connect (long engagement, not first session)
        if depth == 'long' and exchanges >= 4 and not is_first and not session.pattern_surfaced_this_session:
            return SessionStage.CONNECT

        # Continue probing if under ceiling
        if exchanges < ceiling:
            return SessionStage.PROBE

        return SessionStage.CLOSE

    if current == SessionStage.CONNECT:
        # After connecting, one more probe or close
        if exchanges < ceiling:
            return SessionStage.PROBE
        return SessionStage.CLOSE

    # Default to close
    return SessionStage.CLOSE


def should_offer_depth_check(session: SessionState) -> bool:
    """
    Determine if we should ask "want to go deeper?"

    Only ask occasionally, not every session.
    """
    # Only in probe stage
    if session.stage != SessionStage.PROBE:
        return False

    # Don't ask on first session
    if session.is_first_session:
        return False

    # Ask after a few exchanges if they seem engaged
    if session.exchange_count >= 3 and session.last_response_depth in ('medium', 'long'):
        # Only ask ~30% of the time (could track this better)
        return session.exchange_count == 4  # Simple heuristic

    return False


def should_surface_pattern(session: SessionState) -> bool:
    """
    Determine if we should surface a pattern/connection.

    Per design: max once per week, and only when engaged.
    """
    # Already did it this session
    if session.pattern_surfaced_this_session:
        return False

    # Not on first session
    if session.is_first_session:
        return False

    # Only when deeply engaged
    if session.last_response_depth != 'long':
        return False

    # Only in connect stage
    if session.stage != SessionStage.CONNECT:
        return False

    # TODO: Check if we've surfaced a pattern recently (within 7 days)
    # For now, always allow in CONNECT stage
    return True


# ============================================
# SESSION MESSAGE GENERATION
# ============================================

def get_stage_instruction(session: SessionState) -> str:
    """Get instruction for the current stage to include in prompt."""
    stage = session.stage

    if stage == SessionStage.OPENER:
        if session.is_first_session:
            return "Send the opener. Add brief framing since this is their first session."
        return "Send the opener. Keep it light and inviting."

    if stage == SessionStage.ANCHOR:
        return "They've shared something. Focus on one concrete thing and ask them to tell you more about it."

    if stage == SessionStage.PROBE:
        if session.last_response_depth == 'minimal':
            return "Very brief response. One gentle follow-up, then prepare to close."
        if session.last_response_depth == 'short':
            return "Short response. Ask one focused follow-up question."
        return "Go deeper. Ask a follow-up that draws out meaning or feeling."

    if stage == SessionStage.CONNECT:
        return "They're engaged. If you notice a pattern or connection to previous themes, gently surface it as a curiosity."

    if stage == SessionStage.CLOSE:
        return "Time to close. Summarize what emerged briefly, thank them, and say goodbye."

    return ""


def format_session_context(session: SessionState) -> str:
    """Format recent session context for the prompt."""
    recent = session.get_recent_context(4)
    if not recent:
        return ""

    lines = ["Recent conversation:"]
    for msg in recent:
        role = "User" if msg['role'] == 'user' else "You"
        lines.append(f"{role}: {msg['content']}")

    return "\n".join(lines)
