"""Notification formatting for episode updates."""

from datetime import datetime
from typing import NamedTuple

from .tracker import Episode, ShowUpdate


def format_episode_code(episode: Episode) -> str:
    """Format episode as SxxExx or Exx for absolute numbering.

    Args:
        episode: Episode object

    Returns:
        Formatted episode code
    """
    if episode.season is not None:
        return f"S{episode.season:02d}E{episode.number:02d}"
    else:
        # Use absolute numbering for shows without seasons
        return f"E{episode.number:03d}"


def format_notification(
    show_name: str,
    episode: Episode,
    date_format: str = "%Y-%m-%d"
) -> str:
    """Format a notification line for the timeline.

    Args:
        show_name: Name of the show
        episode: Episode information
        date_format: Format string for the date

    Returns:
        Formatted notification line
    """
    date_str = datetime.now().strftime(date_format)
    episode_code = format_episode_code(episode)
    title = episode.title

    return f"{date_str} | {show_name} | {episode_code} | {title}"


def format_show_update(update: ShowUpdate, date_format: str = "%Y-%m-%d") -> str:
    """Format a ShowUpdate as a notification line.

    Args:
        update: ShowUpdate object
        date_format: Format string for the date

    Returns:
        Formatted notification line
    """
    return format_notification(update.show_name, update.episode, date_format)


def format_multiple_notifications(
    updates: list[ShowUpdate],
    date_format: str = "%Y-%m-%d"
) -> list[str]:
    """Format multiple show updates as notification lines.

    Args:
        updates: List of ShowUpdate objects
        date_format: Format string for the date

    Returns:
        List of formatted notification lines
    """
    return [format_show_update(update, date_format) for update in updates]


def parse_notification_line(line: str) -> dict | None:
    """Parse a notification line back into components.

    Args:
        line: Notification line in timeline format

    Returns:
        Dictionary with date, show_name, episode_code, and title
        or None if line cannot be parsed
    """
    parts = [p.strip() for p in line.split('|')]

    if len(parts) != 4:
        return None

    return {
        "date": parts[0],
        "show_name": parts[1],
        "episode_code": parts[2],
        "title": parts[3]
    }


def format_show_list_entry(show: dict) -> str:
    """Format a tracked show for display in list.

    Args:
        show: Show dictionary from storage

    Returns:
        Formatted string for display
    """
    name = show.get("name", "Unknown")
    last_checked = show.get("last_checked", "Never")
    last_season = show.get("last_seen_season")
    last_episode = show.get("last_seen_episode", 0)

    # Format last checked date
    try:
        dt = datetime.fromisoformat(last_checked)
        checked_str = dt.strftime("%Y-%m-%d %H:%M")
    except (ValueError, TypeError):
        checked_str = "Never"

    # Format last episode
    if last_season is not None:
        episode_str = f"S{last_season:02d}E{last_episode:02d}"
    elif last_episode > 0:
        episode_str = f"E{last_episode:03d}"
    else:
        episode_str = "None"

    return f"{name}\n  Last checked: {checked_str}\n  Last episode: {episode_str}"


def format_timeline_entry(line: str) -> str:
    """Format a timeline entry for pretty display.

    Args:
        line: Raw notification line

    Returns:
        Formatted string for display
    """
    parsed = parse_notification_line(line)

    if not parsed:
        return line

    return f"[{parsed['date']}] {parsed['show_name']} - {parsed['episode_code']}: {parsed['title']}"
