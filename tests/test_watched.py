"""Tests for watched module."""

from pathlib import Path

import pytest

from episode_owl.watched import (
    NotificationKey,
    WatchedState,
    filter_unwatched_notifications,
    parse_notification_indices,
)


def test_notification_key_to_string():
    """Test converting notification key to string."""
    key = NotificationKey("2025-11-05", "Breaking Bad", "S05E16")

    assert key.to_string() == "2025-11-05|Breaking Bad|S05E16"


def test_notification_key_from_string():
    """Test parsing notification key from string."""
    key_str = "2025-11-05|Breaking Bad|S05E16"

    key = NotificationKey.from_string(key_str)

    assert key.date == "2025-11-05"
    assert key.show_name == "Breaking Bad"
    assert key.episode_code == "S05E16"


def test_notification_key_from_string_invalid():
    """Test parsing invalid notification key raises error."""
    with pytest.raises(ValueError):
        NotificationKey.from_string("invalid")


def test_notification_key_from_notification_line():
    """Test parsing notification key from notification line."""
    line = "2025-11-05 | Breaking Bad | S05E16 | Felina"

    key = NotificationKey.from_notification_line(line)

    assert key.date == "2025-11-05"
    assert key.show_name == "Breaking Bad"
    assert key.episode_code == "S05E16"


def test_notification_key_from_notification_line_invalid():
    """Test parsing invalid notification line raises error."""
    with pytest.raises(ValueError):
        NotificationKey.from_notification_line("invalid line")


def test_watched_state_initialization(tmp_path):
    """Test creating watched state."""
    watched_file = tmp_path / "watched.json"

    state = WatchedState(watched_file)

    assert state.file_path == watched_file
    assert len(state.watched_keys) == 0


def test_watched_state_mark_watched(tmp_path):
    """Test marking notifications as watched."""
    watched_file = tmp_path / "watched.json"
    state = WatchedState(watched_file)

    keys = [
        NotificationKey("2025-11-05", "Show 1", "S01E01"),
        NotificationKey("2025-11-05", "Show 2", "S01E02"),
    ]

    count = state.mark_watched(keys)

    assert count == 2
    assert state.is_watched(keys[0])
    assert state.is_watched(keys[1])


def test_watched_state_persistence(tmp_path):
    """Test watched state is persisted to file."""
    watched_file = tmp_path / "watched.json"

    # Create and mark some as watched
    state1 = WatchedState(watched_file)
    keys = [NotificationKey("2025-11-05", "Show 1", "S01E01")]
    state1.mark_watched(keys)

    # Load in new instance
    state2 = WatchedState(watched_file)

    assert state2.is_watched(keys[0])


def test_watched_state_is_watched(tmp_path):
    """Test checking if notification is watched."""
    watched_file = tmp_path / "watched.json"
    state = WatchedState(watched_file)

    key1 = NotificationKey("2025-11-05", "Show 1", "S01E01")
    key2 = NotificationKey("2025-11-05", "Show 2", "S01E02")

    state.mark_watched([key1])

    assert state.is_watched(key1) is True
    assert state.is_watched(key2) is False


def test_watched_state_get_watched_count(tmp_path):
    """Test getting count of watched notifications."""
    watched_file = tmp_path / "watched.json"
    state = WatchedState(watched_file)

    assert state.get_watched_count() == 0

    keys = [
        NotificationKey("2025-11-05", "Show 1", "S01E01"),
        NotificationKey("2025-11-05", "Show 2", "S01E02"),
    ]
    state.mark_watched(keys)

    assert state.get_watched_count() == 2


def test_watched_state_archive_old_watched(tmp_path):
    """Test archiving old watched notifications."""
    watched_file = tmp_path / "watched.json"
    state = WatchedState(watched_file)

    keys = [
        NotificationKey("2025-10-01", "Old Show", "S01E01"),  # Old
        NotificationKey("2025-11-05", "New Show", "S01E01"),  # Recent
    ]
    state.mark_watched(keys)

    # Archive notifications older than 7 days
    archived = state.archive_old_watched(days=7)

    assert archived == 1
    assert state.get_watched_count() == 1
    assert state.is_watched(keys[1])  # Recent one still there


def test_watched_state_archive_zero_days(tmp_path):
    """Test archive with zero days does nothing."""
    watched_file = tmp_path / "watched.json"
    state = WatchedState(watched_file)

    keys = [NotificationKey("2025-10-01", "Show", "S01E01")]
    state.mark_watched(keys)

    archived = state.archive_old_watched(days=0)

    assert archived == 0
    assert state.get_watched_count() == 1


def test_filter_unwatched_notifications(tmp_path):
    """Test filtering unwatched notifications."""
    watched_file = tmp_path / "watched.json"
    state = WatchedState(watched_file)

    notifications = [
        "2025-11-05 | Show 1 | S01E01 | Episode 1",
        "2025-11-05 | Show 2 | S01E02 | Episode 2",
        "2025-11-05 | Show 3 | S01E03 | Episode 3",
    ]

    # Mark first one as watched
    key = NotificationKey.from_notification_line(notifications[0])
    state.mark_watched([key])

    unwatched = filter_unwatched_notifications(notifications, state)

    assert len(unwatched) == 2
    assert notifications[1] in unwatched
    assert notifications[2] in unwatched


def test_filter_unwatched_handles_invalid_lines(tmp_path):
    """Test filtering handles invalid notification lines."""
    watched_file = tmp_path / "watched.json"
    state = WatchedState(watched_file)

    notifications = [
        "2025-11-05 | Show 1 | S01E01 | Episode 1",
        "Invalid line format",
    ]

    unwatched = filter_unwatched_notifications(notifications, state)

    # Both should be included (invalid lines are kept)
    assert len(unwatched) == 2


def test_parse_notification_indices_single():
    """Test parsing single index."""
    indices = parse_notification_indices("3", 10)

    assert indices == [2]  # 0-based


def test_parse_notification_indices_multiple():
    """Test parsing multiple indices."""
    indices = parse_notification_indices("1,3,5", 10)

    assert indices == [0, 2, 4]


def test_parse_notification_indices_range():
    """Test parsing range."""
    indices = parse_notification_indices("2-4", 10)

    assert indices == [1, 2, 3]


def test_parse_notification_indices_mixed():
    """Test parsing mixed format."""
    indices = parse_notification_indices("1,3-5,7", 10)

    assert indices == [0, 2, 3, 4, 6]


def test_parse_notification_indices_all():
    """Test parsing 'all'."""
    indices = parse_notification_indices("all", 5)

    assert indices == [0, 1, 2, 3, 4]


def test_parse_notification_indices_none():
    """Test parsing 'none'."""
    indices = parse_notification_indices("none", 5)

    assert indices == []


def test_parse_notification_indices_empty():
    """Test parsing empty string."""
    indices = parse_notification_indices("", 5)

    assert indices == []


def test_parse_notification_indices_out_of_range():
    """Test parsing index out of range."""
    with pytest.raises(ValueError):
        parse_notification_indices("10", 5)


def test_parse_notification_indices_invalid_range():
    """Test parsing invalid range."""
    with pytest.raises(ValueError):
        parse_notification_indices("5-2", 10)


def test_parse_notification_indices_removes_duplicates():
    """Test parsing removes duplicates."""
    indices = parse_notification_indices("1,2,1,2", 10)

    assert indices == [0, 1]
