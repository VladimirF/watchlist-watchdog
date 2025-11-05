"""File I/O operations for persisting show and notification data."""

import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional


class StorageError(Exception):
    """Exception raised for storage-related errors."""
    pass


def load_shows(file_path: Path) -> list[dict]:
    """Load tracked shows from JSON file.

    Args:
        file_path: Path to shows.json file

    Returns:
        List of show dictionaries

    Raises:
        StorageError: If file cannot be read or parsed
    """
    if not file_path.exists():
        return []

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data.get("shows", [])
    except json.JSONDecodeError as e:
        raise StorageError(f"Invalid JSON in {file_path}: {e}")
    except IOError as e:
        raise StorageError(f"Cannot read file {file_path}: {e}")


def save_shows(shows: list[dict], file_path: Path) -> None:
    """Save tracked shows to JSON file with backup.

    Args:
        shows: List of show dictionaries
        file_path: Path to shows.json file

    Raises:
        StorageError: If file cannot be written
    """
    # Create backup if file exists
    if file_path.exists():
        backup_path = file_path.with_suffix('.json.bak')
        try:
            shutil.copy2(file_path, backup_path)
        except IOError:
            pass  # Backup is optional

    # Ensure directory exists
    file_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        # Write to temporary file first
        temp_path = file_path.with_suffix('.json.tmp')
        with open(temp_path, 'w', encoding='utf-8') as f:
            json.dump({"shows": shows}, f, indent=2)

        # Move temporary file to actual location
        temp_path.replace(file_path)

    except IOError as e:
        raise StorageError(f"Cannot write to file {file_path}: {e}")


def add_show(show: dict, file_path: Path) -> None:
    """Add a show to the tracked shows list.

    Args:
        show: Show dictionary with id, name, etc.
        file_path: Path to shows.json file

    Raises:
        StorageError: If file operations fail
    """
    shows = load_shows(file_path)

    # Check if show already exists
    if any(s["id"] == show["id"] for s in shows):
        raise StorageError(f"Show '{show['name']}' is already being tracked")

    shows.append(show)
    save_shows(shows, file_path)


def remove_show(show_id: int, file_path: Path) -> bool:
    """Remove a show from the tracked shows list.

    Args:
        show_id: TVMaze show ID
        file_path: Path to shows.json file

    Returns:
        True if show was removed, False if not found

    Raises:
        StorageError: If file operations fail
    """
    shows = load_shows(file_path)
    original_count = len(shows)

    shows = [s for s in shows if s["id"] != show_id]

    if len(shows) < original_count:
        save_shows(shows, file_path)
        return True

    return False


def update_show(show_id: int, updates: dict, file_path: Path) -> bool:
    """Update a show's information.

    Args:
        show_id: TVMaze show ID
        updates: Dictionary of fields to update
        file_path: Path to shows.json file

    Returns:
        True if show was updated, False if not found

    Raises:
        StorageError: If file operations fail
    """
    shows = load_shows(file_path)

    updated = False
    for show in shows:
        if show["id"] == show_id:
            show.update(updates)
            updated = True
            break

    if updated:
        save_shows(shows, file_path)

    return updated


def load_notifications(file_path: Path, limit: Optional[int] = None) -> list[str]:
    """Load notifications from text file.

    Args:
        file_path: Path to notifications.txt file
        limit: Maximum number of notifications to load (from top)

    Returns:
        List of notification lines
    """
    if not file_path.exists():
        return []

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = [line.strip() for line in f if line.strip()]

        if limit is not None:
            return lines[:limit]

        return lines

    except IOError as e:
        raise StorageError(f"Cannot read file {file_path}: {e}")


def append_notifications(notifications: list[str], file_path: Path) -> None:
    """Append new notifications to the top of the file.

    Args:
        notifications: List of notification lines to add
        file_path: Path to notifications.txt file

    Raises:
        StorageError: If file operations fail
    """
    if not notifications:
        return

    # Ensure directory exists
    file_path.parent.mkdir(parents=True, exist_ok=True)

    # Load existing notifications
    existing = load_notifications(file_path)

    # Combine new (at top) + existing
    all_notifications = notifications + existing

    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            for notification in all_notifications:
                f.write(notification + '\n')

    except IOError as e:
        raise StorageError(f"Cannot write to file {file_path}: {e}")


def prune_notifications(file_path: Path, keep: int) -> int:
    """Keep only the N most recent notifications.

    Args:
        file_path: Path to notifications.txt file
        keep: Number of notifications to keep

    Returns:
        Number of notifications removed

    Raises:
        StorageError: If file operations fail
    """
    notifications = load_notifications(file_path)
    original_count = len(notifications)

    if original_count <= keep:
        return 0

    # Keep only the first N lines (newest)
    notifications = notifications[:keep]

    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            for notification in notifications:
                f.write(notification + '\n')

        return original_count - keep

    except IOError as e:
        raise StorageError(f"Cannot write to file {file_path}: {e}")
