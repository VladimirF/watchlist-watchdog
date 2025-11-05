"""Integration tests for Episode Owl."""

from pathlib import Path
from unittest.mock import patch, Mock

import pytest

from episode_owl import api, storage, tracker, notifications


@patch('episode_owl.api.requests.get')
@patch('episode_owl.api.time.sleep')
def test_add_show_workflow(mock_sleep, mock_get, tmp_path):
    """Test the complete workflow of adding a show."""
    # Mock API search response
    search_response = Mock()
    search_response.json.return_value = [
        {
            "show": {
                "id": 123,
                "name": "Breaking Bad",
                "premiered": "2008-01-20",
                "status": "Ended"
            }
        }
    ]
    search_response.raise_for_status = Mock()

    # Mock API episodes response
    episodes_response = Mock()
    episodes_response.json.return_value = [
        {
            "season": 1,
            "number": 1,
            "name": "Pilot",
            "airdate": "2008-01-20"
        },
        {
            "season": 1,
            "number": 2,
            "name": "Cat's in the Bag...",
            "airdate": "2008-01-27"
        }
    ]
    episodes_response.raise_for_status = Mock()
    episodes_response.status_code = 200

    mock_get.side_effect = [search_response, episodes_response]

    # Search for show
    search_results = api.search_shows("breaking bad")
    assert len(search_results) == 1

    # Get show ID
    show_data = search_results[0]["show"]
    show_id = show_data["id"]
    show_name = show_data["name"]

    # Get episodes
    episodes_data = api.get_show_episodes(show_id)
    assert len(episodes_data) == 2

    # Parse episodes
    episodes = [tracker.parse_episode_from_api(ep) for ep in episodes_data]
    aired = tracker.filter_aired_episodes(episodes)

    # Create show dict
    latest = tracker.get_latest_episode(aired)
    show_dict = tracker.create_show_dict(show_id, show_name, latest)

    # Save to storage
    shows_path = tmp_path / "shows.json"
    storage.add_show(show_dict, shows_path)

    # Verify saved
    shows = storage.load_shows(shows_path)
    assert len(shows) == 1
    assert shows[0]["name"] == "Breaking Bad"
    assert shows[0]["last_seen_episode"] == 2


@patch('episode_owl.api.requests.get')
@patch('episode_owl.api.time.sleep')
def test_check_updates_workflow(mock_sleep, mock_get, tmp_path):
    """Test the complete workflow of checking for updates."""
    # Setup: Add a show that has seen S01E01
    shows_path = tmp_path / "shows.json"
    notif_path = tmp_path / "notifications.txt"

    show = {
        "id": 123,
        "name": "Breaking Bad",
        "last_checked": "2008-01-20T00:00:00",
        "last_seen_season": 1,
        "last_seen_episode": 1
    }

    storage.add_show(show, shows_path)

    # Mock API response with new episodes
    episodes_response = Mock()
    episodes_response.json.return_value = [
        {
            "season": 1,
            "number": 1,
            "name": "Pilot",
            "airdate": "2008-01-20"
        },
        {
            "season": 1,
            "number": 2,
            "name": "Cat's in the Bag...",
            "airdate": "2008-01-27"
        },
        {
            "season": 1,
            "number": 3,
            "name": "...And the Bag's in the River",
            "airdate": "2008-02-10"
        }
    ]
    episodes_response.raise_for_status = Mock()
    episodes_response.status_code = 200

    mock_get.return_value = episodes_response

    # Check for updates
    shows = storage.load_shows(shows_path)
    updates = []

    for show_item in shows:
        episodes_data = api.get_show_episodes(show_item["id"])
        episodes = [tracker.parse_episode_from_api(ep) for ep in episodes_data]
        aired = tracker.filter_aired_episodes(episodes)

        last_seen = (show_item["last_seen_season"], show_item["last_seen_episode"])
        new_episodes = tracker.find_new_episodes(aired, last_seen)

        for episode in new_episodes:
            update = tracker.ShowUpdate(
                show_id=show_item["id"],
                show_name=show_item["name"],
                episode=episode
            )
            updates.append(update)

        # Update show state
        if new_episodes:
            latest = new_episodes[-1]
            storage.update_show(
                show_item["id"],
                tracker.update_show_state(show_item, latest),
                shows_path
            )

    # Save notifications
    assert len(updates) == 2  # Episodes 2 and 3 are new

    notif_lines = notifications.format_multiple_notifications(updates)
    storage.append_notifications(notif_lines, notif_path)

    # Verify notifications
    saved_notifs = storage.load_notifications(notif_path)
    assert len(saved_notifs) == 2
    assert "S01E02" in saved_notifs[0]
    assert "S01E03" in saved_notifs[1]

    # Verify show state updated
    updated_shows = storage.load_shows(shows_path)
    assert updated_shows[0]["last_seen_episode"] == 3


def test_remove_show_workflow(tmp_path):
    """Test the complete workflow of removing a show."""
    shows_path = tmp_path / "shows.json"

    # Add multiple shows
    shows = [
        {"id": 1, "name": "Show 1", "last_seen_episode": 1},
        {"id": 2, "name": "Show 2", "last_seen_episode": 1},
        {"id": 3, "name": "Show 3", "last_seen_episode": 1},
    ]

    for show in shows:
        storage.add_show(show, shows_path)

    # Remove one
    removed = storage.remove_show(2, shows_path)
    assert removed is True

    # Verify
    remaining = storage.load_shows(shows_path)
    assert len(remaining) == 2
    assert not any(s["id"] == 2 for s in remaining)


def test_notification_timeline_workflow(tmp_path):
    """Test the complete workflow of managing notification timeline."""
    notif_path = tmp_path / "notifications.txt"

    # Add some notifications
    notifs1 = [
        "2025-11-05 | Show 1 | S01E01 | Episode 1",
        "2025-11-05 | Show 2 | S01E01 | Pilot",
    ]
    storage.append_notifications(notifs1, notif_path)

    # Add more notifications
    notifs2 = [
        "2025-11-06 | Show 3 | S02E05 | New Episode",
    ]
    storage.append_notifications(notifs2, notif_path)

    # Check order (newest first)
    all_notifs = storage.load_notifications(notif_path)
    assert len(all_notifs) == 3
    assert "Show 3" in all_notifs[0]  # Newest first
    assert "Show 1" in all_notifs[1]
    assert "Show 2" in all_notifs[2]

    # Prune to keep only 2
    removed = storage.prune_notifications(notif_path, keep=2)
    assert removed == 1

    pruned = storage.load_notifications(notif_path)
    assert len(pruned) == 2
    assert "Show 3" in pruned[0]
    assert "Show 1" in pruned[1]
