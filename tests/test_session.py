"""Unit tests for session.py soft close logic."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pytest
from session import (
    has_continuation_signal,
    has_early_close_signal,
    get_ceiling,
    determine_next_stage,
    SessionState,
    SessionStage,
)


# ============================================
# has_continuation_signal() tests
# ============================================

class TestHasContinuationSignal:
    """Tests for detecting continuation signals in user messages."""

    @pytest.mark.parametrize("message", [
        "Also, I wanted to mention...",
        "Actually, there's one more thing",
        "That reminds me of something",
        "oh and another thing",
        "speaking of that...",
        "i forgot to say",
        "What do you think about X?",  # ends with ?
        "also I have a question",
        "One more thing I wanted to add",
        "ACTUALLY now that I think about it",  # case insensitive
    ])
    def test_returns_true_for_continuation_phrases(self, message):
        assert has_continuation_signal(message) is True

    @pytest.mark.parametrize("message", [
        "Normal response without signals",
        "Today was pretty good",
        "I went to the store",
        "Nothing much happened",
        "Just a regular day",
    ])
    def test_returns_false_for_normal_messages(self, message):
        assert has_continuation_signal(message) is False

    def test_question_mark_at_end_triggers_continuation(self):
        assert has_continuation_signal("How do you think I should handle this?") is True
        assert has_continuation_signal("Is that normal?") is True

    def test_question_mark_in_middle_does_not_trigger(self):
        # Question mark not at end
        assert has_continuation_signal("I wondered? But then I stopped.") is False


# ============================================
# has_early_close_signal() tests
# ============================================

class TestHasEarlyCloseSignal:
    """Tests for detecting early close signals in user messages."""

    @pytest.mark.parametrize("message", [
        "I'm tired",
        "im tired",
        "gotta go",
        "need to sleep",
        "good night",
        "goodnight",
        "heading to bed",
        "that's all",
        "i'm done",
        "let's wrap up",
        "call it a night",
        "going to bed now",
        "I'm good",
        "im good",
        "that's it",
        "thats it for me",
    ])
    def test_returns_true_for_close_phrases(self, message):
        assert has_early_close_signal(message) is True

    @pytest.mark.parametrize("message", [
        "Normal message",
        "I had a good day",
        "The meeting went well",
        "I'm feeling better about things",
        "That was interesting",
    ])
    def test_returns_false_for_normal_messages(self, message):
        assert has_early_close_signal(message) is False

    def test_case_insensitivity(self):
        assert has_early_close_signal("GOOD NIGHT") is True
        assert has_early_close_signal("I'M DONE") is True
        assert has_early_close_signal("Gotta Go") is True


# ============================================
# get_ceiling() tests
# ============================================

class TestGetCeiling:
    """Tests for calculating session ceiling with extensions."""

    def _make_session(self, depth="standard", is_first=False, pre_close_count=0):
        """Helper to create session with specific settings."""
        session = SessionState(
            session_id="test",
            user_id="user",
            personality="best_friend",
            depth_setting=depth,
            is_first_session=is_first,
        )
        session.pre_close_count = pre_close_count
        return session

    def test_base_ceilings(self):
        assert get_ceiling(self._make_session(depth="quick")) == 3
        assert get_ceiling(self._make_session(depth="standard")) == 6
        assert get_ceiling(self._make_session(depth="deep")) == 10

    def test_first_session_caps_at_4(self):
        # First session caps at 4 regardless of depth setting
        assert get_ceiling(self._make_session(depth="standard", is_first=True)) == 4
        assert get_ceiling(self._make_session(depth="deep", is_first=True)) == 4
        # Quick is already under 4
        assert get_ceiling(self._make_session(depth="quick", is_first=True)) == 3

    def test_pre_close_extensions(self):
        # Each pre_close_count adds 3
        assert get_ceiling(self._make_session(depth="standard", pre_close_count=0)) == 6
        assert get_ceiling(self._make_session(depth="standard", pre_close_count=1)) == 9
        assert get_ceiling(self._make_session(depth="standard", pre_close_count=2)) == 12

    def test_hard_max_at_15(self):
        # Ceiling is capped at 15 regardless of extensions
        assert get_ceiling(self._make_session(depth="standard", pre_close_count=3)) == 15
        assert get_ceiling(self._make_session(depth="standard", pre_close_count=4)) == 15
        assert get_ceiling(self._make_session(depth="deep", pre_close_count=5)) == 15

    def test_unknown_depth_defaults_to_6(self):
        assert get_ceiling(self._make_session(depth="unknown")) == 6


# ============================================
# determine_next_stage() tests
# ============================================

class TestDetermineNextStage:
    """Tests for session stage transitions including PRE_CLOSE."""

    def _make_session(
        self,
        stage=SessionStage.PROBE,
        depth_setting="standard",
        exchanges=0,
        response_depth="medium",
        is_first=False,
        pre_close_count=0,
    ):
        """Helper to create session with specific state."""
        session = SessionState(
            session_id="test",
            user_id="user",
            personality="best_friend",
            depth_setting=depth_setting,
            is_first_session=is_first,
        )
        session.stage = stage
        session.exchange_count = exchanges
        session.last_response_depth = response_depth
        session.pre_close_count = pre_close_count
        return session

    # --- Entering PRE_CLOSE ---

    def test_probe_at_ceiling_enters_pre_close(self):
        session = self._make_session(stage=SessionStage.PROBE, exchanges=6, depth_setting="standard")
        assert determine_next_stage(session) == SessionStage.PRE_CLOSE

    def test_probe_at_quick_ceiling_enters_pre_close(self):
        session = self._make_session(stage=SessionStage.PROBE, exchanges=3, depth_setting="quick")
        assert determine_next_stage(session) == SessionStage.PRE_CLOSE

    def test_connect_at_ceiling_enters_pre_close(self):
        session = self._make_session(stage=SessionStage.CONNECT, exchanges=6, depth_setting="standard")
        assert determine_next_stage(session) == SessionStage.PRE_CLOSE

    # --- PRE_CLOSE → CLOSE (short response) ---

    def test_pre_close_with_short_response_closes(self):
        session = self._make_session(stage=SessionStage.PRE_CLOSE, exchanges=6, response_depth="short")
        assert determine_next_stage(session) == SessionStage.CLOSE

    def test_pre_close_with_minimal_response_closes(self):
        session = self._make_session(stage=SessionStage.PRE_CLOSE, exchanges=6, response_depth="minimal")
        assert determine_next_stage(session) == SessionStage.CLOSE

    def test_pre_close_with_early_close_signal_closes(self):
        session = self._make_session(stage=SessionStage.PRE_CLOSE, exchanges=6, response_depth="medium")
        assert determine_next_stage(session, last_message="nope, I'm good") == SessionStage.CLOSE

    # --- PRE_CLOSE → PROBE (continuation) ---

    def test_pre_close_with_long_response_continues(self):
        session = self._make_session(stage=SessionStage.PRE_CLOSE, exchanges=6, response_depth="long")
        assert determine_next_stage(session) == SessionStage.PROBE

    def test_pre_close_with_medium_response_continues(self):
        session = self._make_session(stage=SessionStage.PRE_CLOSE, exchanges=6, response_depth="medium")
        assert determine_next_stage(session) == SessionStage.PROBE

    def test_pre_close_with_continuation_signal_continues(self):
        session = self._make_session(stage=SessionStage.PRE_CLOSE, exchanges=6, response_depth="short")
        # Continuation signal should override short response
        assert determine_next_stage(session, last_message="actually yes, one more thing") == SessionStage.PROBE

    # --- Hard ceiling ---

    def test_hard_ceiling_forces_close_from_pre_close(self):
        session = self._make_session(stage=SessionStage.PRE_CLOSE, exchanges=15, response_depth="long")
        assert determine_next_stage(session) == SessionStage.CLOSE

    def test_hard_ceiling_forces_close_from_probe(self):
        session = self._make_session(stage=SessionStage.PROBE, exchanges=15)
        assert determine_next_stage(session) == SessionStage.CLOSE

    # --- Normal stage progressions ---

    def test_opener_to_anchor(self):
        session = self._make_session(stage=SessionStage.OPENER, exchanges=1)
        assert determine_next_stage(session) == SessionStage.ANCHOR

    def test_anchor_to_probe(self):
        session = self._make_session(stage=SessionStage.ANCHOR, exchanges=2)
        assert determine_next_stage(session) == SessionStage.PROBE

    def test_probe_continues_under_ceiling(self):
        session = self._make_session(stage=SessionStage.PROBE, exchanges=3, depth_setting="standard")
        assert determine_next_stage(session) == SessionStage.PROBE

    # --- Early close for disengaged users ---

    def test_minimal_response_early_close(self):
        session = self._make_session(stage=SessionStage.PROBE, exchanges=2, response_depth="minimal")
        assert determine_next_stage(session) == SessionStage.PRE_CLOSE

    def test_short_response_early_close(self):
        session = self._make_session(stage=SessionStage.PROBE, exchanges=3, response_depth="short")
        assert determine_next_stage(session) == SessionStage.PRE_CLOSE
