"""
Tests for Neural DSP plugin tools.

Tests that work without REAPER running:
- Tool registration count
- Fuzzy parameter name matching (Lua logic tested via Python equivalents)
- Plugin detection pattern matching
- Snapshot JSON round-trip
"""

import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


# ============================================================================
# Tool Registration Tests
# ============================================================================

class TestToolRegistration:
    """Test that Neural DSP tools register correctly."""

    def test_register_neural_dsp_tools(self):
        from server.tools.neural_dsp import register_neural_dsp_tools
        mock_mcp = MagicMock()
        mock_mcp.tool.return_value = lambda f: f

        count = register_neural_dsp_tools(mock_mcp)
        assert count == 8

    def test_all_tools_are_async(self):
        import asyncio
        from server.tools.neural_dsp import (
            neural_dsp_find,
            neural_dsp_params,
            neural_dsp_get,
            neural_dsp_set,
            neural_dsp_preset,
            neural_dsp_snapshot,
            neural_dsp_chain,
            neural_dsp_toggle,
        )
        tools = [
            neural_dsp_find,
            neural_dsp_params,
            neural_dsp_get,
            neural_dsp_set,
            neural_dsp_preset,
            neural_dsp_snapshot,
            neural_dsp_chain,
            neural_dsp_toggle,
        ]
        for tool in tools:
            assert asyncio.iscoroutinefunction(tool), f"{tool.__name__} should be async"


# ============================================================================
# Plugin Detection Pattern Tests
# ============================================================================

class TestPluginDetection:
    """Test Neural DSP plugin name pattern matching."""

    # Mirror the Lua NEURAL_DSP_PATTERNS for Python-side validation
    PATTERNS = [
        "neural dsp",
        "archetype:",
        "darkglass",
        "parallax",
        "soldano",
        "nameless",
        "fortin",
        "omega",
        "cali",
        "plini",
        "abasi",
        "nolly",
        "gojira",
        "petrucci",
        "rabea",
        "tim henson",
        "tom morello",
        "corey wong",
        "john petrucci",
        "mark lettieri",
        "morgan wade",
    ]

    def _is_neural_dsp(self, name):
        lower = name.lower()
        return any(p in lower for p in self.PATTERNS)

    def test_archetype_gojira(self):
        assert self._is_neural_dsp("VST3: Archetype: Gojira (Neural DSP)")

    def test_archetype_nolly(self):
        assert self._is_neural_dsp("VST3: Archetype: Nolly (Neural DSP)")

    def test_archetype_tim_henson(self):
        assert self._is_neural_dsp("VST3: Archetype: Tim Henson (Neural DSP)")

    def test_darkglass_ultra(self):
        assert self._is_neural_dsp("VST3: Darkglass Ultra (Neural DSP)")

    def test_parallax(self):
        assert self._is_neural_dsp("VST3: Parallax (Neural DSP)")

    def test_soldano_slo100(self):
        assert self._is_neural_dsp("VST3: Soldano SLO-100 (Neural DSP)")

    def test_fortin_nameless(self):
        assert self._is_neural_dsp("VST3: Fortin Nameless Suite (Neural DSP)")

    def test_plini(self):
        assert self._is_neural_dsp("VST3: Archetype: Plini (Neural DSP)")

    def test_cali(self):
        assert self._is_neural_dsp("VST3: Archetype: Cali (Neural DSP)")

    def test_not_neural_dsp_amplitube(self):
        assert not self._is_neural_dsp("VST3: AmpliTube 5 (IK Multimedia)")

    def test_not_neural_dsp_helix(self):
        assert not self._is_neural_dsp("VST3: Helix Native (Line 6)")

    def test_not_neural_dsp_bias(self):
        assert not self._is_neural_dsp("VST3: BIAS FX 2 (Positive Grid)")

    def test_not_neural_dsp_generic(self):
        assert not self._is_neural_dsp("VST3: ReaEQ (Cockos)")


# ============================================================================
# Fuzzy Name Matching Tests
# ============================================================================

class TestFuzzyMatching:
    """Test fuzzy parameter name matching logic."""

    def _fuzzy_match(self, target, candidate):
        """Mirror the Lua fuzzy_match_param function."""
        t = target.lower()
        c = candidate.lower()
        if t == c:
            return 100
        if t in c:
            return 80
        if c in t:
            return 60
        return 0

    def _find_best_match(self, target, candidates):
        best_score = 0
        best_name = None
        for c in candidates:
            score = self._fuzzy_match(target, c)
            if score > best_score:
                best_score = score
                best_name = c
        return best_name, best_score

    def test_exact_match(self):
        assert self._fuzzy_match("Gain", "Gain") == 100

    def test_case_insensitive_exact(self):
        assert self._fuzzy_match("gain", "GAIN") == 100

    def test_target_in_candidate(self):
        assert self._fuzzy_match("gain", "Input Gain") == 80

    def test_candidate_in_target(self):
        assert self._fuzzy_match("input gain control", "gain") == 60

    def test_no_match(self):
        assert self._fuzzy_match("reverb", "delay") == 0

    def test_find_best_gain(self):
        params = ["Input Gain", "Output Gain", "Bass", "Treble", "Gain"]
        name, score = self._find_best_match("gain", params)
        assert name == "Gain"
        assert score == 100

    def test_find_best_bass(self):
        params = ["Input Gain", "Output Gain", "Bass", "Treble", "Bass Boost"]
        name, score = self._find_best_match("bass", params)
        assert name == "Bass"
        assert score == 100

    def test_find_input_gain(self):
        params = ["Input Gain", "Output Gain", "Bass", "Treble"]
        name, score = self._find_best_match("input gain", params)
        assert name == "Input Gain"
        assert score == 100

    def test_find_partial(self):
        params = ["Amp Input Gain", "Output Level", "Bass EQ", "Treble EQ"]
        name, score = self._find_best_match("gain", params)
        assert name == "Amp Input Gain"
        assert score == 80

    def test_no_match_returns_none(self):
        params = ["Bass", "Treble", "Mid"]
        name, score = self._find_best_match("reverb", params)
        assert name is None
        assert score == 0


# ============================================================================
# Snapshot Round-Trip Tests
# ============================================================================

class TestSnapshotRoundTrip:
    """Test snapshot data serialization."""

    def test_snapshot_json_round_trip(self):
        snapshot = {
            "0": {"name": "Input Gain", "value": 0.5},
            "1": {"name": "Bass", "value": 0.7},
            "2": {"name": "Mid", "value": 0.6},
            "3": {"name": "Treble", "value": 0.4},
        }
        serialized = json.dumps(snapshot)
        deserialized = json.loads(serialized)
        assert deserialized == snapshot

    def test_snapshot_preserves_float_precision(self):
        snapshot = {
            "0": {"name": "Gain", "value": 0.123456789},
        }
        serialized = json.dumps(snapshot)
        deserialized = json.loads(serialized)
        assert abs(deserialized["0"]["value"] - 0.123456789) < 1e-9

    def test_empty_snapshot(self):
        snapshot = {}
        serialized = json.dumps(snapshot)
        deserialized = json.loads(serialized)
        assert deserialized == {}


# ============================================================================
# Tool Function Tests (with mocked bridge)
# ============================================================================

class TestNeuralDSPFind:
    """Test neural_dsp_find tool."""

    @pytest.mark.asyncio
    async def test_find_no_plugins(self):
        from server.tools.neural_dsp import neural_dsp_find
        with patch("server.tools.neural_dsp.bridge") as mock_bridge:
            mock_bridge.call_lua = AsyncMock(return_value={"ok": True, "ret": []})
            result = await neural_dsp_find()
            assert "No Neural DSP plugins found" in result
            mock_bridge.call_lua.assert_called_once_with("NeuralDSP_FindPlugins", [])

    @pytest.mark.asyncio
    async def test_find_with_plugins(self):
        from server.tools.neural_dsp import neural_dsp_find
        with patch("server.tools.neural_dsp.bridge") as mock_bridge:
            mock_bridge.call_lua = AsyncMock(return_value={
                "ok": True,
                "ret": [
                    {
                        "track_idx": 0,
                        "track_name": "Guitar",
                        "fx_idx": 0,
                        "fx_name": "VST3: Archetype: Gojira (Neural DSP)",
                        "enabled": True,
                    }
                ]
            })
            result = await neural_dsp_find()
            assert "1 Neural DSP plugin(s)" in result
            assert "Gojira" in result
            assert "ON" in result


class TestNeuralDSPPreset:
    """Test neural_dsp_preset tool."""

    @pytest.mark.asyncio
    async def test_get_preset(self):
        from server.tools.neural_dsp import neural_dsp_preset
        with patch("server.tools.neural_dsp.bridge") as mock_bridge:
            mock_bridge.call_lua = AsyncMock(return_value={
                "ok": True,
                "ret": {
                    "fx_name": "Archetype: Gojira",
                    "preset_name": "Clean Tone",
                    "has_preset": True,
                }
            })
            result = await neural_dsp_preset(track=0, fx=0)
            assert "Clean Tone" in result
            mock_bridge.call_lua.assert_called_once_with("NeuralDSP_GetPreset", [0, 0])

    @pytest.mark.asyncio
    async def test_set_preset(self):
        from server.tools.neural_dsp import neural_dsp_preset
        with patch("server.tools.neural_dsp.bridge") as mock_bridge:
            mock_bridge.call_lua = AsyncMock(return_value={
                "ok": True,
                "ret": {"preset_name": "Heavy Crunch"}
            })
            result = await neural_dsp_preset(track=0, fx=0, preset="Heavy Crunch")
            assert "Switched to preset" in result
            assert "Heavy Crunch" in result
            mock_bridge.call_lua.assert_called_once_with("NeuralDSP_SetPreset", [0, 0, "Heavy Crunch"])


class TestNeuralDSPToggle:
    """Test neural_dsp_toggle tool."""

    @pytest.mark.asyncio
    async def test_toggle_block(self):
        from server.tools.neural_dsp import neural_dsp_toggle
        with patch("server.tools.neural_dsp.bridge") as mock_bridge:
            mock_bridge.call_lua = AsyncMock(return_value={
                "ok": True,
                "ret": {
                    "idx": 5,
                    "name": "Gate Enable",
                    "was_enabled": True,
                    "now_enabled": False,
                    "match_score": 80,
                }
            })
            result = await neural_dsp_toggle(track=0, fx=0, block="gate")
            assert "ON → OFF" in result
            assert "Gate Enable" in result


# ============================================================================
# Profile Tests
# ============================================================================

class TestNeuralDSPProfile:
    """Test Neural DSP category in tool profiles."""

    def test_neural_dsp_in_category_registry(self):
        try:
            from server.app import CATEGORY_REGISTRY
        except ImportError:
            pytest.skip("mcp module not installed in system Python")
        assert "Neural DSP" in CATEGORY_REGISTRY

    def test_neural_dsp_in_dsl_production(self):
        from server.tool_profiles import TOOL_PROFILES
        categories = TOOL_PROFILES["dsl-production"]["categories"]
        assert "Neural DSP" in categories

    def test_neural_dsp_in_session_template(self):
        from server.tool_profiles import TOOL_PROFILES
        categories = TOOL_PROFILES["session-template"]["categories"]
        assert "Neural DSP" in categories

    def test_neural_dsp_register_function_exists(self):
        from server.tools.neural_dsp import register_neural_dsp_tools
        assert callable(register_neural_dsp_tools)
