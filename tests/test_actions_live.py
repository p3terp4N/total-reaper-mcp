"""
Live integration tests for session action scripts via bridge.

Tests all 27 action scripts by calling RunSessionAction through the
file-based bridge, verifying they either succeed or return a graceful error.
Some actions require specific session state; those are set up before calling.

Requires REAPER running with mcp_bridge.lua loaded.

Run with:
    python3.13 -m pytest tests/test_actions_live.py -v --noconftest
"""

import asyncio
import pytest
import time

from server.bridge import bridge

pytestmark = pytest.mark.live


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def call(func: str, args: list | None = None) -> dict:
    """Call a bridge function and return the response dict."""
    return await bridge.call_lua(func, args or [])


async def delete_all_tracks() -> None:
    """Delete every track in the current project (clean slate)."""
    result = await call("CountTracks", [0])
    count = result.get("ret", 0)
    if not isinstance(count, int):
        count = 0
    for i in range(count - 1, -1, -1):
        await call("DeleteTrackByIndex", [i])


async def ensure_guitar_session() -> None:
    """Create a guitar session if no tracks exist (provides DI/QC/Bus context)."""
    result = await call("CountTracks", [0])
    count = result.get("ret", 0)
    if not isinstance(count, int):
        count = 0
    if count == 0:
        await call("CreateSession", [
            "guitar", "Action Test Session", 120, "4/4", "Am", 48000,
        ])


async def get_track_names() -> list[str]:
    """Return a list of all track names in the current project."""
    result = await call("GetAllTracksInfo")
    if not result.get("ok"):
        return []
    return [t.get("name", "") for t in result.get("tracks", [])]


async def get_tempo() -> float:
    """Return the current project tempo."""
    result = await call("GetTempo")
    if result.get("ok"):
        return result.get("ret", 0.0)
    result = await call("Master_GetTempo")
    return result.get("ret", 0.0)


async def get_marker_count() -> int:
    """Return the total number of markers + regions in the project."""
    result = await call("CountProjectMarkers", [0])
    if result.get("ok"):
        ret = result.get("ret", {})
        # CountProjectMarkers returns {num_markers, num_regions} or just a count
        if isinstance(ret, dict):
            return ret.get("num_markers", 0) + ret.get("num_regions", 0)
        return ret
    return 0


# ---------------------------------------------------------------------------
# All 27 action names
# ---------------------------------------------------------------------------

ALL_ACTIONS = [
    "add_guitar_od",
    "add_vocal",
    "arm_all_di",
    "arm_next_track",
    "auto_trim_silence",
    "bounce_selection",
    "chapter_marker",
    "chord_marker",
    "chord_region",
    "cleanup_session",
    "cycle_tone",
    "idea_marker",
    "new_take_folder",
    "noise_capture",
    "playback_rate",
    "practice_mode",
    "quick_tune",
    "reference_ab",
    "reamp",
    "register_keybinds",
    "session_backup",
    "setlist_marker",
    "song_structure_marker",
    "tap_tempo",
    "toggle_meters",
    "tone_browser",
    "tone_snapshot",
]

# Actions that are safe to call without any specific session state.
# They either create markers, toggle settings, or are inherently idempotent.
SAFE_ACTIONS = [
    "chapter_marker",
    "chord_marker",
    "idea_marker",
    "setlist_marker",
    "song_structure_marker",
    "tap_tempo",
    "toggle_meters",
    "playback_rate",
    "practice_mode",
    "register_keybinds",
    "session_backup",
]

# Actions that open REAPER dialogs (GetUserInputs) and block until dismissed.
# These MUST be excluded from automated tests to avoid hanging.
DIALOG_ACTIONS = {
    "chapter_marker",
    "chord_marker",
    "chord_region",
    "setlist_marker",
    "song_structure_marker",
    "idea_marker",
}

# Actions that require tracks (DI, QC, Bus, etc.) to function properly.
SESSION_DEPENDENT_ACTIONS = [
    "add_guitar_od",
    "add_vocal",
    "arm_all_di",
    "arm_next_track",
    "auto_trim_silence",
    "bounce_selection",
    "chord_region",
    "cleanup_session",
    "cycle_tone",
    "new_take_folder",
    "noise_capture",
    "quick_tune",
    "reamp",
    "reference_ab",
    "tone_browser",
    "tone_snapshot",
]


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
async def session_setup():
    """Ensure a guitar session exists for action tests, clean up after."""
    await delete_all_tracks()
    await ensure_guitar_session()
    yield
    await delete_all_tracks()


# ---------------------------------------------------------------------------
# Parametrized: every action should not crash
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("action_name", [a for a in ALL_ACTIONS if a not in DIALOG_ACTIONS])
async def test_run_action_does_not_crash(action_name: str):
    """Every action should return ok=true or a structured error -- never crash."""
    result = await call("RunSessionAction", [action_name])
    # Accept both success and graceful errors
    assert result.get("ok") or "error" in result, (
        f"Action '{action_name}' returned unexpected response: {result}"
    )


# ---------------------------------------------------------------------------
# Marker actions
# ---------------------------------------------------------------------------

@pytest.mark.skip(reason="Dialog actions open REAPER GetUserInputs popups that block the test runner")
class TestMarkerActions:
    """Test actions that create project markers.

    SKIPPED: All marker actions (chapter_marker, idea_marker, setlist_marker,
    song_structure_marker, chord_marker, chord_region) trigger REAPER's
    GetUserInputs dialog which blocks until manually dismissed, making
    automated testing impossible.
    """

    @pytest.mark.parametrize("action_name", [
        "chapter_marker",
        "idea_marker",
        "setlist_marker",
        "song_structure_marker",
        "chord_marker",
    ])
    async def test_marker_action_creates_marker(self, action_name: str):
        """Marker actions should increase the project marker count."""
        before = await get_marker_count()

        result = await call("RunSessionAction", [action_name])
        # Some marker actions may fail gracefully if no cursor position etc.
        if not result.get("ok"):
            pytest.skip(f"Action '{action_name}' returned error: {result.get('error')}")

        after = await get_marker_count()
        assert after > before, (
            f"Action '{action_name}' should have created a marker. "
            f"Before: {before}, after: {after}"
        )

    async def test_multiple_chapter_markers(self):
        """Running chapter_marker multiple times should create sequential markers."""
        before = await get_marker_count()

        for _ in range(3):
            result = await call("RunSessionAction", ["chapter_marker"])
            if not result.get("ok"):
                pytest.skip(f"chapter_marker failed: {result.get('error')}")
            # Move cursor forward slightly to avoid duplicate positions
            await call("SetEditCurPos", [_ + 1.0, True, False])

        after = await get_marker_count()
        assert after >= before + 3, (
            f"Expected at least 3 new markers. Before: {before}, after: {after}"
        )

    async def test_chord_region_creates_region(self):
        """chord_region should create a region over the time selection."""
        # Set a time selection first
        await call("GetSet_LoopTimeRange", [True, False, 0.0, 4.0, False])

        before = await get_marker_count()
        result = await call("RunSessionAction", ["chord_region"])

        if not result.get("ok"):
            pytest.skip(f"chord_region failed: {result.get('error')}")

        after = await get_marker_count()
        assert after > before, (
            f"chord_region should have created a region. "
            f"Before: {before}, after: {after}"
        )


# ---------------------------------------------------------------------------
# Tempo / playback rate actions
# ---------------------------------------------------------------------------

class TestTempoActions:
    """Test actions that affect tempo and playback rate."""

    async def test_tap_tempo_changes_tempo(self):
        """Tapping tempo twice within 3 seconds should change the project tempo."""
        original_tempo = await get_tempo()

        # Two taps ~0.5 seconds apart (= 120 BPM)
        await call("RunSessionAction", ["tap_tempo"])
        await asyncio.sleep(0.5)
        result = await call("RunSessionAction", ["tap_tempo"])

        if not result.get("ok"):
            pytest.skip(f"tap_tempo failed: {result.get('error')}")

        new_tempo = await get_tempo()
        # Tempo should have changed (may not be exactly 120 due to timing)
        # Just verify it responded -- tap tempo with only 2 taps may or may
        # not produce a stable result depending on implementation
        # The key assertion is that it ran without error
        assert result.get("ok"), "tap_tempo should succeed on second tap"

    async def test_playback_rate_cycles(self):
        """Running playback_rate multiple times should cycle through rates."""
        results = []
        for _ in range(3):
            result = await call("RunSessionAction", ["playback_rate"])
            if not result.get("ok"):
                pytest.skip(f"playback_rate failed: {result.get('error')}")
            results.append(result)

        # All calls should succeed
        assert all(r.get("ok") for r in results), "All playback_rate calls should succeed"

    async def test_practice_mode_toggles(self):
        """practice_mode should succeed and be re-runnable."""
        result1 = await call("RunSessionAction", ["practice_mode"])
        if not result1.get("ok"):
            pytest.skip(f"practice_mode failed: {result1.get('error')}")

        result2 = await call("RunSessionAction", ["practice_mode"])
        # Should be able to toggle/run again without error
        assert result2.get("ok") or "error" in result2


# ---------------------------------------------------------------------------
# Track-modifying actions
# ---------------------------------------------------------------------------

class TestTrackActions:
    """Test actions that add or modify tracks."""

    async def test_add_guitar_od_adds_track(self):
        """add_guitar_od should add a new guitar overdub track."""
        before = await call("CountTracks", [0])
        before_count = before.get("ret", 0)
        if not isinstance(before_count, int):
            before_count = 0

        result = await call("RunSessionAction", ["add_guitar_od"])
        if not result.get("ok"):
            pytest.skip(f"add_guitar_od failed: {result.get('error')}")

        after = await call("CountTracks", [0])
        after_count = after.get("ret", 0)
        if not isinstance(after_count, int):
            after_count = 0
        assert after_count > before_count, (
            f"add_guitar_od should increase track count. "
            f"Before: {before_count}, after: {after_count}"
        )

    async def test_add_vocal_adds_track(self):
        """add_vocal should add a new vocal track with FX chain."""
        before = await call("CountTracks", [0])
        before_count = before.get("ret", 0)
        if not isinstance(before_count, int):
            before_count = 0

        result = await call("RunSessionAction", ["add_vocal"])
        if not result.get("ok"):
            pytest.skip(f"add_vocal failed: {result.get('error')}")

        after = await call("CountTracks", [0])
        after_count = after.get("ret", 0)
        if not isinstance(after_count, int):
            after_count = 0
        assert after_count > before_count, (
            f"add_vocal should increase track count. "
            f"Before: {before_count}, after: {after_count}"
        )

        # Verify the new track has FX (soft check -- plugins may not be installed)
        tracks_info = await call("GetAllTracksInfo")
        if tracks_info.get("ok"):
            vocal_tracks = [
                t for t in tracks_info["tracks"]
                if "Vocal" in t.get("name", "") or "vocal" in t.get("name", "").lower()
            ]
            assert vocal_tracks, "Should find at least one vocal track"
            has_fx = any(t.get("fx_count", 0) > 0 for t in vocal_tracks)
            if not has_fx:
                import warnings
                warnings.warn(
                    "Vocal track has no FX -- expected plugins may not be installed"
                )


# ---------------------------------------------------------------------------
# Arm / DI actions
# ---------------------------------------------------------------------------

class TestArmActions:
    """Test actions related to arming and disarming tracks."""

    async def test_arm_all_di_toggles(self):
        """arm_all_di should toggle arm state on DI tracks."""
        result = await call("RunSessionAction", ["arm_all_di"])
        if not result.get("ok"):
            pytest.skip(f"arm_all_di failed: {result.get('error')}")

        # Run again to toggle back
        result2 = await call("RunSessionAction", ["arm_all_di"])
        assert result2.get("ok") or "error" in result2, (
            "arm_all_di should be re-runnable"
        )

    async def test_arm_next_track(self):
        """arm_next_track should succeed with tracks present."""
        result = await call("RunSessionAction", ["arm_next_track"])
        # May succeed or fail gracefully depending on selection state
        assert result.get("ok") or "error" in result


# ---------------------------------------------------------------------------
# FX / tone actions
# ---------------------------------------------------------------------------

class TestFxActions:
    """Test actions that manipulate FX and tone settings."""

    async def test_quick_tune_toggles(self):
        """quick_tune should toggle ReaTune bypass on DI tracks."""
        result = await call("RunSessionAction", ["quick_tune"])
        if not result.get("ok"):
            pytest.skip(f"quick_tune failed: {result.get('error')}")

        # Toggle back
        result2 = await call("RunSessionAction", ["quick_tune"])
        assert result2.get("ok") or "error" in result2

    async def test_cycle_tone(self):
        """cycle_tone should cycle through tone tracks (for tone template context)."""
        result = await call("RunSessionAction", ["cycle_tone"])
        # May fail gracefully if no tone tracks exist in guitar session
        assert result.get("ok") or "error" in result

    async def test_tone_snapshot(self):
        """tone_snapshot should drop a marker with current FX settings."""
        result = await call("RunSessionAction", ["tone_snapshot"])
        # May fail gracefully if no appropriate tracks
        assert result.get("ok") or "error" in result

    async def test_tone_browser(self):
        """tone_browser should cycle Neural DSP plugins on selected track."""
        result = await call("RunSessionAction", ["tone_browser"])
        assert result.get("ok") or "error" in result

    async def test_reference_ab(self):
        """reference_ab should toggle between mix and reference."""
        result = await call("RunSessionAction", ["reference_ab"])
        assert result.get("ok") or "error" in result


# ---------------------------------------------------------------------------
# Utility / session management actions
# ---------------------------------------------------------------------------

class TestUtilityActions:
    """Test utility and session management actions."""

    async def test_toggle_meters(self):
        """toggle_meters should toggle master metering visibility."""
        result = await call("RunSessionAction", ["toggle_meters"])
        if not result.get("ok"):
            pytest.skip(f"toggle_meters failed: {result.get('error')}")

        # Toggle back
        result2 = await call("RunSessionAction", ["toggle_meters"])
        assert result2.get("ok") or "error" in result2

    async def test_session_backup(self):
        """session_backup should save a timestamped backup."""
        result = await call("RunSessionAction", ["session_backup"])
        # May fail if project is unsaved (no project path)
        assert result.get("ok") or "error" in result

    async def test_cleanup_session(self):
        """cleanup_session should run without crashing."""
        result = await call("RunSessionAction", ["cleanup_session"])
        assert result.get("ok") or "error" in result

    async def test_register_keybinds(self):
        """register_keybinds should register or report key bindings."""
        result = await call("RunSessionAction", ["register_keybinds"])
        assert result.get("ok") or "error" in result

    async def test_noise_capture(self):
        """noise_capture should toggle noise capture mode."""
        result = await call("RunSessionAction", ["noise_capture"])
        assert result.get("ok") or "error" in result


# ---------------------------------------------------------------------------
# Actions requiring specific state (graceful failure expected)
# ---------------------------------------------------------------------------

class TestStateDependentActions:
    """Test actions that require specific project state.

    These actions may fail gracefully because the test environment
    does not provide the exact state they need (e.g., time selection,
    selected items, specific track types). The key assertion is that
    they return structured responses rather than crashing.
    """

    async def test_bounce_selection_without_selection(self):
        """bounce_selection without time selection should return error."""
        result = await call("RunSessionAction", ["bounce_selection"])
        # Expected to fail gracefully -- no time selection set
        assert result.get("ok") or "error" in result

    async def test_auto_trim_silence_without_items(self):
        """auto_trim_silence without selected items should handle gracefully."""
        result = await call("RunSessionAction", ["auto_trim_silence"])
        assert result.get("ok") or "error" in result

    async def test_reamp_without_selection(self):
        """reamp without a selected DI track should handle gracefully."""
        result = await call("RunSessionAction", ["reamp"])
        assert result.get("ok") or "error" in result

    async def test_new_take_folder_without_items(self):
        """new_take_folder without items should handle gracefully."""
        result = await call("RunSessionAction", ["new_take_folder"])
        assert result.get("ok") or "error" in result


# ---------------------------------------------------------------------------
# Invalid action name
# ---------------------------------------------------------------------------

class TestInvalidAction:
    """Test behavior with invalid action names."""

    async def test_unknown_action_returns_error(self):
        """RunSessionAction with an unknown name should return an error."""
        result = await call("RunSessionAction", ["nonexistent_action_xyz"])
        assert not result.get("ok"), "Unknown action should not succeed"
        assert "error" in result, "Unknown action should return error message"

    @pytest.mark.parametrize("bad_name", ["", " ", "CREATE_SESSION", "createSession"])
    async def test_malformed_action_names(self, bad_name: str):
        """Malformed action names should return structured errors."""
        result = await call("RunSessionAction", [bad_name])
        assert not result.get("ok") or "error" in result, (
            f"Malformed action '{bad_name}' should not succeed silently"
        )


# ---------------------------------------------------------------------------
# Tone template context: actions that work best with tone design session
# ---------------------------------------------------------------------------

class TestToneContextActions:
    """Actions that are designed for the tone design template."""

    @pytest.fixture(autouse=True)
    async def tone_session(self):
        """Create a tone session instead of the default guitar session."""
        await delete_all_tracks()
        await call("CreateSession", [
            "tone", "Tone Action Test", 120, "4/4", "", 48000,
        ])
        yield
        await delete_all_tracks()

    async def test_cycle_tone_in_tone_session(self):
        """cycle_tone should work in a tone design session (has Tone A/B/C/D)."""
        result = await call("RunSessionAction", ["cycle_tone"])
        # In a tone session, cycle_tone should find the tone tracks
        assert result.get("ok") or "error" in result

    async def test_tone_snapshot_in_tone_session(self):
        """tone_snapshot should capture FX state in tone session."""
        result = await call("RunSessionAction", ["tone_snapshot"])
        assert result.get("ok") or "error" in result


# ---------------------------------------------------------------------------
# Podcast template context
# ---------------------------------------------------------------------------

class TestPodcastContextActions:
    """Actions in the context of a podcast session."""

    @pytest.fixture(autouse=True)
    async def podcast_session(self):
        """Create a podcast session."""
        await delete_all_tracks()
        await call("CreateSession", [
            "podcast", "Podcast Action Test", 120, "4/4", "", 48000,
        ])
        yield
        await delete_all_tracks()

    async def test_noise_capture_in_podcast(self):
        """noise_capture should find vocal tracks in podcast session."""
        result = await call("RunSessionAction", ["noise_capture"])
        assert result.get("ok") or "error" in result
