"""Smoke tests to catch import errors before deployment."""

import sys
import py_compile
from pathlib import Path

# Add src to path so we can import modules
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))


def test_all_python_files_compile():
    """Verify all Python files have valid syntax (no dependencies required)."""
    src_dir = Path(__file__).parent.parent / "src"

    python_files = list(src_dir.rglob("*.py"))
    assert len(python_files) > 0, "No Python files found in src/"

    for py_file in python_files:
        # py_compile.compile raises py_compile.PyCompileError on syntax errors
        py_compile.compile(str(py_file), doraise=True)


def test_all_modules_import():
    """Verify all source modules can be imported without errors.

    Requires dependencies to be installed (run in CI/deployment environment).
    """
    # Core modules
    import bot
    import client
    import db
    import extractor
    import session
    import scheduler
    import personality
    import prompts
    import values
    import summaries
    import onboarding
    import health_server
    import structured_logging

    # Command modules
    from commands import beliefs
    from commands import data
    from commands import help
    from commands import journal
    from commands import settings
    from commands import summaries as summaries_cmd
    from commands import themes

    # Handler modules
    from handlers import sessions
