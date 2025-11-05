"""TVMaze API client for fetching show and episode data."""

import time
from typing import Optional
import requests


BASE_URL = "https://api.tvmaze.com"
RATE_LIMIT_DELAY = 0.5  # seconds between requests


class TVMazeAPIError(Exception):
    """Exception raised for TVMaze API errors."""
    pass


class NetworkError(Exception):
    """Exception raised for network-related errors."""
    pass


def search_shows(query: str, timeout: int = 10) -> list[dict]:
    """Search for shows on TVMaze.

    Args:
        query: Search term
        timeout: Request timeout in seconds

    Returns:
        List of show dictionaries from API

    Raises:
        NetworkError: If network request fails
        TVMazeAPIError: If API returns an error
    """
    url = f"{BASE_URL}/search/shows"
    params = {"q": query}

    try:
        response = requests.get(url, params=params, timeout=timeout)
        response.raise_for_status()
        return response.json()
    except requests.Timeout:
        raise NetworkError(f"Request timed out after {timeout} seconds")
    except requests.RequestException as e:
        raise NetworkError(f"Network error: {e}")
    except ValueError as e:
        raise TVMazeAPIError(f"Invalid JSON response: {e}")


def get_show_episodes(show_id: int, timeout: int = 10, retry_attempts: int = 1) -> list[dict]:
    """Get all episodes for a show.

    Args:
        show_id: TVMaze show ID
        timeout: Request timeout in seconds
        retry_attempts: Number of retry attempts on failure

    Returns:
        List of episode dictionaries from API

    Raises:
        NetworkError: If network request fails after retries
        TVMazeAPIError: If API returns an error
    """
    url = f"{BASE_URL}/shows/{show_id}/episodes"

    last_error = None
    for attempt in range(retry_attempts + 1):
        try:
            response = requests.get(url, timeout=timeout)

            # Handle 404 gracefully - show might not have episodes yet
            if response.status_code == 404:
                return []

            response.raise_for_status()
            episodes = response.json()

            # Add small delay to respect rate limits
            time.sleep(RATE_LIMIT_DELAY)

            return episodes

        except requests.Timeout:
            last_error = NetworkError(f"Request timed out after {timeout} seconds")
            if attempt < retry_attempts:
                # Exponential backoff: 2s, 4s, 8s...
                wait_time = 2 ** (attempt + 1)
                time.sleep(wait_time)
        except requests.RequestException as e:
            last_error = NetworkError(f"Network error: {e}")
            if attempt < retry_attempts:
                wait_time = 2 ** (attempt + 1)
                time.sleep(wait_time)
        except ValueError as e:
            raise TVMazeAPIError(f"Invalid JSON response: {e}")

    # If we've exhausted retries, raise the last error
    if last_error:
        raise last_error

    return []


def get_show_by_id(show_id: int, timeout: int = 10) -> Optional[dict]:
    """Get show information by ID.

    Args:
        show_id: TVMaze show ID
        timeout: Request timeout in seconds

    Returns:
        Show dictionary from API or None if not found

    Raises:
        NetworkError: If network request fails
        TVMazeAPIError: If API returns an error
    """
    url = f"{BASE_URL}/shows/{show_id}"

    try:
        response = requests.get(url, timeout=timeout)

        if response.status_code == 404:
            return None

        response.raise_for_status()
        return response.json()

    except requests.Timeout:
        raise NetworkError(f"Request timed out after {timeout} seconds")
    except requests.RequestException as e:
        raise NetworkError(f"Network error: {e}")
    except ValueError as e:
        raise TVMazeAPIError(f"Invalid JSON response: {e}")
