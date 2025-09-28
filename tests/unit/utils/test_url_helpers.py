"""Tests for URL helper utilities."""

import pytest

from api.utils.url_helpers import extract_id_from_url


class TestUrlHelpers:
    """Test cases for URL helper functions."""

    def test_extract_id_from_url_with_trailing_slash(self):
        """Test extracting ID from URL with trailing slash."""
        url = "https://swapi.dev/api/people/42/"
        result = extract_id_from_url(url)
        assert result == 42

    def test_extract_id_from_url_without_trailing_slash(self):
        """Test extracting ID from URL without trailing slash."""
        url = "https://swapi.dev/api/people/42"
        result = extract_id_from_url(url)
        assert result == 42

    def test_extract_id_from_url_different_endpoints(self):
        """Test extracting ID from different SWAPI endpoints."""
        test_cases = [
            ("https://swapi.dev/api/films/1/", 1),
            ("https://swapi.dev/api/starships/12/", 12),
            ("https://swapi.dev/api/planets/3/", 3),
            ("https://swapi.dev/api/vehicles/14", 14),
        ]

        for url, expected_id in test_cases:
            result = extract_id_from_url(url)
            assert result == expected_id

    def test_extract_id_from_url_invalid_url(self):
        """Test handling of invalid URLs."""
        with pytest.raises((ValueError, IndexError, AttributeError)):
            extract_id_from_url("invalid-url")

    def test_extract_id_from_url_no_id(self):
        """Test handling of URLs without numeric ID."""
        with pytest.raises((ValueError, IndexError, AttributeError)):
            extract_id_from_url("https://swapi.dev/api/people/")

    def test_extract_id_from_url_non_numeric_id(self):
        """Test handling of URLs with non-numeric ID."""
        with pytest.raises((ValueError, TypeError)):
            extract_id_from_url("https://swapi.dev/api/people/abc/")
