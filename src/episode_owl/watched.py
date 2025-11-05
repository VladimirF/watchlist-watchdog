"""Watched status tracking for notifications."""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Set, NamedTuple


class NotificationKey(NamedTuple):
    """Unique identifier for a notification.

    Attributes:
        date: Notification date (YYYY-MM-DD format)
        show_name: Show name
        episode_code: Episode code (S01E01 or E001 format)
    """
    date: str
    show_name: str
    episode_code: str

    def to_string(self) -> str:
        """Convert to string representation for storage.

        Returns:
            String in format "date|show_name|episode_code"
        """
        return f"{self.date}|{self.show_name}|{self.episode_code}"

    @staticmethod
    def from_string(key_str: str) -> 'NotificationKey':
        """Parse NotificationKey from string.

        Args:
            key_str: String in format "date|show_name|episode_code"

        Returns:
            NotificationKey object

        Raises:
            ValueError: If string format is invalid
        """
        parts = key_str.split('|')
        if len(parts) != 3:
            raise ValueError(f"Invalid notification key format: {key_str}")

        return NotificationKey(date=parts[0], show_name=parts[1], episode_code=parts[2])

    @staticmethod
    def from_notification_line(line: str) -> 'NotificationKey':
        """Parse NotificationKey from notification line.

        Args:
            line: Notification line in format "date | show | episode | title"

        Returns:
            NotificationKey object

        Raises:
            ValueError: If line format is invalid
        """
        parts = [p.strip() for p in line.split('|')]
        if len(parts) < 3:
            raise ValueError(f"Invalid notification line format: {line}")

        return NotificationKey(date=parts[0], show_name=parts[1], episode_code=parts[2])


class WatchedState:
    """Manages watched status for notifications.

    Attributes:
        watched_keys: Set of watched notification keys
        file_path: Path to watched.json file
    """

    def __init__(self, file_path: Path):
        """Initialize watched state.

        Args:
            file_path: Path to watched.json file
        """
        self.file_path = file_path
        self.watched_keys: Set[str] = set()
        self._load()

    def _load(self) -> None:
        """Load watched state from file."""
        if not self.file_path.exists():
            return

        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self.watched_keys = set(data.get("watched", []))
        except (json.JSONDecodeError, IOError) as e:
            # If file is corrupted, start fresh
            print(f"Warning: Could not load watched state: {e}")
            self.watched_keys = set()

    def _save(self) -> None:
        """Save watched state to file."""
        self.file_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump({"watched": sorted(list(self.watched_keys))}, f, indent=2)
        except IOError as e:
            print(f"Warning: Could not save watched state: {e}")

    def mark_watched(self, keys: List[NotificationKey]) -> int:
        """Mark notifications as watched.

        Args:
            keys: List of notification keys to mark

        Returns:
            Number of notifications marked
        """
        initial_count = len(self.watched_keys)

        for key in keys:
            self.watched_keys.add(key.to_string())

        self._save()

        return len(self.watched_keys) - initial_count

    def is_watched(self, key: NotificationKey) -> bool:
        """Check if notification is watched.

        Args:
            key: Notification key to check

        Returns:
            True if notification is watched
        """
        return key.to_string() in self.watched_keys

    def get_watched_count(self) -> int:
        """Get count of watched notifications.

        Returns:
            Number of watched notifications
        """
        return len(self.watched_keys)

    def archive_old_watched(self, days: int = 30) -> int:
        """Remove watched notifications older than specified days.

        Args:
            days: Number of days to keep

        Returns:
            Number of notifications archived (removed)
        """
        if days <= 0:
            return 0

        cutoff_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        initial_count = len(self.watched_keys)

        # Filter out old watched notifications
        self.watched_keys = {
            key for key in self.watched_keys
            if self._extract_date_from_key(key) >= cutoff_date
        }

        if len(self.watched_keys) < initial_count:
            self._save()

        return initial_count - len(self.watched_keys)

    def _extract_date_from_key(self, key_str: str) -> str:
        """Extract date from notification key string.

        Args:
            key_str: Notification key string

        Returns:
            Date string (YYYY-MM-DD)
        """
        try:
            return key_str.split('|')[0]
        except IndexError:
            return "9999-12-31"  # Future date for invalid keys


def filter_unwatched_notifications(
    notifications: List[str],
    watched_state: WatchedState
) -> List[str]:
    """Filter notification list to only unwatched items.

    Args:
        notifications: List of notification lines
        watched_state: WatchedState object

    Returns:
        List of unwatched notification lines
    """
    unwatched = []

    for line in notifications:
        try:
            key = NotificationKey.from_notification_line(line)
            if not watched_state.is_watched(key):
                unwatched.append(line)
        except ValueError:
            # If we can't parse the line, include it anyway
            unwatched.append(line)

    return unwatched


def parse_notification_indices(
    input_str: str,
    max_index: int
) -> List[int]:
    """Parse user input for notification indices.

    Args:
        input_str: User input (e.g., "1,3,5", "all", "1-3")
        max_index: Maximum valid index

    Returns:
        List of zero-based indices

    Raises:
        ValueError: If input format is invalid
    """
    input_str = input_str.strip().lower()

    if not input_str or input_str == "none":
        return []

    if input_str == "all":
        return list(range(max_index))

    indices = []

    # Split by comma
    for part in input_str.split(','):
        part = part.strip()

        # Handle range (e.g., "1-3")
        if '-' in part:
            try:
                start, end = part.split('-', 1)
                start_idx = int(start.strip()) - 1  # Convert to 0-based
                end_idx = int(end.strip()) - 1

                if start_idx < 0 or end_idx >= max_index or start_idx > end_idx:
                    raise ValueError(f"Invalid range: {part}")

                indices.extend(range(start_idx, end_idx + 1))
            except ValueError as e:
                raise ValueError(f"Invalid range format: {part}") from e
        else:
            # Single number
            try:
                idx = int(part) - 1  # Convert to 0-based
                if idx < 0 or idx >= max_index:
                    raise ValueError(f"Index out of range: {part}")
                indices.append(idx)
            except ValueError as e:
                raise ValueError(f"Invalid number: {part}") from e

    # Remove duplicates and sort
    return sorted(list(set(indices)))
