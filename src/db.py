"""Database operations for Kodak v2."""

import os
import json
import logging
import aiosqlite
import uuid
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional

from values import (
    ALL_VALUES, ValueProfile, ValueScore, BeliefValueMapping,
    aggregate_value_profile
)

logger = logging.getLogger('kodak')

# Allowed columns for dynamic updates (SQL injection prevention)
ALLOWED_USER_COLUMNS = {
    'username', 'personality_preset', 'prompt_time', 'prompt_depth', 'timezone',
    'onboarding_complete', 'tracking_paused', 'last_prompt_sent', 'last_prompt_responded',
    'prompts_ignored', 'last_active', 'last_prompt_date', 'last_opener', 'updated_at',
    'last_weekly_summary_prompt', 'first_session_complete'
}

ALLOWED_SESSION_COLUMNS = {
    'session_stage', 'ended_at', 'message_count', 'beliefs_extracted', 'opener_used'
}

# Database path configuration
_default_db_path = Path(__file__).parent.parent / "kodak.db"
DB_PATH = Path(os.getenv("KODAK_DB_PATH", str(_default_db_path)))
SCHEMA_PATH = Path(__file__).parent.parent / "schema.sql"


# ============================================
# INITIALIZATION
# ============================================

async def init_db():
    """Initialize the database with v2 schema."""
    async with aiosqlite.connect(DB_PATH) as db:
        with open(SCHEMA_PATH) as f:
            await db.executescript(f.read())
        await db.commit()

        # Migrations for existing databases
        await _run_migrations(db)

        logger.info(f"Database initialized at {DB_PATH}")


async def _run_migrations(db):
    """Run schema migrations for existing databases."""
    cursor = await db.execute("PRAGMA table_info(users)")
    columns = [row[1] for row in await cursor.fetchall()]

    if 'last_opener' not in columns:
        await db.execute("ALTER TABLE users ADD COLUMN last_opener TEXT")
        await db.commit()
        logger.info("Migration: added last_opener column to users")

    if 'last_weekly_summary_prompt' not in columns:
        await db.execute("ALTER TABLE users ADD COLUMN last_weekly_summary_prompt TEXT")
        await db.commit()
        logger.info("Migration: added last_weekly_summary_prompt column to users")

    if 'last_prompt_date' not in columns:
        await db.execute("ALTER TABLE users ADD COLUMN last_prompt_date TEXT")
        await db.commit()
        logger.info("Migration: added last_prompt_date column to users")


# ============================================
# USERS
# ============================================

async def get_or_create_user(user_id: str, username: str = None) -> dict:
    """Get or create a user record."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM users WHERE user_id = ?", (user_id,)
        )
        row = await cursor.fetchone()

        if row:
            return dict(row)

        # Create new user
        await db.execute(
            "INSERT INTO users (user_id, username) VALUES (?, ?)",
            (user_id, username)
        )
        await db.commit()

        cursor = await db.execute(
            "SELECT * FROM users WHERE user_id = ?", (user_id,)
        )
        row = await cursor.fetchone()
        return dict(row)


async def update_user(user_id: str, **kwargs) -> dict:
    """Update user fields."""
    if not kwargs:
        return await get_or_create_user(user_id)

    # Handle mid-day schedule change: if user changes prompt_time to a future
    # time today, clear last_prompt_date so they can receive a prompt today
    if 'prompt_time' in kwargs:
        new_time = kwargs['prompt_time']
        if new_time and _is_future_time_today(new_time):
            kwargs['last_prompt_date'] = None

    updates = []
    values = []
    for key, value in kwargs.items():
        # Validate column name to prevent SQL injection
        if key not in ALLOWED_USER_COLUMNS:
            logger.warning(f"Attempted to update disallowed column: {key}")
            continue
        updates.append(f"{key} = ?")
        values.append(value)

    # If all columns were filtered, just return current user
    if not updates:
        return await get_or_create_user(user_id)

    updates.append("updated_at = ?")
    values.append(datetime.now().isoformat())
    values.append(user_id)

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            f"UPDATE users SET {', '.join(updates)} WHERE user_id = ?",
            values
        )
        await db.commit()

    return await get_or_create_user(user_id)


def _is_future_time_today(time_str: str) -> bool:
    """Check if a time string (HH:MM) is in the future today."""
    try:
        hour, minute = map(int, time_str.split(':'))
        now = datetime.now()
        scheduled = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        return scheduled > now
    except (ValueError, AttributeError):
        return False


async def get_users_for_prompt(current_time: str) -> list[dict]:
    """
    Get users who should receive a prompt at the given time.

    DEPRECATED: Use get_users_eligible_for_prompt() with timezone-aware filtering.
    Kept for backwards compatibility.

    current_time format: "HH:MM" (24-hour)
    """
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row

        # Get users where:
        # - onboarding complete
        # - tracking not paused
        # - prompt_time matches current time
        # - haven't received prompt today
        today = datetime.now().date().isoformat()

        cursor = await db.execute(
            """SELECT * FROM users
               WHERE onboarding_complete = 1
                 AND tracking_paused = 0
                 AND prompt_time = ?
                 AND (last_prompt_sent IS NULL OR last_prompt_sent < ?)
            """,
            (current_time, today)
        )
        return [dict(row) for row in await cursor.fetchall()]


async def get_users_eligible_for_prompt() -> list[dict]:
    """
    Get all users who are eligible for a prompt today (haven't been prompted yet).

    Returns users who:
    - Have completed onboarding
    - Have tracking enabled (not paused)
    - Have a prompt_time set
    - Haven't received a prompt today

    The caller should filter by timezone to determine if it's the right time.
    """
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row

        today = datetime.now().date().isoformat()

        cursor = await db.execute(
            """SELECT * FROM users
               WHERE onboarding_complete = 1
                 AND tracking_paused = 0
                 AND prompt_time IS NOT NULL
                 AND (last_prompt_sent IS NULL OR last_prompt_sent < ?)
            """,
            (today,)
        )
        return [dict(row) for row in await cursor.fetchall()]


async def get_users_with_missed_prompts() -> list[dict]:
    """Get users who missed their prompt today (for catch-up on startup)."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row

        today = datetime.now().date().isoformat()
        current_time = datetime.now().strftime("%H:%M")

        cursor = await db.execute(
            """SELECT * FROM users
               WHERE onboarding_complete = 1
                 AND tracking_paused = 0
                 AND prompt_time IS NOT NULL
                 AND prompt_time < ?
                 AND (last_prompt_sent IS NULL OR last_prompt_sent < ?)
            """,
            (current_time, today)
        )
        return [dict(row) for row in await cursor.fetchall()]


async def get_users_needing_reengagement(days_threshold: int = 14) -> list[dict]:
    """Get users who haven't been active for a while."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row

        threshold_date = (datetime.now() - timedelta(days=days_threshold)).isoformat()

        cursor = await db.execute(
            """SELECT * FROM users
               WHERE onboarding_complete = 1
                 AND (last_active IS NULL OR last_active < ?)
            """,
            (threshold_date,)
        )
        return [dict(row) for row in await cursor.fetchall()]


async def mark_prompt_sent(user_id: str):
    """Mark that a prompt was sent to the user."""
    await update_user(
        user_id,
        last_prompt_sent=datetime.now().isoformat(),
        last_prompt_responded=0
    )


async def mark_prompt_responded(user_id: str):
    """Mark that the user responded to their prompt."""
    await update_user(
        user_id,
        last_prompt_responded=1,
        prompts_ignored=0,
        last_active=datetime.now().isoformat()
    )


async def increment_prompts_ignored(user_id: str) -> int:
    """Increment ignored prompt counter and return new count."""
    user = await get_or_create_user(user_id)
    new_count = user.get('prompts_ignored', 0) + 1
    await update_user(user_id, prompts_ignored=new_count)
    return new_count


# ============================================
# JOURNAL SESSIONS
# ============================================

async def create_session(
    user_id: str,
    prompt_type: str = 'scheduled',
    opener_used: str = None,
    session_id: str = None
) -> dict:
    """Create a new journal session."""
    if session_id is None:
        session_id = str(uuid.uuid4())

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """INSERT INTO journal_sessions
               (id, user_id, started_at, prompt_type, opener_used)
               VALUES (?, ?, ?, ?, ?)""",
            (session_id, user_id, datetime.now().isoformat(), prompt_type, opener_used)
        )
        await db.commit()

    return await get_session(session_id)


async def get_session(session_id: str) -> Optional[dict]:
    """Get a session by ID."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM journal_sessions WHERE id = ?", (session_id,)
        )
        row = await cursor.fetchone()
        return dict(row) if row else None


async def get_active_session(user_id: str) -> Optional[dict]:
    """Get the user's active (not ended) session if any."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            """SELECT * FROM journal_sessions
               WHERE user_id = ? AND ended_at IS NULL
               ORDER BY started_at DESC LIMIT 1""",
            (user_id,)
        )
        row = await cursor.fetchone()
        return dict(row) if row else None


async def update_session(session_id: str, **kwargs) -> dict:
    """Update session fields."""
    if not kwargs:
        return await get_session(session_id)

    updates = []
    values = []
    for key, value in kwargs.items():
        # Validate column name to prevent SQL injection
        if key not in ALLOWED_SESSION_COLUMNS:
            logger.warning(f"Attempted to update disallowed session column: {key}")
            continue
        updates.append(f"{key} = ?")
        values.append(value)

    # If all columns were filtered, just return current session
    if not updates:
        return await get_session(session_id)

    values.append(session_id)

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            f"UPDATE journal_sessions SET {', '.join(updates)} WHERE id = ?",
            values
        )
        await db.commit()

    return await get_session(session_id)


async def end_session(session_id: str) -> dict:
    """End a session."""
    return await update_session(
        session_id,
        ended_at=datetime.now().isoformat(),
        session_stage='ended'
    )


async def increment_session_messages(session_id: str) -> int:
    """Increment message count for a session."""
    session = await get_session(session_id)
    if not session:
        return 0
    new_count = session.get('message_count', 0) + 1
    await update_session(session_id, message_count=new_count)
    return new_count


async def get_recent_openers(user_id: str, limit: int = 5) -> list[str]:
    """Get recently used openers for a user (for rotation)."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            """SELECT opener_used FROM journal_sessions
               WHERE user_id = ? AND opener_used IS NOT NULL
               ORDER BY started_at DESC LIMIT ?""",
            (user_id, limit)
        )
        rows = await cursor.fetchall()
        return [row[0] for row in rows]


async def get_completed_session_count(user_id: str) -> int:
    """Get count of completed sessions for a user."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            """SELECT COUNT(*) FROM journal_sessions
               WHERE user_id = ? AND ended_at IS NOT NULL""",
            (user_id,)
        )
        result = await cursor.fetchone()
        return result[0] if result else 0


# ============================================
# BELIEFS
# ============================================

async def add_belief(
    user_id: str,
    statement: str,
    confidence: float = 0.5,
    source_type: str = None,
    context: str = None,
    session_id: str = None,
    message_id: str = None,
    channel_id: str = None,
    topics: list[str] = None
) -> dict:
    """Add a new belief."""
    belief_id = str(uuid.uuid4())

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """INSERT INTO beliefs
               (id, user_id, statement, confidence, source_type, context,
                session_id, message_id, channel_id)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (belief_id, user_id, statement, confidence, source_type, context,
             session_id, message_id, channel_id)
        )

        # Add topics
        if topics:
            for topic in topics:
                await db.execute(
                    "INSERT INTO belief_topics (belief_id, topic) VALUES (?, ?)",
                    (belief_id, topic.lower().strip())
                )

        # Increment session beliefs count
        if session_id:
            await db.execute(
                """UPDATE journal_sessions
                   SET beliefs_extracted = beliefs_extracted + 1
                   WHERE id = ?""",
                (session_id,)
            )

        await db.commit()

    return await get_belief(belief_id)


async def get_belief(belief_id: str) -> Optional[dict]:
    """Get a belief by ID."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM beliefs WHERE id = ?", (belief_id,)
        )
        row = await cursor.fetchone()
        if not row:
            return None

        belief = dict(row)

        # Get topics
        cursor = await db.execute(
            "SELECT topic FROM belief_topics WHERE belief_id = ?",
            (belief_id,)
        )
        belief['topics'] = [r['topic'] for r in await cursor.fetchall()]

        # Get values
        cursor = await db.execute(
            "SELECT value_name, weight, mapping_confidence FROM belief_values WHERE belief_id = ?",
            (belief_id,)
        )
        belief['values'] = [dict(r) for r in await cursor.fetchall()]

        return belief


async def get_belief_by_id(user_id: str, belief_id: str) -> Optional[dict]:
    """Get a belief by ID, verifying it belongs to the user."""
    belief = await get_belief(belief_id)
    if belief and belief.get('user_id') == user_id:
        return belief
    return None


async def get_user_beliefs(
    user_id: str,
    include_deleted: bool = False,
    include_values: bool = False,
    limit: int = None
) -> list[dict]:
    """Get all beliefs for a user."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row

        query = "SELECT * FROM beliefs WHERE user_id = ?"
        params = [user_id]

        if not include_deleted:
            query += " AND is_deleted = 0"

        query += " ORDER BY first_expressed DESC"

        if limit:
            query += f" LIMIT {limit}"

        cursor = await db.execute(query, params)
        beliefs = [dict(row) for row in await cursor.fetchall()]

        # Fetch topics for each belief
        for belief in beliefs:
            cursor = await db.execute(
                "SELECT topic FROM belief_topics WHERE belief_id = ?",
                (belief['id'],)
            )
            belief['topics'] = [r['topic'] for r in await cursor.fetchall()]

            # Optionally fetch values for each belief
            if include_values:
                cursor = await db.execute(
                    "SELECT value_name, weight FROM belief_values WHERE belief_id = ?",
                    (belief['id'],)
                )
                belief['values'] = [dict(r) for r in await cursor.fetchall()]

        return beliefs


async def get_recent_beliefs(user_id: str, limit: int = 5) -> list[dict]:
    """Get most recent beliefs."""
    return await get_user_beliefs(user_id, limit=limit)


async def get_all_topics(user_id: str) -> list[str]:
    """Get all unique topics for a user's beliefs."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            """SELECT DISTINCT bt.topic FROM belief_topics bt
               JOIN beliefs b ON bt.belief_id = b.id
               WHERE b.user_id = ? AND b.is_deleted = 0
               ORDER BY bt.topic""",
            (user_id,)
        )
        return [row[0] for row in await cursor.fetchall()]


async def get_beliefs_by_topic(user_id: str, topic: str) -> list[dict]:
    """Get beliefs for a user filtered by topic."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            """SELECT b.* FROM beliefs b
               JOIN belief_topics bt ON b.id = bt.belief_id
               WHERE b.user_id = ? AND bt.topic = ? AND b.is_deleted = 0
               ORDER BY b.first_expressed DESC""",
            (user_id, topic.lower())
        )
        beliefs = [dict(row) for row in await cursor.fetchall()]

        for belief in beliefs:
            cursor = await db.execute(
                "SELECT topic FROM belief_topics WHERE belief_id = ?",
                (belief['id'],)
            )
            belief['topics'] = [r[0] for r in await cursor.fetchall()]

        return beliefs


async def update_belief_confidence(belief_id: str, user_id: str, new_confidence: float, trigger: str = None) -> bool:
    """Update a belief's confidence and record evolution."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        # Get current confidence
        cursor = await db.execute(
            "SELECT confidence FROM beliefs WHERE id = ? AND user_id = ? AND is_deleted = 0",
            (belief_id, user_id)
        )
        row = await cursor.fetchone()
        if not row:
            return False

        old_confidence = row['confidence']

        # Update the belief
        cursor = await db.execute(
            "UPDATE beliefs SET confidence = ?, last_referenced = CURRENT_TIMESTAMP WHERE id = ? AND user_id = ?",
            (new_confidence, belief_id, user_id)
        )
        await db.commit()

        if cursor.rowcount == 0:
            return False

    # Record evolution
    await record_belief_evolution(
        belief_id=belief_id,
        old_confidence=old_confidence,
        new_confidence=new_confidence,
        trigger=trigger
    )
    return True


async def update_belief_importance(belief_id: str, user_id: str, importance: int) -> bool:
    """Update a belief's importance (1-5 scale)."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "UPDATE beliefs SET importance = ? WHERE id = ? AND user_id = ? AND is_deleted = 0",
            (importance, belief_id, user_id)
        )
        await db.commit()
        return cursor.rowcount > 0


async def get_important_beliefs(user_id: str, min_importance: int = 4) -> list[dict]:
    """Get beliefs marked as important."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            """SELECT * FROM beliefs
               WHERE user_id = ? AND is_deleted = 0 AND importance >= ?
               ORDER BY importance DESC, first_expressed DESC""",
            (user_id, min_importance)
        )
        beliefs = [dict(row) for row in await cursor.fetchall()]

        for belief in beliefs:
            cursor = await db.execute(
                "SELECT topic FROM belief_topics WHERE belief_id = ?",
                (belief['id'],)
            )
            belief['topics'] = [r[0] for r in await cursor.fetchall()]

        return beliefs


async def get_last_deleted_belief(user_id: str) -> Optional[dict]:
    """Get the most recently deleted belief for undo."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            """SELECT * FROM beliefs
               WHERE user_id = ? AND is_deleted = 1
               ORDER BY first_expressed DESC LIMIT 1""",
            (user_id,)
        )
        row = await cursor.fetchone()
        return dict(row) if row else None


async def soft_delete_belief(belief_id: str, user_id: str) -> bool:
    """Soft delete a belief."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "UPDATE beliefs SET is_deleted = 1 WHERE id = ? AND user_id = ?",
            (belief_id, user_id)
        )
        await db.commit()
        return cursor.rowcount > 0


async def restore_belief(belief_id: str, user_id: str) -> bool:
    """Restore a soft-deleted belief."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "UPDATE beliefs SET is_deleted = 0 WHERE id = ? AND user_id = ? AND is_deleted = 1",
            (belief_id, user_id)
        )
        await db.commit()
        return cursor.rowcount > 0


async def restore_last_deleted_belief(user_id: str) -> Optional[dict]:
    """Get and restore the most recently deleted belief for a user."""
    last_deleted = await get_last_deleted_belief(user_id)
    if last_deleted:
        await restore_belief(last_deleted['id'], user_id)
        return last_deleted
    return None


# ============================================
# BELIEF EVOLUTION & TENSIONS
# ============================================

async def record_belief_evolution(
    belief_id: str,
    old_confidence: float = None,
    new_confidence: float = None,
    old_statement: str = None,
    new_statement: str = None,
    trigger: str = None
):
    """Record a change in a belief's confidence or wording."""
    evolution_id = str(uuid.uuid4())

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """INSERT INTO belief_evolution
               (id, belief_id, old_confidence, new_confidence, old_statement, new_statement, trigger)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (evolution_id, belief_id, old_confidence, new_confidence, old_statement, new_statement, trigger)
        )
        await db.commit()


async def get_belief_history(belief_id: str) -> list[dict]:
    """Get the evolution history of a specific belief."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            """SELECT * FROM belief_evolution
               WHERE belief_id = ?
               ORDER BY timestamp DESC""",
            (belief_id,)
        )
        return [dict(row) for row in await cursor.fetchall()]


async def get_recent_changes(user_id: str, days: int = 30) -> list[dict]:
    """Get beliefs that have evolved in the last N days."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            """SELECT be.*, b.statement as current_statement, b.confidence as current_confidence,
                      b.importance, b.id as belief_id
               FROM belief_evolution be
               JOIN beliefs b ON be.belief_id = b.id
               WHERE b.user_id = ? AND b.is_deleted = 0
                 AND be.timestamp >= datetime('now', ?)
               ORDER BY be.timestamp DESC""",
            (user_id, f'-{days} days')
        )
        return [dict(row) for row in await cursor.fetchall()]


async def get_all_tensions(user_id: str) -> list[dict]:
    """Get all contradicting belief pairs for a user."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            """SELECT br.*,
                      b1.statement as source_statement, b1.confidence as source_confidence,
                      b1.importance as source_importance, b1.id as source_id,
                      b2.statement as target_statement, b2.confidence as target_confidence,
                      b2.importance as target_importance, b2.id as target_id
               FROM belief_relations br
               JOIN beliefs b1 ON br.source_id = b1.id
               JOIN beliefs b2 ON br.target_id = b2.id
               WHERE b1.user_id = ?
                 AND br.relation_type = 'contradicts'
                 AND b1.is_deleted = 0
                 AND b2.is_deleted = 0
               ORDER BY br.strength DESC, b1.importance DESC""",
            (user_id,)
        )
        return [dict(row) for row in await cursor.fetchall()]


async def add_belief_relation(
    source_id: str,
    target_id: str,
    relation_type: str,
    strength: float = 1.0
):
    """Add a relation between two beliefs."""
    relation_id = str(uuid.uuid4())

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """INSERT OR REPLACE INTO belief_relations
               (id, source_id, target_id, relation_type, strength)
               VALUES (?, ?, ?, ?, ?)""",
            (relation_id, source_id, target_id, relation_type, strength)
        )
        await db.commit()


# ============================================
# BELIEF VALUES
# ============================================

async def add_belief_values(
    belief_id: str,
    values: list[tuple[str, float, float]]  # (value_name, weight, mapping_confidence)
):
    """Add value mappings for a belief."""
    async with aiosqlite.connect(DB_PATH) as db:
        for value_name, weight, mapping_confidence in values:
            await db.execute(
                """INSERT OR REPLACE INTO belief_values
                   (belief_id, value_name, weight, mapping_confidence)
                   VALUES (?, ?, ?, ?)""",
                (belief_id, value_name, weight, mapping_confidence)
            )
        await db.commit()


async def get_belief_value_mappings(user_id: str) -> list[BeliefValueMapping]:
    """Get all belief-value mappings for a user (for profile calculation)."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row

        cursor = await db.execute(
            """SELECT b.id, b.statement, b.confidence, b.first_expressed,
                      bv.value_name, bv.weight, bv.mapping_confidence
               FROM beliefs b
               JOIN belief_values bv ON b.id = bv.belief_id
               WHERE b.user_id = ?
                 AND b.is_deleted = 0
                 AND b.include_in_values = 1
               ORDER BY b.id""",
            (user_id,)
        )

        rows = await cursor.fetchall()

        # Group by belief
        belief_map = {}
        for row in rows:
            bid = row['id']
            if bid not in belief_map:
                belief_map[bid] = BeliefValueMapping(
                    belief_id=bid,
                    belief_statement=row['statement'],
                    belief_confidence=row['confidence'],
                    belief_timestamp=row['first_expressed'],
                    values=[]
                )
            belief_map[bid].values.append((
                row['value_name'],
                row['weight'],
                row['mapping_confidence']
            ))

        return list(belief_map.values())


# ============================================
# USER VALUES
# ============================================

async def update_user_value_profile(user_id: str) -> ValueProfile:
    """Recalculate and store user's value profile."""
    mappings = await get_belief_value_mappings(user_id)
    aggregated = aggregate_value_profile(mappings)

    async with aiosqlite.connect(DB_PATH) as db:
        now = datetime.now().isoformat()

        for value_name, (raw_score, normalized_score, belief_count) in aggregated.items():
            await db.execute(
                """INSERT OR REPLACE INTO user_values
                   (user_id, value_name, score, raw_score, belief_count, last_updated)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (user_id, value_name, normalized_score, raw_score, belief_count, now)
            )

        await db.commit()

    return await get_user_value_profile(user_id)


async def get_user_value_profile(user_id: str) -> ValueProfile:
    """Get user's current value profile."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row

        cursor = await db.execute(
            "SELECT * FROM user_values WHERE user_id = ?",
            (user_id,)
        )
        rows = await cursor.fetchall()

        scores = {}
        last_updated = None

        for row in rows:
            scores[row['value_name']] = ValueScore(
                value_name=row['value_name'],
                raw_score=row['raw_score'],
                normalized_score=row['score'],
                belief_count=row['belief_count'],
                last_updated=row['last_updated']
            )
            if row['last_updated']:
                last_updated = row['last_updated']

        # Fill in missing values with zeros
        for value_name in ALL_VALUES:
            if value_name not in scores:
                scores[value_name] = ValueScore(
                    value_name=value_name,
                    raw_score=0.0,
                    normalized_score=0.0,
                    belief_count=0
                )

        return ValueProfile(
            user_id=user_id,
            scores=scores,
            last_updated=last_updated
        )


async def create_value_snapshot(user_id: str, force: bool = False) -> Optional[str]:
    """Create a snapshot of user's current value profile.

    Args:
        user_id: The user's ID
        force: If True, create snapshot even if one exists for today

    Returns:
        The snapshot ID if created, None if skipped (already exists for today)
    """
    today = datetime.now().date().isoformat()

    async with aiosqlite.connect(DB_PATH) as db:
        # Check if snapshot already exists for today (unless forcing)
        if not force:
            cursor = await db.execute(
                "SELECT id FROM value_snapshots WHERE user_id = ? AND snapshot_date = ?",
                (user_id, today)
            )
            existing = await cursor.fetchone()
            if existing:
                return None  # Snapshot already exists for today

        # Get current profile
        profile = await get_user_value_profile(user_id)
        if not profile:
            return None

        values_json = json.dumps({
            v: profile.scores[v].normalized_score
            for v in ALL_VALUES
        })

        snapshot_id = str(uuid.uuid4())

        await db.execute(
            """INSERT INTO value_snapshots (id, user_id, snapshot_date, values_json)
               VALUES (?, ?, ?, ?)""",
            (snapshot_id, user_id, today, values_json)
        )
        await db.commit()

    return snapshot_id


async def get_value_snapshot(user_id: str, days_ago: int = 30) -> Optional[ValueProfile]:
    """Get a historical value snapshot."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row

        target_date = (datetime.now() - timedelta(days=days_ago)).date().isoformat()

        cursor = await db.execute(
            """SELECT * FROM value_snapshots
               WHERE user_id = ? AND snapshot_date <= ?
               ORDER BY snapshot_date DESC LIMIT 1""",
            (user_id, target_date)
        )
        row = await cursor.fetchone()

        if not row:
            return None

        values_dict = json.loads(row['values_json'])

        scores = {}
        for value_name, score in values_dict.items():
            scores[value_name] = ValueScore(
                value_name=value_name,
                raw_score=0.0,  # Not stored in snapshot
                normalized_score=score,
                belief_count=0,  # Not stored in snapshot
                last_updated=row['snapshot_date']
            )

        return ValueProfile(
            user_id=user_id,
            scores=scores,
            last_updated=row['snapshot_date']
        )


async def get_value_profile_history(user_id: str, days: int = 30) -> list[ValueProfile]:
    """Get historical value profile snapshots for a user."""
    from datetime import datetime, timedelta
    cutoff_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            """SELECT * FROM value_snapshots
               WHERE user_id = ? AND snapshot_date >= ?
               ORDER BY snapshot_date ASC""",
            (user_id, cutoff_date)
        )
        rows = await cursor.fetchall()

        profiles = []
        for row in rows:
            values_data = json.loads(row['values_json'])
            profile = ValueProfile(
                values={k: ValueScore(**v) for k, v in values_data.items()},
                last_updated=row['snapshot_date']
            )
            profiles.append(profile)

        return profiles


# ============================================
# CONVERSATIONS
# ============================================

async def add_conversation_message(
    user_id: str,
    role: str,
    content: str,
    session_id: str = None,
    channel_id: str = None,
    message_id: str = None
):
    """Store a conversation message."""
    msg_id = str(uuid.uuid4())

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """INSERT INTO conversations
               (id, user_id, session_id, channel_id, message_id, role, content)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (msg_id, user_id, session_id, channel_id, message_id, role, content)
        )
        await db.commit()


async def get_session_conversation(session_id: str) -> list[dict]:
    """Get all messages from a session."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            """SELECT role, content, timestamp FROM conversations
               WHERE session_id = ?
               ORDER BY timestamp""",
            (session_id,)
        )
        return [dict(row) for row in await cursor.fetchall()]


async def get_recent_conversation(user_id: str, limit: int = 20) -> list[dict]:
    """Get recent conversation history for a user."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            """SELECT role, content, timestamp FROM conversations
               WHERE user_id = ?
               ORDER BY timestamp DESC
               LIMIT ?""",
            (user_id, limit)
        )
        messages = [dict(row) for row in await cursor.fetchall()]
        return list(reversed(messages))


# ============================================
# DATA EXPORT / CLEAR
# ============================================

async def export_user_data(user_id: str) -> dict:
    """Export all user data."""
    user = await get_or_create_user(user_id)
    beliefs = await get_user_beliefs(user_id, include_deleted=True)
    profile = await get_user_value_profile(user_id)

    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row

        # Sessions
        cursor = await db.execute(
            "SELECT * FROM journal_sessions WHERE user_id = ?", (user_id,)
        )
        sessions = [dict(row) for row in await cursor.fetchall()]

        # Conversations
        cursor = await db.execute(
            "SELECT * FROM conversations WHERE user_id = ? ORDER BY timestamp",
            (user_id,)
        )
        conversations = [dict(row) for row in await cursor.fetchall()]

        # Value snapshots
        cursor = await db.execute(
            "SELECT * FROM value_snapshots WHERE user_id = ?", (user_id,)
        )
        snapshots = [dict(row) for row in await cursor.fetchall()]

    return {
        "user": user,
        "beliefs": beliefs,
        "value_profile": {
            v: {
                "score": profile.scores[v].normalized_score,
                "raw_score": profile.scores[v].raw_score,
                "belief_count": profile.scores[v].belief_count
            }
            for v in ALL_VALUES
        },
        "sessions": sessions,
        "conversations": conversations,
        "value_snapshots": snapshots,
        "exported_at": datetime.now().isoformat()
    }


async def clear_all_user_data(user_id: str) -> bool:
    """Delete all data for a user."""
    async with aiosqlite.connect(DB_PATH) as db:
        # Order matters due to foreign keys
        await db.execute("DELETE FROM belief_values WHERE belief_id IN (SELECT id FROM beliefs WHERE user_id = ?)", (user_id,))
        await db.execute("DELETE FROM belief_topics WHERE belief_id IN (SELECT id FROM beliefs WHERE user_id = ?)", (user_id,))
        await db.execute("DELETE FROM belief_relations WHERE source_id IN (SELECT id FROM beliefs WHERE user_id = ?)", (user_id,))
        await db.execute("DELETE FROM belief_evolution WHERE belief_id IN (SELECT id FROM beliefs WHERE user_id = ?)", (user_id,))
        await db.execute("DELETE FROM beliefs WHERE user_id = ?", (user_id,))
        await db.execute("DELETE FROM conversations WHERE user_id = ?", (user_id,))
        await db.execute("DELETE FROM journal_sessions WHERE user_id = ?", (user_id,))
        await db.execute("DELETE FROM user_values WHERE user_id = ?", (user_id,))
        await db.execute("DELETE FROM value_snapshots WHERE user_id = ?", (user_id,))
        await db.execute("DELETE FROM summaries WHERE user_id = ?", (user_id,))
        await db.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
        await db.commit()
        return True


# ============================================
# SUMMARIES
# ============================================

async def get_sessions_in_range(user_id: str, start_date: str, end_date: str) -> list[dict]:
    """Get completed sessions within a date range."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            """SELECT * FROM journal_sessions
               WHERE user_id = ?
                 AND ended_at IS NOT NULL
                 AND started_at >= ?
                 AND started_at < ?
               ORDER BY started_at""",
            (user_id, start_date, end_date)
        )
        return [dict(row) for row in await cursor.fetchall()]


async def get_beliefs_from_sessions(user_id: str, session_ids: list[str]) -> list[dict]:
    """Get beliefs extracted from specific sessions."""
    if not session_ids:
        return []

    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        placeholders = ','.join('?' * len(session_ids))
        cursor = await db.execute(
            f"""SELECT * FROM beliefs
               WHERE user_id = ?
                 AND session_id IN ({placeholders})
                 AND is_deleted = 0
               ORDER BY first_expressed""",
            [user_id] + session_ids
        )
        beliefs = [dict(row) for row in await cursor.fetchall()]

        # Fetch topics for each belief
        for belief in beliefs:
            cursor = await db.execute(
                "SELECT topic FROM belief_topics WHERE belief_id = ?",
                (belief['id'],)
            )
            belief['topics'] = [r['topic'] for r in await cursor.fetchall()]

            # Fetch values for each belief
            cursor = await db.execute(
                "SELECT value_name, weight FROM belief_values WHERE belief_id = ?",
                (belief['id'],)
            )
            belief['values'] = [dict(r) for r in await cursor.fetchall()]

        return beliefs


async def get_topics_frequency(beliefs: list[dict]) -> dict[str, int]:
    """Count topic frequency from a list of beliefs."""
    topic_counts = {}
    for belief in beliefs:
        for topic in belief.get('topics', []):
            topic_counts[topic] = topic_counts.get(topic, 0) + 1
    return dict(sorted(topic_counts.items(), key=lambda x: -x[1]))


async def store_summary(
    user_id: str,
    period_type: str,
    period_start: str,
    period_end: str,
    data_json: str,
    narrative: str,
    highlights: str,
    session_count: int,
    belief_count: int
) -> str:
    """Store a generated summary."""
    summary_id = str(uuid.uuid4())

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """INSERT INTO summaries
               (id, user_id, period_type, period_start, period_end,
                data_json, narrative, highlights, session_count, belief_count)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (summary_id, user_id, period_type, period_start, period_end,
             data_json, narrative, highlights, session_count, belief_count)
        )
        await db.commit()

    return summary_id


async def get_past_summaries(user_id: str, period_type: str = None, limit: int = 10) -> list[dict]:
    """Get past summaries for a user."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row

        if period_type:
            cursor = await db.execute(
                """SELECT * FROM summaries
                   WHERE user_id = ? AND period_type = ?
                   ORDER BY period_start DESC
                   LIMIT ?""",
                (user_id, period_type, limit)
            )
        else:
            cursor = await db.execute(
                """SELECT * FROM summaries
                   WHERE user_id = ?
                   ORDER BY period_start DESC
                   LIMIT ?""",
                (user_id, limit)
            )
        return [dict(row) for row in await cursor.fetchall()]


async def get_value_profile_at_date(user_id: str, target_date: str) -> Optional[dict]:
    """Get the value profile snapshot closest to (but not after) a target date."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            """SELECT * FROM value_snapshots
               WHERE user_id = ? AND snapshot_date <= ?
               ORDER BY snapshot_date DESC
               LIMIT 1""",
            (user_id, target_date)
        )
        row = await cursor.fetchone()
        if row:
            return json.loads(row['values_json'])
        return None
