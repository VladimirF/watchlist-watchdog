"""Fuzzy search and matching logic for show names."""

from typing import NamedTuple
from rapidfuzz import fuzz, process


class SearchResult(NamedTuple):
    """A search result with show information and match score.

    Attributes:
        show_id: TVMaze show ID
        name: Show name
        year: Premiere year (optional)
        status: Show status (Running, Ended, etc.)
        score: Fuzzy match score (0-100)
    """
    show_id: int
    name: str
    year: int | None
    status: str
    score: float


def extract_show_info(api_result: dict) -> tuple[int, str]:
    """Extract show ID and name from TVMaze API result.

    Args:
        api_result: Dictionary from TVMaze search endpoint

    Returns:
        Tuple of (show_id, show_name)
    """
    show = api_result.get("show", {})
    show_id = show.get("id", 0)
    name = show.get("name", "Unknown")
    return show_id, name


def rank_search_results(query: str, api_results: list[dict], limit: int = 5) -> list[SearchResult]:
    """Rank and filter search results using fuzzy matching.

    Args:
        query: User's search query
        api_results: Results from TVMaze API
        limit: Maximum number of results to return

    Returns:
        List of SearchResult objects, sorted by match score (descending)
    """
    if not api_results:
        return []

    results = []
    for api_result in api_results:
        show = api_result.get("show", {})

        show_id = show.get("id", 0)
        name = show.get("name", "Unknown")
        premiered = show.get("premiered", "")
        year = int(premiered[:4]) if premiered and len(premiered) >= 4 else None
        status = show.get("status", "Unknown")

        # Calculate fuzzy match score
        score = fuzz.ratio(query.lower(), name.lower())

        results.append(SearchResult(
            show_id=show_id,
            name=name,
            year=year,
            status=status,
            score=score
        ))

    # Sort by score descending, then by name
    results.sort(key=lambda r: (-r.score, r.name))

    return results[:limit]


def find_show_by_name(query: str, shows: list[dict], threshold: float = 60.0) -> int | None:
    """Find a show ID by fuzzy matching against a list of tracked shows.

    Args:
        query: Search query (show name or partial name)
        shows: List of show dictionaries with 'id' and 'name' keys
        threshold: Minimum fuzzy match score (0-100)

    Returns:
        Show ID if a good match is found, None otherwise
    """
    if not shows:
        return None

    # Build list of (name, show_id) tuples
    choices = [(show["name"], show["id"]) for show in shows]

    # Use process.extractOne to find best match
    # Use token_set_ratio for better partial matching
    result = process.extractOne(
        query,
        [choice[0] for choice in choices],
        scorer=fuzz.token_set_ratio
    )

    if result and result[1] >= threshold:
        # Find the show_id for the matched name
        matched_name = result[0]
        for name, show_id in choices:
            if name == matched_name:
                return show_id

    return None


def format_search_result(result: SearchResult, index: int) -> str:
    """Format a search result for display.

    Args:
        result: SearchResult object
        index: Result index (for display numbering)

    Returns:
        Formatted string for display
    """
    year_str = f"({result.year})" if result.year else ""
    status_str = f"[{result.status}]"

    return f"{index}. {result.name} {year_str} {status_str} (Match: {result.score:.0f}%)"
