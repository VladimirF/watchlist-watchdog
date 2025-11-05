"""Tests for notifications module."""

import pytest

from episode_owl.notifications import (
    format_episode_code,
    format_notification,
    format_show_update,
    format_multiple_notifications,
    parse_notification_line,
    format_show_list_entry,
    format_timeline_entry,
)
from episode_owl.tracker import Episode, ShowUpdate


def test_format_episode_code_standard():
    """Test formatting standard episode code."""
    episode = Episode(season=1, number=5, title="Test", airdate="2025-11-01")

    code = format_episode_code(episode)

    assert code == "S01E05"


def test_format_episode_code_large_numbers():
    """Test formatting episode code with large numbers."""
    episode = Episode(season=16, number=23, title="Test", airdate="2025-11-01")

    code = format_episode_code(episode)

    assert code == "S16E23"


def test_format_episode_code_absolute():
    """Test formatting episode code for absolute numbering."""
    episode = Episode(season=None, number=42, title="Test", airdate="2025-11-01")

    code = format_episode_code(episode)

    assert code == "E042"


def test_format_notification():
    """Test formatting notification line."""
    episode = Episode(season=1, number=5, title="The Test Episode", airdate="2025-11-01")

    line = format_notification("Breaking Bad", episode, "%Y-%m-%d")

    assert "Breaking Bad" in line
    assert "S01E05" in line
    assert "The Test Episode" in line
    assert "|" in line


def test_format_show_update():
    """Test formatting show update."""
    episode = Episode(season=2, number=10, title="Finale", airdate="2025-11-01")
    update = ShowUpdate(show_id=123, show_name="The Wire", episode=episode)

    line = format_show_update(update)

    assert "The Wire" in line
    assert "S02E10" in line
    assert "Finale" in line


def test_format_multiple_notifications():
    """Test formatting multiple notifications."""
    updates = [
        ShowUpdate(
            show_id=1,
            show_name="Show 1",
            episode=Episode(season=1, number=1, title="Pilot", airdate="2025-11-01")
        ),
        ShowUpdate(
            show_id=2,
            show_name="Show 2",
            episode=Episode(season=2, number=5, title="Episode 5", airdate="2025-11-02")
        ),
    ]

    lines = format_multiple_notifications(updates)

    assert len(lines) == 2
    assert "Show 1" in lines[0]
    assert "Show 2" in lines[1]


def test_parse_notification_line_valid():
    """Test parsing valid notification line."""
    line = "2025-11-05 | Breaking Bad | S05E16 | Felina"

    parsed = parse_notification_line(line)

    assert parsed is not None
    assert parsed["date"] == "2025-11-05"
    assert parsed["show_name"] == "Breaking Bad"
    assert parsed["episode_code"] == "S05E16"
    assert parsed["title"] == "Felina"


def test_parse_notification_line_invalid():
    """Test parsing invalid notification line."""
    line = "This is not a valid notification"

    parsed = parse_notification_line(line)

    assert parsed is None


def test_parse_notification_line_with_extra_pipes():
    """Test parsing notification line with pipes in title."""
    line = "2025-11-05 | Show | S01E01 | Title | With | Pipes"

    parsed = parse_notification_line(line)

    # Should fail because we expect exactly 4 parts
    assert parsed is None


def test_format_show_list_entry():
    """Test formatting show list entry."""
    show = {
        "name": "Breaking Bad",
        "last_checked": "2025-11-05T10:30:00",
        "last_seen_season": 5,
        "last_seen_episode": 16
    }

    formatted = format_show_list_entry(show)

    assert "Breaking Bad" in formatted
    assert "2025-11-05" in formatted
    assert "S05E16" in formatted


def test_format_show_list_entry_no_season():
    """Test formatting show list entry without season."""
    show = {
        "name": "One Piece",
        "last_checked": "2025-11-05T10:30:00",
        "last_seen_season": None,
        "last_seen_episode": 1100
    }

    formatted = format_show_list_entry(show)

    assert "One Piece" in formatted
    assert "E1100" in formatted


def test_format_show_list_entry_never_checked():
    """Test formatting show list entry that was never checked."""
    show = {
        "name": "New Show",
        "last_checked": "Never",
        "last_seen_season": None,
        "last_seen_episode": 0
    }

    formatted = format_show_list_entry(show)

    assert "New Show" in formatted
    assert "Never" in formatted


def test_format_timeline_entry():
    """Test formatting timeline entry."""
    line = "2025-11-05 | Breaking Bad | S05E16 | Felina"

    formatted = format_timeline_entry(line)

    assert "[2025-11-05]" in formatted
    assert "Breaking Bad" in formatted
    assert "S05E16" in formatted
    assert "Felina" in formatted


def test_format_timeline_entry_invalid():
    """Test formatting invalid timeline entry."""
    line = "Invalid line"

    formatted = format_timeline_entry(line)

    # Should return original line
    assert formatted == line
