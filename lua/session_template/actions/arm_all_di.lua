-- actions/arm_all_di.lua — Arm or disarm all DI tracks for recording
-- Finds every track with "DI" in its name. If any DI track is armed, disarm all.
-- If none are armed, arm all. This gives a single-action toggle.

dofile(debug.getinfo(1, "S").source:match("@?(.*/)") .. "init.lua")

local utils = require("utils")

utils.undo_block("Toggle arm all DI tracks", function()
    local count = reaper.CountTracks(0)
    local di_tracks = {}
    local any_armed = false

    -- Collect all DI tracks and check if any are armed
    for i = 0, count - 1 do
        local track = reaper.GetTrack(0, i)
        local _, name = reaper.GetSetMediaTrackInfo_String(track, "P_NAME", "", false)

        if name and name:find("DI") then
            di_tracks[#di_tracks + 1] = { track = track, name = name }
            local armed = reaper.GetMediaTrackInfo_Value(track, "I_RECARM")
            if armed == 1 then
                any_armed = true
            end
        end
    end

    if #di_tracks == 0 then
        utils.log("No DI tracks found.")
        return
    end

    -- Toggle: if any are armed, disarm all; otherwise arm all
    local new_state = any_armed and 0 or 1
    local action = any_armed and "Disarmed" or "Armed"

    for _, entry in ipairs(di_tracks) do
        reaper.SetMediaTrackInfo_Value(entry.track, "I_RECARM", new_state)
    end

    utils.log(action .. " " .. #di_tracks .. " DI track(s):")
    for _, entry in ipairs(di_tracks) do
        utils.log("  " .. entry.name)
    end
end)

reaper.defer(function() end)
