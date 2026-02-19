-- actions/quick_tune.lua — Toggle ReaTune bypass on all DI tracks
-- Finds every track with "DI" in its name and toggles ReaTune on/off.
-- Useful for quickly enabling tuner across all guitar/bass DI inputs.

dofile(debug.getinfo(1, "S").source:match("@?(.*/)") .. "init.lua")

local utils  = require("utils")
local tracks = require("tracks")
local fx     = require("fx")

utils.undo_block("Toggle ReaTune on DI tracks", function()
    local count = reaper.CountTracks(0)
    local toggled = 0

    for i = 0, count - 1 do
        local track = reaper.GetTrack(0, i)
        local _, name = reaper.GetSetMediaTrackInfo_String(track, "P_NAME", "", false)

        if name and name:find("DI") then
            local fx_idx = fx.find_on_track(track, "ReaTune")
            if fx_idx >= 0 then
                -- Read current enabled state and flip it
                local is_enabled = reaper.TrackFX_GetEnabled(track, fx_idx)
                fx.set_bypass(track, fx_idx, is_enabled) -- enabled → bypass, bypassed → enable
                toggled = toggled + 1

                local state = is_enabled and "bypassed" or "enabled"
                utils.log("ReaTune " .. state .. " on: " .. name)
            else
                utils.log("No ReaTune found on: " .. name)
            end
        end
    end

    if toggled == 0 then
        utils.log("No DI tracks with ReaTune found.")
    else
        utils.log("Toggled ReaTune on " .. toggled .. " DI track(s).")
    end
end)

reaper.defer(function() end)
