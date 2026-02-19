# tests/test_backing_tracks.py
"""
Tests for Backing Track tools and DSL wrappers.

Tests that work without REAPER running:
- Tool registration count
- Genre list completeness
- Instrument validation
- DSL natural language parsing
"""

import pytest
from unittest.mock import MagicMock


# ============================================================================
# Tool Registration Tests
# ============================================================================

class TestBackingTrackToolRegistration:
    """Verify backing track tools register the expected count."""

    def test_register_returns_correct_count(self):
        from server.tools.backing_tracks import register_backing_track_tools

        mock_mcp = MagicMock()
        mock_mcp.tool.return_value = lambda f: f

        count = register_backing_track_tools(mock_mcp)
        # 5 direct tools + 1 DSL wrapper = 6
        assert count == 6


# ============================================================================
# Genre List Tests
# ============================================================================

class TestGenreList:
    """Verify AVAILABLE_GENRES has all 10 expected genres."""

    def test_available_genres_count(self):
        from server.tools.backing_tracks import AVAILABLE_GENRES
        assert len(AVAILABLE_GENRES) == 10

    def test_available_genres_contents(self):
        from server.tools.backing_tracks import AVAILABLE_GENRES
        expected = {
            "blues", "country", "funk", "jazz", "latin",
            "metal", "pop", "r&b", "reggae", "rock",
        }
        assert set(AVAILABLE_GENRES) == expected

    def test_available_genres_sorted(self):
        from server.tools.backing_tracks import AVAILABLE_GENRES
        assert AVAILABLE_GENRES == sorted(AVAILABLE_GENRES)

    def test_genre_descriptions_match(self):
        from server.tools.backing_tracks import AVAILABLE_GENRES, GENRE_DESCRIPTIONS
        for genre in AVAILABLE_GENRES:
            assert genre in GENRE_DESCRIPTIONS, f"Missing description for '{genre}'"


# ============================================================================
# Instrument Validation Tests
# ============================================================================

class TestInstrumentValidation:
    """Verify VALID_INSTRUMENTS has all 4 expected instruments."""

    def test_valid_instruments_count(self):
        from server.tools.backing_tracks import VALID_INSTRUMENTS
        assert len(VALID_INSTRUMENTS) == 4

    def test_valid_instruments_contents(self):
        from server.tools.backing_tracks import VALID_INSTRUMENTS
        expected = {"drums", "bass", "keys", "guitar"}
        assert set(VALID_INSTRUMENTS) == expected


# ============================================================================
# DSL Parsing Tests
# ============================================================================

class TestDSLParsing:
    """Test natural language parsing of backing track requests."""

    def test_parse_backing_track_request(self):
        from server.dsl.backing_wrappers import parse_backing_request
        result = parse_backing_request("backing track for Wonderwall by Oasis")
        assert result is not None
        assert result["song"] == "Wonderwall"
        assert result["artist"] == "Oasis"

    def test_parse_jam_track_request(self):
        from server.dsl.backing_wrappers import parse_backing_request
        result = parse_backing_request("jam track for Superstition by Stevie Wonder")
        assert result is not None
        assert result["song"] == "Superstition"
        assert result["artist"] == "Stevie Wonder"

    def test_parse_simple_format(self):
        from server.dsl.backing_wrappers import parse_backing_request
        result = parse_backing_request("Hotel California by Eagles")
        assert result is not None
        assert result["song"] == "Hotel California"
        assert result["artist"] == "Eagles"

    def test_parse_quoted_format(self):
        from server.dsl.backing_wrappers import parse_backing_request
        result = parse_backing_request('"Bohemian Rhapsody" by "Queen"')
        assert result is not None
        assert result["song"] == "Bohemian Rhapsody"
        assert result["artist"] == "Queen"

    def test_parse_unknown_returns_none(self):
        from server.dsl.backing_wrappers import parse_backing_request
        result = parse_backing_request("make me a sandwich")
        assert result is None


# ============================================================================
# Tool Profile Tests
# ============================================================================

class TestBackingTrackProfile:
    """Test backing-track profile configuration."""

    def test_backing_track_profile_exists(self):
        from server.tool_profiles import TOOL_PROFILES
        assert "backing-track" in TOOL_PROFILES

    def test_backing_track_profile_includes_backing_tracks(self):
        from server.tool_profiles import TOOL_PROFILES
        profile = TOOL_PROFILES["backing-track"]
        assert "Backing Tracks" in profile["categories"]

    def test_backing_track_profile_includes_dependencies(self):
        from server.tool_profiles import TOOL_PROFILES
        categories = TOOL_PROFILES["backing-track"]["categories"]
        assert "MIDI" in categories
        assert "Tracks" in categories
        assert "FX" in categories
        assert "Transport" in categories
        assert "Project" in categories
