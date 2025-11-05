"""Tests for search module."""

import pytest

from episode_owl.search import (
    SearchResult,
    extract_show_info,
    rank_search_results,
    find_show_by_name,
    format_search_result,
)


def test_search_result_creation():
    """Test SearchResult namedtuple creation."""
    result = SearchResult(
        show_id=123,
        name="Breaking Bad",
        year=2008,
        status="Ended",
        score=95.0
    )

    assert result.show_id == 123
    assert result.name == "Breaking Bad"
    assert result.year == 2008
    assert result.status == "Ended"
    assert result.score == 95.0


def test_extract_show_info():
    """Test extracting show info from API result."""
    api_result = {
        "show": {
            "id": 456,
            "name": "The Wire"
        }
    }

    show_id, name = extract_show_info(api_result)

    assert show_id == 456
    assert name == "The Wire"


def test_extract_show_info_missing_fields():
    """Test extracting show info with missing fields."""
    api_result = {
        "show": {}
    }

    show_id, name = extract_show_info(api_result)

    assert show_id == 0
    assert name == "Unknown"


def test_rank_search_results():
    """Test ranking search results."""
    api_results = [
        {
            "show": {
                "id": 1,
                "name": "Breaking Bad",
                "premiered": "2008-01-20",
                "status": "Ended"
            }
        },
        {
            "show": {
                "id": 2,
                "name": "Breaking In",
                "premiered": "2011-04-06",
                "status": "Ended"
            }
        },
        {
            "show": {
                "id": 3,
                "name": "The Breaking Point",
                "premiered": "2015-01-01",
                "status": "Ended"
            }
        },
    ]

    results = rank_search_results("breaking bad", api_results, limit=5)

    assert len(results) <= 5
    assert results[0].name == "Breaking Bad"  # Best match should be first
    assert all(r.score >= 0 for r in results)


def test_rank_search_results_empty():
    """Test ranking with no results."""
    results = rank_search_results("nonexistent", [], limit=5)

    assert len(results) == 0


def test_rank_search_results_limit():
    """Test ranking with limit."""
    api_results = [
        {"show": {"id": i, "name": f"Show {i}", "status": "Running"}}
        for i in range(10)
    ]

    results = rank_search_results("show", api_results, limit=3)

    assert len(results) == 3


def test_rank_search_results_no_year():
    """Test ranking results without premiere date."""
    api_results = [
        {
            "show": {
                "id": 1,
                "name": "Test Show",
                "status": "Running"
            }
        }
    ]

    results = rank_search_results("test", api_results)

    assert len(results) == 1
    assert results[0].year is None


def test_find_show_by_name_exact_match():
    """Test finding show by exact name match."""
    shows = [
        {"id": 1, "name": "Breaking Bad"},
        {"id": 2, "name": "The Wire"},
        {"id": 3, "name": "The Sopranos"},
    ]

    show_id = find_show_by_name("breaking bad", shows)

    assert show_id == 1


def test_find_show_by_name_partial_match():
    """Test finding show by partial name match."""
    shows = [
        {"id": 1, "name": "It's Always Sunny in Philadelphia"},
        {"id": 2, "name": "The Wire"},
    ]

    # Use lower threshold for partial matches
    show_id = find_show_by_name("always sunny", shows, threshold=40.0)

    assert show_id == 1


def test_find_show_by_name_fuzzy_match():
    """Test finding show by fuzzy match."""
    shows = [
        {"id": 1, "name": "The Office"},
        {"id": 2, "name": "Parks and Recreation"},
    ]

    # Use lower threshold for fuzzy typo matching
    show_id = find_show_by_name("ofice", shows, threshold=50.0)

    assert show_id == 1


def test_find_show_by_name_no_match():
    """Test finding show when there's no good match."""
    shows = [
        {"id": 1, "name": "Breaking Bad"},
        {"id": 2, "name": "The Wire"},
    ]

    show_id = find_show_by_name("totally different", shows, threshold=80.0)

    assert show_id is None


def test_find_show_by_name_empty_list():
    """Test finding show in empty list."""
    show_id = find_show_by_name("test", [])

    assert show_id is None


def test_format_search_result():
    """Test formatting search result."""
    result = SearchResult(
        show_id=123,
        name="Breaking Bad",
        year=2008,
        status="Ended",
        score=95.0
    )

    formatted = format_search_result(result, 1)

    assert "1." in formatted
    assert "Breaking Bad" in formatted
    assert "(2008)" in formatted
    assert "[Ended]" in formatted
    assert "95%" in formatted


def test_format_search_result_no_year():
    """Test formatting search result without year."""
    result = SearchResult(
        show_id=123,
        name="New Show",
        year=None,
        status="Running",
        score=85.0
    )

    formatted = format_search_result(result, 2)

    assert "2." in formatted
    assert "New Show" in formatted
    assert "[Running]" in formatted
    assert "()" not in formatted  # No empty parentheses
