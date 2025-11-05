"""Core tracking logic for comparing episodes and detecting updates."""

from datetime import datetime
from typing import NamedTuple, Optional


class Episode(NamedTuple):
    """Represents a TV show episode.

    Attributes:
        season: Season number (None for absolute numbering)
        number: Episode number within season
        title: Episode title
        airdate: Air date string (YYYY-MM-DD format)
        absolute_number: Absolute episode number (optional)
        episode_type: Episode type from API (regular, significant_special, etc.)
    """
    season: int | None
    number: int
    title: str
    airdate: str
    absolute_number: int | None = None
    episode_type: str | None = None


class ShowUpdate(NamedTuple):
    """Represents a detected show update.

    Attributes:
        show_id: TVMaze show ID
        show_name: Show name
        episode: New episode detected
    """
    show_id: int
    show_name: str
    episode: Episode


def parse_episode_from_api(episode_data: dict) -> Episode:
    """Parse episode information from TVMaze API response.

    Args:
        episode_data: Episode dictionary from API

    Returns:
        Episode object
    """
    season = episode_data.get("season")
    number = episode_data.get("number", 0)
    title = episode_data.get("name", f"Episode {number}")
    airdate = episode_data.get("airdate", "")
    absolute_number = episode_data.get("number")  # Some shows use absolute numbering
    episode_type = episode_data.get("type")  # Type: regular, significant_special, etc.

    return Episode(
        season=season,
        number=number,
        title=title,
        airdate=airdate,
        absolute_number=absolute_number,
        episode_type=episode_type
    )


def compare_episodes(last_seen: tuple[int | None, int], episode: Episode) -> bool:
    """Check if an episode is newer than the last seen episode.

    Args:
        last_seen: Tuple of (last_season, last_episode)
        episode: Episode to compare

    Returns:
        True if episode is newer than last_seen
    """
    last_season, last_episode = last_seen

    # Handle shows without season numbers (absolute numbering)
    if episode.season is None or last_season is None:
        # Use absolute episode number
        if episode.absolute_number is not None:
            return episode.absolute_number > last_episode
        return episode.number > last_episode

    # Compare season first, then episode
    if episode.season > last_season:
        return True
    elif episode.season == last_season and episode.number > last_episode:
        return True

    return False


def get_latest_episode(episodes: list[Episode]) -> Episode | None:
    """Get the most recent episode from a list.

    Args:
        episodes: List of Episode objects

    Returns:
        Latest episode or None if list is empty
    """
    if not episodes:
        return None

    # Sort by season (or 0 if None), then by episode number
    sorted_episodes = sorted(
        episodes,
        key=lambda e: ((e.season or 0), e.number)
    )

    return sorted_episodes[-1]


def find_new_episodes(
    episodes: list[Episode],
    last_seen: tuple[int | None, int]
) -> list[Episode]:
    """Find all episodes that are newer than the last seen episode.

    Args:
        episodes: List of all episodes
        last_seen: Tuple of (last_season, last_episode)

    Returns:
        List of new episodes, sorted chronologically
    """
    new_episodes = [ep for ep in episodes if compare_episodes(last_seen, ep)]

    # Sort by season and episode number
    new_episodes.sort(key=lambda e: ((e.season or 0), e.number))

    return new_episodes


def should_include_episode(episode: Episode, include_specials: str = "smart") -> bool:
    """Determine if an episode should be included in tracking.

    Args:
        episode: Episode to check
        include_specials: How to handle specials - "smart" (movies only), "all", or "none"

    Returns:
        True if episode should be tracked
    """
    # Skip episodes without air dates (not yet released)
    if not episode.airdate:
        return False

    # Check if episode has aired
    try:
        airdate = datetime.strptime(episode.airdate, "%Y-%m-%d")
        if airdate > datetime.now():
            return False
    except ValueError:
        # Invalid date format, skip
        return False

    # Handle special episodes (season 0) based on mode
    if episode.season == 0:
        if include_specials == "none":
            return False
        elif include_specials == "all":
            return True
        elif include_specials == "smart":
            # Smart mode: include only significant specials (movies)
            # If we have type information, use it
            if episode.episode_type:
                return episode.episode_type == "significant_special"
            else:
                # Fallback: include all season 0 (API doesn't always have type)
                # User can change to "none" if they get too many OVAs
                return True

    return True


def filter_aired_episodes(episodes: list[Episode], include_specials: str = "smart") -> list[Episode]:
    """Filter episodes to only include those that have aired.

    Args:
        episodes: List of all episodes
        include_specials: How to handle specials - "smart" (movies only), "all", or "none"

    Returns:
        Filtered list of episodes
    """
    return [ep for ep in episodes if should_include_episode(ep, include_specials)]


def create_show_dict(
    show_id: int,
    name: str,
    latest_episode: Episode | None = None
) -> dict:
    """Create a show dictionary for storage.

    Args:
        show_id: TVMaze show ID
        name: Show name
        latest_episode: Most recent episode (for initial state)

    Returns:
        Dictionary ready for storage
    """
    now = datetime.now().isoformat()

    show_dict = {
        "id": show_id,
        "name": name,
        "last_checked": now,
        "last_seen_season": None,
        "last_seen_episode": 0
    }

    if latest_episode:
        show_dict["last_seen_season"] = latest_episode.season
        show_dict["last_seen_episode"] = latest_episode.number

    return show_dict


def update_show_state(show: dict, latest_episode: Episode) -> dict:
    """Update show's last_seen state with new episode.

    Args:
        show: Show dictionary
        latest_episode: Latest episode detected

    Returns:
        Updated show dictionary (new dict, not mutated)
    """
    updated = show.copy()
    updated["last_checked"] = datetime.now().isoformat()
    updated["last_seen_season"] = latest_episode.season
    updated["last_seen_episode"] = latest_episode.number

    return updated
