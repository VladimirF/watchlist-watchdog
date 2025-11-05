"""Tests for utils module."""

import os
from pathlib import Path
from unittest.mock import Mock, patch, call

import pytest

from episode_owl.utils import (
    open_timeline_file,
    is_running_in_ci,
    should_auto_open,
)


def test_open_timeline_file_windows(tmp_path):
    """Test opening file on Windows."""
    timeline_file = tmp_path / "notifications.txt"
    timeline_file.write_text("test")

    with patch('episode_owl.utils.sys.platform', 'win32'):
        with patch('episode_owl.utils.os.startfile', create=True) as mock_startfile:
            result = open_timeline_file(timeline_file)

            assert result is True
            mock_startfile.assert_called_once_with(str(timeline_file))


@patch('episode_owl.utils.sys.platform', 'darwin')
@patch('episode_owl.utils.subprocess.Popen')
def test_open_timeline_file_macos(mock_popen, tmp_path):
    """Test opening file on macOS."""
    timeline_file = tmp_path / "notifications.txt"
    timeline_file.write_text("test")

    result = open_timeline_file(timeline_file)

    assert result is True
    mock_popen.assert_called_once_with(["open", str(timeline_file)])


@patch('episode_owl.utils.sys.platform', 'linux')
@patch('episode_owl.utils.subprocess.Popen')
def test_open_timeline_file_linux(mock_popen, tmp_path):
    """Test opening file on Linux."""
    timeline_file = tmp_path / "notifications.txt"
    timeline_file.write_text("test")

    result = open_timeline_file(timeline_file)

    assert result is True
    mock_popen.assert_called_once_with(["xdg-open", str(timeline_file)])


def test_open_timeline_file_creates_if_not_exists(tmp_path):
    """Test creating file if it doesn't exist."""
    timeline_file = tmp_path / "notifications.txt"

    with patch('episode_owl.utils.sys.platform', 'win32'):
        with patch('episode_owl.utils.os.startfile', create=True) as mock_startfile:
            result = open_timeline_file(timeline_file)

            assert result is True
            assert timeline_file.exists()
            mock_startfile.assert_called_once()


def test_open_timeline_file_windows_fallback_to_notepad(tmp_path):
    """Test fallback to notepad when os.startfile fails."""
    timeline_file = tmp_path / "notifications.txt"
    timeline_file.write_text("test")

    with patch('episode_owl.utils.sys.platform', 'win32'):
        with patch('episode_owl.utils.os.startfile', create=True, side_effect=OSError("Error")):
            with patch('episode_owl.utils.subprocess.Popen') as mock_popen:
                result = open_timeline_file(timeline_file)

                assert result is True
                mock_popen.assert_called_once_with(["notepad.exe", str(timeline_file)])


def test_open_timeline_file_handles_errors_gracefully(tmp_path):
    """Test that errors are handled gracefully."""
    timeline_file = tmp_path / "notifications.txt"
    timeline_file.write_text("test")

    with patch('episode_owl.utils.sys.platform', 'win32'):
        with patch('episode_owl.utils.os.startfile', create=True, side_effect=Exception("Error")):
            with patch('episode_owl.utils.subprocess.Popen', side_effect=Exception("Error")):
                result = open_timeline_file(timeline_file)

                # Should return False but not crash
                assert result is False


def test_is_running_in_ci_true():
    """Test CI detection when running in CI."""
    with patch.dict(os.environ, {"CI": "true"}):
        assert is_running_in_ci() is True


def test_is_running_in_ci_github_actions():
    """Test CI detection for GitHub Actions."""
    with patch.dict(os.environ, {"GITHUB_ACTIONS": "true"}):
        assert is_running_in_ci() is True


def test_is_running_in_ci_false():
    """Test CI detection when not in CI."""
    with patch.dict(os.environ, {}, clear=True):
        assert is_running_in_ci() is False


def test_should_auto_open_config_enabled():
    """Test auto-open when config is enabled."""
    with patch('episode_owl.utils.is_running_in_ci', return_value=False):
        assert should_auto_open(True, False) is True


def test_should_auto_open_config_disabled():
    """Test auto-open when config is disabled."""
    with patch('episode_owl.utils.is_running_in_ci', return_value=False):
        assert should_auto_open(False, False) is False


def test_should_auto_open_cli_override():
    """Test auto-open with CLI override."""
    with patch('episode_owl.utils.is_running_in_ci', return_value=False):
        assert should_auto_open(True, True) is False


def test_should_auto_open_in_ci():
    """Test auto-open is disabled in CI."""
    with patch('episode_owl.utils.is_running_in_ci', return_value=True):
        assert should_auto_open(True, False) is False
