-- Kodak v2.0 Schema
-- Reflective journaling companion with values framework

-- ============================================
-- USERS
-- ============================================

CREATE TABLE IF NOT EXISTS users (
    user_id TEXT PRIMARY KEY,
    username TEXT,

    -- Personality settings
    warmth INTEGER DEFAULT 3,
    directness INTEGER DEFAULT 3,
    playfulness INTEGER DEFAULT 3,
    formality INTEGER DEFAULT 3,
    personality_preset TEXT DEFAULT 'best_friend',

    -- Scheduling
    prompt_time TEXT,                              -- "20:00" (24hr format)
    timezone TEXT DEFAULT 'local',
    prompt_depth TEXT DEFAULT 'standard',          -- quick/standard/deep
    prompt_frequency TEXT DEFAULT 'daily',         -- daily/every_other/weekly
    last_prompt_sent TEXT,                         -- ISO timestamp
    last_prompt_responded INTEGER DEFAULT 1,       -- Did they respond to last prompt?
    prompts_ignored INTEGER DEFAULT 0,             -- Consecutive ignored prompts

    -- State
    onboarding_complete INTEGER DEFAULT 0,
    tracking_paused INTEGER DEFAULT 0,
    first_session_complete INTEGER DEFAULT 0,      -- For special first session handling
    last_active TEXT,                              -- Last interaction timestamp
    last_opener TEXT,                              -- Last opener used (avoid repeats)
    last_weekly_summary_prompt TEXT,               -- Last time prompted for weekly summary

    -- Metadata
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- JOURNAL SESSIONS
-- ============================================

CREATE TABLE IF NOT EXISTS journal_sessions (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,

    -- Timing
    started_at TEXT NOT NULL,
    ended_at TEXT,

    -- Session info
    prompt_type TEXT,                              -- 'scheduled', 'user_initiated', 'catch_up', 'first'
    session_stage TEXT DEFAULT 'opener',           -- opener/anchor/probe/connect/close/ended
    opener_used TEXT,                              -- Which opener was used (for rotation)

    -- Stats
    message_count INTEGER DEFAULT 0,
    beliefs_extracted INTEGER DEFAULT 0,

    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- ============================================
-- BELIEFS
-- ============================================

CREATE TABLE IF NOT EXISTS beliefs (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,

    -- Content
    statement TEXT NOT NULL,
    confidence REAL DEFAULT 0.5,                   -- 0.0 to 1.0
    source_type TEXT,                              -- experience/reasoning/authority/intuition/inherited
    context TEXT,                                  -- What prompted this belief

    -- Metadata
    importance INTEGER DEFAULT 3,                  -- 1-5 scale
    visibility TEXT DEFAULT 'shareable',           -- public/shareable/private/hidden
    is_deleted INTEGER DEFAULT 0,
    include_in_values INTEGER DEFAULT 1,           -- Whether to include in value derivation

    -- Source tracking
    session_id TEXT,                               -- Which journal session
    message_id TEXT,
    channel_id TEXT,

    -- Timestamps
    first_expressed TEXT DEFAULT CURRENT_TIMESTAMP,
    last_referenced TEXT DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (session_id) REFERENCES journal_sessions(id)
);

-- ============================================
-- BELIEF TOPICS
-- ============================================

CREATE TABLE IF NOT EXISTS belief_topics (
    belief_id TEXT NOT NULL,
    topic TEXT NOT NULL,
    PRIMARY KEY (belief_id, topic),
    FOREIGN KEY (belief_id) REFERENCES beliefs(id)
);

-- ============================================
-- BELIEF RELATIONS
-- ============================================

CREATE TABLE IF NOT EXISTS belief_relations (
    id TEXT PRIMARY KEY,
    source_id TEXT NOT NULL,
    target_id TEXT NOT NULL,
    relation_type TEXT NOT NULL,                   -- supports/contradicts/assumes/derives_from/relates_to
    strength REAL DEFAULT 0.5,
    discovered_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (source_id) REFERENCES beliefs(id),
    FOREIGN KEY (target_id) REFERENCES beliefs(id)
);

-- ============================================
-- BELIEF EVOLUTION
-- ============================================

CREATE TABLE IF NOT EXISTS belief_evolution (
    id TEXT PRIMARY KEY,
    belief_id TEXT NOT NULL,
    old_confidence REAL,
    new_confidence REAL,
    old_statement TEXT,
    new_statement TEXT,
    trigger TEXT,                                  -- What caused the change
    timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (belief_id) REFERENCES beliefs(id)
);

-- ============================================
-- VALUES FRAMEWORK (Schwartz)
-- ============================================

-- Belief-to-value mapping
CREATE TABLE IF NOT EXISTS belief_values (
    belief_id TEXT NOT NULL,
    value_name TEXT NOT NULL,                      -- achievement/benevolence/etc.
    weight REAL DEFAULT 1.0,                       -- primary=1.0, secondary=0.5
    mapping_confidence REAL DEFAULT 1.0,           -- How clearly this belief maps to this value
    PRIMARY KEY (belief_id, value_name),
    FOREIGN KEY (belief_id) REFERENCES beliefs(id)
);

-- Aggregated value scores per user
CREATE TABLE IF NOT EXISTS user_values (
    user_id TEXT NOT NULL,
    value_name TEXT NOT NULL,
    score REAL DEFAULT 0.0,                        -- Normalized 0.0 to 1.0
    raw_score REAL DEFAULT 0.0,                    -- Before normalization
    belief_count INTEGER DEFAULT 0,                -- How many beliefs contributed
    last_updated TEXT,
    PRIMARY KEY (user_id, value_name),
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- Value profile snapshots (for tracking change over time)
CREATE TABLE IF NOT EXISTS value_snapshots (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    snapshot_date TEXT NOT NULL,
    values_json TEXT NOT NULL,                     -- JSON: {"achievement": 0.7, "benevolence": 0.4, ...}
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);
-- Note: Consider retention policy for long-term (weekly -> monthly -> quarterly)

-- ============================================
-- CONVERSATIONS
-- ============================================

CREATE TABLE IF NOT EXISTS conversations (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    session_id TEXT,                               -- Link to journal session if applicable
    channel_id TEXT,
    message_id TEXT,
    role TEXT NOT NULL,                            -- 'user' or 'assistant'
    content TEXT NOT NULL,
    timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (session_id) REFERENCES journal_sessions(id)
);

-- ============================================
-- SUMMARIES (weekly, monthly, yearly)
-- ============================================

CREATE TABLE IF NOT EXISTS summaries (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,

    -- Period
    period_type TEXT NOT NULL,                     -- 'week', 'month', 'year'
    period_start TEXT NOT NULL,                    -- ISO date
    period_end TEXT NOT NULL,                      -- ISO date

    -- Raw data (for regeneration/analysis)
    data_json TEXT NOT NULL,                       -- Structured data: sessions, beliefs, topics, value changes

    -- Generated content
    narrative TEXT,                                -- The LLM-generated summary text
    highlights TEXT,                               -- Short punchy insights (JSON array)

    -- Metadata
    session_count INTEGER DEFAULT 0,
    belief_count INTEGER DEFAULT 0,
    generated_at TEXT DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- ============================================
-- SCHEMA VERSION (for migrations)
-- ============================================

CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER PRIMARY KEY,
    applied_at TEXT NOT NULL
);

-- Mark as v2 schema
INSERT OR IGNORE INTO schema_version (version, applied_at) VALUES (100, CURRENT_TIMESTAMP);
INSERT OR IGNORE INTO schema_version (version, applied_at) VALUES (101, CURRENT_TIMESTAMP);

-- ============================================
-- INDEXES
-- ============================================

CREATE INDEX IF NOT EXISTS idx_beliefs_user ON beliefs(user_id);
CREATE INDEX IF NOT EXISTS idx_beliefs_session ON beliefs(session_id);
CREATE INDEX IF NOT EXISTS idx_sessions_user ON journal_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_conversations_user ON conversations(user_id);
CREATE INDEX IF NOT EXISTS idx_conversations_session ON conversations(session_id);
CREATE INDEX IF NOT EXISTS idx_belief_values_belief ON belief_values(belief_id);
CREATE INDEX IF NOT EXISTS idx_belief_values_value ON belief_values(value_name);
CREATE INDEX IF NOT EXISTS idx_user_values_user ON user_values(user_id);
CREATE INDEX IF NOT EXISTS idx_value_snapshots_user ON value_snapshots(user_id);
CREATE INDEX IF NOT EXISTS idx_summaries_user ON summaries(user_id);
CREATE INDEX IF NOT EXISTS idx_summaries_period ON summaries(user_id, period_type, period_start);
