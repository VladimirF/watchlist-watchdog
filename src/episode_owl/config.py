"""Configuration management for Episode Owl."""

import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional


@dataclass
class Config:
    """Application configuration.

    Attributes:
        output_path: Path to notifications output file
        date_format: Format string for dates in notifications
        max_notifications: Maximum number of notifications to keep
        api_timeout: Timeout for API requests in seconds
        retry_attempts: Number of retry attempts for failed requests
    """
    output_path: str = "data/notifications.txt"
    date_format: str = "%Y-%m-%d"
    max_notifications: int = 100
    api_timeout: int = 10
    retry_attempts: int = 1


def load_config(config_path: Path) -> Config:
    """Load configuration from JSON file.

    Args:
        config_path: Path to config.json file

    Returns:
        Config object with loaded or default values
    """
    if not config_path.exists():
        return Config()

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return Config(**data)
    except (json.JSONDecodeError, TypeError) as e:
        # If config is malformed, return defaults
        print(f"Warning: Could not parse config file: {e}")
        return Config()


def save_config(config: Config, config_path: Path) -> None:
    """Save configuration to JSON file.

    Args:
        config: Config object to save
        config_path: Path to config.json file
    """
    config_path.parent.mkdir(parents=True, exist_ok=True)

    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(asdict(config), f, indent=2)


def get_default_paths() -> dict[str, Path]:
    """Get default paths for application data.

    Returns:
        Dictionary with paths for shows, notifications, and config files
    """
    base_dir = Path(__file__).parent.parent.parent / "data"

    return {
        "shows": base_dir / "shows.json",
        "notifications": base_dir / "notifications.txt",
        "config": base_dir / "config.json",
    }
