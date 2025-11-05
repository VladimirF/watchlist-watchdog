"""Tests for storage module."""

import json
from pathlib import Path

import pytest

from episode_owl.storage import (
    StorageError,
    load_shows,
    save_shows,
    add_show,
    remove_show,
    update_show,
    load_notifications,
    append_notifications,
    prune_notifications,
)


def test_load_shows_nonexistent(tmp_path):
    """Test loading shows when file doesn't exist."""
    shows_path = tmp_path / "shows.json"

    shows = load_shows(shows_path)

    assert shows == []


def test_save_and_load_shows(tmp_path):
    """Test saving and loading shows."""
    shows_path = tmp_path / "shows.json"

    shows_data = [
        {"id": 1, "name": "Show 1"},
        {"id": 2, "name": "Show 2"},
    ]

    save_shows(shows_data, shows_path)

    assert shows_path.exists()

    loaded = load_shows(shows_path)

    assert len(loaded) == 2
    assert loaded[0]["name"] == "Show 1"
    assert loaded[1]["name"] == "Show 2"


def test_save_shows_creates_directory(tmp_path):
    """Test that save_shows creates parent directories."""
    shows_path = tmp_path / "nested" / "dir" / "shows.json"

    shows_data = [{"id": 1, "name": "Test"}]

    save_shows(shows_data, shows_path)

    assert shows_path.exists()


def test_save_shows_creates_backup(tmp_path):
    """Test that save_shows creates backup of existing file."""
    shows_path = tmp_path / "shows.json"

    # Create initial file
    shows_data = [{"id": 1, "name": "Original"}]
    save_shows(shows_data, shows_path)

    # Update file
    new_data = [{"id": 2, "name": "Updated"}]
    save_shows(new_data, shows_path)

    # Backup should exist
    backup_path = shows_path.with_suffix('.json.bak')
    assert backup_path.exists()

    # Backup should have original data
    with open(backup_path) as f:
        backup_data = json.load(f)
    assert backup_data["shows"][0]["name"] == "Original"


def test_load_shows_invalid_json(tmp_path):
    """Test loading shows with invalid JSON."""
    shows_path = tmp_path / "shows.json"
    shows_path.write_text("{ invalid json }")

    with pytest.raises(StorageError):
        load_shows(shows_path)


def test_add_show(tmp_path):
    """Test adding a show."""
    shows_path = tmp_path / "shows.json"

    show = {"id": 123, "name": "Breaking Bad"}

    add_show(show, shows_path)

    shows = load_shows(shows_path)
    assert len(shows) == 1
    assert shows[0]["id"] == 123


def test_add_show_duplicate(tmp_path):
    """Test adding duplicate show raises error."""
    shows_path = tmp_path / "shows.json"

    show = {"id": 123, "name": "Breaking Bad"}

    add_show(show, shows_path)

    with pytest.raises(StorageError):
        add_show(show, shows_path)


def test_remove_show(tmp_path):
    """Test removing a show."""
    shows_path = tmp_path / "shows.json"

    shows_data = [
        {"id": 1, "name": "Show 1"},
        {"id": 2, "name": "Show 2"},
    ]

    save_shows(shows_data, shows_path)

    result = remove_show(1, shows_path)

    assert result is True

    shows = load_shows(shows_path)
    assert len(shows) == 1
    assert shows[0]["id"] == 2


def test_remove_show_nonexistent(tmp_path):
    """Test removing nonexistent show."""
    shows_path = tmp_path / "shows.json"

    shows_data = [{"id": 1, "name": "Show 1"}]
    save_shows(shows_data, shows_path)

    result = remove_show(999, shows_path)

    assert result is False


def test_update_show(tmp_path):
    """Test updating a show."""
    shows_path = tmp_path / "shows.json"

    shows_data = [
        {"id": 1, "name": "Show 1", "last_seen_episode": 5},
    ]

    save_shows(shows_data, shows_path)

    updates = {"last_seen_episode": 10, "last_seen_season": 2}

    result = update_show(1, updates, shows_path)

    assert result is True

    shows = load_shows(shows_path)
    assert shows[0]["last_seen_episode"] == 10
    assert shows[0]["last_seen_season"] == 2


def test_update_show_nonexistent(tmp_path):
    """Test updating nonexistent show."""
    shows_path = tmp_path / "shows.json"

    shows_data = [{"id": 1, "name": "Show 1"}]
    save_shows(shows_data, shows_path)

    result = update_show(999, {"name": "New Name"}, shows_path)

    assert result is False


def test_load_notifications_nonexistent(tmp_path):
    """Test loading notifications when file doesn't exist."""
    notif_path = tmp_path / "notifications.txt"

    notifications = load_notifications(notif_path)

    assert notifications == []


def test_load_notifications(tmp_path):
    """Test loading notifications."""
    notif_path = tmp_path / "notifications.txt"

    notif_path.write_text(
        "2025-11-05 | Show 1 | S01E01 | Pilot\n"
        "2025-11-04 | Show 2 | S02E05 | Episode 5\n"
        "\n"  # Empty line
        "2025-11-03 | Show 3 | S01E10 | Finale\n"
    )

    notifications = load_notifications(notif_path)

    assert len(notifications) == 3  # Empty lines are filtered
    assert "Show 1" in notifications[0]
    assert "Show 2" in notifications[1]


def test_load_notifications_with_limit(tmp_path):
    """Test loading notifications with limit."""
    notif_path = tmp_path / "notifications.txt"

    notif_path.write_text(
        "Line 1\n"
        "Line 2\n"
        "Line 3\n"
        "Line 4\n"
        "Line 5\n"
    )

    notifications = load_notifications(notif_path, limit=2)

    assert len(notifications) == 2
    assert notifications[0] == "Line 1"
    assert notifications[1] == "Line 2"


def test_append_notifications(tmp_path):
    """Test appending notifications."""
    notif_path = tmp_path / "notifications.txt"

    # Create existing file
    notif_path.write_text("Old 1\nOld 2\n")

    new_notifications = ["New 1", "New 2"]

    append_notifications(new_notifications, notif_path)

    notifications = load_notifications(notif_path)

    # New should be at the top
    assert len(notifications) == 4
    assert notifications[0] == "New 1"
    assert notifications[1] == "New 2"
    assert notifications[2] == "Old 1"
    assert notifications[3] == "Old 2"


def test_append_notifications_empty(tmp_path):
    """Test appending empty list does nothing."""
    notif_path = tmp_path / "notifications.txt"

    append_notifications([], notif_path)

    # File should not be created
    assert not notif_path.exists()


def test_append_notifications_new_file(tmp_path):
    """Test appending to new file."""
    notif_path = tmp_path / "notifications.txt"

    new_notifications = ["First", "Second"]

    append_notifications(new_notifications, notif_path)

    notifications = load_notifications(notif_path)

    assert len(notifications) == 2
    assert notifications[0] == "First"


def test_prune_notifications(tmp_path):
    """Test pruning old notifications."""
    notif_path = tmp_path / "notifications.txt"

    # Create file with 10 notifications
    lines = [f"Notification {i}" for i in range(10)]
    notif_path.write_text("\n".join(lines))

    removed = prune_notifications(notif_path, keep=5)

    assert removed == 5

    notifications = load_notifications(notif_path)
    assert len(notifications) == 5
    assert notifications[0] == "Notification 0"  # Newest
    assert notifications[4] == "Notification 4"


def test_prune_notifications_under_limit(tmp_path):
    """Test pruning when under limit."""
    notif_path = tmp_path / "notifications.txt"

    lines = ["Line 1", "Line 2"]
    notif_path.write_text("\n".join(lines))

    removed = prune_notifications(notif_path, keep=10)

    assert removed == 0

    notifications = load_notifications(notif_path)
    assert len(notifications) == 2
