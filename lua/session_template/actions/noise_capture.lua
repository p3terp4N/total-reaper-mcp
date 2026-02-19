-- actions/noise_capture.lua — Toggle record for noise capture on vocal tracks
-- Finds tracks with "Host", "Guest", or "Vocal" in the name and toggles
-- their record arm state. Displays a message about capturing room noise
-- for ReaFIR noise profile building.

dofile(debug.getinfo(1, "S").source:match("@?(.*/)") .. "init.lua")

local utils = require("utils")

utils.undo_block("Noise Capture Toggle", function()
    local count = reaper.CountTracks(0)
    local vocal_tracks = {}
    local any_armed = false

    -- Find all vocal/host/guest tracks
    for i = 0, count - 1 do
        local track = reaper.GetTrack(0, i)
        local _, name = reaper.GetSetMediaTrackInfo_String(track, "P_NAME", "", false)

        if name and (name:find("Host") or name:find("Guest") or name:find("Vocal")) then
            vocal_tracks[#vocal_tracks + 1] = { track = track, name = name }
            local armed = reaper.GetMediaTrackInfo_Value(track, "I_RECARM")
            if armed == 1 then
                any_armed = true
            end
        end
    end

    if #vocal_tracks == 0 then
        utils.log("Noise Capture: No vocal tracks found (looking for Host/Guest/Vocal).")
        return
    end

    -- Toggle: if any are armed, disarm all; otherwise arm all
    local new_state = any_armed and 0 or 1
    local action = any_armed and "Disarmed" or "Armed"

    for _, entry in ipairs(vocal_tracks) do
        reaper.SetMediaTrackInfo_Value(entry.track, "I_RECARM", new_state)
    end

    utils.log(action .. " " .. #vocal_tracks .. " vocal track(s) for noise capture:")
    for _, entry in ipairs(vocal_tracks) do
        utils.log("  " .. entry.name)
    end

    if not any_armed then
        utils.log("")
        utils.log("--- NOISE CAPTURE MODE ---")
        utils.log("1. Press Record and capture 5-10 seconds of room silence")
        utils.log("2. Select the recorded noise clip")
        utils.log("3. Open ReaFIR on each track → set mode to 'Subtract'")
        utils.log("4. Click 'Automatically build noise profile' and play the noise clip")
        utils.log("5. Disable 'Automatically build noise profile' when done")
        utils.log("--------------------------")
    else
        utils.log("Noise capture mode disabled.")
    end
end)

reaper.defer(function() end)
