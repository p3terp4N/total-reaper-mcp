# tests/test_backing_tracks.py
"""
Tests for Backing Track tools and DSL wrappers.

Tests that work without REAPER running:
- Tool registration count
- Genre list completeness
- Instrument validation
- DSL natural language parsing
- Integration tests (mocked bridge)
"""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch


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


# ============================================================================
# Integration Tests (mocked bridge, no REAPER needed)
# ============================================================================

class TestGenerateBackingTrack:
    """Test generate_backing_track with mocked dependencies."""

    @pytest.mark.asyncio
    async def test_invalid_instruments_rejected(self):
        from server.tools.backing_tracks import generate_backing_track
        result = await generate_backing_track("Test", "Artist", instruments="drums,banjo")
        assert "Invalid instruments" in result
        assert "banjo" in result

    @pytest.mark.asyncio
    async def test_all_invalid_instruments_rejected(self):
        from server.tools.backing_tracks import generate_backing_track
        result = await generate_backing_track("Test", "Artist", instruments="violin,cello")
        assert "Invalid instruments" in result
        assert "violin" in result
        assert "cello" in result

    @pytest.mark.asyncio
    async def test_lookup_failure_returns_message(self):
        from server.tools.backing_tracks import generate_backing_track
        with patch("server.tools.backing_tracks.lookup_song", return_value=None):
            result = await generate_backing_track("Nonexistent", "Nobody")
        assert "Could not find chord chart" in result
        assert "manual_chart()" in result

    @pytest.mark.asyncio
    async def test_successful_generation_with_mocked_bridge(self):
        from server.tools.backing_tracks import generate_backing_track

        fake_chart = {
            "title": "Test Song", "artist": "Test Artist",
            "key": "C", "bpm": 120, "time_sig": "4/4",
            "sections": [{"name": "verse", "bars": 4, "chords": ["C", "G", "Am", "F"]}],
        }
        fake_bridge_result = {
            "ok": True,
            "ret": {"tracks": ["drums", "bass"]},
        }

        with patch("server.tools.backing_tracks.lookup_song", return_value=fake_chart), \
             patch("server.tools.backing_tracks.bridge") as mock_bridge:
            mock_bridge.call_lua = AsyncMock(return_value=fake_bridge_result)
            result = await generate_backing_track("Test Song", "Test Artist")

        assert "Backing track generated" in result
        assert "C" in result
        assert "120 BPM" in result

    @pytest.mark.asyncio
    async def test_bridge_failure_raises(self):
        from server.tools.backing_tracks import generate_backing_track

        fake_chart = {
            "title": "Test", "artist": "Test",
            "key": "Am", "bpm": 100, "time_sig": "4/4",
            "sections": [{"name": "verse", "bars": 4, "chords": ["Am"]}],
        }

        with patch("server.tools.backing_tracks.lookup_song", return_value=fake_chart), \
             patch("server.tools.backing_tracks.bridge") as mock_bridge:
            mock_bridge.call_lua = AsyncMock(return_value={"ok": False, "error": "Lua error"})
            with pytest.raises(Exception, match="Lua error"):
                await generate_backing_track("Test", "Test")


class TestManualChart:
    """Test manual_chart with mocked bridge."""

    @pytest.mark.asyncio
    async def test_invalid_instruments_rejected(self):
        from server.tools.backing_tracks import manual_chart
        result = await manual_chart("[Verse] C G Am F", instruments="drums,tuba")
        assert "Invalid instruments" in result
        assert "tuba" in result

    @pytest.mark.asyncio
    async def test_empty_chart_returns_message(self):
        from server.tools.backing_tracks import manual_chart
        result = await manual_chart("no sections here")
        assert "No sections found" in result

    @pytest.mark.asyncio
    async def test_successful_manual_chart(self):
        from server.tools.backing_tracks import manual_chart

        fake_bridge_result = {
            "ok": True,
            "ret": {"tracks": ["drums", "bass"]},
        }

        with patch("server.tools.backing_tracks.bridge") as mock_bridge:
            mock_bridge.call_lua = AsyncMock(return_value=fake_bridge_result)
            result = await manual_chart(
                "[Verse]\nC G Am F",
                title="My Song",
                bpm=100,
            )

        assert "Backing track generated from manual chart" in result
        assert "My Song" in result


class TestDSLMakeBackingTrack:
    """Test the DSL make_backing_track wrapper."""

    @pytest.mark.asyncio
    async def test_unparseable_returns_help(self):
        from server.dsl.backing_wrappers import make_backing_track
        result = await make_backing_track("just play something cool")
        assert "Could not parse" in result
        assert "Try formats like" in result

    @pytest.mark.asyncio
    async def test_parsed_request_calls_generate(self):
        from server.dsl.backing_wrappers import make_backing_track

        with patch("server.tools.backing_tracks.generate_backing_track", new_callable=AsyncMock) as mock_gen:
            mock_gen.return_value = "Generated!"
            result = await make_backing_track("backing track for Test by Artist")

        mock_gen.assert_called_once_with(
            song="Test", artist="Artist", instruments="drums,bass", style="genre",
        )
        assert result == "Generated!"


class TestListBackingGenres:
    """Test list_backing_genres output."""

    @pytest.mark.asyncio
    async def test_list_genres_contains_all(self):
        from server.tools.backing_tracks import list_backing_genres, AVAILABLE_GENRES
        result = await list_backing_genres()
        for genre in AVAILABLE_GENRES:
            assert genre in result

    @pytest.mark.asyncio
    async def test_list_genres_has_header(self):
        from server.tools.backing_tracks import list_backing_genres
        result = await list_backing_genres()
        assert "Available backing track genres:" in result


class TestGetSongChart:
    """Test get_song_chart with mocked lookup."""

    @pytest.mark.asyncio
    async def test_chart_not_found(self):
        from server.tools.backing_tracks import get_song_chart
        with patch("server.tools.backing_tracks.lookup_song", return_value=None):
            result = await get_song_chart("Nothing", "Nobody")
        assert "Could not find chord chart" in result

    @pytest.mark.asyncio
    async def test_chart_found_returns_formatted(self):
        from server.tools.backing_tracks import get_song_chart

        fake_chart = {
            "title": "Test", "artist": "Artist",
            "key": "G", "bpm": 110, "time_sig": "4/4",
            "sections": [{"name": "Verse", "bars": 4, "chords": ["G", "D", "Em", "C"]}],
        }

        with patch("server.tools.backing_tracks.lookup_song", return_value=fake_chart):
            result = await get_song_chart("Test", "Artist")

        assert "Chart: Test by Artist" in result
        assert "Key: G" in result
        assert "BPM: 110" in result
        assert "[Verse]" in result
        assert "G | D | Em | C" in result
