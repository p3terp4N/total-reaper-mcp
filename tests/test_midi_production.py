"""Tests for MIDI production tools (mock-based, no REAPER needed)."""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock


class TestInsertMidi:
    """Test batch MIDI insertion."""

    @pytest.mark.asyncio
    @patch('server.tools.midi_production.bridge')
    async def test_insert_midi_creates_item_and_notes(self, mock_bridge):
        """Test inserting multiple MIDI notes with auto item creation."""
        from server.tools.midi_production import insert_midi

        mock_bridge.call_lua = AsyncMock(side_effect=[
            # Master_GetTempo
            {"ok": True, "ret": 120},
            # GetTrack
            {"ok": True, "ret": "track_handle"},
            # CreateNewMIDIItemInProj
            {"ok": True, "ret": "item_handle"},
            # CountMediaItems
            {"ok": True, "ret": 1},
            # InsertMIDINoteToItemTake (note 1)
            {"ok": True},
            # InsertMIDINoteToItemTake (note 2)
            {"ok": True},
            # InsertMIDINoteToItemTake (note 3)
            {"ok": True},
            # SortMIDIInItemTake
            {"ok": True},
        ])

        notes = [
            {"pitch": 60, "start": 0.0, "duration": 1.0, "velocity": 80},
            {"pitch": 64, "start": 1.0, "duration": 1.0, "velocity": 90},
            {"pitch": 67, "start": 2.0, "duration": 1.0, "velocity": 100},
        ]

        result = await insert_midi(track_index=0, notes=notes)

        assert "3/3 MIDI notes" in result
        assert "track 0" in result

    @pytest.mark.asyncio
    @patch('server.tools.midi_production.bridge')
    async def test_insert_midi_empty_notes(self, mock_bridge):
        """Test inserting empty note list."""
        from server.tools.midi_production import insert_midi

        result = await insert_midi(track_index=0, notes=[])

        assert "No notes provided" in result

    @pytest.mark.asyncio
    @patch('server.tools.midi_production.bridge')
    async def test_insert_midi_clamps_values(self, mock_bridge):
        """Test that values are clamped to valid MIDI range."""
        from server.tools.midi_production import insert_midi

        mock_bridge.call_lua = AsyncMock(side_effect=[
            {"ok": True, "ret": 120},       # Master_GetTempo
            {"ok": True, "ret": "track"},    # GetTrack
            {"ok": True, "ret": "item"},     # CreateNewMIDIItemInProj
            {"ok": True, "ret": 1},          # CountMediaItems
            {"ok": True},                     # InsertMIDINoteToItemTake
            {"ok": True},                     # SortMIDIInItemTake
        ])

        # Note with out-of-range values
        notes = [
            {"pitch": 200, "start": 0.0, "duration": 1.0, "velocity": 200, "channel": 20},
        ]

        result = await insert_midi(track_index=0, notes=notes)

        assert "1/1 MIDI notes" in result

    @pytest.mark.asyncio
    @patch('server.tools.midi_production.bridge')
    async def test_insert_midi_track_not_found(self, mock_bridge):
        """Test error when track doesn't exist."""
        from server.tools.midi_production import insert_midi

        mock_bridge.call_lua = AsyncMock(side_effect=[
            {"ok": True, "ret": 120},         # Master_GetTempo
            {"ok": False, "ret": None},        # GetTrack fails
        ])

        notes = [{"pitch": 60, "start": 0.0, "duration": 1.0}]

        with pytest.raises(Exception, match="Track 5 not found"):
            await insert_midi(track_index=5, notes=notes)


class TestScaleLock:
    """Test scale lock / MIDI filter."""

    @pytest.mark.asyncio
    @patch('server.tools.midi_production.bridge')
    async def test_scale_lock_c_major(self, mock_bridge):
        """Test setting C major scale lock."""
        from server.tools.midi_production import scale_lock

        mock_bridge.call_lua = AsyncMock(return_value={"ok": True})

        result = await scale_lock(key="C", scale="major")

        assert "Scale lock set: C major" in result
        assert "C, D, E, F, G, A, B" in result

    @pytest.mark.asyncio
    @patch('server.tools.midi_production.bridge')
    async def test_scale_lock_a_minor(self, mock_bridge):
        """Test setting A minor scale lock."""
        from server.tools.midi_production import scale_lock

        mock_bridge.call_lua = AsyncMock(return_value={"ok": True})

        result = await scale_lock(key="A", scale="minor")

        assert "Scale lock set: A minor" in result
        assert "A" in result
        assert "B" in result
        assert "C" in result

    @pytest.mark.asyncio
    @patch('server.tools.midi_production.bridge')
    async def test_scale_lock_blues(self, mock_bridge):
        """Test setting blues scale lock."""
        from server.tools.midi_production import scale_lock

        mock_bridge.call_lua = AsyncMock(return_value={"ok": True})

        result = await scale_lock(key="E", scale="blues")

        assert "Scale lock set: E blues" in result

    @pytest.mark.asyncio
    async def test_scale_lock_invalid_key(self):
        """Test invalid key returns error."""
        from server.tools.midi_production import scale_lock

        result = await scale_lock(key="X", scale="major")

        assert "Unknown key" in result

    @pytest.mark.asyncio
    async def test_scale_lock_invalid_scale(self):
        """Test invalid scale returns error."""
        from server.tools.midi_production import scale_lock

        result = await scale_lock(key="C", scale="nonexistent")

        assert "Unknown scale" in result

    @pytest.mark.asyncio
    @patch('server.tools.midi_production.bridge')
    async def test_scale_lock_stores_project_state(self, mock_bridge):
        """Test that scale lock stores state in project."""
        from server.tools.midi_production import scale_lock

        mock_bridge.call_lua = AsyncMock(return_value={"ok": True})

        await scale_lock(key="D", scale="dorian")

        # Should have called SetProjExtState multiple times
        calls = mock_bridge.call_lua.call_args_list
        set_ext_calls = [c for c in calls if c[0][0] == "SetProjExtState"]
        assert len(set_ext_calls) >= 4  # root, scale, mask, enabled


class TestGenerateDrums:
    """Test genre-aware drum generation."""

    @pytest.mark.asyncio
    @patch('server.tools.midi_production.bridge')
    async def test_generate_drums_rock(self, mock_bridge):
        """Test generating rock drum pattern."""
        from server.tools.midi_production import generate_drums

        async def mock_call_lua(func, args):
            if func == "GetTrack":
                return {"ok": True, "ret": "track_handle"}
            elif func == "CreateNewMIDIItemInProj":
                return {"ok": True, "ret": "item_handle"}
            elif func == "CountMediaItems":
                return {"ok": True, "ret": 1}
            elif func == "GetMediaItem":
                return {"ok": True, "ret": "item_handle"}
            elif func == "GetMediaItemTake":
                return {"ok": True, "ret": "take_handle"}
            elif func == "MIDI_InsertNote":
                return {"ok": True}
            elif func == "MIDI_Sort":
                return {"ok": True}
            return {"ok": True, "ret": 0}

        mock_bridge.call_lua = mock_call_lua

        result = await generate_drums(
            genre="rock", tempo=120, bars=4, track_index=0
        )

        assert "Rock drum pattern" in result
        assert "4 bars" in result
        assert "120 BPM" in result
        assert "notes" in result

    @pytest.mark.asyncio
    @patch('server.tools.midi_production.bridge')
    async def test_generate_drums_jazz(self, mock_bridge):
        """Test generating jazz drum pattern."""
        from server.tools.midi_production import generate_drums

        async def mock_call_lua(func, args):
            if func == "GetTrack":
                return {"ok": True, "ret": "track_handle"}
            elif func == "CreateNewMIDIItemInProj":
                return {"ok": True, "ret": "item_handle"}
            elif func == "CountMediaItems":
                return {"ok": True, "ret": 1}
            elif func == "GetMediaItem":
                return {"ok": True, "ret": "item_handle"}
            elif func == "GetMediaItemTake":
                return {"ok": True, "ret": "take_handle"}
            elif func == "MIDI_InsertNote":
                return {"ok": True}
            elif func == "MIDI_Sort":
                return {"ok": True}
            return {"ok": True, "ret": 0}

        mock_bridge.call_lua = mock_call_lua

        result = await generate_drums(
            genre="jazz", tempo=140, bars=8, track_index=0
        )

        assert "Jazz drum pattern" in result
        assert "8 bars" in result

    @pytest.mark.asyncio
    @patch('server.tools.midi_production.bridge')
    async def test_generate_drums_funk(self, mock_bridge):
        """Test generating funk drum pattern."""
        from server.tools.midi_production import generate_drums

        async def mock_call_lua(func, args):
            if func == "GetTrack":
                return {"ok": True, "ret": "track_handle"}
            elif func == "CreateNewMIDIItemInProj":
                return {"ok": True, "ret": "item_handle"}
            elif func == "CountMediaItems":
                return {"ok": True, "ret": 1}
            elif func == "GetMediaItem":
                return {"ok": True, "ret": "item_handle"}
            elif func == "GetMediaItemTake":
                return {"ok": True, "ret": "take_handle"}
            elif func == "MIDI_InsertNote":
                return {"ok": True}
            elif func == "MIDI_Sort":
                return {"ok": True}
            return {"ok": True, "ret": 0}

        mock_bridge.call_lua = mock_call_lua

        result = await generate_drums(
            genre="funk", tempo=100, bars=4, track_index=0
        )

        assert "Funk drum pattern" in result

    @pytest.mark.asyncio
    async def test_generate_drums_invalid_genre(self):
        """Test invalid genre returns error."""
        from server.tools.midi_production import generate_drums

        result = await generate_drums(genre="dubstep", tempo=140, bars=4)

        assert "Unknown genre" in result
        assert "Available" in result

    @pytest.mark.asyncio
    async def test_generate_drums_no_target(self):
        """Test error when neither item_index nor track_index provided."""
        from server.tools.midi_production import generate_drums

        result = await generate_drums(genre="rock", tempo=120, bars=4)

        assert "Provide either item_index" in result

    @pytest.mark.asyncio
    @patch('server.tools.midi_production.bridge')
    async def test_generate_drums_all_genres(self, mock_bridge):
        """Test that all 12 genres can generate patterns."""
        from server.tools.midi_production import generate_drums, DRUM_PATTERNS

        async def mock_call_lua(func, args):
            if func == "GetTrack":
                return {"ok": True, "ret": "track_handle"}
            elif func == "CreateNewMIDIItemInProj":
                return {"ok": True, "ret": "item_handle"}
            elif func == "CountMediaItems":
                return {"ok": True, "ret": 1}
            elif func == "GetMediaItem":
                return {"ok": True, "ret": "item_handle"}
            elif func == "GetMediaItemTake":
                return {"ok": True, "ret": "take_handle"}
            elif func == "MIDI_InsertNote":
                return {"ok": True}
            elif func == "MIDI_Sort":
                return {"ok": True}
            return {"ok": True, "ret": 0}

        mock_bridge.call_lua = mock_call_lua

        for genre in DRUM_PATTERNS:
            result = await generate_drums(
                genre=genre, tempo=120, bars=2, track_index=0
            )
            assert "drum pattern" in result, f"Failed for genre: {genre}"
            assert "notes" in result, f"No notes generated for genre: {genre}"

    @pytest.mark.asyncio
    @patch('server.tools.midi_production.bridge')
    async def test_generate_drums_existing_item(self, mock_bridge):
        """Test generating into an existing MIDI item."""
        from server.tools.midi_production import generate_drums

        mock_bridge.call_lua = AsyncMock(return_value={"ok": True, "ret": "handle"})

        result = await generate_drums(
            genre="rock", tempo=120, bars=4,
            item_index=0, take_index=0
        )

        assert "Rock drum pattern" in result


class TestMidiProductionRegistration:
    """Test tool registration."""

    def test_register_midi_production_tools(self):
        """Test that registration returns correct tool count."""
        from server.tools.midi_production import register_midi_production_tools

        mock_mcp = MagicMock()
        mock_mcp.tool.return_value = lambda f: f

        count = register_midi_production_tools(mock_mcp)

        assert count == 3  # insert_midi, scale_lock, generate_drums
