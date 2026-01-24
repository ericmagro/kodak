"""Database operations for Kodak."""

import aiosqlite
import uuid
from pathlib import Path
from datetime import datetime
from typing import Optional

DB_PATH = Path(__file__).parent.parent / "kodak.db"
SCHEMA_PATH = Path(__file__).parent.parent / "schema.sql"


async def init_db():
    """Initialize the database with schema."""
    async with aiosqlite.connect(DB_PATH) as db:
        with open(SCHEMA_PATH) as f:
            await db.executescript(f.read())
        await db.commit()


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

        if topics:
            for topic in topics:
                await db.execute(
                    "INSERT INTO belief_topics (belief_id, topic) VALUES (?, ?)",
                    (belief_id, topic.lower())
                )

        await db.commit()

    return {
        "id": belief_id,
        "user_id": user_id,
        "statement": statement,
        "confidence": confidence,
        "source_type": source_type,
        "context": context,
        "topics": topics or []
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
    """Get all relations for a belief."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            """SELECT br.*, b.statement as target_statement
               FROM belief_relations br
               JOIN beliefs b ON br.target_id = b.id
               WHERE br.source_id = ?""",
            (belief_id,)
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
