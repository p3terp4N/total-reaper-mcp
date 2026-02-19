-- actions/add_vocal.lua — Add a vocal track
-- Creates a new track named "Vocal [N]" (auto-numbered), sets input to
-- Tascam Ch 1 (MV7X mic), arms for recording, applies purple color,
-- and loads the vocal_dynamic FX chain from config.

dofile(debug.getinfo(1, "S").source:match("@?(.*/)") .. "init.lua")

local config = require("config")
local utils  = require("utils")
local tracks = require("tracks")
local fx     = require("fx")

utils.undo_block("Add Vocal Track", function()
    -- Count existing Vocal tracks to determine the next number
    local count = reaper.CountTracks(0)
    local vocal_count = 0

    for i = 0, count - 1 do
        local track = reaper.GetTrack(0, i)
        local _, name = reaper.GetSetMediaTrackInfo_String(track, "P_NAME", "", false)

        if name and name:find("^Vocal %d") then
            vocal_count = vocal_count + 1
        end
    end

    local new_num = vocal_count + 1
    local new_name = "Vocal " .. new_num

    -- Insert at the end of the track list
    local insert_idx = count
    reaper.InsertTrackAtIndex(insert_idx, false)
    local new_track = reaper.GetTrack(0, insert_idx)

    if not new_track then
        utils.log("Add Vocal: Failed to create track.")
        return
    end

    -- Set track properties
    reaper.GetSetMediaTrackInfo_String(new_track, "P_NAME", new_name, true)
    reaper.SetMediaTrackInfo_Value(new_track, "I_CUSTOMCOLOR", utils.color(config.colors.purple))

    -- Set input to Tascam Ch 1 (MV7X mic)
    local input_val = utils.encode_audio_input(config.tascam.channels.mic_mv7x, false)
    reaper.SetMediaTrackInfo_Value(new_track, "I_RECINPUT", input_val)

    -- Arm for recording
    reaper.SetMediaTrackInfo_Value(new_track, "I_RECARM", 1)

    -- Input monitoring (normal)
    reaper.SetMediaTrackInfo_Value(new_track, "I_RECMON", 1)

    -- Add the vocal_dynamic FX chain: gate → Pre 1973 → Mantra
    local chain_results = fx.add_named_chain(new_track, "vocal_dynamic", false)

    utils.log("Created: " .. new_name)
    utils.log("  Input: Tascam Ch " .. config.tascam.channels.mic_mv7x .. " (MV7X Mic)")
    utils.log("  Color: Purple | Armed: Yes | Monitoring: On")
    utils.log("  FX chain (vocal_dynamic):")
    for _, result in ipairs(chain_results) do
        if result.plugin then
            utils.log("    " .. result.key .. " → " .. result.plugin)
        else
            utils.log("    " .. result.key .. " → (not available)")
        end
    end
end)

reaper.defer(function() end)
