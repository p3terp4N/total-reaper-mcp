-- actions/arm_next_track.lua — Find current armed track, disarm it, arm the next track
-- Walks all tracks to find the first armed one, disarms it, then arms the
-- next track in the track list. Wraps around to the first track if at the end.

dofile(debug.getinfo(1, "S").source:match("@?(.*/)") .. "init.lua")

local utils = require("utils")

utils.undo_block("Arm Next Track", function()
    local count = reaper.CountTracks(0)
    if count == 0 then
        utils.log("Arm Next: No tracks in project.")
        return
    end

    -- Find the first armed track
    local armed_idx = nil
    for i = 0, count - 1 do
        local track = reaper.GetTrack(0, i)
        local armed = reaper.GetMediaTrackInfo_Value(track, "I_RECARM")
        if armed == 1 then
            armed_idx = i
            break
        end
    end

    if armed_idx == nil then
        -- No track armed — arm the first track
        local first_track = reaper.GetTrack(0, 0)
        reaper.SetMediaTrackInfo_Value(first_track, "I_RECARM", 1)
        local _, name = reaper.GetSetMediaTrackInfo_String(first_track, "P_NAME", "", false)
        utils.log("Arm Next: No track was armed. Armed first track: " .. (name or "Track 1"))
        return
    end

    -- Disarm the current track
    local current_track = reaper.GetTrack(0, armed_idx)
    reaper.SetMediaTrackInfo_Value(current_track, "I_RECARM", 0)
    local _, current_name = reaper.GetSetMediaTrackInfo_String(current_track, "P_NAME", "", false)

    -- Arm the next track (wrap around)
    local next_idx = armed_idx + 1
    if next_idx >= count then
        next_idx = 0
    end

    local next_track = reaper.GetTrack(0, next_idx)
    reaper.SetMediaTrackInfo_Value(next_track, "I_RECARM", 1)
    local _, next_name = reaper.GetSetMediaTrackInfo_String(next_track, "P_NAME", "", false)

    utils.log("Arm Next: " .. (current_name or "Track " .. (armed_idx + 1))
        .. " → " .. (next_name or "Track " .. (next_idx + 1)))
end)

reaper.defer(function() end)
