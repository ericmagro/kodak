"""Database operations for Kodak."""

import os
import logging
import aiosqlite
import uuid
from pathlib import Path
from datetime import datetime
from typing import Optional

logger = logging.getLogger('kodak')

# Allow DB_PATH to be configured via environment variable
_default_db_path = Path(__file__).parent.parent / "kodak.db"
DB_PATH = Path(os.getenv("KODAK_DB_PATH", str(_default_db_path)))
SCHEMA_PATH = Path(__file__).parent.parent / "schema.sql"

# Current schema version - increment when adding migrations
SCHEMA_VERSION = 1

# Migrations: list of (version, description, sql) tuples
# Each migration brings the DB from version-1 to version
MIGRATIONS = [
    # Version 1: Add visibility column to beliefs table (for v0.3 privacy features)
    (1, "Add visibility column to beliefs", """
        ALTER TABLE beliefs ADD COLUMN visibility TEXT DEFAULT 'shareable';
    """),
]


async def _get_schema_version(db) -> int:
    """Get current schema version, or 0 if not set."""
    try:
        cursor = await db.execute(
            "SELECT version FROM schema_version ORDER BY version DESC LIMIT 1"
        )
        row = await cursor.fetchone()
        return row[0] if row else 0
    except aiosqlite.OperationalError:
        # Table doesn't exist yet
        return 0


async def _run_migrations(db):
    """Run any pending migrations."""
    current_version = await _get_schema_version(db)

    for version, description, sql in MIGRATIONS:
        if version > current_version:
            try:
                logger.info(f"Running migration {version}: {description}")
                await db.executescript(sql)
                await db.execute(
                    "INSERT INTO schema_version (version, applied_at) VALUES (?, ?)",
                    (version, datetime.now().isoformat())
                )
                await db.commit()
                logger.info(f"Migration {version} complete")
            except aiosqlite.OperationalError as e:
                # Column might already exist from schema.sql
                if "duplicate column name" in str(e).lower():
                    logger.info(f"Migration {version}: Column already exists, skipping")
                    await db.execute(
                        "INSERT INTO schema_version (version, applied_at) VALUES (?, ?)",
                        (version, datetime.now().isoformat())
                    )
                    await db.commit()
                else:
                    raise


# Topic synonyms for normalization
# Maps variant terms to a canonical form
TOPIC_SYNONYMS = {
    # Work/career
    "job": "work",
    "career": "work",
    "employment": "work",
    "profession": "work",
    "occupation": "work",
    # Relationships
    "dating": "relationships",
    "romance": "relationships",
    "love": "relationships",
    "marriage": "relationships",
    "partner": "relationships",
    # Family
    "parents": "family",
    "children": "family",
    "kids": "family",
    "parenting": "family",
    # Health
    "fitness": "health",
    "wellness": "health",
    "exercise": "health",
    "mental health": "health",
    # Money
    "finance": "money",
    "finances": "money",
    "financial": "money",
    "wealth": "money",
    "investing": "money",
    # Politics
    "political": "politics",
    "government": "politics",
    # Religion/spirituality
    "faith": "spirituality",
    "religion": "spirituality",
    "religious": "spirituality",
    "god": "spirituality",
    # Technology
    "tech": "technology",
    "ai": "technology",
    "computers": "technology",
    "software": "technology",
}


def normalize_topic(topic: str) -> str:
    """Normalize a topic to its canonical form."""
    topic = topic.lower().strip()
    return TOPIC_SYNONYMS.get(topic, topic)


async def init_db():
    """Initialize the database with schema and run migrations."""
    async with aiosqlite.connect(DB_PATH) as db:
        # Create schema_version table if it doesn't exist
        await db.execute("""
            CREATE TABLE IF NOT EXISTS schema_version (
                version INTEGER PRIMARY KEY,
                applied_at TEXT NOT NULL
            )
        """)
        await db.commit()

        # Run the base schema
        with open(SCHEMA_PATH) as f:
            await db.executescript(f.read())
        await db.commit()

        # Run any pending migrations
        await _run_migrations(db)


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

        # Create new user with defaults
        await db.execute(
            """INSERT INTO users (user_id, username) VALUES (?, ?)""",
            (user_id, username)
        )
        await db.commit()

        cursor = await db.execute(
            "SELECT * FROM users WHERE user_id = ?", (user_id,)
        )
        row = await cursor.fetchone()
        return dict(row)


async def update_user_personality(
    user_id: str,
    warmth: int = None,
    directness: int = None,
    playfulness: int = None,
    formality: int = None,
    extraction_mode: str = None
) -> dict:
    """Update user personality settings."""
    updates = []
    values = []

    if warmth is not None:
        updates.append("warmth = ?")
        values.append(warmth)
    if directness is not None:
        updates.append("directness = ?")
        values.append(directness)
    if playfulness is not None:
        updates.append("playfulness = ?")
        values.append(playfulness)
    if formality is not None:
        updates.append("formality = ?")
        values.append(formality)
    if extraction_mode is not None:
        updates.append("extraction_mode = ?")
        values.append(extraction_mode)

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


async def complete_onboarding(user_id: str) -> dict:
    """Mark user onboarding as complete."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET onboarding_complete = 1, updated_at = ? WHERE user_id = ?",
            (datetime.now().isoformat(), user_id)
        )
        await db.commit()
    return await get_or_create_user(user_id)


async def set_tracking_paused(user_id: str, paused: bool) -> dict:
    """Pause or resume belief tracking for a user."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET tracking_paused = ?, updated_at = ? WHERE user_id = ?",
            (1 if paused else 0, datetime.now().isoformat(), user_id)
        )
        await db.commit()
    return await get_or_create_user(user_id)


async def increment_message_count(user_id: str) -> int:
    """Increment message count since last summary. Returns new count."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET messages_since_summary = messages_since_summary + 1 WHERE user_id = ?",
            (user_id,)
        )
        await db.commit()

        cursor = await db.execute(
            "SELECT messages_since_summary FROM users WHERE user_id = ?",
            (user_id,)
        )
        row = await cursor.fetchone()
        return row[0] if row else 0


async def reset_message_count(user_id: str):
    """Reset message count after showing a summary."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET messages_since_summary = 0 WHERE user_id = ?",
            (user_id,)
        )
        await db.commit()


async def get_recent_beliefs(user_id: str, limit: int = 5) -> list[dict]:
    """Get the most recently captured beliefs."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            """SELECT * FROM beliefs
               WHERE user_id = ? AND is_deleted = 0
               ORDER BY first_expressed DESC
               LIMIT ?""",
            (user_id, limit)
        )
        beliefs = [dict(row) for row in await cursor.fetchall()]

        for belief in beliefs:
            cursor = await db.execute(
                "SELECT topic FROM belief_topics WHERE belief_id = ?",
                (belief["id"],)
            )
            belief["topics"] = [row["topic"] for row in await cursor.fetchall()]

        return beliefs


async def clear_all_user_data(user_id: str) -> bool:
    """Delete all data for a user (GDPR-style clear)."""
    async with aiosqlite.connect(DB_PATH) as db:
        # Delete belief relations first (foreign key)
        await db.execute(
            """DELETE FROM belief_relations WHERE source_id IN
               (SELECT id FROM beliefs WHERE user_id = ?)""",
            (user_id,)
        )
        await db.execute(
            """DELETE FROM belief_topics WHERE belief_id IN
               (SELECT id FROM beliefs WHERE user_id = ?)""",
            (user_id,)
        )
        await db.execute(
            """DELETE FROM belief_evolution WHERE belief_id IN
               (SELECT id FROM beliefs WHERE user_id = ?)""",
            (user_id,)
        )
        await db.execute("DELETE FROM beliefs WHERE user_id = ?", (user_id,))
        await db.execute("DELETE FROM conversations WHERE user_id = ?", (user_id,))
        await db.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
        await db.commit()
        return True


async def export_user_data(user_id: str) -> dict:
    """Export all user data as a dictionary."""
    user = await get_or_create_user(user_id)
    beliefs = await get_user_beliefs(user_id, include_deleted=True)

    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row

        # Get all relations
        cursor = await db.execute(
            """SELECT br.* FROM belief_relations br
               JOIN beliefs b ON br.source_id = b.id
               WHERE b.user_id = ?""",
            (user_id,)
        )
        relations = [dict(row) for row in await cursor.fetchall()]

        # Get conversation history
        cursor = await db.execute(
            "SELECT * FROM conversations WHERE user_id = ? ORDER BY timestamp",
            (user_id,)
        )
        conversations = [dict(row) for row in await cursor.fetchall()]

    return {
        "user": user,
        "beliefs": beliefs,
        "relations": relations,
        "conversations": conversations,
        "exported_at": datetime.now().isoformat()
    }


async def add_belief(
    user_id: str,
    statement: str,
    confidence: float = 0.5,
    source_type: str = None,
    context: str = None,
    message_id: str = None,
    channel_id: str = None,
    topics: list[str] = None
) -> dict:
    """Add a new belief to the database."""
    belief_id = str(uuid.uuid4())

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """INSERT INTO beliefs
               (id, user_id, statement, confidence, source_type, context, message_id, channel_id)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (belief_id, user_id, statement, confidence, source_type, context, message_id, channel_id)
        )

        # Normalize and deduplicate topics
        normalized_topics = []
        if topics:
            seen = set()
            for topic in topics:
                normalized = normalize_topic(topic)
                if normalized not in seen:
                    seen.add(normalized)
                    normalized_topics.append(normalized)
                    await db.execute(
                        "INSERT INTO belief_topics (belief_id, topic) VALUES (?, ?)",
                        (belief_id, normalized)
                    )

        await db.commit()

    return {
        "id": belief_id,
        "user_id": user_id,
        "statement": statement,
        "confidence": confidence,
        "source_type": source_type,
        "context": context,
        "topics": normalized_topics
    }


async def add_belief_relation(
    source_id: str,
    target_id: str,
    relation_type: str,
    strength: float = 0.5
) -> dict:
    """Add a relationship between two beliefs."""
    relation_id = str(uuid.uuid4())

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """INSERT INTO belief_relations
               (id, source_id, target_id, relation_type, strength)
               VALUES (?, ?, ?, ?, ?)""",
            (relation_id, source_id, target_id, relation_type, strength)
        )
        await db.commit()

    return {
        "id": relation_id,
        "source_id": source_id,
        "target_id": target_id,
        "relation_type": relation_type,
        "strength": strength
    }


async def get_user_beliefs(user_id: str, include_deleted: bool = False) -> list[dict]:
    """Get all beliefs for a user."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row

        if include_deleted:
            cursor = await db.execute(
                "SELECT * FROM beliefs WHERE user_id = ? ORDER BY last_referenced DESC",
                (user_id,)
            )
        else:
            cursor = await db.execute(
                "SELECT * FROM beliefs WHERE user_id = ? AND is_deleted = 0 ORDER BY last_referenced DESC",
                (user_id,)
            )

        beliefs = [dict(row) for row in await cursor.fetchall()]

        # Fetch topics for each belief
        for belief in beliefs:
            cursor = await db.execute(
                "SELECT topic FROM belief_topics WHERE belief_id = ?",
                (belief["id"],)
            )
            belief["topics"] = [row["topic"] for row in await cursor.fetchall()]

        return beliefs


async def get_beliefs_by_topic(user_id: str, topic: str) -> list[dict]:
    """Get beliefs for a user filtered by topic."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            """SELECT b.* FROM beliefs b
               JOIN belief_topics bt ON b.id = bt.belief_id
               WHERE b.user_id = ? AND bt.topic = ? AND b.is_deleted = 0
               ORDER BY b.last_referenced DESC""",
            (user_id, topic.lower())
        )
        beliefs = [dict(row) for row in await cursor.fetchall()]

        for belief in beliefs:
            cursor = await db.execute(
                "SELECT topic FROM belief_topics WHERE belief_id = ?",
                (belief["id"],)
            )
            belief["topics"] = [row["topic"] for row in await cursor.fetchall()]

        return beliefs


async def get_belief_relations(belief_id: str) -> list[dict]:
    """Get all relations where this belief is the source."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            """SELECT br.*, b.statement as target_statement, b.confidence as target_confidence,
                      b.importance as target_importance
               FROM belief_relations br
               JOIN beliefs b ON br.target_id = b.id
               WHERE br.source_id = ? AND b.is_deleted = 0""",
            (belief_id,)
        )
        return [dict(row) for row in await cursor.fetchall()]


async def get_belief_relations_inverse(belief_id: str) -> list[dict]:
    """Get all relations where this belief is the target (other beliefs point to this one)."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            """SELECT br.*, b.statement as source_statement, b.confidence as source_confidence,
                      b.importance as source_importance, b.id as source_belief_id
               FROM belief_relations br
               JOIN beliefs b ON br.source_id = b.id
               WHERE br.target_id = ? AND b.is_deleted = 0""",
            (belief_id,)
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


async def soft_delete_belief(belief_id: str, user_id: str) -> bool:
    """Soft delete a belief (mark as deleted)."""
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


async def set_belief_importance(belief_id: str, user_id: str, importance: int) -> bool:
    """Set the importance level of a belief (1-5)."""
    if importance < 1 or importance > 5:
        return False

    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "UPDATE beliefs SET importance = ? WHERE id = ? AND user_id = ? AND is_deleted = 0",
            (importance, belief_id, user_id)
        )
        await db.commit()
        return cursor.rowcount > 0


async def get_beliefs_by_importance(user_id: str, min_importance: int = 4) -> list[dict]:
    """Get beliefs at or above a certain importance level."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            """SELECT b.*, GROUP_CONCAT(bt.topic) as topics
               FROM beliefs b
               LEFT JOIN belief_topics bt ON b.id = bt.belief_id
               WHERE b.user_id = ? AND b.is_deleted = 0 AND b.importance >= ?
               GROUP BY b.id
               ORDER BY b.importance DESC, b.last_referenced DESC""",
            (user_id, min_importance)
        )
        rows = await cursor.fetchall()
        beliefs = []
        for row in rows:
            belief = dict(row)
            belief['topics'] = belief['topics'].split(',') if belief['topics'] else []
            beliefs.append(belief)
        return beliefs


async def add_conversation_message(
    user_id: str,
    role: str,
    content: str,
    channel_id: str = None,
    message_id: str = None
):
    """Store a conversation message for context."""
    msg_id = str(uuid.uuid4())

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """INSERT INTO conversations (id, user_id, channel_id, message_id, role, content)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (msg_id, user_id, channel_id, message_id, role, content)
        )
        await db.commit()


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
        return list(reversed(messages))  # Oldest first


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


async def update_belief_confidence(belief_id: str, user_id: str, new_confidence: float, trigger: str = None) -> bool:
    """Update a belief's confidence and record the evolution."""
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
        await db.execute(
            "UPDATE beliefs SET confidence = ?, last_referenced = CURRENT_TIMESTAMP WHERE id = ?",
            (new_confidence, belief_id)
        )
        await db.commit()

    # Record evolution
    await record_belief_evolution(
        belief_id=belief_id,
        old_confidence=old_confidence,
        new_confidence=new_confidence,
        trigger=trigger
    )
    return True


async def create_comparison_request(requester_id: str, target_id: str) -> dict:
    """Create a comparison request between two users."""
    request_id = str(uuid.uuid4())

    async with aiosqlite.connect(DB_PATH) as db:
        # Check if there's already a pending request
        cursor = await db.execute(
            """SELECT id FROM comparison_requests
               WHERE requester_id = ? AND target_id = ? AND status = 'pending'""",
            (requester_id, target_id)
        )
        existing = await cursor.fetchone()
        if existing:
            return {"id": existing[0], "status": "already_pending"}

        await db.execute(
            """INSERT INTO comparison_requests (id, requester_id, target_id)
               VALUES (?, ?, ?)""",
            (request_id, requester_id, target_id)
        )
        await db.commit()

    return {"id": request_id, "status": "created"}


async def get_pending_requests(user_id: str) -> list[dict]:
    """Get pending comparison requests for a user (where they are the target)."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            """SELECT cr.*, u.username as requester_username
               FROM comparison_requests cr
               JOIN users u ON cr.requester_id = u.user_id
               WHERE cr.target_id = ? AND cr.status = 'pending'
               ORDER BY cr.requested_at DESC""",
            (user_id,)
        )
        return [dict(row) for row in await cursor.fetchall()]


async def respond_to_comparison(request_id: str, user_id: str, accept: bool) -> bool:
    """Accept or decline a comparison request."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            """UPDATE comparison_requests
               SET status = ?, responded_at = CURRENT_TIMESTAMP
               WHERE id = ? AND target_id = ? AND status = 'pending'""",
            ('accepted' if accept else 'declined', request_id, user_id)
        )
        await db.commit()
        return cursor.rowcount > 0


async def get_comparison_request(request_id: str) -> Optional[dict]:
    """Get a specific comparison request."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM comparison_requests WHERE id = ?",
            (request_id,)
        )
        row = await cursor.fetchone()
        return dict(row) if row else None


async def get_shareable_beliefs(user_id: str) -> list[dict]:
    """Get beliefs that can be shared in comparisons (not private/hidden)."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            """SELECT b.*, GROUP_CONCAT(bt.topic) as topics_str
               FROM beliefs b
               LEFT JOIN belief_topics bt ON b.id = bt.belief_id
               WHERE b.user_id = ? AND b.is_deleted = 0
                 AND b.visibility IN ('public', 'shareable')
               GROUP BY b.id
               ORDER BY b.importance DESC, b.confidence DESC""",
            (user_id,)
        )
        rows = await cursor.fetchall()
        beliefs = []
        for row in rows:
            belief = dict(row)
            belief['topics'] = belief['topics_str'].split(',') if belief['topics_str'] else []
            del belief['topics_str']
            beliefs.append(belief)
        return beliefs


async def get_accepted_comparison(requester_id: str, target_id: str) -> Optional[dict]:
    """Check if there's an accepted comparison between two users."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            """SELECT * FROM comparison_requests
               WHERE ((requester_id = ? AND target_id = ?)
                  OR (requester_id = ? AND target_id = ?))
                 AND status = 'accepted'
               ORDER BY responded_at DESC
               LIMIT 1""",
            (requester_id, target_id, target_id, requester_id)
        )
        row = await cursor.fetchone()
        return dict(row) if row else None


async def store_comparison_result(
    request_id: str,
    user_a_id: str,
    user_b_id: str,
    overall_similarity: float,
    core_similarity: float,
    agreement_count: int,
    difference_count: int,
    bridging_beliefs: list[dict] = None
) -> str:
    """Store comparison results for bridging score calculation."""
    result_id = str(uuid.uuid4())

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """INSERT INTO comparison_results
               (id, request_id, user_a_id, user_b_id, overall_similarity,
                core_similarity, agreement_count, difference_count)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (result_id, request_id, user_a_id, user_b_id, overall_similarity,
             core_similarity, agreement_count, difference_count)
        )

        # Store bridging beliefs (agreements despite low overall similarity)
        if bridging_beliefs and overall_similarity < 0.5:
            for bb in bridging_beliefs:
                bb_id = str(uuid.uuid4())
                await db.execute(
                    """INSERT INTO bridging_beliefs
                       (id, comparison_id, belief_id, matched_with_belief_id, user_id)
                       VALUES (?, ?, ?, ?, ?)""",
                    (bb_id, result_id, bb['belief_id'], bb.get('matched_id'), bb['user_id'])
                )

        await db.commit()

    return result_id


async def get_bridging_score(user_id: str) -> dict:
    """Calculate bridging score based on comparison history."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row

        # Get all comparisons involving this user
        cursor = await db.execute(
            """SELECT * FROM comparison_results
               WHERE user_a_id = ? OR user_b_id = ?
               ORDER BY computed_at DESC""",
            (user_id, user_id)
        )
        comparisons = [dict(row) for row in await cursor.fetchall()]

        if not comparisons:
            return {
                "score": 0,
                "comparisons_count": 0,
                "bridging_comparisons": 0,
                "bridging_beliefs": [],
                "message": "No comparisons yet. Use /compare to start."
            }

        # Count comparisons with low similarity but some agreements
        bridging_comparisons = 0
        total_agreements_with_different = 0

        for comp in comparisons:
            if comp['overall_similarity'] < 0.5 and comp['agreement_count'] > 0:
                bridging_comparisons += 1
                total_agreements_with_different += comp['agreement_count']

        # Get bridging beliefs for this user
        cursor = await db.execute(
            """SELECT bb.*, b.statement, b.importance
               FROM bridging_beliefs bb
               JOIN beliefs b ON bb.belief_id = b.id
               WHERE bb.user_id = ?
               ORDER BY b.importance DESC
               LIMIT 10""",
            (user_id,)
        )
        bridging_beliefs = [dict(row) for row in await cursor.fetchall()]

        # Calculate score
        if len(comparisons) == 0:
            score = 0
        else:
            # Score based on: % of comparisons that had bridging + avg agreements
            bridging_ratio = bridging_comparisons / len(comparisons)
            avg_agreements = total_agreements_with_different / max(bridging_comparisons, 1)
            score = min(1.0, (bridging_ratio * 0.6) + (min(avg_agreements, 5) / 5 * 0.4))

        return {
            "score": score,
            "comparisons_count": len(comparisons),
            "bridging_comparisons": bridging_comparisons,
            "bridging_beliefs": bridging_beliefs,
            "total_bridging_agreements": total_agreements_with_different
        }


async def set_belief_visibility(belief_id: str, user_id: str, visibility: str) -> bool:
    """Set the visibility level of a belief."""
    valid_levels = ('public', 'shareable', 'private', 'hidden')
    if visibility not in valid_levels:
        return False

    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "UPDATE beliefs SET visibility = ? WHERE id = ? AND user_id = ? AND is_deleted = 0",
            (visibility, belief_id, user_id)
        )
        await db.commit()
        return cursor.rowcount > 0


async def set_topic_visibility(user_id: str, topic: str, visibility: str) -> int:
    """Set visibility for all beliefs with a given topic. Returns count updated."""
    valid_levels = ('public', 'shareable', 'private', 'hidden')
    if visibility not in valid_levels:
        return 0

    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            """UPDATE beliefs SET visibility = ?
               WHERE id IN (
                   SELECT b.id FROM beliefs b
                   JOIN belief_topics bt ON b.id = bt.belief_id
                   WHERE b.user_id = ? AND bt.topic = ? AND b.is_deleted = 0
               )""",
            (visibility, user_id, topic.lower())
        )
        await db.commit()
        return cursor.rowcount


async def get_visibility_breakdown(user_id: str) -> dict:
    """Get count of beliefs by visibility level."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            """SELECT visibility, COUNT(*) as count
               FROM beliefs
               WHERE user_id = ? AND is_deleted = 0
               GROUP BY visibility""",
            (user_id,)
        )
        rows = await cursor.fetchall()
        breakdown = {'public': 0, 'shareable': 0, 'private': 0, 'hidden': 0}
        for row in rows:
            if row[0] in breakdown:
                breakdown[row[0]] = row[1]
        return breakdown


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
