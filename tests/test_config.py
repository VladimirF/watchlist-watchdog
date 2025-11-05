"""Tests for config module."""

import json
from pathlib import Path

import pytest

from episode_owl.config import Config, load_config, save_config, get_default_paths


def test_config_defaults():
    """Test default configuration values."""
    config = Config()

    assert config.output_path == "data/notifications.txt"
    assert config.date_format == "%Y-%m-%d"
    assert config.max_notifications == 100
    assert config.api_timeout == 10
    assert config.retry_attempts == 1


def test_load_config_nonexistent(tmp_path):
    """Test loading config when file doesn't exist."""
    config_path = tmp_path / "config.json"

    config = load_config(config_path)

    # Should return defaults
    assert isinstance(config, Config)
    assert config.api_timeout == 10


def test_save_and_load_config(tmp_path):
    """Test saving and loading configuration."""
    config_path = tmp_path / "config.json"

    # Create custom config
    config = Config(
        output_path="custom/path.txt",
        date_format="%d/%m/%Y",
        max_notifications=50,
        api_timeout=20,
        retry_attempts=3
    )

    # Save it
    save_config(config, config_path)

    assert config_path.exists()

    # Load it back
    loaded = load_config(config_path)

    assert loaded.output_path == "custom/path.txt"
    assert loaded.date_format == "%d/%m/%Y"
    assert loaded.max_notifications == 50
    assert loaded.api_timeout == 20
    assert loaded.retry_attempts == 3


def test_load_config_malformed(tmp_path):
    """Test loading malformed config file."""
    config_path = tmp_path / "config.json"

    # Write invalid JSON
    config_path.write_text("{ invalid json }")

    # Should return defaults without crashing
    config = load_config(config_path)
    assert isinstance(config, Config)


def test_load_config_wrong_types(tmp_path):
    """Test loading config with wrong data types."""
    config_path = tmp_path / "config.json"

    # Write config with wrong types
    config_path.write_text(json.dumps({
        "api_timeout": "not a number",
        "max_notifications": "also not a number"
    }))

    # Should return defaults due to TypeError
    config = load_config(config_path)
    assert isinstance(config, Config)


def test_get_default_paths():
    """Test getting default paths."""
    paths = get_default_paths()

    assert "shows" in paths
    assert "notifications" in paths
    assert "config" in paths

    assert isinstance(paths["shows"], Path)
    assert isinstance(paths["notifications"], Path)
    assert isinstance(paths["config"], Path)

    assert paths["shows"].name == "shows.json"
    assert paths["notifications"].name == "notifications.txt"
    assert paths["config"].name == "config.json"
