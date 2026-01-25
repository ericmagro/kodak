"""Onboarding flow for Kodak v2."""

import logging
import discord
from discord import ui
from typing import Callable, Awaitable, Optional

from personality import PRESETS, PRESET_ORDER, get_preset
from scheduler import parse_time_input, format_time_display

logger = logging.getLogger('kodak')


# ============================================
# ONBOARDING STATE
# ============================================

class OnboardingState:
    """Track onboarding progress for a user."""

    def __init__(self, user_id: str):
        self.user_id = user_id
        self.selected_personality: Optional[str] = None
        self.selected_time: Optional[str] = None
        self.preview_index: int = 0  # Which personality they're previewing


# In-memory onboarding state
_onboarding_states: dict[str, OnboardingState] = {}


def get_onboarding_state(user_id: str) -> OnboardingState:
    """Get or create onboarding state for a user."""
    if user_id not in _onboarding_states:
        _onboarding_states[user_id] = OnboardingState(user_id)
    return _onboarding_states[user_id]


def clear_onboarding_state(user_id: str):
    """Clear onboarding state after completion."""
    _onboarding_states.pop(user_id, None)


# ============================================
# ONBOARDING VIEWS (Discord UI)
# ============================================

class PersonalitySelectView(ui.View):
    """Initial personality selection with buttons."""

    def __init__(self, user_id: str, on_select: Callable[[str, str], Awaitable[None]]):
        super().__init__(timeout=300)  # 5 minute timeout
        self.user_id = user_id
        self.on_select = on_select

        # Add a button for each personality
        for key in PRESET_ORDER:
            preset = PRESETS[key]
            button = ui.Button(
                label=preset.name,
                style=discord.ButtonStyle.secondary,
                custom_id=f"personality_{key}"
            )
            button.callback = self._make_callback(key)
            self.add_item(button)

    def _make_callback(self, preset_key: str):
        async def callback(interaction: discord.Interaction):
            if str(interaction.user.id) != self.user_id:
                await interaction.response.send_message(
                    "This isn't your onboarding flow!",
                    ephemeral=True
                )
                return
            await self.on_select(interaction, preset_key)
        return callback


class PersonalityPreviewView(ui.View):
    """Preview a personality with example exchange."""

    def __init__(
        self,
        user_id: str,
        preset_key: str,
        on_choose: Callable[[str], Awaitable[None]],
        on_see_another: Callable[[str], Awaitable[None]]
    ):
        super().__init__(timeout=300)
        self.user_id = user_id
        self.preset_key = preset_key
        self.on_choose = on_choose
        self.on_see_another = on_see_another

    @ui.button(label="Choose this one", style=discord.ButtonStyle.primary)
    async def choose_button(self, interaction: discord.Interaction, button: ui.Button):
        if str(interaction.user.id) != self.user_id:
            await interaction.response.send_message("This isn't your onboarding!", ephemeral=True)
            return
        await self.on_choose(interaction)

    @ui.button(label="See another", style=discord.ButtonStyle.secondary)
    async def another_button(self, interaction: discord.Interaction, button: ui.Button):
        if str(interaction.user.id) != self.user_id:
            await interaction.response.send_message("This isn't your onboarding!", ephemeral=True)
            return
        await self.on_see_another(interaction)


class TimeSelectView(ui.View):
    """Select check-in time with preset buttons."""

    def __init__(self, user_id: str, on_select: Callable[[str, str], Awaitable[None]]):
        super().__init__(timeout=300)
        self.user_id = user_id
        self.on_select = on_select

        # Preset time buttons
        for time in ["7pm", "8pm", "9pm", "10pm"]:
            button = ui.Button(
                label=time,
                style=discord.ButtonStyle.secondary,
                custom_id=f"time_{time}"
            )
            button.callback = self._make_callback(time)
            self.add_item(button)

        # Other time button (opens modal)
        other_button = ui.Button(
            label="Other time...",
            style=discord.ButtonStyle.secondary,
            custom_id="time_other"
        )
        other_button.callback = self._other_callback
        self.add_item(other_button)

    def _make_callback(self, time: str):
        async def callback(interaction: discord.Interaction):
            if str(interaction.user.id) != self.user_id:
                await interaction.response.send_message("This isn't your onboarding!", ephemeral=True)
                return
            parsed = parse_time_input(time)
            await self.on_select(interaction, parsed)
        return callback

    async def _other_callback(self, interaction: discord.Interaction):
        if str(interaction.user.id) != self.user_id:
            await interaction.response.send_message("This isn't your onboarding!", ephemeral=True)
            return
        await interaction.response.send_modal(TimeInputModal(self.user_id, self.on_select))


class TimeInputModal(ui.Modal, title="Set Check-in Time"):
    """Modal for entering custom time."""

    time_input = ui.TextInput(
        label="What time? (e.g., 8:30pm, 20:00)",
        placeholder="8pm",
        required=True,
        max_length=10
    )

    def __init__(self, user_id: str, on_select: Callable[[str, str], Awaitable[None]]):
        super().__init__()
        self.user_id = user_id
        self.on_select = on_select

    async def on_submit(self, interaction: discord.Interaction):
        parsed = parse_time_input(self.time_input.value)
        if not parsed:
            await interaction.response.send_message(
                f"Couldn't understand '{self.time_input.value}'. Try something like '8pm' or '20:00'.",
                ephemeral=True
            )
            return
        await self.on_select(interaction, parsed)


class SampleSessionView(ui.View):
    """Show a sample session to demonstrate what journaling looks like."""

    def __init__(self, user_id: str, on_continue: Callable):
        super().__init__(timeout=300)
        self.user_id = user_id
        self.on_continue = on_continue
        self.example_index = 0

    @ui.button(label="Got it! Let's set this up", style=discord.ButtonStyle.primary, emoji="👍")
    async def continue_button(self, interaction: discord.Interaction, button: ui.Button):
        if str(interaction.user.id) != self.user_id:
            await interaction.response.send_message("This isn't your onboarding!", ephemeral=True)
            return
        await self.on_continue(interaction)

    @ui.button(label="Show me another example", style=discord.ButtonStyle.secondary, emoji="🔄")
    async def another_example(self, interaction: discord.Interaction, button: ui.Button):
        if str(interaction.user.id) != self.user_id:
            await interaction.response.send_message("This isn't your onboarding!", ephemeral=True)
            return

        # Cycle through examples
        self.example_index = (self.example_index + 1) % 3
        sample_sessions = [
            self._get_work_stress_sample(),
            self._get_relationship_sample(),
            self._get_goals_sample()
        ]

        new_sample = sample_sessions[self.example_index]
        await interaction.response.edit_message(content=new_sample, view=self)

    def _get_work_stress_sample(self):
        return """**Here's what a typical session looks like:**

> **Kodak:** What's been sitting with you today?
>
> **You:** Work stuff. My manager announced a reorg and I might have to move teams. I'm not even sure I'm upset about it but I can't stop thinking about it.
>
> **Kodak:** What is it about the uncertainty that's hard to let go of?
>
> **You:** I think it's that I finally felt like I knew what I was doing. Now I might have to start over proving myself again.
>
> **Kodak:** That's interesting—it sounds less about the team and more about losing a sense of competence you'd built up. Is that fair?
>
> **You:** Yeah, actually. I hadn't thought of it that way.
>
> **Kodak:** Something worth remembering: *"I value feeling competent and established in my work"*
>
> Thanks for reflecting with me tonight.

Notice how I ask follow-up questions to understand what really matters to you, then capture insights that emerge naturally."""

    def _get_relationship_sample(self):
        return """**Here's what a typical session looks like:**

> **Kodak:** What's on your mind tonight?
>
> **You:** Had dinner with my sister. She's going through a rough divorce and I want to help but don't know how.
>
> **Kodak:** What feels hard about not knowing how to help?
>
> **You:** I hate seeing people I care about struggle when I could do something. Even if it's not really my problem to solve.
>
> **Kodak:** Sounds like you feel responsible for the wellbeing of people close to you. What drives that?
>
> **You:** I guess I've always been the one people come to. It feels wrong to just... not help.
>
> **Kodak:** Something worth remembering: *"I feel responsible for helping people I care about, even when it's not my problem to solve"*

See how the conversation reveals what matters to you through natural reflection, not surveys about your values."""

    def _get_goals_sample(self):
        return """**Here's what a typical session looks like:**

> **Kodak:** How was your day?
>
> **You:** Pretty good. Made progress on my side project for the first time in weeks.
>
> **Kodak:** What made today different?
>
> **You:** I finally just sat down and worked on it instead of overthinking the plan. Felt so good to actually build something.
>
> **Kodak:** What is it about building that feels good?
>
> **You:** I love that moment when an idea becomes real. Like, I can imagine something and then make it exist.
>
> **Kodak:** Something worth remembering: *"I'm energized by turning ideas into reality through building"*
>
> Sweet dreams, creator.

The patterns I notice become your theme profile over time—no personality tests needed, just honest conversation."""


class FirstSessionPromptView(ui.View):
    """Ask if user wants to start first session now."""

    def __init__(
        self,
        user_id: str,
        on_start_now: Callable[[], Awaitable[None]],
        on_wait: Callable[[], Awaitable[None]]
    ):
        super().__init__(timeout=300)
        self.user_id = user_id
        self.on_start_now = on_start_now
        self.on_wait = on_wait

    @ui.button(label="Let's go", style=discord.ButtonStyle.primary)
    async def start_button(self, interaction: discord.Interaction, button: ui.Button):
        if str(interaction.user.id) != self.user_id:
            await interaction.response.send_message("This isn't your onboarding!", ephemeral=True)
            return
        await interaction.response.defer()
        await self.on_start_now()

    @ui.button(label="I'll wait for the first prompt", style=discord.ButtonStyle.secondary)
    async def wait_button(self, interaction: discord.Interaction, button: ui.Button):
        if str(interaction.user.id) != self.user_id:
            await interaction.response.send_message("This isn't your onboarding!", ephemeral=True)
            return
        await interaction.response.defer()
        await self.on_wait()


# ============================================
# ONBOARDING FLOW ORCHESTRATION
# ============================================

class OnboardingFlow:
    """
    Manages the complete onboarding flow for a user.

    Usage:
        flow = OnboardingFlow(channel, user_id, on_complete_callback)
        await flow.start()
    """

    def __init__(
        self,
        channel: discord.DMChannel,
        user_id: str,
        on_complete: Callable[[str, str, bool], Awaitable[None]]
    ):
        """
        Initialize onboarding flow.

        Args:
            channel: The DM channel to send messages to
            user_id: The user's Discord ID
            on_complete: Callback when done (personality, time, start_now)
        """
        self.channel = channel
        self.user_id = user_id
        self.on_complete = on_complete
        self.state = get_onboarding_state(user_id)

    async def start(self):
        """Start the onboarding flow."""
        # Welcome message
        welcome = (
            "Hey! I'm Kodak.\n\n"
            "I'm a journaling companion. Each day at a time you choose, "
            "I'll check in with a prompt to help you reflect.\n\n"
            "Over time, I'll surface your core values and how they shift — "
            "you can even compare with friends to see how you align.\n\n"
            "Everything stays private on your device.\n\n"
            "**First — how would you like me to show up?**"
        )

        view = PersonalitySelectView(self.user_id, self._on_personality_select)
        await self.channel.send(welcome, view=view)

    async def _on_personality_select(self, interaction: discord.Interaction, preset_key: str):
        """Handle personality selection."""
        self.state.selected_personality = preset_key
        await self._show_personality_preview(interaction, preset_key)

    async def _show_personality_preview(self, interaction: discord.Interaction, preset_key: str):
        """Show preview of selected personality."""
        preset = get_preset(preset_key)
        if not preset:
            preset = PRESETS["best_friend"]

        user_msg, bot_response = preset.example_exchange

        preview = (
            f"**{preset.name}**\n"
            f"*{preset.journaling_style}*\n\n"
            f"**Example:**\n"
            f"> You: {user_msg}\n"
            f"> Kodak: {bot_response}"
        )

        view = PersonalityPreviewView(
            self.user_id,
            preset_key,
            on_choose=self._on_personality_confirmed,
            on_see_another=self._on_see_another
        )

        await interaction.response.edit_message(content=preview, view=view)

    async def _on_personality_confirmed(self, interaction: discord.Interaction):
        """Handle personality confirmation, show sample session before time selection."""
        await self._show_sample_session(interaction)

    async def _on_see_another(self, interaction: discord.Interaction):
        """Show next personality preview."""
        self.state.preview_index = (self.state.preview_index + 1) % len(PRESET_ORDER)
        next_key = PRESET_ORDER[self.state.preview_index]
        self.state.selected_personality = next_key
        await self._show_personality_preview(interaction, next_key)

    async def _show_sample_session(self, interaction: discord.Interaction):
        """Show a sample session to demonstrate what journaling looks like."""
        view = SampleSessionView(self.user_id, self._on_sample_session_continue)

        # Start with the work stress example
        sample_content = view._get_work_stress_sample()

        await interaction.response.edit_message(content=sample_content, view=view)

    async def _on_sample_session_continue(self, interaction: discord.Interaction):
        """Handle continuation from sample session to time selection."""
        await self._show_time_selection(interaction)

    async def _show_time_selection(self, interaction: discord.Interaction):
        """Show time selection UI."""
        message = (
            "**When should I check in?**\n\n"
            "Most people like evening — time to reflect on the day."
        )

        view = TimeSelectView(self.user_id, self._on_time_selected)
        await interaction.response.edit_message(content=message, view=view)

    async def _on_time_selected(self, interaction: discord.Interaction, time_24h: str):
        """Handle time selection, show final confirmation."""
        self.state.selected_time = time_24h
        display_time = format_time_display(time_24h)

        message = (
            f"**You're all set!**\n\n"
            f"I'll message you at **{display_time}** each day.\n\n"
            f"Or just message me anytime you want to reflect.\n\n"
            f"Ready for your first session?"
        )

        view = FirstSessionPromptView(
            self.user_id,
            on_start_now=self._on_start_now,
            on_wait=self._on_wait
        )

        await interaction.response.edit_message(content=message, view=view)

    async def _on_start_now(self):
        """User wants to start first session immediately."""
        personality = self.state.selected_personality or "best_friend"
        time = self.state.selected_time or "20:00"

        clear_onboarding_state(self.user_id)
        await self.on_complete(personality, time, True)

    async def _on_wait(self):
        """User wants to wait for scheduled prompt."""
        personality = self.state.selected_personality or "best_friend"
        time = self.state.selected_time or "20:00"
        display_time = format_time_display(time)

        await self.channel.send(
            f"Sounds good! I'll message you at **{display_time}**. Talk then!"
        )

        clear_onboarding_state(self.user_id)
        await self.on_complete(personality, time, False)


# ============================================
# QUICK ONBOARDING (Minimal Flow)
# ============================================

async def quick_onboard(
    channel: discord.DMChannel,
    user_id: str,
    personality: str = "best_friend",
    time: str = "20:00"
) -> tuple[str, str]:
    """
    Quick onboarding with defaults (for testing or returning users).

    Returns: (personality, time)
    """
    display_time = format_time_display(time)

    await channel.send(
        f"Welcome back! I've set you up with **The Best Friend** personality "
        f"and **{display_time}** check-ins.\n\n"
        f"Use `/setup` to change personality or `/schedule` to change time."
    )

    return (personality, time)
