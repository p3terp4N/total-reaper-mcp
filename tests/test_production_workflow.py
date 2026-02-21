"""Tests for production workflow tools (social_clip, arrangement_template, analyze_form).

These are mock-based tests that do not require a running REAPER instance.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock


# ============================================================================
# Test data and helpers
# ============================================================================

def make_ok(value=None, **extra):
    """Build a successful bridge response."""
    resp = {"ok": True}
    if value is not None:
        resp["ret"] = value
    resp.update(extra)
    return resp


def make_err(msg="test error"):
    return {"ok": False, "error": msg}


# ============================================================================
# social_clip tests
# ============================================================================

class TestSocialClip:
    """Test social_clip export tool."""

    @pytest.mark.asyncio
    @patch("server.tools.production_workflow.bridge")
    async def test_social_clip_30s_from_cursor(self, mock_bridge):
        """Export a 30-second clip using cursor position."""
        from server.tools.production_workflow import social_clip

        mock_bridge.call_lua = AsyncMock(side_effect=[
            # GetSet_LoopTimeRange (check existing time selection) - no selection
            make_ok([0.0, 0.0]),
            # GetCursorPosition
            make_ok(10.0),
            # GetProjectLength
            make_ok(180.0),
            # GetSet_LoopTimeRange (set)
            make_ok(),
            # GetSetProjectInfo (RENDER_BOUNDSFLAG)
            make_ok(),
            # Main_OnCommand (render)
            make_ok(),
        ])

        result = await social_clip(duration=30)

        assert "30s clip" in result
        assert "10.0s - 40.0s" in result
        assert "Render dialog opened" in result

    @pytest.mark.asyncio
    @patch("server.tools.production_workflow.bridge")
    async def test_social_clip_60s_with_explicit_start(self, mock_bridge):
        """Export a 60-second clip from a specified start time."""
        from server.tools.production_workflow import social_clip

        mock_bridge.call_lua = AsyncMock(side_effect=[
            # GetProjectLength
            make_ok(300.0),
            # GetSet_LoopTimeRange (set)
            make_ok(),
            # GetSetProjectInfo (RENDER_BOUNDSFLAG)
            make_ok(),
            # Main_OnCommand (render)
            make_ok(),
        ])

        result = await social_clip(duration=60, start_time=30.0)

        assert "60s clip" in result
        assert "30.0s - 90.0s" in result

    @pytest.mark.asyncio
    @patch("server.tools.production_workflow.bridge")
    async def test_social_clip_from_time_selection(self, mock_bridge):
        """Export clip using an existing time selection."""
        from server.tools.production_workflow import social_clip

        mock_bridge.call_lua = AsyncMock(side_effect=[
            # GetSet_LoopTimeRange (check existing) - has selection
            make_ok([20.0, 50.0]),
            # GetProjectLength
            make_ok(180.0),
            # GetSet_LoopTimeRange (set)
            make_ok(),
            # GetSetProjectInfo (RENDER_BOUNDSFLAG)
            make_ok(),
            # Main_OnCommand (render)
            make_ok(),
        ])

        result = await social_clip(duration=30)

        # Should use the start of the existing time selection (20.0)
        assert "20.0s - 50.0s" in result

    @pytest.mark.asyncio
    @patch("server.tools.production_workflow.bridge")
    async def test_social_clip_invalid_duration(self, mock_bridge):
        """Reject unsupported clip duration."""
        from server.tools.production_workflow import social_clip

        result = await social_clip(duration=45)

        assert "Invalid duration" in result
        assert "45s" in result

    @pytest.mark.asyncio
    @patch("server.tools.production_workflow.bridge")
    async def test_social_clip_project_too_short(self, mock_bridge):
        """Handle project shorter than requested duration."""
        from server.tools.production_workflow import social_clip

        mock_bridge.call_lua = AsyncMock(side_effect=[
            # GetProjectLength
            make_ok(15.0),
        ])

        result = await social_clip(duration=30, start_time=0.0)

        assert "shorter than" in result

    @pytest.mark.asyncio
    @patch("server.tools.production_workflow.bridge")
    async def test_social_clip_clamps_to_end(self, mock_bridge):
        """Clip is clamped when start_time + duration exceeds project length."""
        from server.tools.production_workflow import social_clip

        mock_bridge.call_lua = AsyncMock(side_effect=[
            # GetProjectLength
            make_ok(45.0),
            # GetSet_LoopTimeRange (set)
            make_ok(),
            # GetSetProjectInfo (RENDER_BOUNDSFLAG)
            make_ok(),
            # Main_OnCommand (render)
            make_ok(),
        ])

        result = await social_clip(duration=30, start_time=25.0)

        # Should clamp: render_end=45, render_start=15
        assert "15.0s - 45.0s" in result

    @pytest.mark.asyncio
    @patch("server.tools.production_workflow.bridge")
    async def test_social_clip_with_output_path(self, mock_bridge):
        """Export with explicit output path."""
        from server.tools.production_workflow import social_clip

        mock_bridge.call_lua = AsyncMock(side_effect=[
            # GetProjectLength
            make_ok(120.0),
            # GetSet_LoopTimeRange (set)
            make_ok(),
            # GetSetProjectInfo (RENDER_BOUNDSFLAG)
            make_ok(),
            # GetSetProjectInfo_String (RENDER_FILE)
            make_ok(),
            # Main_OnCommand (render)
            make_ok(),
        ])

        result = await social_clip(
            duration=30, start_time=0.0,
            output_path="/tmp/my_clip.wav"
        )

        assert "/tmp/my_clip.wav" in result


# ============================================================================
# arrangement_template tests
# ============================================================================

class TestArrangementTemplate:
    """Test arrangement_template tool."""

    @pytest.mark.asyncio
    @patch("server.tools.production_workflow.bridge")
    async def test_pop_template(self, mock_bridge):
        """Apply a pop arrangement template."""
        from server.tools.production_workflow import arrangement_template

        # Pop template has 10 sections
        mock_bridge.call_lua = AsyncMock(side_effect=[
            # CountTempoTimeSigMarkers
            make_ok(0),
            # SetTempoTimeSigMarker (create new)
            make_ok(),
            # AddProjectMarker2 x10 (one per section)
            make_ok(0),
            make_ok(1),
            make_ok(2),
            make_ok(3),
            make_ok(4),
            make_ok(5),
            make_ok(6),
            make_ok(7),
            make_ok(8),
            make_ok(9),
            # UpdateTimeline
            make_ok(),
        ])

        result = await arrangement_template("pop")

        assert "Pop" in result
        assert "120 BPM" in result
        assert "Intro" in result
        assert "Verse 1" in result
        assert "Chorus" in result
        assert "Bridge" in result
        assert "Outro" in result
        assert "Regions created: 10" in result

    @pytest.mark.asyncio
    @patch("server.tools.production_workflow.bridge")
    async def test_blues_template_with_custom_tempo(self, mock_bridge):
        """Apply a blues template with custom tempo."""
        from server.tools.production_workflow import arrangement_template

        # Blues has 6 sections
        mock_bridge.call_lua = AsyncMock(side_effect=[
            # CountTempoTimeSigMarkers
            make_ok(1),
            # SetTempoTimeSigMarker (modify existing marker 0)
            make_ok(),
            # AddProjectMarker2 x6
            make_ok(0),
            make_ok(1),
            make_ok(2),
            make_ok(3),
            make_ok(4),
            make_ok(5),
            # UpdateTimeline
            make_ok(),
        ])

        result = await arrangement_template("blues", tempo=85.0)

        assert "Blues" in result
        assert "85 BPM" in result
        assert "12-bar" in result
        assert "Solo" in result

    @pytest.mark.asyncio
    @patch("server.tools.production_workflow.bridge")
    async def test_unknown_genre(self, mock_bridge):
        """Reject unknown genre."""
        from server.tools.production_workflow import arrangement_template

        result = await arrangement_template("polka")

        assert "Unknown genre" in result
        assert "polka" in result
        assert "pop" in result  # should list available genres

    @pytest.mark.asyncio
    @patch("server.tools.production_workflow.bridge")
    async def test_edm_template(self, mock_bridge):
        """Apply EDM template with build/drop structure."""
        from server.tools.production_workflow import arrangement_template

        # EDM has 7 sections
        mock_bridge.call_lua = AsyncMock(side_effect=[
            make_ok(0),  # CountTempoTimeSigMarkers
            make_ok(),   # SetTempoTimeSigMarker
            make_ok(0), make_ok(1), make_ok(2), make_ok(3),
            make_ok(4), make_ok(5), make_ok(6),  # 7 sections
            make_ok(),   # UpdateTimeline
        ])

        result = await arrangement_template("edm")

        assert "EDM" in result
        assert "128 BPM" in result
        assert "Drop" in result
        assert "Build" in result
        assert "Breakdown" in result

    @pytest.mark.asyncio
    @patch("server.tools.production_workflow.bridge")
    async def test_all_genres_valid(self, mock_bridge):
        """Verify all defined genres are recognized."""
        from server.tools.production_workflow import ARRANGEMENT_TEMPLATES

        for genre in ARRANGEMENT_TEMPLATES:
            template = ARRANGEMENT_TEMPLATES[genre]
            assert "name" in template
            assert "sections" in template
            assert len(template["sections"]) > 0
            assert "tempo_range" in template
            assert "time_sig" in template

    @pytest.mark.asyncio
    @patch("server.tools.production_workflow.bridge")
    async def test_template_bar_counts(self, mock_bridge):
        """All templates should have reasonable total bar counts."""
        from server.tools.production_workflow import ARRANGEMENT_TEMPLATES

        for genre, template in ARRANGEMENT_TEMPLATES.items():
            total_bars = sum(s["bars"] for s in template["sections"])
            # A typical song is 32-200 bars
            assert total_bars >= 32, f"{genre} too short: {total_bars} bars"
            assert total_bars <= 200, f"{genre} too long: {total_bars} bars"


# ============================================================================
# analyze_form tests
# ============================================================================

class TestAnalyzeForm:
    """Test analyze_form tool."""

    @pytest.mark.asyncio
    @patch("server.tools.production_workflow.bridge")
    async def test_analyze_empty_project(self, mock_bridge):
        """Analyze a project with no markers or regions."""
        from server.tools.production_workflow import analyze_form

        mock_bridge.call_lua = AsyncMock(side_effect=[
            # Master_GetTempo
            make_ok(120.0),
            # GetTempoTimeSigMarker (for time sig)
            make_ok(timesig_num=4, timesig_denom=4),
            # GetProjectLength
            make_ok(180.0),
            # CountTracks
            make_ok(8),
            # CountMediaItems
            make_ok(24),
            # CountProjectMarkers
            make_ok([0, 0]),
            # EnumProjectMarkers (returns nothing)
            make_err(),
        ])

        result = await analyze_form()

        assert "120.0 BPM" in result
        assert "4/4" in result
        assert "8" in result  # tracks
        assert "No regions or markers found" in result
        assert "arrangement_template" in result

    @pytest.mark.asyncio
    @patch("server.tools.production_workflow.bridge")
    async def test_analyze_with_regions(self, mock_bridge):
        """Analyze a project with region markers defining sections."""
        from server.tools.production_workflow import analyze_form

        # Simulate a project at 120 BPM with 4 regions
        bar_duration = 2.0  # at 120 BPM, 4/4
        mock_bridge.call_lua = AsyncMock(side_effect=[
            # Master_GetTempo
            make_ok(120.0),
            # GetTempoTimeSigMarker
            make_ok(timesig_num=4, timesig_denom=4),
            # GetProjectLength
            make_ok(128.0),
            # CountTracks
            make_ok(6),
            # CountMediaItems
            make_ok(12),
            # CountProjectMarkers
            make_ok([0, 4]),
            # EnumProjectMarkers for each region
            make_ok([1, True, 0.0, 8.0, "Intro"]),
            make_ok([2, True, 8.0, 24.0, "Verse 1"]),
            make_ok([3, True, 24.0, 40.0, "Chorus"]),
            make_ok([4, True, 40.0, 48.0, "Outro"]),
            # EnumProjectMarkers returns nothing (end of list)
            make_ok([0, False, 0, 0, ""]),
        ])

        result = await analyze_form()

        assert "120.0 BPM" in result
        assert "Intro" in result
        assert "Verse 1" in result
        assert "Chorus" in result
        assert "Outro" in result
        assert "Sections (4 regions found)" in result
        assert "Identified form" in result

    @pytest.mark.asyncio
    @patch("server.tools.production_workflow.bridge")
    async def test_analyze_suggests_missing_sections(self, mock_bridge):
        """Suggestions should note missing typical sections."""
        from server.tools.production_workflow import analyze_form

        mock_bridge.call_lua = AsyncMock(side_effect=[
            make_ok(120.0),   # Master_GetTempo
            make_ok(timesig_num=4, timesig_denom=4),  # GetTempoTimeSigMarker
            make_ok(64.0),    # GetProjectLength
            make_ok(4),       # CountTracks
            make_ok(8),       # CountMediaItems
            make_ok([0, 2]),  # CountProjectMarkers
            # Only verse regions, no intro/outro/chorus
            make_ok([1, True, 0.0, 16.0, "Verse 1"]),
            make_ok([2, True, 16.0, 32.0, "Verse 2"]),
            make_ok([0, False, 0, 0, ""]),  # end
        ])

        result = await analyze_form()

        assert "Consider adding an Intro" in result
        assert "Consider adding an Outro" in result
        assert "consider adding a Chorus" in result

    @pytest.mark.asyncio
    @patch("server.tools.production_workflow.bridge")
    async def test_analyze_with_only_markers(self, mock_bridge):
        """Analyze when project has point markers but no regions."""
        from server.tools.production_workflow import analyze_form

        mock_bridge.call_lua = AsyncMock(side_effect=[
            make_ok(140.0),   # Master_GetTempo
            make_ok(timesig_num=4, timesig_denom=4),
            make_ok(120.0),   # GetProjectLength
            make_ok(10),      # CountTracks
            make_ok(30),      # CountMediaItems
            make_ok([3, 0]),  # 3 markers, 0 regions
            # 3 point markers
            make_ok([1, False, 0.0, 0.0, "Start"]),
            make_ok([2, False, 30.0, 0.0, "Solo"]),
            make_ok([3, False, 90.0, 0.0, "End"]),
            make_ok([0, False, 0, 0, ""]),  # end
        ])

        result = await analyze_form()

        assert "Markers" in result
        assert "no regions" in result
        assert "Convert markers to regions" in result


# ============================================================================
# Integration: template data consistency
# ============================================================================

class TestTemplateDataIntegrity:
    """Verify template data is consistent and well-formed."""

    def test_all_sections_have_name_and_bars(self):
        from server.tools.production_workflow import ARRANGEMENT_TEMPLATES

        for genre, template in ARRANGEMENT_TEMPLATES.items():
            for i, section in enumerate(template["sections"]):
                assert "name" in section, f"{genre} section {i} missing 'name'"
                assert "bars" in section, f"{genre} section {i} missing 'bars'"
                assert section["bars"] > 0, f"{genre} section {i} has 0 bars"

    def test_tempo_ranges_valid(self):
        from server.tools.production_workflow import ARRANGEMENT_TEMPLATES

        for genre, template in ARRANGEMENT_TEMPLATES.items():
            lo, hi = template["tempo_range"]
            default = template["default_tempo"]
            assert lo < hi, f"{genre} tempo range inverted"
            assert lo <= default <= hi, f"{genre} default {default} outside range {lo}-{hi}"

    def test_time_signatures_valid(self):
        from server.tools.production_workflow import ARRANGEMENT_TEMPLATES

        for genre, template in ARRANGEMENT_TEMPLATES.items():
            num, denom = template["time_sig"]
            assert num > 0, f"{genre} invalid time sig numerator"
            assert denom in (2, 4, 8, 16), f"{genre} unusual time sig denominator {denom}"

    def test_section_keywords_coverage(self):
        """Common section names should be recognized."""
        from server.tools.production_workflow import SECTION_KEYWORDS

        expected = ["intro", "verse", "chorus", "bridge", "solo", "outro"]
        for s in expected:
            assert s in SECTION_KEYWORDS, f"Missing keyword category: {s}"
