-- Kodak Database Schema

-- User settings and personality configuration
CREATE TABLE IF NOT EXISTS users (
    user_id TEXT PRIMARY KEY,           -- Discord user ID
    username TEXT,                       -- Cached username
    warmth INTEGER DEFAULT 3,            -- 1-5 scale
    playfulness INTEGER DEFAULT 3,       -- 1-5 scale
    directness INTEGER DEFAULT 3,        -- 1-5 scale
    formality INTEGER DEFAULT 3,         -- 1-5 scale
    extraction_mode TEXT DEFAULT 'active', -- active | passive | hybrid
    onboarding_complete INTEGER DEFAULT 0, -- Has user completed onboarding?
    tracking_paused INTEGER DEFAULT 0,   -- Is belief tracking paused?
    messages_since_summary INTEGER DEFAULT 0, -- Messages since last belief summary
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Core belief nodes
CREATE TABLE IF NOT EXISTS beliefs (
    id TEXT PRIMARY KEY,                 -- UUID
    user_id TEXT NOT NULL,               -- Discord user ID
    statement TEXT NOT NULL,             -- The belief itself
    confidence REAL DEFAULT 0.5,         -- 0.0 - 1.0
    importance INTEGER DEFAULT 3,        -- 1-5 scale (1=peripheral, 5=core)
    source_type TEXT,                    -- experience | reasoning | authority | intuition | inherited
    context TEXT,                        -- What prompted this belief to surface
    first_expressed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_referenced TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    message_id TEXT,                     -- Discord message ID where first expressed
    channel_id TEXT,                     -- Discord channel ID
    is_deleted INTEGER DEFAULT 0,        -- Soft delete for /forget
    visibility TEXT DEFAULT 'shareable', -- public | shareable | private | hidden
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- Topics/tags for beliefs (many-to-many)
CREATE TABLE IF NOT EXISTS belief_topics (
    belief_id TEXT NOT NULL,
    topic TEXT NOT NULL,
    PRIMARY KEY (belief_id, topic),
    FOREIGN KEY (belief_id) REFERENCES beliefs(id)
);

-- Relationships between beliefs
CREATE TABLE IF NOT EXISTS belief_relations (
    id TEXT PRIMARY KEY,
    source_id TEXT NOT NULL,             -- The belief making the connection
    target_id TEXT NOT NULL,             -- The belief being connected to
    relation_type TEXT NOT NULL,         -- supports | contradicts | assumes | derives_from | relates_to
    strength REAL DEFAULT 0.5,           -- How strong is this connection
    discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (source_id) REFERENCES beliefs(id),
    FOREIGN KEY (target_id) REFERENCES beliefs(id)
);

-- Track how beliefs evolve over time
CREATE TABLE IF NOT EXISTS belief_evolution (
    id TEXT PRIMARY KEY,
    belief_id TEXT NOT NULL,
    old_confidence REAL,
    new_confidence REAL,
    old_statement TEXT,
    new_statement TEXT,
    trigger TEXT,                        -- What caused the shift
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (belief_id) REFERENCES beliefs(id)
);

-- Conversation history for context
CREATE TABLE IF NOT EXISTS conversations (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    channel_id TEXT,
    message_id TEXT,
    role TEXT NOT NULL,                  -- user | assistant
    content TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_beliefs_user ON beliefs(user_id);
CREATE INDEX IF NOT EXISTS idx_beliefs_user_active ON beliefs(user_id, is_deleted);
CREATE INDEX IF NOT EXISTS idx_belief_topics_topic ON belief_topics(topic);
CREATE INDEX IF NOT EXISTS idx_relations_source ON belief_relations(source_id);
CREATE INDEX IF NOT EXISTS idx_relations_target ON belief_relations(target_id);
CREATE INDEX IF NOT EXISTS idx_conversations_user ON conversations(user_id);
