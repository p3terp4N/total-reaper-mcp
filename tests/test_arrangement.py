"""Tests for arrangement tools (mock-based, no REAPER needed)."""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock


class TestArrangementTemplate:
    """Test genre arrangement templates."""

    @pytest.mark.asyncio
    @patch('server.tools.arrangement.bridge')
    async def test_arrangement_template_pop(self, mock_bridge):
        """Test applying pop arrangement template."""
        from server.tools.arrangement import arrangement_template

        mock_bridge.call_lua = AsyncMock(return_value={"ok": True, "ret": 120})

        result = await arrangement_template(genre="pop", tempo=120)

        assert "Pop arrangement template" in result
        assert "sections" in result
        assert "bars total" in result
        assert "120 BPM" in result
        assert "Intro" in result
        assert "Verse" in result
        assert "Chorus" in result

    @pytest.mark.asyncio
    @patch('server.tools.arrangement.bridge')
    async def test_arrangement_template_rock(self, mock_bridge):
        """Test applying rock arrangement template."""
        from server.tools.arrangement import arrangement_template

        mock_bridge.call_lua = AsyncMock(return_value={"ok": True, "ret": 120})

        result = await arrangement_template(genre="rock")

        assert "Rock arrangement template" in result
        assert "Solo" in result

    @pytest.mark.asyncio
    @patch('server.tools.arrangement.bridge')
    async def test_arrangement_template_blues(self, mock_bridge):
        """Test applying blues (12-bar) arrangement template."""
        from server.tools.arrangement import arrangement_template

        mock_bridge.call_lua = AsyncMock(return_value={"ok": True, "ret": 120})

        result = await arrangement_template(genre="blues")

        assert "Blues" in result
        # Blues verses should be 12 bars
        assert "12 bars" in result

    @pytest.mark.asyncio
    @patch('server.tools.arrangement.bridge')
    async def test_arrangement_template_edm(self, mock_bridge):
        """Test applying EDM arrangement template."""
        from server.tools.arrangement import arrangement_template

        mock_bridge.call_lua = AsyncMock(return_value={"ok": True, "ret": 128})

        result = await arrangement_template(genre="edm", tempo=128)

        assert "EDM arrangement template" in result
        assert "Drop" in result
        assert "Build-Up" in result
        assert "128 BPM" in result

    @pytest.mark.asyncio
    @patch('server.tools.arrangement.bridge')
    async def test_arrangement_template_jazz(self, mock_bridge):
        """Test applying jazz AABA arrangement template."""
        from server.tools.arrangement import arrangement_template

        mock_bridge.call_lua = AsyncMock(return_value={"ok": True, "ret": 140})

        result = await arrangement_template(genre="jazz")

        assert "Jazz" in result
        assert "A Section" in result
        assert "B Section" in result

    @pytest.mark.asyncio
    async def test_arrangement_template_invalid_genre(self):
        """Test invalid genre returns error."""
        from server.tools.arrangement import arrangement_template

        result = await arrangement_template(genre="underwater_basket_weaving")

        assert "Unknown genre" in result
        assert "Available" in result

    @pytest.mark.asyncio
    @patch('server.tools.arrangement.bridge')
    async def test_arrangement_template_with_tempo(self, mock_bridge):
        """Test that providing tempo sets it via SetTempoTimeSigMarker."""
        from server.tools.arrangement import arrangement_template

        mock_bridge.call_lua = AsyncMock(return_value={"ok": True, "ret": 0})

        result = await arrangement_template(genre="pop", tempo=140)

        assert "140 BPM" in result

        # Check that SetTempoTimeSigMarker or CountTempoTimeSigMarkers was called
        calls = mock_bridge.call_lua.call_args_list
        func_names = [c[0][0] for c in calls]
        assert "CountTempoTimeSigMarkers" in func_names

    @pytest.mark.asyncio
    @patch('server.tools.arrangement.bridge')
    async def test_arrangement_template_uses_project_tempo(self, mock_bridge):
        """Test that without explicit tempo, uses project tempo."""
        from server.tools.arrangement import arrangement_template

        mock_bridge.call_lua = AsyncMock(return_value={"ok": True, "ret": 100})

        result = await arrangement_template(genre="rock")

        # Should use the project tempo (returned as 100)
        assert "100 BPM" in result

    @pytest.mark.asyncio
    @patch('server.tools.arrangement.bridge')
    async def test_arrangement_template_clear_existing(self, mock_bridge):
        """Test clearing existing markers before applying template."""
        from server.tools.arrangement import arrangement_template

        call_count = 0

        async def mock_call_lua(func, args):
            nonlocal call_count
            call_count += 1
            if func == "CountProjectMarkers":
                return {"ok": True, "ret": [3, 2]}  # 3 markers, 2 regions
            return {"ok": True, "ret": 120}

        mock_bridge.call_lua = mock_call_lua

        result = await arrangement_template(genre="pop", clear_existing=True)

        assert "Pop arrangement template" in result

    @pytest.mark.asyncio
    @patch('server.tools.arrangement.bridge')
    async def test_arrangement_template_all_genres(self, mock_bridge):
        """Test that all genres can generate templates."""
        from server.tools.arrangement import arrangement_template, ARRANGEMENT_TEMPLATES

        mock_bridge.call_lua = AsyncMock(return_value={"ok": True, "ret": 120})

        for genre in ARRANGEMENT_TEMPLATES:
            result = await arrangement_template(genre=genre)
            assert "arrangement template" in result, f"Failed for genre: {genre}"
            assert "sections" in result, f"No sections for genre: {genre}"
            assert "bars total" in result, f"No bar count for genre: {genre}"

    @pytest.mark.asyncio
    @patch('server.tools.arrangement.bridge')
    async def test_arrangement_template_creates_regions(self, mock_bridge):
        """Test that AddProjectMarker2 is called for each section."""
        from server.tools.arrangement import arrangement_template, ARRANGEMENT_TEMPLATES

        mock_bridge.call_lua = AsyncMock(return_value={"ok": True, "ret": 120})

        result = await arrangement_template(genre="pop")

        calls = mock_bridge.call_lua.call_args_list
        add_marker_calls = [
            c for c in calls
            if c[0][0] in ("AddProjectMarker2", "AddProjectMarker")
        ]

        expected_sections = len(ARRANGEMENT_TEMPLATES["pop"]["sections"])
        assert len(add_marker_calls) == expected_sections


class TestAnalyzeForm:
    """Test project form analysis."""

    @pytest.mark.asyncio
    @patch('server.tools.arrangement.bridge')
    async def test_analyze_form_basic(self, mock_bridge):
        """Test basic form analysis."""
        from server.tools.arrangement import analyze_form

        async def mock_call_lua(func, args):
            responses = {
                "CountTracks": {"ok": True, "ret": 8},
                "CountMediaItems": {"ok": True, "ret": 24},
                "GetProjectLength": {"ok": True, "ret": 240.0},
                "Master_GetTempo": {"ok": True, "ret": 120},
                "CountProjectMarkers": {"ok": True, "ret": [2, 4]},
                "EnumProjectMarkers": {"ok": True, "ret": [0, True, 0.0, 30.0, "Intro"]},
                "GetTrack": {"ok": True, "ret": "track_handle"},
                "GetTrackName": {"ok": True, "ret": "Guitar"},
                "CountTrackMediaItems": {"ok": True, "ret": 3},
                "GetMediaTrackInfo_Value": {"ok": True, "ret": 0},
                "TrackFX_GetCount": {"ok": True, "ret": 2},
                "CountTempoTimeSigMarkers": {"ok": True, "ret": 1},
            }
            return responses.get(func, {"ok": True, "ret": 0})

        mock_bridge.call_lua = mock_call_lua

        result = await analyze_form()

        assert "Project Overview" in result
        assert "8 tracks" in result
        assert "24 items" in result
        assert "Track Layout" in result

    @pytest.mark.asyncio
    @patch('server.tools.arrangement.bridge')
    async def test_analyze_form_empty_project(self, mock_bridge):
        """Test analysis of empty project."""
        from server.tools.arrangement import analyze_form

        async def mock_call_lua(func, args):
            if func == "CountTracks":
                return {"ok": True, "ret": 0}
            elif func == "CountMediaItems":
                return {"ok": True, "ret": 0}
            elif func == "GetProjectLength":
                return {"ok": True, "ret": 0.0}
            elif func == "Master_GetTempo":
                return {"ok": True, "ret": 120}
            elif func == "CountProjectMarkers":
                return {"ok": True, "ret": [0, 0]}
            elif func == "CountTempoTimeSigMarkers":
                return {"ok": True, "ret": 0}
            return {"ok": True, "ret": 0}

        mock_bridge.call_lua = mock_call_lua

        result = await analyze_form()

        assert "Project Overview" in result
        assert "0 tracks" in result

    @pytest.mark.asyncio
    @patch('server.tools.arrangement.bridge')
    async def test_analyze_form_with_regions(self, mock_bridge):
        """Test analysis with existing song sections."""
        from server.tools.arrangement import analyze_form

        call_idx = 0

        async def mock_call_lua(func, args):
            nonlocal call_idx
            call_idx += 1

            if func == "CountTracks":
                return {"ok": True, "ret": 4}
            elif func == "CountMediaItems":
                return {"ok": True, "ret": 10}
            elif func == "GetProjectLength":
                return {"ok": True, "ret": 180.0}
            elif func == "Master_GetTempo":
                return {"ok": True, "ret": 120}
            elif func == "CountProjectMarkers":
                return {"ok": True, "ret": [0, 3]}  # 0 markers, 3 regions
            elif func == "EnumProjectMarkers":
                idx = args[0] if args else 0
                regions = [
                    [0, True, 0.0, 16.0, "Intro"],
                    [1, True, 16.0, 48.0, "Verse"],
                    [2, True, 48.0, 80.0, "Chorus"],
                ]
                if idx < len(regions):
                    return {"ok": True, "ret": regions[idx]}
                return {"ok": True, "ret": [0, False, 0, 0, ""]}
            elif func == "GetTrack":
                return {"ok": True, "ret": "track_handle"}
            elif func == "GetTrackName":
                return {"ok": True, "ret": f"Track {args[0] + 1 if args else 1}"}
            elif func == "CountTrackMediaItems":
                return {"ok": True, "ret": 3}
            elif func == "GetMediaTrackInfo_Value":
                return {"ok": True, "ret": 0}
            elif func == "TrackFX_GetCount":
                return {"ok": True, "ret": 1}
            elif func == "CountTempoTimeSigMarkers":
                return {"ok": True, "ret": 1}
            return {"ok": True, "ret": 0}

        mock_bridge.call_lua = mock_call_lua

        result = await analyze_form()

        assert "Song Sections" in result
        assert "Intro" in result
        assert "Verse" in result
        assert "Chorus" in result

    @pytest.mark.asyncio
    @patch('server.tools.arrangement.bridge')
    async def test_analyze_form_suggests_no_regions(self, mock_bridge):
        """Test that missing regions trigger suggestion."""
        from server.tools.arrangement import analyze_form

        async def mock_call_lua(func, args):
            if func == "CountTracks":
                return {"ok": True, "ret": 2}
            elif func == "CountMediaItems":
                return {"ok": True, "ret": 5}
            elif func == "GetProjectLength":
                return {"ok": True, "ret": 60.0}
            elif func == "Master_GetTempo":
                return {"ok": True, "ret": 120}
            elif func == "CountProjectMarkers":
                return {"ok": True, "ret": [0, 0]}
            elif func == "GetTrack":
                return {"ok": True, "ret": "track"}
            elif func == "GetTrackName":
                return {"ok": True, "ret": "Track 1"}
            elif func == "CountTrackMediaItems":
                return {"ok": True, "ret": 2}
            elif func == "GetMediaTrackInfo_Value":
                return {"ok": True, "ret": 0}
            elif func == "TrackFX_GetCount":
                return {"ok": True, "ret": 0}
            elif func == "CountTempoTimeSigMarkers":
                return {"ok": True, "ret": 0}
            return {"ok": True, "ret": 0}

        mock_bridge.call_lua = mock_call_lua

        result = await analyze_form()

        assert "No song sections defined" in result
        assert "Suggestions" in result
        assert "arrangement_template()" in result


class TestArrangementRegistration:
    """Test tool registration."""

    def test_register_arrangement_tools(self):
        """Test that registration returns correct tool count."""
        from server.tools.arrangement import register_arrangement_tools

        mock_mcp = MagicMock()
        mock_mcp.tool.return_value = lambda f: f

        count = register_arrangement_tools(mock_mcp)

        assert count == 2  # arrangement_template, analyze_form


class TestArrangementTemplateData:
    """Test arrangement template data integrity."""

    def test_all_templates_have_sections(self):
        """Test that all templates have at least 3 sections."""
        from server.tools.arrangement import ARRANGEMENT_TEMPLATES

        for genre, template in ARRANGEMENT_TEMPLATES.items():
            sections = template["sections"]
            assert len(sections) >= 3, f"{genre} has only {len(sections)} sections"

    def test_all_templates_have_name(self):
        """Test that all templates have a display name."""
        from server.tools.arrangement import ARRANGEMENT_TEMPLATES

        for genre, template in ARRANGEMENT_TEMPLATES.items():
            assert "name" in template, f"{genre} missing 'name'"
            assert template["name"], f"{genre} has empty name"

    def test_all_sections_have_valid_bar_counts(self):
        """Test that all sections have positive bar counts."""
        from server.tools.arrangement import ARRANGEMENT_TEMPLATES

        for genre, template in ARRANGEMENT_TEMPLATES.items():
            for section_name, bar_count in template["sections"]:
                assert bar_count > 0, (
                    f"{genre}/{section_name} has invalid bar count: {bar_count}"
                )

    def test_section_colors_exist(self):
        """Test that section color mapping has entries."""
        from server.tools.arrangement import SECTION_COLORS

        assert len(SECTION_COLORS) > 0
        # Check that common sections have colors
        assert any("Intro" in k for k in SECTION_COLORS)
        assert any("Chorus" in k for k in SECTION_COLORS)
        assert any("Verse" in k for k in SECTION_COLORS)


class TestDrumPatternData:
    """Test drum pattern data integrity."""

    def test_all_patterns_have_required_keys(self):
        """Test that all drum patterns have name, patterns, velocity_map."""
        from server.tools.midi_production import DRUM_PATTERNS

        for genre, pattern in DRUM_PATTERNS.items():
            assert "name" in pattern, f"{genre} missing 'name'"
            assert "patterns" in pattern, f"{genre} missing 'patterns'"
            assert "velocity_map" in pattern, f"{genre} missing 'velocity_map'"

    def test_all_patterns_use_valid_drums(self):
        """Test that all patterns reference valid GM drum names."""
        from server.tools.midi_production import DRUM_PATTERNS, GM_DRUMS

        for genre, pattern_def in DRUM_PATTERNS.items():
            for drum_name in pattern_def["patterns"]:
                assert drum_name in GM_DRUMS, (
                    f"{genre} uses unknown drum: {drum_name}"
                )

    def test_all_patterns_have_kick_or_ride(self):
        """Test that all patterns have at least kick or ride."""
        from server.tools.midi_production import DRUM_PATTERNS

        for genre, pattern_def in DRUM_PATTERNS.items():
            drums = pattern_def["patterns"]
            has_beat_source = ("kick" in drums or "ride" in drums)
            assert has_beat_source, f"{genre} has no kick or ride pattern"

    def test_velocity_values_in_range(self):
        """Test that all velocity values are in MIDI range."""
        from server.tools.midi_production import DRUM_PATTERNS

        for genre, pattern_def in DRUM_PATTERNS.items():
            for drum, velocity in pattern_def["velocity_map"].items():
                assert 1 <= velocity <= 127, (
                    f"{genre}/{drum} velocity {velocity} out of range"
                )
