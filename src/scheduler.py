"""Daily prompt scheduler for Kodak v2."""

import asyncio
import logging
import pytz
from datetime import datetime, timedelta
from typing import Callable, Awaitable, Optional

logger = logging.getLogger('kodak')


def get_user_local_time(user: dict) -> datetime:
    """Get the current time in the user's timezone."""
    tz_name = user.get('timezone') or 'UTC'
    try:
        tz = pytz.timezone(tz_name)
    except pytz.UnknownTimeZoneError:
        logger.warning(f"Unknown timezone '{tz_name}' for user {user.get('user_id')}, using UTC")
        tz = pytz.UTC
    return datetime.now(tz)


def is_prompt_time_for_user(user: dict) -> bool:
    """Check if it's currently the user's scheduled prompt time in their timezone."""
    prompt_time = user.get('prompt_time')
    if not prompt_time:
        return False

    user_now = get_user_local_time(user)
    current_time_str = user_now.strftime("%H:%M")
    return current_time_str == prompt_time


def is_too_late_for_user(user: dict) -> bool:
    """Check if it's too late (after 11pm) in the user's timezone."""
    user_now = get_user_local_time(user)
    return user_now.hour >= 23


class JournalScheduler:
    """
    Background scheduler for daily journal prompts.

    Runs as an asyncio task, checking every minute for users
    who should receive their daily prompt. Handles timezone-aware scheduling.
    """

    def __init__(
        self,
        get_users_eligible_for_prompt: Callable[[], Awaitable[list[dict]]],
        get_users_with_missed_prompts: Callable[[], Awaitable[list[dict]]],
        get_users_needing_reengagement: Callable[[int], Awaitable[list[dict]]],
        send_scheduled_prompt: Callable[[dict], Awaitable[None]],
        send_catch_up_prompt: Callable[[dict, int], Awaitable[None]],
        send_reengagement_prompt: Callable[[dict], Awaitable[None]],
        mark_prompt_sent: Callable[[str], Awaitable[None]],
        check_interval_seconds: int = 60
    ):
        """
        Initialize the scheduler.

        Args:
            get_users_eligible_for_prompt: Async function to get users who haven't been prompted today
            get_users_with_missed_prompts: Async function to get users who missed today's prompt
            get_users_needing_reengagement: Async function to get inactive users
            send_scheduled_prompt: Async function to send a scheduled prompt to a user
            send_catch_up_prompt: Async function to send a catch-up prompt (with hours_missed)
            send_reengagement_prompt: Async function to send re-engagement message
            mark_prompt_sent: Async function to mark that prompt was sent
            check_interval_seconds: How often to check (default 60 seconds)
        """
        self.get_users_eligible_for_prompt = get_users_eligible_for_prompt
        self.get_users_with_missed_prompts = get_users_with_missed_prompts
        self.get_users_needing_reengagement = get_users_needing_reengagement
        self.send_scheduled_prompt = send_scheduled_prompt
        self.send_catch_up_prompt = send_catch_up_prompt
        self.send_reengagement_prompt = send_reengagement_prompt
        self.mark_prompt_sent = mark_prompt_sent
        self.check_interval = check_interval_seconds

        self._task: Optional[asyncio.Task] = None
        self._running = False
        self._last_check_minute: Optional[int] = None  # Track by UTC minute to avoid duplicate checks
        self._startup_check_done = False
        self._last_reengagement_check: Optional[datetime] = None

    async def start(self):
        """Start the scheduler background task."""
        if self._running:
            logger.warning("Scheduler already running")
            return

        self._running = True
        self._task = asyncio.create_task(self._scheduler_loop())
        logger.info("Journal scheduler started")

    async def stop(self):
        """Stop the scheduler."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Journal scheduler stopped")

    async def _scheduler_loop(self):
        """Main scheduler loop."""
        while self._running:
            try:
                # On first run, check for missed prompts
                if not self._startup_check_done:
                    await self._check_missed_prompts()
                    await self._check_reengagement()
                    self._startup_check_done = True

                # Check for scheduled prompts
                await self._check_scheduled_prompts()

                # Periodic re-engagement check (once per day at 2pm)
                await self._periodic_reengagement_check()

            except Exception as e:
                logger.error(f"Scheduler error: {e}")

            await asyncio.sleep(self.check_interval)

    async def _periodic_reengagement_check(self):
        """Check for re-engagement periodically (daily at 2pm)."""
        now = datetime.now()

        # Only check at 2pm
        if now.hour != 14:
            return

        # Only check once per day
        if (self._last_reengagement_check and
            self._last_reengagement_check.date() == now.date()):
            return

        self._last_reengagement_check = now
        logger.info("Running periodic re-engagement check")
        await self._check_reengagement()

    async def _check_scheduled_prompts(self):
        """Check if any users are due for their scheduled prompt (timezone-aware)."""
        # Only check once per minute (use UTC minute to deduplicate)
        current_utc_minute = datetime.utcnow().minute
        if current_utc_minute == self._last_check_minute:
            return
        self._last_check_minute = current_utc_minute

        try:
            # Get all users eligible for a prompt today
            users = await self.get_users_eligible_for_prompt()

            for user in users:
                # Check if it's the right time in the user's timezone
                if not is_prompt_time_for_user(user):
                    continue

                try:
                    logger.info(f"Sending scheduled prompt to user:{user['user_id']} (tz: {user.get('timezone', 'UTC')})")
                    await self.send_scheduled_prompt(user)
                    await self.mark_prompt_sent(user['user_id'])
                except Exception as e:
                    logger.error(f"Failed to send prompt to {user['user_id']}: {e}")

        except Exception as e:
            logger.error(f"Error checking scheduled prompts: {e}")

    async def _check_missed_prompts(self):
        """Check for and handle missed prompts (called on startup). Timezone-aware."""
        try:
            users = await self.get_users_with_missed_prompts()

            for user in users:
                hours_since = self._hours_since_prompt_time(user)

                if hours_since is None:
                    continue

                # Within 4 hours: send catch-up
                if hours_since < 4:
                    try:
                        logger.info(f"Sending catch-up prompt to user:{user['user_id']} ({hours_since:.1f}h late)")
                        await self.send_catch_up_prompt(user, int(hours_since))
                        await self.mark_prompt_sent(user['user_id'])
                    except Exception as e:
                        logger.error(f"Failed to send catch-up to {user['user_id']}: {e}")

                # 4-12 hours and not too late in user's timezone: gentle catch-up
                elif hours_since < 12 and not is_too_late_for_user(user):
                    try:
                        logger.info(f"Sending gentle catch-up to user:{user['user_id']} ({hours_since:.1f}h late)")
                        await self.send_catch_up_prompt(user, int(hours_since))
                        await self.mark_prompt_sent(user['user_id'])
                    except Exception as e:
                        logger.error(f"Failed to send gentle catch-up to {user['user_id']}: {e}")

                # Otherwise: skip, wait for tomorrow
                else:
                    logger.info(f"Skipping missed prompt for user:{user['user_id']} ({hours_since:.1f}h late, too late)")

        except Exception as e:
            logger.error(f"Error checking missed prompts: {e}")

    async def _check_reengagement(self):
        """Check for users needing re-engagement."""
        try:
            users = await self.get_users_needing_reengagement(14)  # 2 weeks

            for user in users:
                try:
                    logger.info(f"Sending re-engagement to user:{user['user_id']}")
                    await self.send_reengagement_prompt(user)
                except Exception as e:
                    logger.error(f"Failed to send re-engagement to {user['user_id']}: {e}")

        except Exception as e:
            logger.error(f"Error checking re-engagement: {e}")

    def _hours_since_prompt_time(self, user: dict) -> Optional[float]:
        """Calculate hours since the user's scheduled prompt time today (timezone-aware)."""
        prompt_time = user.get('prompt_time')
        if not prompt_time:
            return None

        try:
            hour, minute = map(int, prompt_time.split(':'))
            user_now = get_user_local_time(user)
            scheduled = user_now.replace(hour=hour, minute=minute, second=0, microsecond=0)

            # If scheduled time is in the future, it wasn't missed
            if scheduled > user_now:
                return None

            delta = user_now - scheduled
            return delta.total_seconds() / 3600

        except (ValueError, AttributeError):
            return None


# ============================================
# UTILITY FUNCTIONS
# ============================================

def parse_time_input(time_str: str) -> Optional[str]:
    """
    Parse user time input into 24-hour format.

    Accepts: "8pm", "8:00pm", "20:00", "8:00 PM", etc.
    Returns: "HH:MM" format or None if invalid
    """
    time_str = time_str.strip().lower().replace(' ', '')

    # Try parsing with am/pm
    for fmt in ['%I%p', '%I:%M%p', '%I:%M %p']:
        try:
            dt = datetime.strptime(time_str, fmt)
            return dt.strftime("%H:%M")
        except ValueError:
            continue

    # Try 24-hour format
    for fmt in ['%H:%M', '%H%M']:
        try:
            dt = datetime.strptime(time_str, fmt)
            return dt.strftime("%H:%M")
        except ValueError:
            continue

    # Try just hour
    try:
        hour = int(time_str.replace(':', ''))
        if 0 <= hour <= 23:
            return f"{hour:02d}:00"
    except ValueError:
        pass

    return None


def format_time_display(time_24h: str) -> str:
    """
    Format 24-hour time for display.

    "20:00" -> "8:00 PM"
    """
    try:
        dt = datetime.strptime(time_24h, "%H:%M")
        return dt.strftime("%-I:%M %p").lower()
    except ValueError:
        return time_24h
