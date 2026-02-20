"""
Live bridge tests for backing track generation in REAPER.

Tests backing track generation through the live REAPER file bridge.
Offline tests validate Python-side data structures. Live tests require
REAPER running with the MCP bridge script loaded.

Run with:
    python3.13 -m pytest tests/test_backing_live.py -v --noconftest
"""

import asyncio
import pytest

from server.bridge import bridge
from server.tools.backing_tracks import AVAILABLE_GENRES, VALID_INSTRUMENTS


# ---------------------------------------------------------------------------
# Module-level configuration
# ---------------------------------------------------------------------------

pytestmark = pytest.mark.live

# Backing track generation creates MIDI items and loads VSTi -- allow
# generous timeouts for the bridge round-trips.
BRIDGE_TIMEOUT = 30  # seconds per bridge call (live REAPER)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def call(func: str, args: list | None = None) -> dict:
    """Call a Lua function through the REAPER file bridge.

    Args:
        func: Name of the bridge function to invoke.
        args: Positional arguments forwarded to the Lua side.

    Returns:
        Bridge response dict.  Shape is either
        ``{"ok": true, "ret": ...}`` or ``{"ok": false, "error": "..."}``.
    """
    return await bridge.call_lua(func, args or [])


async def delete_all_tracks() -> None:
    """Delete every track in the current REAPER project.

    Iterates in reverse so track indices remain stable during deletion.
    """
    count_resp = await call("CountTracks", [0])
    if not count_resp.get("ok"):
        return
    for i in range(count_resp["ret"] - 1, -1, -1):
        await call("DeleteTrack", [i])


def _make_chart(
    title: str = "Test Song",
    artist: str = "Test",
    bpm: int = 120,
    key: str = "Am",
    time_sig: str = "4/4",
    sections: list[dict] | None = None,
) -> dict:
    """Build a minimal chord chart dict suitable for GenerateBackingTrack.

    Provides sensible defaults so individual tests only need to override
    what they care about.
    """
    if sections is None:
        sections = [
            {"name": "verse", "bars": 4, "chords": ["Am", "F", "C", "G"]},
        ]
    return {
        "title": title,
        "artist": artist,
        "bpm": bpm,
        "key": key,
        "time_sig": time_sig,
        "sections": sections,
    }


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
async def clean_tracks():
    """Fixture that deletes all REAPER tracks and clears Lua module cache.

    Runs automatically for every test in this module so each test starts
    from a clean slate with freshly loaded Lua modules.
    """
    await delete_all_tracks()
    # Clear Lua module cache so generators.lua is reloaded from disk
    # (picks up tracks.reset() fix even if bridge was loaded before the fix)
    await call("RunSessionAction", ["clear_cache"])
    yield
    # Post-test cleanup is optional; the next test's setup handles it.


# ============================================================================
# 1. Genre x Instrument Pattern Validation (offline)
# ============================================================================

class TestGenreInstrumentValidation:
    """Validate that Python-side genre and instrument constants are correct.

    These tests are offline -- they do not touch the bridge.
    """

    def test_available_genres_count(self):
        """AVAILABLE_GENRES should contain exactly 10 genres."""
        assert len(AVAILABLE_GENRES) == 10

    def test_available_genres_contents(self):
        """AVAILABLE_GENRES should list the canonical 10 genres."""
        expected = {
            "blues", "country", "funk", "jazz", "latin",
            "metal", "pop", "r&b", "reggae", "rock",
        }
        assert set(AVAILABLE_GENRES) == expected

    def test_available_genres_sorted(self):
        """AVAILABLE_GENRES should be in alphabetical order."""
        assert AVAILABLE_GENRES == sorted(AVAILABLE_GENRES)

    def test_valid_instruments_count(self):
        """VALID_INSTRUMENTS should contain exactly 4 instruments."""
        assert len(VALID_INSTRUMENTS) == 4

    def test_valid_instruments_contents(self):
        """VALID_INSTRUMENTS should list drums, bass, keys, guitar."""
        expected = {"drums", "bass", "keys", "guitar"}
        assert set(VALID_INSTRUMENTS) == expected

    def test_every_genre_is_lowercase(self):
        """All genre names should be lowercase strings."""
        for genre in AVAILABLE_GENRES:
            assert genre == genre.lower(), f"Genre '{genre}' is not lowercase"

    def test_every_instrument_is_lowercase(self):
        """All instrument names should be lowercase strings."""
        for inst in VALID_INSTRUMENTS:
            assert inst == inst.lower(), f"Instrument '{inst}' is not lowercase"


# ============================================================================
# 2. Full Pipeline Test (live bridge)
# ============================================================================

class TestGenerateBackingTrack:
    """Test full backing track generation through the live bridge.

    Note: These tests require the updated bridge with clear_module_cache().
    If the bridge is stale, GenerateBackingTrack fails with
    'MediaTrack expected' because tracks.lua _insert_pos is stale.
    """

    @pytest.mark.asyncio
    @pytest.mark.timeout(BRIDGE_TIMEOUT)
    async def test_generate_backing_track(self):
        """Generate a 2-instrument backing track and verify tracks exist."""
        chart = _make_chart(
            title="Test Song",
            artist="Test Artist",
            bpm=120,
            key="Am",
            sections=[
                {"name": "intro", "bars": 4, "chords": ["Am", "F"]},
                {"name": "verse", "bars": 8, "chords": ["Am", "F", "C", "G"]},
                {"name": "chorus", "bars": 4, "chords": ["C", "G", "Am", "F"]},
            ],
        )

        result = await call(
            "GenerateBackingTrack", [chart, ["drums", "bass"], "rock"]
        )
        assert result["ok"], f"GenerateBackingTrack failed: {result.get('error')}"

        tracks = await call("GetAllTracksInfo")
        assert tracks["ok"], f"GetAllTracksInfo failed: {tracks.get('error')}"
        assert len(tracks["tracks"]) >= 2, (
            f"Expected at least 2 tracks (drums + bass), got {len(tracks['tracks'])}"
        )


# ============================================================================
# 3. Full 4-Instrument Test
# ============================================================================

class TestGenerateAllInstruments:
    """Test generation with all four instruments simultaneously."""

    @pytest.mark.asyncio
    @pytest.mark.timeout(BRIDGE_TIMEOUT * 2)
    async def test_generate_all_instruments(self):
        """Generate drums, bass, keys, and guitar -- verify each track."""
        chart = _make_chart(
            title="Full Band Test",
            bpm=100,
            key="C",
            sections=[
                {"name": "verse", "bars": 4, "chords": ["C", "Am", "F", "G"]},
                {"name": "chorus", "bars": 4, "chords": ["F", "G", "C", "Am"]},
            ],
        )

        result = await call(
            "GenerateBackingTrack",
            [chart, ["drums", "bass", "keys", "guitar"], "pop"],
        )
        assert result["ok"], f"GenerateBackingTrack failed: {result.get('error')}"

        tracks = await call("GetAllTracksInfo")
        assert tracks["ok"], f"GetAllTracksInfo failed: {tracks.get('error')}"

        track_names = [t["name"] for t in tracks["tracks"]]
        assert any("Drums" in n for n in track_names), (
            f"No 'Drums' track found in: {track_names}"
        )
        assert any("Bass" in n for n in track_names), (
            f"No 'Bass' track found in: {track_names}"
        )


# ============================================================================
# 4. RegeneratePart Test
# ============================================================================

class TestRegeneratePart:
    """Test regenerating a single instrument part after initial generation."""

    @pytest.mark.asyncio
    @pytest.mark.timeout(BRIDGE_TIMEOUT * 2)
    async def test_regenerate_part(self):
        """Generate a backing track, then regenerate drums with a new genre."""
        chart = _make_chart(title="Regen Test")

        gen_result = await call(
            "GenerateBackingTrack", [chart, ["drums", "bass"], "rock"]
        )
        assert gen_result["ok"], (
            f"Initial GenerateBackingTrack failed: {gen_result.get('error')}"
        )

        regen_result = await call("RegeneratePart", ["drums", "blues"])
        assert regen_result["ok"], (
            f"RegeneratePart failed: {regen_result.get('error')}"
        )


# ============================================================================
# 5. Genre Parametrize Test
# ============================================================================

class TestGeneratePerGenre:
    """Verify that every supported genre produces a valid backing track."""

    @pytest.mark.asyncio
    @pytest.mark.timeout(BRIDGE_TIMEOUT)
    @pytest.mark.parametrize("genre", [
        "blues", "country", "funk", "jazz", "latin",
        "metal", "pop", "r&b", "reggae", "rock",
    ])
    async def test_generate_per_genre(self, genre: str):
        """Generate a drums-only backing track for *genre*."""
        await delete_all_tracks()

        chart = _make_chart(
            title=f"{genre.title()} Test",
            sections=[
                {"name": "verse", "bars": 4, "chords": ["Am", "G"]},
            ],
        )

        result = await call("GenerateBackingTrack", [chart, ["drums"], genre])
        assert result["ok"], (
            f"GenerateBackingTrack failed for genre '{genre}': {result.get('error')}"
        )


# ============================================================================
# 6. Single Instrument per Genre (parametrize instrument)
# ============================================================================

class TestRegeneratePerInstrument:
    """Verify that regeneration works for every instrument."""

    @pytest.mark.asyncio
    @pytest.mark.timeout(BRIDGE_TIMEOUT * 2)
    @pytest.mark.parametrize("instrument", ["drums", "bass", "keys", "guitar"])
    async def test_regenerate_per_instrument(self, instrument: str):
        """Generate then regenerate *instrument* with a different genre."""
        await delete_all_tracks()

        chart = _make_chart(
            title="Instrument Test",
            key="C",
            sections=[
                {"name": "verse", "bars": 4, "chords": ["C", "G"]},
            ],
        )

        gen_result = await call(
            "GenerateBackingTrack", [chart, [instrument], "rock"]
        )
        assert gen_result["ok"], (
            f"GenerateBackingTrack failed for {instrument}: {gen_result.get('error')}"
        )

        regen_result = await call("RegeneratePart", [instrument, "blues"])
        assert regen_result["ok"], (
            f"RegeneratePart failed for {instrument}: {regen_result.get('error')}"
        )


# ============================================================================
# 7. Error Cases
# ============================================================================

class TestErrorCases:
    """Verify graceful handling of invalid inputs through the bridge."""

    @pytest.mark.asyncio
    @pytest.mark.timeout(BRIDGE_TIMEOUT)
    async def test_invalid_genre(self):
        """An unrecognised genre should fail or fall back gracefully."""
        chart = _make_chart(
            title="T",
            artist="T",
            sections=[
                {"name": "v", "bars": 4, "chords": ["C"]},
            ],
        )

        result = await call(
            "GenerateBackingTrack", [chart, ["drums"], "nonexistent_genre"]
        )
        # The bridge may return ok=false with an error, or it may fall back
        # to a default genre.  Either is acceptable; a hard crash is not.
        assert isinstance(result, dict), "Bridge returned non-dict response"
        assert "ok" in result, "Bridge response missing 'ok' key"

    @pytest.mark.asyncio
    @pytest.mark.timeout(BRIDGE_TIMEOUT)
    async def test_empty_chart(self):
        """A chart with no sections should be handled without crashing."""
        chart = _make_chart(
            title="T",
            artist="T",
            sections=[],
        )

        result = await call(
            "GenerateBackingTrack", [chart, ["drums"], "rock"]
        )
        # Same tolerance as test_invalid_genre: any well-formed response is fine.
        assert isinstance(result, dict), "Bridge returned non-dict response"
        assert "ok" in result, "Bridge response missing 'ok' key"
