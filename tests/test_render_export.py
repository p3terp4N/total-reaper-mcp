"""Tests for render & export tools (mock-based, no REAPER needed)."""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock


class TestRenderExport:
    """Test render/export functions with mocked bridge."""

    @pytest.mark.asyncio
    @patch('server.tools.render_export.bridge')
    async def test_render_mix_wav(self, mock_bridge):
        """Test rendering full mix as WAV."""
        from server.tools.render_export import render_mix

        mock_bridge.call_lua = AsyncMock(return_value={"ok": True})

        result = await render_mix(format="wav", path="/tmp/output", sample_rate=48000)

        assert "Rendered full mix as WAV" in result
        assert "48000Hz" in result
        assert "/tmp/output" in result

        # Verify bridge was called for setting render bounds, sample rate, and render
        calls = mock_bridge.call_lua.call_args_list
        assert len(calls) >= 3  # At least: set path, set bounds, set srate, render

    @pytest.mark.asyncio
    @patch('server.tools.render_export.bridge')
    async def test_render_mix_mp3(self, mock_bridge):
        """Test rendering full mix as MP3."""
        from server.tools.render_export import render_mix

        mock_bridge.call_lua = AsyncMock(return_value={"ok": True})

        result = await render_mix(format="mp3")

        assert "Rendered full mix as MP3" in result

    @pytest.mark.asyncio
    @patch('server.tools.render_export.bridge')
    async def test_render_mix_invalid_format(self, mock_bridge):
        """Test rendering with invalid format returns error."""
        from server.tools.render_export import render_mix

        result = await render_mix(format="ogg")

        assert "Unsupported format" in result

    @pytest.mark.asyncio
    @patch('server.tools.render_export.bridge')
    async def test_render_stems(self, mock_bridge):
        """Test rendering stems."""
        from server.tools.render_export import render_stems

        mock_bridge.call_lua = AsyncMock(return_value={"ok": True})

        result = await render_stems(path="/tmp/stems")

        assert "Rendered stems" in result
        assert "/tmp/stems" in result

    @pytest.mark.asyncio
    @patch('server.tools.render_export.bridge')
    async def test_render_selection(self, mock_bridge):
        """Test rendering a time selection."""
        from server.tools.render_export import render_selection

        mock_bridge.call_lua = AsyncMock(return_value={"ok": True})

        result = await render_selection(start=10.0, end=30.0, path="/tmp/clip.wav")

        assert "Rendered selection" in result
        assert "10.0s" in result
        assert "30.0s" in result
        assert "20.0s" in result  # duration

    @pytest.mark.asyncio
    @patch('server.tools.render_export.bridge')
    async def test_render_selection_invalid_range(self, mock_bridge):
        """Test render selection with invalid time range."""
        from server.tools.render_export import render_selection

        result = await render_selection(start=30.0, end=10.0)

        assert "Error" in result
        assert "end time must be greater" in result

    @pytest.mark.asyncio
    @patch('server.tools.render_export.bridge')
    async def test_social_clip_30s(self, mock_bridge):
        """Test exporting a 30-second social clip."""
        from server.tools.render_export import social_clip

        mock_bridge.call_lua = AsyncMock(return_value={"ok": True})

        result = await social_clip(duration=30, path="/tmp/clip.mp3")

        assert "30s social media clip" in result
        assert "44.1kHz" in result
        assert "fade-out" in result
        assert "/tmp/clip.mp3" in result

    @pytest.mark.asyncio
    @patch('server.tools.render_export.bridge')
    async def test_social_clip_60s(self, mock_bridge):
        """Test exporting a 60-second social clip."""
        from server.tools.render_export import social_clip

        mock_bridge.call_lua = AsyncMock(return_value={"ok": True})

        result = await social_clip(duration=60, start_time=30.0)

        assert "60s social media clip" in result
        assert "30.0s" in result  # start time
        assert "90.0s" in result  # end time

    @pytest.mark.asyncio
    @patch('server.tools.render_export.bridge')
    async def test_social_clip_custom_duration_warning(self, mock_bridge):
        """Test that non-standard duration gives warning."""
        from server.tools.render_export import social_clip

        result = await social_clip(duration=45)

        assert "non-standard duration" in result

    @pytest.mark.asyncio
    @patch('server.tools.render_export.bridge')
    async def test_social_clip_render_failure(self, mock_bridge):
        """Test social clip handling render failure."""
        from server.tools.render_export import social_clip

        mock_bridge.call_lua = AsyncMock(side_effect=[
            {"ok": True},   # GetSet_LoopTimeRange
            {"ok": True},   # RENDER_BOUNDSFLAG
            {"ok": True},   # RENDER_TAILMS
            {"ok": True},   # RENDER_FILE
            {"ok": True},   # RENDER_SRATE
            {"ok": False, "error": "Render failed"},  # Main_OnCommand
        ])

        with pytest.raises(Exception, match="Failed to export social clip"):
            await social_clip(duration=30, path="/tmp/fail.mp3")


class TestRenderExportRegistration:
    """Test tool registration."""

    def test_register_render_export_tools(self):
        """Test that registration returns correct tool count."""
        from server.tools.render_export import register_render_export_tools

        mock_mcp = MagicMock()
        mock_mcp.tool.return_value = lambda f: f

        count = register_render_export_tools(mock_mcp)

        assert count == 4  # render_mix, render_stems, render_selection, social_clip
