"""Tests for api module."""

import pytest
import requests
from unittest.mock import Mock, patch

from episode_owl.api import (
    TVMazeAPIError,
    NetworkError,
    search_shows,
    get_show_episodes,
    get_show_by_id,
)


@patch('episode_owl.api.requests.get')
def test_search_shows_success(mock_get):
    """Test successful show search."""
    mock_response = Mock()
    mock_response.json.return_value = [
        {"show": {"id": 1, "name": "Test Show"}}
    ]
    mock_response.raise_for_status = Mock()
    mock_get.return_value = mock_response

    results = search_shows("test")

    assert len(results) == 1
    assert results[0]["show"]["name"] == "Test Show"
    mock_get.assert_called_once()


@patch('episode_owl.api.requests.get')
def test_search_shows_timeout(mock_get):
    """Test search with timeout."""
    mock_get.side_effect = requests.Timeout()

    with pytest.raises(NetworkError) as exc_info:
        search_shows("test", timeout=5)

    assert "timed out" in str(exc_info.value).lower()


@patch('episode_owl.api.requests.get')
def test_search_shows_network_error(mock_get):
    """Test search with network error."""
    mock_get.side_effect = requests.RequestException("Connection failed")

    with pytest.raises(NetworkError):
        search_shows("test")


@patch('episode_owl.api.requests.get')
def test_search_shows_invalid_json(mock_get):
    """Test search with invalid JSON response."""
    mock_response = Mock()
    mock_response.json.side_effect = ValueError("Invalid JSON")
    mock_response.raise_for_status = Mock()
    mock_get.return_value = mock_response

    with pytest.raises(TVMazeAPIError):
        search_shows("test")


@patch('episode_owl.api.requests.get')
@patch('episode_owl.api.time.sleep')
def test_get_show_episodes_success(mock_sleep, mock_get):
    """Test getting show episodes successfully."""
    mock_response = Mock()
    mock_response.json.return_value = [
        {"id": 1, "season": 1, "number": 1, "name": "Pilot"}
    ]
    mock_response.raise_for_status = Mock()
    mock_get.return_value = mock_response

    episodes = get_show_episodes(123)

    assert len(episodes) == 1
    assert episodes[0]["name"] == "Pilot"


@patch('episode_owl.api.requests.get')
@patch('episode_owl.api.time.sleep')
def test_get_show_episodes_404(mock_sleep, mock_get):
    """Test getting episodes for show without episodes."""
    mock_response = Mock()
    mock_response.status_code = 404
    mock_get.return_value = mock_response

    episodes = get_show_episodes(123)

    assert episodes == []


@patch('episode_owl.api.requests.get')
@patch('episode_owl.api.time.sleep')
def test_get_show_episodes_retry(mock_sleep, mock_get):
    """Test retry logic for failed requests."""
    # First attempt fails, second succeeds
    mock_response_fail = Mock()
    mock_response_fail.raise_for_status.side_effect = requests.Timeout()

    mock_response_success = Mock()
    mock_response_success.json.return_value = [{"id": 1}]
    mock_response_success.raise_for_status = Mock()
    mock_response_success.status_code = 200

    mock_get.side_effect = [requests.Timeout(), mock_response_success]

    episodes = get_show_episodes(123, timeout=10, retry_attempts=1)

    assert len(episodes) == 1
    assert mock_get.call_count == 2
    assert mock_sleep.call_count >= 1  # Should sleep for backoff


@patch('episode_owl.api.requests.get')
@patch('episode_owl.api.time.sleep')
def test_get_show_episodes_retry_exhausted(mock_sleep, mock_get):
    """Test that retries eventually fail."""
    mock_get.side_effect = requests.Timeout()

    with pytest.raises(NetworkError):
        get_show_episodes(123, timeout=10, retry_attempts=2)

    # Should try initial + 2 retries = 3 times
    assert mock_get.call_count == 3


@patch('episode_owl.api.requests.get')
def test_get_show_by_id_success(mock_get):
    """Test getting show by ID successfully."""
    mock_response = Mock()
    mock_response.json.return_value = {"id": 123, "name": "Test Show"}
    mock_response.raise_for_status = Mock()
    mock_get.return_value = mock_response

    show = get_show_by_id(123)

    assert show is not None
    assert show["name"] == "Test Show"


@patch('episode_owl.api.requests.get')
def test_get_show_by_id_not_found(mock_get):
    """Test getting show that doesn't exist."""
    mock_response = Mock()
    mock_response.status_code = 404
    mock_get.return_value = mock_response

    show = get_show_by_id(999)

    assert show is None


@patch('episode_owl.api.requests.get')
def test_get_show_by_id_timeout(mock_get):
    """Test getting show with timeout."""
    mock_get.side_effect = requests.Timeout()

    with pytest.raises(NetworkError):
        get_show_by_id(123)
