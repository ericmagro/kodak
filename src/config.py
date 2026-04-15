"""Centralized configuration for Kodak.

All environment-driven settings live here. To change a setting in production,
update the env var in Railway and restart — no code change needed.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# LLM
# When Anthropic deprecates a model, update MODEL here. That's the only place.
# Model deprecation schedule: https://docs.anthropic.com/en/docs/about-claude/model-deprecations
MODEL = "claude-sonnet-4-6"
LLM_TIMEOUT = 30.0

# Discord
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

# Database
_default_db_path = Path(__file__).parent.parent / "kodak.db"
DB_PATH = Path(os.getenv("KODAK_DB_PATH", str(_default_db_path)))

# Logging
LOG_LEVEL = os.getenv("KODAK_LOG_LEVEL", "INFO")
JSON_LOGS = os.getenv("KODAK_JSON_LOGS", "false").lower() == "true"

# Health server
HEALTH_PORT = int(os.getenv("PORT", "8080"))
