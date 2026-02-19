-- lib/tracks.lua — Track creation, folders, buses, sends
-- All track operations use REAPER's native API directly.
-- config.lua provides hardware mappings; utils.lua provides helpers.

local config = require("config")
local utils = require("utils")

local tracks = {}

-- Internal: track the current insert position (0-based)
local _insert_pos = 0

--- Reset the insert position counter.
-- Call at the start of each template build.
function tracks.reset()
    _insert_pos = reaper.CountTracks(0)
end

--- Get the current insert position.
-- @return number 0-based track index for next insert
function tracks.get_insert_pos()
    return _insert_pos
end

-- ============================================================================
-- Track Creation
-- ============================================================================

--- Create a single track with name, color, and optional input/volume/pan.
-- @param opts table {name, color, input, input_stereo, midi_device, midi_channel,
--   rec_arm, rec_mon, rec_mode, volume_db, pan}
-- @return MediaTrack The created track
function tracks.create(opts)
    opts = opts or {}
    local idx = _insert_pos
    reaper.InsertTrackAtIndex(idx, false)
    local track = reaper.GetTrack(0, idx)
    _insert_pos = _insert_pos + 1

    if not track then return nil end

    -- Name
    if opts.name then
        reaper.GetSetMediaTrackInfo_String(track, "P_NAME", opts.name, true)
    end

    -- Color
    if opts.color then
        local c = opts.color
        if type(c) == "table" then
            c = utils.color(c)
        end
        reaper.SetMediaTrackInfo_Value(track, "I_CUSTOMCOLOR", c)
    end

    -- Volume (dB)
    if opts.volume_db then
        local vol = 10 ^ (opts.volume_db / 20)
        reaper.SetMediaTrackInfo_Value(track, "D_VOL", vol)
    end

    -- Pan (-1.0 = full left, 0 = center, 1.0 = full right)
    if opts.pan then
        reaper.SetMediaTrackInfo_Value(track, "D_PAN", opts.pan)
    end

    -- Audio input
    if opts.input then
        local input_val = utils.encode_audio_input(opts.input, opts.input_stereo or false)
        reaper.SetMediaTrackInfo_Value(track, "I_RECINPUT", input_val)
    end

    -- MIDI input
    if opts.midi_device ~= nil and opts.midi_channel then
        local input_val = utils.encode_midi_input(opts.midi_device, opts.midi_channel)
        reaper.SetMediaTrackInfo_Value(track, "I_RECINPUT", input_val)
    end

    -- Record arm
    if opts.rec_arm then
        reaper.SetMediaTrackInfo_Value(track, "I_RECARM", 1)
    end

    -- Record monitoring (0=off, 1=normal, 2=not when playing)
    if opts.rec_mon then
        reaper.SetMediaTrackInfo_Value(track, "I_RECMON", opts.rec_mon)
    end

    -- Record mode (0=input, 1=stereo out, 2=none, 3=stereo out latcomp, etc.)
    if opts.rec_mode then
        reaper.SetMediaTrackInfo_Value(track, "I_RECMODE", opts.rec_mode)
    end

    return track
end

--- Create a folder parent track.
-- The next N tracks will be children of this folder.
-- @param opts table Same as tracks.create() plus {children = N}
-- @return MediaTrack The folder parent track
function tracks.create_folder(opts)
    opts = opts or {}
    local track = tracks.create(opts)
    if not track then return nil end

    -- Set as folder parent (I_FOLDERDEPTH = 1)
    reaper.SetMediaTrackInfo_Value(track, "I_FOLDERDEPTH", 1)

    return track
end

--- Close the current folder.
-- Call after creating all children of a folder.
-- Sets the last child's folder depth to -1.
function tracks.close_folder()
    -- The last inserted track should close the folder
    local last_idx = _insert_pos - 1
    if last_idx >= 0 then
        local track = reaper.GetTrack(0, last_idx)
        if track then
            local current_depth = reaper.GetMediaTrackInfo_Value(track, "I_FOLDERDEPTH")
            reaper.SetMediaTrackInfo_Value(track, "I_FOLDERDEPTH", current_depth - 1)
        end
    end
end

--- Create a bus/submix track (receives from other tracks).
-- @param opts table Same as tracks.create()
-- @return MediaTrack The bus track
function tracks.create_bus(opts)
    opts = opts or {}
    -- Buses have no direct input
    opts.input = nil
    opts.midi_device = nil
    local track = tracks.create(opts)
    return track
end

-- ============================================================================
-- Sends / Receives
-- ============================================================================

--- Create a send from one track to another.
-- @param src_track MediaTrack Source track
-- @param dst_track MediaTrack Destination track
-- @param opts table {volume, pan, mute, pre_fader}
-- @return number Send index (0-based)
function tracks.create_send(src_track, dst_track, opts)
    opts = opts or {}
    local send_idx = reaper.CreateTrackSend(src_track, dst_track)

    if opts.volume then
        -- Send volume: 0.0 = -inf, 1.0 = 0dB
        reaper.SetTrackSendInfo_Value(src_track, 0, send_idx, "D_VOL", opts.volume)
    end

    if opts.pan then
        reaper.SetTrackSendInfo_Value(src_track, 0, send_idx, "D_PAN", opts.pan)
    end

    if opts.mute then
        reaper.SetTrackSendInfo_Value(src_track, 0, send_idx, "B_MUTE", 1)
    end

    if opts.pre_fader then
        -- 0 = post-fader, 1 = pre-fader, 3 = pre-fx
        reaper.SetTrackSendInfo_Value(src_track, 0, send_idx, "I_SENDMODE", 1)
    end

    return send_idx
end

--- Create sends from multiple source tracks to a single destination.
-- @param src_tracks table Array of MediaTrack
-- @param dst_track MediaTrack Destination
-- @param opts table Send options (applied to all sends)
function tracks.create_sends_to_bus(src_tracks, dst_track, opts)
    for _, src in ipairs(src_tracks) do
        tracks.create_send(src, dst_track, opts)
    end
end

-- ============================================================================
-- Track Properties
-- ============================================================================

--- Set track volume in dB.
-- @param track MediaTrack
-- @param db number Volume in dB (0 = unity)
function tracks.set_volume_db(track, db)
    local vol = 10 ^ (db / 20)
    reaper.SetMediaTrackInfo_Value(track, "D_VOL", vol)
end

--- Mute a track.
-- @param track MediaTrack
-- @param muted boolean
function tracks.set_mute(track, muted)
    reaper.SetMediaTrackInfo_Value(track, "B_MUTE", muted and 1 or 0)
end

--- Solo a track.
-- @param track MediaTrack
-- @param soloed boolean
function tracks.set_solo(track, soloed)
    reaper.SetMediaTrackInfo_Value(track, "I_SOLO", soloed and 1 or 0)
end

--- Disable master send on a track (for FX return routing).
-- @param track MediaTrack
function tracks.disable_master_send(track)
    reaper.SetMediaTrackInfo_Value(track, "B_MAINSEND", 0)
end

--- Set the track to receive from all other tracks (pre-fader).
-- Used for "capture" tracks that record the full mix.
-- @param track MediaTrack Capture destination track
-- @param source_tracks table Array of MediaTrack to receive from
function tracks.setup_capture_bus(track, source_tracks)
    for _, src in ipairs(source_tracks) do
        tracks.create_send(src, track, { pre_fader = true, volume = 1.0 })
    end
end

-- ============================================================================
-- Sidechain
-- ============================================================================

--- Set up a sidechain send (auxiliary input to a compressor).
-- @param src_track MediaTrack Source (e.g., kick drum)
-- @param dst_track MediaTrack Destination with compressor
-- @param dst_fx_idx number 0-based FX index of the compressor
-- @param opts table {volume, mute}
function tracks.create_sidechain(src_track, dst_track, dst_fx_idx, opts)
    opts = opts or {}
    local send_idx = reaper.CreateTrackSend(src_track, dst_track)

    -- Route to channels 3/4 (sidechain input) instead of 1/2
    reaper.SetTrackSendInfo_Value(src_track, 0, send_idx, "I_DSTCHAN", 2) -- 0-based: ch 3/4

    if opts.volume then
        reaper.SetTrackSendInfo_Value(src_track, 0, send_idx, "D_VOL", opts.volume)
    end

    if opts.mute then
        reaper.SetTrackSendInfo_Value(src_track, 0, send_idx, "B_MUTE", 1)
    end
end

-- ============================================================================
-- Utility: Find track by name
-- ============================================================================

--- Find a track by name in the current project.
-- @param name string Track name to search for
-- @return MediaTrack|nil
function tracks.find_by_name(name)
    for i = 0, reaper.CountTracks(0) - 1 do
        local track = reaper.GetTrack(0, i)
        local _, track_name = reaper.GetSetMediaTrackInfo_String(track, "P_NAME", "", false)
        if track_name == name then
            return track
        end
    end
    return nil
end

return tracks
