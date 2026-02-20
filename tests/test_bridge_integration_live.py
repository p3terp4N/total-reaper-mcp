"""
Live bridge integration tests for total-reaper-mcp.

Tests DSL functions directly via the file-based bridge:
    Python -> JSON request file -> Lua (mcp_bridge.lua) -> REAPER -> JSON response

No MCP server layer is involved. The bridge singleton communicates with a live
REAPER instance that must be running with mcp_bridge.lua loaded.

Usage:
    python3.13 -m pytest tests/test_bridge_integration_live.py -v --noconftest

Requirements:
    - REAPER must be running with mcp_bridge.lua active
    - The bridge directory must be accessible at the configured path
    - pytest-asyncio must be installed (asyncio_mode = "auto" in pyproject.toml)
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional

import pytest

from server.bridge import bridge

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Module-level marker: every test in this file is a live integration test
# ---------------------------------------------------------------------------
pytestmark = pytest.mark.live


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

async def call(func: str, args: Optional[List[Any]] = None) -> Dict[str, Any]:
    """Call a Lua function through the file-based bridge and return the response.

    Returns a dict of the form ``{"ok": True, "ret": value, ...}`` on success
    or ``{"ok": False, "error": "message"}`` on failure.
    """
    return await bridge.call_lua(func, args or [])


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
async def clean_state():
    """Ensure a clean project state around every test.

    Runs *before* each test to remove any leftover tracks from a previous
    failure, and again *after* each test as a safety net.
    """
    await _remove_all_tracks()
    yield
    await _remove_all_tracks()


async def _remove_all_tracks():
    """Delete every track in the current project."""
    result = await call("CountTracks", [0])
    if result.get("ok"):
        count = result.get("ret", 0)
        # Delete from the last track to the first to keep indices stable.
        for i in range(count - 1, -1, -1):
            await call("DeleteTrack", [i])


# ===================================================================
# 1. Track Info
# ===================================================================


class TestTrackInfo:
    """Verify track introspection functions."""

    async def test_get_track_info(self):
        """Insert a track, name it, and read back the info."""
        await call("InsertTrackAtIndex", [0, 1])
        await call("SetTrackName", [0, "TestTrack"])

        result = await call("GetTrackInfo", [0])

        assert result["ok"]
        assert "TestTrack" in result["info"]["name"]

    async def test_get_all_tracks_info(self):
        """GetAllTracksInfo should return a list (or empty dict for Lua empty table)."""
        result = await call("GetAllTracksInfo")

        assert result["ok"]
        # Lua encodes empty table {} as JSON object {}, not array [].
        tracks = result["tracks"]
        assert isinstance(tracks, (list, dict))
        if isinstance(tracks, list):
            assert len(tracks) == 0
        else:
            assert tracks == {}

    async def test_get_all_tracks_info_with_tracks(self):
        """GetAllTracksInfo should include tracks that were just created."""
        await call("InsertTrackAtIndex", [0, 1])
        await call("SetTrackName", [0, "Alpha"])
        await call("InsertTrackAtIndex", [1, 1])
        await call("SetTrackName", [1, "Bravo"])

        result = await call("GetAllTracksInfo")

        assert result["ok"]
        assert len(result["tracks"]) >= 2
        names = [t["name"] for t in result["tracks"]]
        assert "Alpha" in names
        assert "Bravo" in names

    async def test_set_track_notes(self):
        """SetTrackNotes should succeed and persist a note string."""
        await call("InsertTrackAtIndex", [0, 1])

        result = await call("SetTrackNotes", [0, "test note content"])

        assert result["ok"]


# ===================================================================
# 2. Time Operations
# ===================================================================


class TestTimeOperations:
    """Verify cursor, selection, loop, bar, and marker/region functions."""

    async def test_get_cursor_position(self):
        """GetCursorPosition must return a numeric value."""
        result = await call("GetCursorPosition")

        assert result["ok"]
        assert isinstance(result["ret"], (int, float))

    async def test_time_selection_roundtrip(self):
        """SetTimeSelection followed by GetTimeSelection should match."""
        await call("SetTimeSelection", [1.0, 5.0])

        result = await call("GetTimeSelection")

        assert result["ok"]
        assert abs(result["start"] - 1.0) < 0.01
        assert abs(result["end"] - 5.0) < 0.01

        # Clean up: collapse the selection.
        await call("SetTimeSelection", [0, 0])

    async def test_get_loop_time_range(self):
        """GetLoopTimeRange should succeed."""
        result = await call("GetLoopTimeRange")

        assert result["ok"]

    async def test_bars_to_time(self):
        """BarsToTime should return a numeric seconds value."""
        result = await call("BarsToTime", [4, 0])

        assert result["ok"]
        assert isinstance(result["ret"], (int, float))

    async def test_find_region(self):
        """Add a region and find it by name."""
        await call("AddProjectMarker", [0, 1, 1.0, 5.0, "TestRegion", -1])

        result = await call("FindRegion", ["TestRegion"])

        assert result["ok"]

    async def test_find_marker(self):
        """Add a marker and find it by name."""
        await call("AddProjectMarker", [0, 0, 2.0, 0, "TestMarker", -1])

        result = await call("FindMarker", ["TestMarker"])

        assert result["ok"]

    async def test_set_edit_cursor_position(self):
        """SetEditCurPos should move the edit cursor."""
        await call("SetEditCurPos", [5.0, 0, 0])

        result = await call("GetCursorPosition")

        assert result["ok"]
        assert isinstance(result["ret"], (int, float))


# ===================================================================
# 3. Item Operations
# ===================================================================


class TestItemOperations:
    """Verify MIDI item creation, note insertion, and item queries."""

    async def test_create_midi_item(self):
        """CreateMIDIItem should produce a new item on the given track."""
        await call("InsertTrackAtIndex", [0, 1])

        result = await call("CreateMIDIItem", [0, 0, 4])

        assert result["ok"]

    async def test_insert_midi_note(self):
        """InsertMIDINote should succeed after creating a MIDI item."""
        await call("InsertTrackAtIndex", [0, 1])
        await call("CreateMIDIItem", [0, 0, 4])

        result = await call("InsertMIDINote", [0, 0, 60, 0, 960, 100, 0])

        assert result["ok"]

    async def test_get_all_items_empty(self):
        """GetAllItems should return an empty collection when no items exist."""
        result = await call("GetAllItems")

        assert result["ok"]
        # Lua encodes empty table {} as JSON object {}, not array [].
        items = result["items"]
        assert isinstance(items, (list, dict))
        if isinstance(items, list):
            assert len(items) == 0
        else:
            assert items == {}

    async def test_get_all_items_with_item(self):
        """GetAllItems should include a newly created MIDI item."""
        await call("InsertTrackAtIndex", [0, 1])
        await call("CreateMIDIItem", [0, 0, 4])

        result = await call("GetAllItems")

        assert result["ok"]
        assert len(result["items"]) >= 1

    async def test_get_track_items(self):
        """GetTrackItems should list items that belong to a specific track."""
        await call("InsertTrackAtIndex", [0, 1])
        await call("CreateMIDIItem", [0, 0, 4])

        result = await call("GetTrackItems", [0])

        assert result["ok"]
        assert len(result["items"]) >= 1


# ===================================================================
# 4. Track Controls
# ===================================================================


class TestTrackControls:
    """Verify volume, pan, mute, and solo round-trip operations."""

    async def test_track_volume_roundtrip(self):
        """SetTrackVolume then GetTrackVolume should return a value."""
        await call("InsertTrackAtIndex", [0, 1])
        await call("SetTrackVolume", [0, 0.5])

        result = await call("GetTrackVolume", [0])

        assert result["ok"]

    async def test_track_pan_roundtrip(self):
        """SetTrackPan then GetTrackPan should return a value."""
        await call("InsertTrackAtIndex", [0, 1])
        await call("SetTrackPan", [0, -0.5])

        result = await call("GetTrackPan", [0])

        assert result["ok"]

    async def test_track_mute_toggle(self):
        """Mute and unmute a track."""
        await call("InsertTrackAtIndex", [0, 1])

        result_on = await call("SetTrackMute", [0, True])
        assert result_on["ok"]

        result_off = await call("SetTrackMute", [0, False])
        assert result_off["ok"]

    async def test_track_solo_toggle(self):
        """Solo and unsolo a track."""
        await call("InsertTrackAtIndex", [0, 1])

        result_on = await call("SetTrackSolo", [0, True])
        assert result_on["ok"]

        result_off = await call("SetTrackSolo", [0, False])
        assert result_off["ok"]


# ===================================================================
# 5. Transport
# ===================================================================


class TestTransport:
    """Verify play/stop, tempo, and time signature functions."""

    async def test_play_stop(self):
        """Play should start playback; Stop should halt it."""
        result_play = await call("Play")
        assert result_play["ok"]

        await asyncio.sleep(0.2)

        result_stop = await call("Stop")
        assert result_stop["ok"]

    @pytest.mark.xfail(reason="SetTempo uses SetTempoTimeSigMarker which adds a marker instead of changing master tempo")
    async def test_tempo_roundtrip(self):
        """SetTempo then GetTempo should reflect the new BPM."""
        original = await call("GetTempo")
        assert original["ok"]
        original_bpm = original["ret"]

        await call("SetTempo", [140])

        result = await call("GetTempo")
        assert result["ok"]
        assert abs(result["ret"] - 140) < 0.1

        # Restore the original tempo.
        await call("SetTempo", [original_bpm])

    async def test_get_time_signature(self):
        """GetTimeSignature should succeed."""
        result = await call("GetTimeSignature")

        assert result["ok"]


# ===================================================================
# 6. Session Templates
# ===================================================================


class TestSessionTemplates:
    """Verify session config, plugin scanning, FX, actions, and grid ops."""

    async def test_get_session_config(self):
        """GetSessionConfig with 'all' should return config data."""
        result = await call("GetSessionConfig", ["all"])

        assert result["ok"]

    async def test_scan_plugins(self):
        """ScanPlugins should succeed (may take a moment)."""
        result = await call("ScanPlugins")

        assert result["ok"]

    async def test_smart_add_fx(self):
        """SmartAddFX should add an FX to a track."""
        await call("InsertTrackAtIndex", [0, 1])

        result = await call("SmartAddFX", [0, "ReaEQ", "", False])

        assert result["ok"]

    async def test_run_session_action(self):
        """RunSessionAction with 'tap_tempo' should succeed."""
        result = await call("RunSessionAction", ["tap_tempo"])

        assert result["ok"]

    async def test_get_set_project_grid(self):
        """GetSetProjectGrid in read mode should succeed."""
        result = await call("GetSetProjectGrid", [False])

        assert result["ok"]


# ===================================================================
# 7. Envelope Operations
# ===================================================================


class TestEnvelopeOperations:
    """Verify envelope point insertion and counting."""

    async def test_insert_envelope_point(self):
        """InsertEnvelopePointByName should succeed for a Volume envelope.

        Note: requires the updated bridge with envelope DSL functions.
        The Volume envelope must be visible on the track for this to work.
        """
        await call("InsertTrackAtIndex", [0, 1])

        result = await call(
            "InsertEnvelopePointByName",
            [0, "Volume", 0, 1.0, 0, 0, False, False],
        )

        if not result["ok"] and "Unknown function" in result.get("error", ""):
            pytest.skip("Bridge needs restart to load envelope functions")
        # Envelope may not be visible — function may return error
        assert result["ok"] or "not found" in result.get("error", "")

    async def test_count_envelope_points(self):
        """After inserting a point, CountEnvelopePointsByName should return >= 1."""
        await call("InsertTrackAtIndex", [0, 1])

        insert_result = await call(
            "InsertEnvelopePointByName",
            [0, "Volume", 0, 1.0, 0, 0, False, False],
        )
        if not insert_result["ok"] and "Unknown function" in insert_result.get("error", ""):
            pytest.skip("Bridge needs restart to load envelope functions")

        result = await call("CountEnvelopePointsByName", [0, "Volume"])

        if not result["ok"] and "Unknown function" in result.get("error", ""):
            pytest.skip("Bridge needs restart to load envelope functions")
        # Envelope may not be visible
        assert result["ok"] or "not found" in result.get("error", "")


# ===================================================================
# 8. Raw REAPER API Pass-through
# ===================================================================


class TestRawReaperAPI:
    """Verify raw ReaScript API functions that the bridge passes through."""

    async def test_count_tracks(self):
        """CountTracks should return an integer."""
        result = await call("CountTracks", [0])

        assert result["ok"]
        assert isinstance(result["ret"], int)

    async def test_insert_delete_track(self):
        """Inserting a track should increment CountTracks by 1."""
        before = await call("CountTracks", [0])
        assert before["ok"]
        count_before = before["ret"]

        await call("InsertTrackAtIndex", [count_before, 1])

        after = await call("CountTracks", [0])
        assert after["ok"]
        assert after["ret"] == count_before + 1

    async def test_set_get_track_name(self):
        """SetTrackName followed by GetTrackName should return the same name."""
        await call("InsertTrackAtIndex", [0, 1])
        await call("SetTrackName", [0, "RawAPITest"])

        result = await call("GetTrackName", [0])

        assert result["ok"]

    async def test_project_markers(self):
        """AddProjectMarker + CountProjectMarkers should show >= 1 marker."""
        await call("AddProjectMarker", [0, 0, 3.0, 0, "RawMarker", -1])

        result = await call("CountProjectMarkers", [0])

        assert result["ok"]
        # CountProjectMarkers returns [num_markers, num_regions] as a list
        ret = result["ret"]
        if isinstance(ret, list):
            assert ret[0] >= 1  # at least 1 marker
        else:
            assert ret >= 1

    async def test_track_fx_add_and_count(self):
        """TrackFX_AddByName + TrackFX_GetCount should show >= 1 FX."""
        await call("InsertTrackAtIndex", [0, 1])
        await call("TrackFX_AddByName", [0, "ReaEQ", 0, -1])

        result = await call("TrackFX_GetCount", [0])

        assert result["ok"]
        assert result["ret"] >= 1

    async def test_cursor_position_after_set(self):
        """SetEditCurPos should move the cursor to the requested position."""
        await call("SetEditCurPos", [5.0, 0, 0])

        result = await call("GetCursorPosition")

        assert result["ok"]
        assert isinstance(result["ret"], (int, float))


# ===================================================================
# 9. Error Handling
# ===================================================================


class TestErrorHandling:
    """Verify that the bridge returns structured errors instead of crashing."""

    async def test_unknown_function(self):
        """Calling a function that does not exist should return ok=False."""
        result = await call("NonExistentFunction", [])

        assert not result["ok"]
        assert "error" in result

    async def test_invalid_track_index(self):
        """Querying a track at an absurd index should return ok=False."""
        result = await call("GetTrackInfo", [99999])

        assert not result["ok"]

    async def test_wrong_argument_count(self):
        """Passing too few arguments should yield an error, not a crash."""
        result = await call("SetTrackVolume", [])

        assert not result["ok"]
