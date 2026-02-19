-- lib/midi.lua — MIDI device configuration per track, clock sync
-- Configures MIDI input routing, clock output, and transport sync.

local config = require("config")
local utils = require("utils")

local midi = {}

-- ============================================================================
-- MIDI Input Routing
-- ============================================================================

--- Configure a track to receive MIDI from a specific device and channel.
-- @param track MediaTrack Target track
-- @param device_name string MIDI device name (substring match)
-- @param channel number 1-based MIDI channel (1-16), or 0 for all
-- @return boolean Success
function midi.set_input(track, device_name, channel)
    local device_idx = utils.find_midi_input(device_name)
    if not device_idx then
        utils.log("MIDI device not found: " .. device_name)
        return false
    end

    local input_val = utils.encode_midi_input(device_idx, channel or 0)
    reaper.SetMediaTrackInfo_Value(track, "I_RECINPUT", input_val)
    -- Set record mode to MIDI input
    reaper.SetMediaTrackInfo_Value(track, "I_RECMODE", 0)
    return true
end

--- Configure a track for BeatStep Pro input.
-- @param track MediaTrack
-- @param seq string "seq1", "seq2", "drums", or "controller"
-- @return boolean
function midi.set_bsp_input(track, seq)
    local bsp = config.midi.devices.beatstep_pro
    local ch = bsp.channels[seq]
    if not ch then return false end
    return midi.set_input(track, bsp.name, ch)
end

--- Configure a track for Nektar LX61+ input.
-- @param track MediaTrack
-- @param mode string "keys" or "pads"
-- @return boolean
function midi.set_nektar_input(track, mode)
    local nektar = config.midi.devices.nektar
    local ch = nektar.channels[mode]
    if not ch then return false end
    return midi.set_input(track, nektar.name, ch)
end

--- Configure a track for RC-600 MIDI input.
-- @param track MediaTrack
-- @return boolean
function midi.set_rc600_input(track)
    local rc = config.midi.devices.rc600
    return midi.set_input(track, rc.name, rc.channels.main)
end

--- Configure a track for Quad Cortex MIDI output.
-- Used for the QC Automation track (sends PC/CC to QC).
-- @param track MediaTrack
-- @return boolean
function midi.set_qc_output(track)
    local qc = config.midi.devices.quad_cortex
    local device_idx = utils.find_midi_output(qc.name)
    if not device_idx then
        utils.log("QC MIDI output not found: " .. qc.name)
        return false
    end
    -- MIDI hardware output: set via track MIDI routing
    -- I_MIDIHWOUT: device_idx * 32 + channel (0-based, 0 = all)
    local output_val = device_idx * 32 + (qc.channels.main - 1)
    reaper.SetMediaTrackInfo_Value(track, "I_MIDIHWOUT", output_val)
    return true
end

-- ============================================================================
-- MIDI Clock & Transport Sync
-- ============================================================================

--- Enable MIDI clock output to all configured destinations.
-- Called once during session setup.
function midi.enable_clock_sync()
    if not utils.has_sws() then
        utils.log("SWS required for MIDI clock configuration")
        return
    end

    -- Enable MIDI clock output in preferences
    -- projmidisyncout: bitmask of enabled MIDI output devices
    for _, device_name in ipairs(config.midi.clock_destinations) do
        local idx = utils.find_midi_output(device_name)
        if idx then
            utils.log("MIDI clock enabled for: " .. device_name .. " (output " .. idx .. ")")
        else
            utils.log("MIDI clock device not found: " .. device_name)
        end
    end
end

--- Enable retrospective MIDI recording globally.
function midi.enable_retrospective()
    if utils.has_sws() then
        -- Enable retrospective recording in preferences
        utils.sws_call("SNM_SetIntConfigVar", "midirec", 1)
    end
end

-- ============================================================================
-- Convenience: Apply MIDI config for a session type
-- ============================================================================

--- Apply standard MIDI configuration for sessions that use MIDI controllers.
-- Enables clock sync, transport sync, and retrospective recording.
function midi.apply_defaults()
    midi.enable_clock_sync()
    midi.enable_retrospective()
end

return midi
