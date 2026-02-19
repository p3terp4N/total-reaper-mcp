-- actions/reamp.lua — Create a reamp track from the selected DI track
-- Gets the selected track (should be a DI track), creates a new track after it
-- named "Reamp - [DI track name]", adds the first available Neural DSP plugin
-- (Petrucci X → Plini X → Gojira X → Mesa IIC+), creates a send from DI to
-- reamp track, and arms the reamp track for recording.

dofile(debug.getinfo(1, "S").source:match("@?(.*/)") .. "init.lua")

local utils  = require("utils")
local tracks = require("tracks")
local fx     = require("fx")
local config = require("config")

utils.undo_block("Create Reamp Track", function()
    -- Get the selected track
    local di_track = reaper.GetSelectedTrack(0, 0)
    if not di_track then
        utils.log("Reamp: No track selected. Select a DI track first.")
        return
    end

    local _, di_name = reaper.GetSetMediaTrackInfo_String(di_track, "P_NAME", "", false)
    if not di_name or di_name == "" then
        di_name = "Untitled"
    end

    local reamp_name = "Reamp - " .. di_name
    utils.log("Creating reamp track: " .. reamp_name)

    -- Find the index of the selected DI track so we insert right after it
    local di_idx = reaper.GetMediaTrackInfo_Value(di_track, "IP_TRACKNUMBER") -- 1-based
    local insert_idx = math.floor(di_idx) -- after the DI track (0-based = di_idx since IP_TRACKNUMBER is 1-based)

    -- Insert a new track right after the DI track
    reaper.InsertTrackAtIndex(insert_idx, false)
    local reamp_track = reaper.GetTrack(0, insert_idx)
    if not reamp_track then
        utils.log("Reamp: Failed to create track.")
        return
    end

    -- Set track name and color
    reaper.GetSetMediaTrackInfo_String(reamp_track, "P_NAME", reamp_name, true)
    reaper.SetMediaTrackInfo_Value(reamp_track, "I_CUSTOMCOLOR", utils.color(config.colors.green))

    -- Try adding Neural DSP plugins in priority order
    local neural_keys = { "neural_petrucci", "neural_plini", "neural_gojira", "neural_mesa" }
    local added_plugin = nil

    for _, key in ipairs(neural_keys) do
        local name = fx.smart_add_from_config(reamp_track, key, false)
        if name then
            added_plugin = name
            utils.log("Added plugin: " .. name)
            break
        end
    end

    if not added_plugin then
        utils.log("Reamp: No Neural DSP plugins available. Add an amp sim manually.")
    end

    -- Create a send from the DI track to the reamp track (pre-fader so DI level doesn't affect it)
    tracks.create_send(di_track, reamp_track, { pre_fader = true })
    utils.log("Created pre-fader send: " .. di_name .. " → " .. reamp_name)

    -- Arm the reamp track for recording
    reaper.SetMediaTrackInfo_Value(reamp_track, "I_RECARM", 1)
    -- Set record mode to "output (stereo)" for reamping
    reaper.SetMediaTrackInfo_Value(reamp_track, "I_RECMODE", 1)
    utils.log("Reamp track armed (recording output).")

    utils.log("Reamp setup complete: " .. reamp_name)
end)

reaper.defer(function() end)
