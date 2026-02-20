-- lib/backing/generators.lua — Orchestrator for backing track generation
--
-- Takes a SongChart (JSON-decoded table) and generates MIDI notes
-- for each requested instrument. Creates REAPER tracks with VSTi,
-- creates MIDI items, and inserts all generated notes.
--
-- Usage:
--   local generators = require("backing.generators")
--   local result = generators.build(chart, {"drums", "bass", "keys"}, "rock")
--
-- Chart format:
--   { bpm = 120, sections = {
--       { name = "verse",  bars = 8, chords = {"Am", "F", "C", "G"} },
--       { name = "chorus", bars = 4, chords = {"C", "G", "Am", "F"} },
--   }}

local generators = {}

local tracks = require("tracks")
local fx = require("fx")
local utils = require("utils")
local config = require("config")

-- ============================================================================
-- Lazy-load instrument pattern modules
-- ============================================================================

--- Cached instrument modules (loaded on first access).
local _modules = {}

--- Get the pattern module for an instrument, loading it lazily.
-- @param instrument string "drums", "bass", "keys", or "guitar"
-- @return table|nil The instrument module, or nil if unknown
local function get_module(instrument)
    if _modules[instrument] then
        return _modules[instrument]
    end

    local mod
    if instrument == "drums" then
        mod = require("backing.drums")
    elseif instrument == "bass" then
        mod = require("backing.bass")
    elseif instrument == "keys" then
        mod = require("backing.keys")
    elseif instrument == "guitar" then
        mod = require("backing.guitar")
    end

    if mod then
        _modules[instrument] = mod
    end
    return mod
end

-- ============================================================================
-- Instrument Configuration
-- ============================================================================
-- Per-instrument settings: track name prefix, preferred/fallback VSTi,
-- track color, and MIDI channel (0-indexed for REAPER API).

local INSTRUMENT_CONFIG = {
    drums = {
        name_prefix    = "BT - Drums",
        preferred      = "Addictive Drums 2",
        fallback       = "MT-PowerDrumKit",
        color          = config.colors.purple or { 128, 0, 255 },
        midi_channel   = 9,   -- GM drums (0-indexed = MIDI channel 10)
        volume_db      = -3,  -- Drums sit slightly below peak
        pan            = 0,   -- Center (stereo spread handled by VSTi)
    },
    bass = {
        name_prefix    = "BT - Bass",
        preferred      = "Kontakt",
        fallback       = "ReaSynth",
        color          = config.colors.red or { 255, 0, 0 },
        midi_channel   = 0,   -- MIDI channel 1
        volume_db      = -4,  -- Bass below drums, foundation level
        pan            = 0,   -- Center (always)
    },
    keys = {
        name_prefix    = "BT - Keys",
        preferred      = "Analog Lab V",
        fallback       = "ReaSynth",
        color          = config.colors.blue or { 0, 128, 255 },
        midi_channel   = 1,   -- MIDI channel 2
        volume_db      = -8,  -- Keys sit back in the mix
        pan            = -0.2, -- Slight left (L20)
    },
    guitar = {
        name_prefix    = "BT - Rhythm Guitar",
        preferred      = "Ample Guitar",
        fallback       = "ReaSynth",
        color          = config.colors.orange or { 255, 128, 0 },
        midi_channel   = 3,   -- MIDI channel 4
        volume_db      = -6,  -- Guitar below drums/bass
        pan            = 0.2,  -- Slight right (R20) — opposite keys
    },
}

-- ============================================================================
-- PPQ Conversion
-- ============================================================================

--- Convert a beat position/duration to PPQ ticks.
-- REAPER uses 960 PPQ per quarter note by default.
-- @param beats number Beat value (e.g. 1.0 = one quarter note)
-- @return number PPQ tick count (integer)
local function beats_to_ppq(beats)
    return math.floor(beats * 960)
end

-- ============================================================================
-- MIDI Note Insertion
-- ============================================================================

--- Insert an array of note events into a MIDI take.
-- Each note is offset by bar_offset_beats (absolute position within the song).
-- @param take MediaItem_Take The MIDI take to insert into
-- @param notes table Array of {pitch, start_beats, length_beats, velocity}
-- @param bar_offset_beats number Beat offset for absolute positioning
-- @param channel number 0-indexed MIDI channel
local function insert_notes(take, notes, bar_offset_beats, channel)
    for _, n in ipairs(notes) do
        local start_ppq = beats_to_ppq(bar_offset_beats + n.start_beats)
        local end_ppq = start_ppq + beats_to_ppq(n.length_beats)
        reaper.MIDI_InsertNote(
            take,
            false,        -- selected
            false,        -- muted
            start_ppq,    -- startppqpos
            end_ppq,      -- endppqpos
            channel,      -- channel (0-indexed)
            n.pitch,      -- pitch (MIDI note number)
            n.velocity,   -- velocity (1-127)
            false         -- noSort (we sort once at the end)
        )
    end
end

-- ============================================================================
-- Generate Instrument Notes
-- ============================================================================

--- Generate all MIDI notes for one instrument across the entire song chart.
-- Loops through each section, generating one bar at a time using the
-- instrument's pattern function for the given style/genre.
--
-- @param instrument string "drums", "bass", "keys", or "guitar"
-- @param chart table SongChart with .sections array
-- @param style string Genre name ("rock", "jazz", etc.) or "simple"
-- @return table|nil Array of {pitch, start_beats, length_beats, velocity}, or nil on error
-- @return string|nil Error message on failure
function generators.generate_instrument(instrument, chart, style)
    local mod = get_module(instrument)
    if not mod then
        return nil, "Unknown instrument: " .. tostring(instrument)
    end

    -- Resolve the pattern function for this genre
    -- "simple" forces the fallback simple pattern; nil/unknown also falls back
    local genre = style
    if style == "simple" then
        genre = nil  -- force simple pattern via get_pattern miss
    end
    local pattern_fn = genre and mod.get_pattern(genre) or mod.simple

    local all_notes = {}
    local beat_cursor = 0

    for _, section in ipairs(chart.sections) do
        local bars = section.bars or #section.chords
        local chords = section.chords or {}
        -- Ensure at least one chord to avoid division by zero
        if #chords == 0 then
            chords = { "C" }
        end

        for bar = 0, bars - 1 do
            -- Determine which chord is active for this bar (cycling through chords)
            local chord_idx = (bar % #chords) + 1
            local chord_name = chords[chord_idx] or "C"

            -- Generate one bar of notes
            -- Drums: pattern_fn(section_name, bar_in_phrase)
            -- Others: pattern_fn(chord_name, section_name, bar_in_phrase)
            local bar_notes
            if instrument == "drums" then
                bar_notes = pattern_fn(section.name, bar + 1)
            else
                bar_notes = pattern_fn(chord_name, section.name, bar + 1)
            end

            -- Offset each note to its absolute position in the song
            for _, n in ipairs(bar_notes) do
                all_notes[#all_notes + 1] = {
                    pitch        = n.pitch,
                    start_beats  = beat_cursor + n.start_beats,
                    length_beats = n.length_beats,
                    velocity     = n.velocity,
                }
            end

            beat_cursor = beat_cursor + 4  -- 4 beats per bar (4/4 time assumed)
        end
    end

    return all_notes
end

-- ============================================================================
-- Build Full Backing Track
-- ============================================================================

--- Create REAPER tracks with VSTi instruments and insert generated MIDI notes
-- for a complete backing track.
--
-- Workflow:
--   1. Calculate total song length from chart sections
--   2. Set project tempo to chart BPM
--   3. Create a folder track ("Backing Track")
--   4. For each requested instrument:
--      a. Generate all notes via generate_instrument()
--      b. Create a track with color from INSTRUMENT_CONFIG
--      c. Add preferred VSTi (with fallback)
--      d. Create a MIDI item spanning the full song length
--      e. Insert all generated notes into the MIDI take
--      f. Sort MIDI events
--   5. Close the folder
--   6. Create a bus track with a limiter for the backing mix
--
-- @param chart table SongChart: { bpm, sections = { {name, bars, chords}, ... } }
-- @param instruments table|nil Array of instrument names; defaults to {"drums", "bass"}
-- @param style string|nil Genre name ("rock", "jazz", "simple", etc.); defaults to "rock"
-- @return table { ok, tracks_created, notes_inserted, total_bars, total_seconds }
function generators.build(chart, instruments, style)
    instruments = instruments or { "drums", "bass" }
    style = style or "rock"

    -- Reset the track insert position to current track count so new tracks
    -- are appended after any existing ones (avoids stale _insert_pos)
    tracks.reset()

    -- Calculate total song length in beats and seconds
    local total_beats = 0
    for _, section in ipairs(chart.sections) do
        local bars = section.bars or #section.chords
        total_beats = total_beats + bars * 4
    end
    local bpm = chart.bpm or 120
    local total_seconds = total_beats / bpm * 60

    -- Set project tempo via tempo marker (CSurf_OnTempoChange doesn't persist in defer loop)
    local count = reaper.CountTempoTimeSigMarkers(0)
    if count > 0 then
        reaper.SetTempoTimeSigMarker(0, 0, 0, -1, -1, bpm, 0, 0, false)
    else
        reaper.SetTempoTimeSigMarker(0, -1, 0, -1, -1, bpm, 0, 0, false)
    end

    -- Create folder track for all backing instruments
    local folder = tracks.create_folder({
        name = "Backing Track",
        color = config.colors.gray or { 128, 128, 128 },
    })

    local tracks_created = 0
    local notes_inserted = 0
    local instrument_tracks = {}

    for _, instrument in ipairs(instruments) do
        local inst_config = INSTRUMENT_CONFIG[instrument]
        if not inst_config then
            utils.log("WARN: Unknown backing instrument: " .. tostring(instrument))
            goto continue
        end

        -- Generate all notes for this instrument
        local all_notes, err = generators.generate_instrument(instrument, chart, style)
        if not all_notes then
            utils.log("WARN: " .. (err or "generation failed for " .. instrument))
            goto continue
        end

        -- Create the instrument track (with gain staging)
        local track = tracks.create({
            name = inst_config.name_prefix,
            color = inst_config.color,
            volume_db = inst_config.volume_db,
            pan = inst_config.pan,
        })
        tracks_created = tracks_created + 1
        instrument_tracks[#instrument_tracks + 1] = track

        -- Add VSTi (preferred with fallback)
        fx.smart_add(track, inst_config.preferred, inst_config.fallback)

        -- Create a single MIDI item spanning the full song length
        local item = reaper.CreateNewMIDIItemInProj(track, 0, total_seconds, false)
        if item then
            local take = reaper.GetActiveTake(item)
            if take then
                -- Insert all generated notes into the take
                insert_notes(take, all_notes, 0, inst_config.midi_channel)
                -- Sort MIDI events once after all notes are inserted
                reaper.MIDI_Sort(take)
                notes_inserted = notes_inserted + #all_notes
            end
        end

        ::continue::
    end

    -- Close the backing track folder
    tracks.close_folder()

    -- Create a bus track with limiter for the backing mix
    -- Bus sits at -6dB to provide headroom before the limiter
    local bus = tracks.create_bus({
        name = "BT - Bus",
        color = config.colors.gray or { 128, 128, 128 },
        volume_db = -6,
    })
    fx.smart_add(bus, "ReaLimit", nil)

    -- Send all instrument tracks to the bus
    if #instrument_tracks > 0 then
        tracks.create_sends_to_bus(instrument_tracks, bus, { volume = 1.0 })
    end

    return {
        ok = true,
        tracks_created = tracks_created,
        notes_inserted = notes_inserted,
        total_bars = total_beats / 4,
        total_seconds = total_seconds,
    }
end

return generators
