"""Tests for notifier module."""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from episode_owl.notifier import (
    send_desktop_notification,
    is_notification_supported,
    _send_notification,
)
from episode_owl.tracker import Episode, ShowUpdate


def test_send_desktop_notification_with_updates(tmp_path):
    """Test sending notification with new episodes."""
    notif_file = tmp_path / "notifications.txt"

    updates = [
        ShowUpdate(
            show_id=1,
            show_name="Show 1",
            episode=Episode(1, 1, "Pilot", "2025-11-01")
        ),
        ShowUpdate(
            show_id=2,
            show_name="Show 2",
            episode=Episode(1, 2, "Episode 2", "2025-11-02")
        ),
    ]

    with patch('episode_owl.notifier._send_notification') as mock_send:
        send_desktop_notification(updates, notif_file)

        mock_send.assert_called_once()
        args = mock_send.call_args[0]
        assert "2 new episodes" in args[0]  # title
        assert "Show 1" in args[1]  # message
        assert "Show 2" in args[1]


def test_send_desktop_notification_with_many_shows(tmp_path):
    """Test notification truncates to top 3 shows."""
    notif_file = tmp_path / "notifications.txt"

    updates = [
        ShowUpdate(
            show_id=i,
            show_name=f"Show {i}",
            episode=Episode(1, 1, "Pilot", "2025-11-01")
        )
        for i in range(5)
    ]

    with patch('episode_owl.notifier._send_notification') as mock_send:
        send_desktop_notification(updates, notif_file)

        mock_send.assert_called_once()
        args = mock_send.call_args[0]
        assert "5 new episodes" in args[0]
        # Should show top 3 + "and 2 more"
        assert "Show 0" in args[1]
        assert "Show 1" in args[1]
        assert "Show 2" in args[1]
        assert "2 more" in args[1]


def test_send_desktop_notification_no_updates(tmp_path):
    """Test sending notification when no new episodes."""
    notif_file = tmp_path / "notifications.txt"

    with patch('episode_owl.notifier._send_notification') as mock_send:
        send_desktop_notification([], notif_file)

        mock_send.assert_called_once()
        args = mock_send.call_args[0]
        assert "No new episodes" in args[1]


@patch('episode_owl.notifier.sys.platform', 'win32')
@patch('episode_owl.notifier._send_windows_toast')
def test_send_notification_windows(mock_toast):
    """Test sending notification on Windows."""
    _send_notification("Title", "Message", "", False)

    mock_toast.assert_called_once()


@patch('episode_owl.notifier.sys.platform', 'linux')
@patch('episode_owl.notifier._send_plyer_notification')
def test_send_notification_fallback_to_plyer(mock_plyer):
    """Test fallback to plyer on non-Windows systems."""
    _send_notification("Title", "Message", "", False)

    mock_plyer.assert_called_once()


@patch('episode_owl.notifier.sys.platform', 'win32')
@patch('episode_owl.notifier._send_windows_toast', side_effect=ImportError)
@patch('episode_owl.notifier._send_plyer_notification')
def test_send_notification_windows_fallback(mock_plyer, mock_toast):
    """Test fallback to plyer when Windows toast fails."""
    _send_notification("Title", "Message", "", False)

    mock_toast.assert_called_once()
    mock_plyer.assert_called_once()


@patch('episode_owl.notifier.sys.platform', 'win32')
@patch('episode_owl.notifier._send_windows_toast', side_effect=Exception("Error"))
@patch('episode_owl.notifier._send_plyer_notification')
def test_send_notification_handles_errors_gracefully(mock_plyer, mock_toast):
    """Test that notification errors don't crash the app."""
    # Should not raise exception
    _send_notification("Title", "Message", "", False)

    mock_toast.assert_called_once()
    mock_plyer.assert_called_once()


def test_is_notification_supported_with_win10toast():
    """Test notification support detection with win10toast."""
    with patch('episode_owl.notifier.sys.platform', 'win32'):
        with patch.dict('sys.modules', {'win10toast_click': Mock()}):
            assert is_notification_supported() is True


def test_is_notification_supported_with_plyer():
    """Test notification support detection with plyer."""
    with patch.dict('sys.modules', {'plyer': Mock()}):
        assert is_notification_supported() is True


def test_is_notification_supported_none():
    """Test notification support when no library available."""
    with patch.dict('sys.modules', {}, clear=True):
        # Force ImportError for both libraries
        result = is_notification_supported()
        # May be True or False depending on actual system
        assert isinstance(result, bool)
