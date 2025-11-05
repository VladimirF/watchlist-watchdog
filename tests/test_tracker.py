"""Tests for tracker module."""

from datetime import datetime, timedelta

import pytest

from episode_owl.tracker import (
    Episode,
    ShowUpdate,
    parse_episode_from_api,
    compare_episodes,
    get_latest_episode,
    find_new_episodes,
    should_include_episode,
    filter_aired_episodes,
    create_show_dict,
    update_show_state,
)


def test_episode_creation():
    """Test Episode namedtuple creation."""
    episode = Episode(
        season=1,
        number=5,
        title="Test Episode",
        airdate="2025-11-05",
        absolute_number=5
    )

    assert episode.season == 1
    assert episode.number == 5
    assert episode.title == "Test Episode"
    assert episode.airdate == "2025-11-05"


def test_parse_episode_from_api():
    """Test parsing episode from API response."""
    api_data = {
        "season": 2,
        "number": 10,
        "name": "The Test",
        "airdate": "2025-11-01"
    }

    episode = parse_episode_from_api(api_data)

    assert episode.season == 2
    assert episode.number == 10
    assert episode.title == "The Test"
    assert episode.airdate == "2025-11-01"


def test_parse_episode_missing_title():
    """Test parsing episode with missing title."""
    api_data = {
        "season": 1,
        "number": 3,
        "airdate": "2025-11-01"
    }

    episode = parse_episode_from_api(api_data)

    assert episode.title == "Episode 3"


def test_parse_episode_no_season():
    """Test parsing episode without season (absolute numbering)."""
    api_data = {
        "number": 42,
        "name": "Episode 42",
        "airdate": "2025-11-01"
    }

    episode = parse_episode_from_api(api_data)

    assert episode.season is None
    assert episode.number == 42


def test_compare_episodes_newer_season():
    """Test comparing episodes - newer season."""
    last_seen = (1, 10)
    episode = Episode(season=2, number=1, title="Test", airdate="2025-11-01")

    assert compare_episodes(last_seen, episode) is True


def test_compare_episodes_same_season_newer():
    """Test comparing episodes - same season, newer episode."""
    last_seen = (1, 5)
    episode = Episode(season=1, number=10, title="Test", airdate="2025-11-01")

    assert compare_episodes(last_seen, episode) is True


def test_compare_episodes_same_episode():
    """Test comparing episodes - same episode."""
    last_seen = (1, 5)
    episode = Episode(season=1, number=5, title="Test", airdate="2025-11-01")

    assert compare_episodes(last_seen, episode) is False


def test_compare_episodes_older():
    """Test comparing episodes - older episode."""
    last_seen = (2, 10)
    episode = Episode(season=1, number=5, title="Test", airdate="2025-11-01")

    assert compare_episodes(last_seen, episode) is False


def test_compare_episodes_absolute_numbering():
    """Test comparing episodes with absolute numbering."""
    last_seen = (None, 42)
    episode = Episode(season=None, number=45, title="Test", airdate="2025-11-01", absolute_number=45)

    assert compare_episodes(last_seen, episode) is True


def test_get_latest_episode():
    """Test getting latest episode from list."""
    episodes = [
        Episode(season=1, number=1, title="First", airdate="2025-11-01"),
        Episode(season=1, number=3, title="Third", airdate="2025-11-03"),
        Episode(season=1, number=2, title="Second", airdate="2025-11-02"),
    ]

    latest = get_latest_episode(episodes)

    assert latest is not None
    assert latest.number == 3


def test_get_latest_episode_empty():
    """Test getting latest episode from empty list."""
    latest = get_latest_episode([])

    assert latest is None


def test_get_latest_episode_across_seasons():
    """Test getting latest episode across multiple seasons."""
    episodes = [
        Episode(season=1, number=10, title="S1E10", airdate="2024-01-01"),
        Episode(season=2, number=5, title="S2E5", airdate="2025-01-01"),
        Episode(season=2, number=1, title="S2E1", airdate="2024-12-01"),
    ]

    latest = get_latest_episode(episodes)

    assert latest is not None
    assert latest.season == 2
    assert latest.number == 5


def test_find_new_episodes():
    """Test finding new episodes."""
    episodes = [
        Episode(season=1, number=1, title="E1", airdate="2025-11-01"),
        Episode(season=1, number=2, title="E2", airdate="2025-11-02"),
        Episode(season=1, number=3, title="E3", airdate="2025-11-03"),
        Episode(season=1, number=4, title="E4", airdate="2025-11-04"),
    ]

    last_seen = (1, 2)
    new = find_new_episodes(episodes, last_seen)

    assert len(new) == 2
    assert new[0].number == 3
    assert new[1].number == 4


def test_find_new_episodes_none():
    """Test finding new episodes when there are none."""
    episodes = [
        Episode(season=1, number=1, title="E1", airdate="2025-11-01"),
        Episode(season=1, number=2, title="E2", airdate="2025-11-02"),
    ]

    last_seen = (1, 5)
    new = find_new_episodes(episodes, last_seen)

    assert len(new) == 0


def test_should_include_episode_aired():
    """Test should_include_episode for aired episode."""
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    episode = Episode(season=1, number=1, title="Test", airdate=yesterday)

    assert should_include_episode(episode) is True


def test_should_include_episode_not_aired():
    """Test should_include_episode for future episode."""
    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    episode = Episode(season=1, number=1, title="Test", airdate=tomorrow)

    assert should_include_episode(episode) is False


def test_should_include_episode_no_airdate():
    """Test should_include_episode for episode without airdate."""
    episode = Episode(season=1, number=1, title="Test", airdate="")

    assert should_include_episode(episode) is False


def test_should_include_episode_special():
    """Test should_include_episode for special episode."""
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    episode = Episode(season=0, number=1, title="Special", airdate=yesterday)

    assert should_include_episode(episode, include_specials=False) is False
    assert should_include_episode(episode, include_specials=True) is True


def test_filter_aired_episodes():
    """Test filtering aired episodes."""
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")

    episodes = [
        Episode(season=1, number=1, title="E1", airdate=yesterday),
        Episode(season=1, number=2, title="E2", airdate=tomorrow),
        Episode(season=1, number=3, title="E3", airdate=""),
        Episode(season=0, number=1, title="Special", airdate=yesterday),
    ]

    filtered = filter_aired_episodes(episodes)

    assert len(filtered) == 1
    assert filtered[0].number == 1


def test_create_show_dict():
    """Test creating show dictionary for storage."""
    show = create_show_dict(123, "Test Show")

    assert show["id"] == 123
    assert show["name"] == "Test Show"
    assert show["last_seen_season"] is None
    assert show["last_seen_episode"] == 0
    assert "last_checked" in show


def test_create_show_dict_with_episode():
    """Test creating show dictionary with initial episode."""
    episode = Episode(season=1, number=5, title="Test", airdate="2025-11-01")

    show = create_show_dict(123, "Test Show", episode)

    assert show["id"] == 123
    assert show["name"] == "Test Show"
    assert show["last_seen_season"] == 1
    assert show["last_seen_episode"] == 5


def test_update_show_state():
    """Test updating show state."""
    show = {
        "id": 123,
        "name": "Test Show",
        "last_checked": "2025-11-01T10:00:00",
        "last_seen_season": 1,
        "last_seen_episode": 5
    }

    episode = Episode(season=1, number=10, title="Test", airdate="2025-11-05")

    updated = update_show_state(show, episode)

    # Original should not be modified
    assert show["last_seen_episode"] == 5

    # Updated should have new values
    assert updated["id"] == 123
    assert updated["last_seen_episode"] == 10
    assert updated["last_seen_season"] == 1
    assert updated["last_checked"] != "2025-11-01T10:00:00"
