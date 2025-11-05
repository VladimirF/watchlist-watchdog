"""Desktop notification system for Episode Owl."""

import sys
import logging
from pathlib import Path
from typing import List

from .tracker import ShowUpdate


# Set up logging
logger = logging.getLogger(__name__)


def send_desktop_notification(
    updates: List[ShowUpdate],
    notifications_file: Path,
    enable_sound: bool = False
) -> None:
    """Send desktop notification about new episodes.

    Args:
        updates: List of show updates to notify about
        notifications_file: Path to notifications file (for click action)
        enable_sound: Whether to play notification sound

    Note:
        This function will not raise exceptions - it logs warnings if
        notification system is unavailable.
    """
    if not updates:
        _send_no_updates_notification(enable_sound)
        return

    # Format notification message
    count = len(updates)
    title = f"🦉 {count} new episode{'s' if count != 1 else ''} found!"

    # Show top 3 shows
    show_names = list(dict.fromkeys(update.show_name for update in updates))
    top_shows = show_names[:3]

    if len(show_names) > 3:
        message = "\n".join(top_shows) + f"\n... and {len(show_names) - 3} more"
    else:
        message = "\n".join(top_shows)

    _send_notification(title, message, str(notifications_file), enable_sound)


def _send_no_updates_notification(enable_sound: bool = False) -> None:
    """Send notification when no new episodes found.

    Args:
        enable_sound: Whether to play notification sound
    """
    title = "Episode Owl"
    message = "No new episodes found"
    _send_notification(title, message, "", enable_sound, duration=3)


def _send_notification(
    title: str,
    message: str,
    callback_path: str = "",
    enable_sound: bool = False,
    duration: int = 10
) -> None:
    """Send desktop notification using available backend.

    Args:
        title: Notification title
        message: Notification message
        callback_path: File path to open on click (Windows only)
        enable_sound: Whether to play notification sound
        duration: How long to show notification (seconds)
    """
    try:
        # Try Windows toast first (better experience with click support)
        if sys.platform == "win32":
            try:
                _send_windows_toast(title, message, callback_path, duration)
                return
            except ImportError:
                logger.debug("win10toast-click not available, falling back to plyer")
            except Exception as e:
                logger.warning(f"Windows toast notification failed: {e}")

        # Fall back to plyer for cross-platform support
        try:
            _send_plyer_notification(title, message, duration)
            return
        except ImportError:
            logger.warning("Neither win10toast-click nor plyer available for notifications")
        except Exception as e:
            logger.warning(f"Plyer notification failed: {e}")

    except Exception as e:
        # Catch-all to ensure notification failures don't crash the app
        logger.warning(f"Desktop notification failed: {e}")


def _send_windows_toast(
    title: str,
    message: str,
    callback_path: str,
    duration: int
) -> None:
    """Send Windows toast notification with click support.

    Args:
        title: Notification title
        message: Notification message
        callback_path: File path to open on click
        duration: How long to show notification (seconds)

    Raises:
        ImportError: If win10toast-click is not installed
    """
    from win10toast_click import ToastNotifier

    toaster = ToastNotifier()

    # Set up click callback to open file
    def on_click():
        if callback_path:
            try:
                import os
                os.startfile(callback_path)
            except Exception as e:
                logger.warning(f"Failed to open file on click: {e}")

    # Show toast (non-blocking, with timeout)
    try:
        if callback_path:
            toaster.show_toast(
                title,
                message,
                duration=duration,
                threaded=True,
                callback_on_click=on_click
            )
        else:
            toaster.show_toast(
                title,
                message,
                duration=duration,
                threaded=True
            )
    except Exception as e:
        logger.warning(f"Toast notification display failed: {e}")


def _send_plyer_notification(title: str, message: str, duration: int) -> None:
    """Send cross-platform notification using plyer.

    Args:
        title: Notification title
        message: Notification message
        duration: How long to show notification (seconds)

    Raises:
        ImportError: If plyer is not installed
    """
    from plyer import notification

    notification.notify(
        title=title,
        message=message,
        app_name="Episode Owl",
        timeout=duration
    )


def is_notification_supported() -> bool:
    """Check if desktop notifications are supported on this system.

    Returns:
        True if notifications can be sent, False otherwise
    """
    try:
        if sys.platform == "win32":
            try:
                import win10toast_click
                return True
            except ImportError:
                pass

        try:
            import plyer
            return True
        except ImportError:
            pass

        return False
    except Exception:
        return False
