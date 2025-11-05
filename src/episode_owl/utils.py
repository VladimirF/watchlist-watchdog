"""Utility functions for Episode Owl."""

import os
import sys
import subprocess
import logging
from pathlib import Path


logger = logging.getLogger(__name__)


def open_timeline_file(file_path: Path) -> bool:
    """Open timeline file in system default editor.

    Args:
        file_path: Path to file to open

    Returns:
        True if file was opened successfully, False otherwise

    Note:
        This function does not wait for the editor to close.
        Failures are logged but do not raise exceptions.
    """
    if not file_path.exists():
        logger.warning(f"Timeline file does not exist: {file_path}")
        # Create empty file so editor can open it
        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.touch()
        except IOError as e:
            logger.error(f"Could not create timeline file: {e}")
            return False

    try:
        if sys.platform == "win32":
            # Windows: use os.startfile or notepad.exe
            _open_file_windows(file_path)
        elif sys.platform == "darwin":
            # macOS: use open command
            subprocess.Popen(["open", str(file_path)])
        else:
            # Linux: try xdg-open
            subprocess.Popen(["xdg-open", str(file_path)])

        return True

    except Exception as e:
        logger.warning(f"Could not open timeline file: {e}")
        return False


def _open_file_windows(file_path: Path) -> None:
    """Open file on Windows using best available method.

    Args:
        file_path: Path to file to open

    Raises:
        Exception: If file cannot be opened
    """
    try:
        # Try os.startfile first (most reliable on Windows)
        os.startfile(str(file_path))
    except (AttributeError, OSError):
        # Fall back to notepad.exe
        subprocess.Popen(["notepad.exe", str(file_path)])


def is_running_in_ci() -> bool:
    """Check if running in CI/automated environment.

    Returns:
        True if running in CI environment
    """
    # Common CI environment variables
    ci_indicators = [
        "CI",
        "CONTINUOUS_INTEGRATION",
        "GITHUB_ACTIONS",
        "GITLAB_CI",
        "CIRCLECI",
        "TRAVIS",
        "JENKINS_HOME",
        "BUILDKITE",
    ]

    return any(os.getenv(indicator) for indicator in ci_indicators)


def should_auto_open(config_enabled: bool, cli_override: bool = False) -> bool:
    """Determine if timeline should auto-open.

    Args:
        config_enabled: Whether auto-open is enabled in config
        cli_override: Whether CLI flag overrides config

    Returns:
        True if timeline should auto-open
    """
    # Don't auto-open in CI environments
    if is_running_in_ci():
        return False

    # CLI override takes precedence
    if cli_override:
        return False

    # Otherwise use config setting
    return config_enabled
