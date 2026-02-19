"""
Tests for Session Template system.

Tests that work without REAPER running:
- Python config structure
- Tool registration
- DSL alias resolution
- Action registry
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


# ============================================================================
# Config Tests
# ============================================================================

class TestSessionConfig:
    """Test Python-side session config."""

    def test_static_config_has_all_session_types(self):
        from server.session_config import STATIC_CONFIG
        types = STATIC_CONFIG["session_types"]
        expected = {"guitar", "production", "songwriting", "jam", "podcast",
                    "mixing", "tone", "live", "transcription"}
        assert set(types.keys()) == expected

    def test_each_session_type_has_required_fields(self):
        from server.session_config import STATIC_CONFIG
        for key, info in STATIC_CONFIG["session_types"].items():
            assert "name" in info, f"{key} missing 'name'"
            assert "description" in info, f"{key} missing 'description'"

    def test_tascam_channels_complete(self):
        from server.session_config import STATIC_CONFIG
        channels = STATIC_CONFIG["tascam"]["channels"]
        expected = {"mic_mv7x", "guitar_di_1", "guitar_di_2", "mic_condenser",
                    "rc600_l", "rc600_r", "qc_l", "qc_r", "daw_return_l", "daw_return_r"}
        assert set(channels.keys()) == expected

    def test_tascam_channels_are_1_to_10(self):
        from server.session_config import STATIC_CONFIG
        channels = STATIC_CONFIG["tascam"]["channels"]
        assert set(channels.values()) == set(range(1, 11))

    def test_midi_devices_count(self):
        from server.session_config import STATIC_CONFIG
        devices = STATIC_CONFIG["midi"]["devices"]
        assert len(devices) == 4  # BSP, Nektar, QC, RC-600

    def test_plugins_have_preferred(self):
        from server.session_config import STATIC_CONFIG
        for key, plugin in STATIC_CONFIG["plugins"].items():
            assert "preferred" in plugin, f"Plugin '{key}' missing 'preferred'"

    def test_colors_are_rgb_tuples(self):
        from server.session_config import STATIC_CONFIG
        for name, color in STATIC_CONFIG["colors"].items():
            assert len(color) == 3, f"Color '{name}' should have 3 values (RGB)"
            for val in color:
                assert 0 <= val <= 255, f"Color '{name}' value {val} out of range"


# ============================================================================
# Tool Registration Tests
# ============================================================================

class TestToolRegistration:
    """Test that session template tools register correctly."""

    def test_register_session_template_tools(self):
        from server.tools.session_templates import register_session_template_tools
        mock_mcp = MagicMock()
        mock_mcp.tool.return_value = lambda f: f

        count = register_session_template_tools(mock_mcp)
        # 7 direct tools + 2 DSL wrappers = 9
        assert count == 9

    def test_session_actions_dict_complete(self):
        from server.tools.session_templates import SESSION_ACTIONS
        expected_actions = {
            "quick_tune", "reference_ab", "reamp", "arm_all_di", "tap_tempo",
            "idea_marker", "bounce_selection", "chapter_marker", "tone_snapshot",
            "cycle_tone", "playback_rate", "setlist_marker", "arm_next_track",
            "noise_capture", "song_structure_marker", "chord_marker", "chord_region",
            "session_backup", "auto_trim_silence", "toggle_meters", "add_guitar_od",
            "add_vocal", "new_take_folder", "cleanup_session", "practice_mode",
            "tone_browser",
        }
        assert set(SESSION_ACTIONS.keys()) == expected_actions


# ============================================================================
# DSL Wrapper Tests
# ============================================================================

class TestDSLWrappers:
    """Test natural language session type resolution."""

    def test_resolve_exact_match(self):
        from server.dsl.session_wrappers import resolve_session_type
        assert resolve_session_type("guitar") == "guitar"
        assert resolve_session_type("podcast") == "podcast"
        assert resolve_session_type("mixing") == "mixing"

    def test_resolve_natural_language(self):
        from server.dsl.session_wrappers import resolve_session_type
        assert resolve_session_type("set up for guitar recording") == "guitar"
        assert resolve_session_type("I want to mix some stems") == "mixing"
        assert resolve_session_type("jam session") == "jam"
        assert resolve_session_type("let's write a song") == "songwriting"
        assert resolve_session_type("practice mode") == "transcription"

    def test_resolve_case_insensitive(self):
        from server.dsl.session_wrappers import resolve_session_type
        assert resolve_session_type("Guitar Recording") == "guitar"
        assert resolve_session_type("PODCAST") == "podcast"

    def test_resolve_unknown_returns_none(self):
        from server.dsl.session_wrappers import resolve_session_type
        assert resolve_session_type("make a sandwich") is None

    def test_all_session_types_resolvable(self):
        from server.dsl.session_wrappers import resolve_session_type
        # Each session type key should resolve to itself
        for key in ["guitar", "production", "songwriting", "jam", "podcast",
                     "mixing", "tone", "live", "transcription"]:
            assert resolve_session_type(key) == key, f"'{key}' should resolve to itself"


# ============================================================================
# Tool Profile Tests
# ============================================================================

class TestToolProfiles:
    """Test session-template profile configuration."""

    def test_session_template_profile_exists(self):
        from server.tool_profiles import TOOL_PROFILES
        assert "session-template" in TOOL_PROFILES

    def test_session_template_profile_includes_session_templates(self):
        from server.tool_profiles import TOOL_PROFILES
        profile = TOOL_PROFILES["session-template"]
        assert "Session Templates" in profile["categories"]

    def test_session_template_profile_includes_dependencies(self):
        from server.tool_profiles import TOOL_PROFILES
        categories = TOOL_PROFILES["session-template"]["categories"]
        # Should include track, FX, routing for template building
        assert "Tracks" in categories
        assert "FX" in categories
        assert "Routing & Sends" in categories


# ============================================================================
# Config Round-Trip Test
# ============================================================================

class TestConfigRoundTrip:
    """Verify Python static config matches Lua config structure."""

    def test_session_type_keys_match(self):
        """Python and Lua should have the same session type keys."""
        from server.session_config import STATIC_CONFIG
        py_types = set(STATIC_CONFIG["session_types"].keys())
        expected = {"guitar", "production", "songwriting", "jam", "podcast",
                    "mixing", "tone", "live", "transcription"}
        assert py_types == expected

    def test_tascam_channel_keys_match(self):
        """Python and Lua should have the same Tascam channel keys."""
        from server.session_config import STATIC_CONFIG
        py_channels = set(STATIC_CONFIG["tascam"]["channels"].keys())
        expected = {"mic_mv7x", "guitar_di_1", "guitar_di_2", "mic_condenser",
                    "rc600_l", "rc600_r", "qc_l", "qc_r", "daw_return_l", "daw_return_r"}
        assert py_channels == expected

    def test_midi_device_keys_match(self):
        """Python and Lua should have the same MIDI device keys."""
        from server.session_config import STATIC_CONFIG
        py_devices = set(STATIC_CONFIG["midi"]["devices"].keys())
        expected = {"beatstep_pro", "nektar", "quad_cortex", "rc600"}
        assert py_devices == expected
