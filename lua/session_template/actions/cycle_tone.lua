-- actions/cycle_tone.lua — Cycle through tone tracks (Tone A, B, C, D)
-- Unmutes the next tone track and mutes the current one.
-- Stores the current index in ExtState for persistence.

dofile(debug.getinfo(1, "S").source:match("@?(.*/)") .. "init.lua")

local utils  = require("utils")
local tracks = require("tracks")

utils.undo_block("Cycle Tone Track", function()
    local tone_names = { "Tone A", "Tone B", "Tone C", "Tone D" }

    -- Find all tone tracks that exist
    local tone_tracks = {}
    for _, name in ipairs(tone_names) do
        local track = tracks.find_by_name(name)
        if track then
            tone_tracks[#tone_tracks + 1] = { track = track, name = name }
        end
    end

    if #tone_tracks == 0 then
        utils.log("Cycle Tone: No tone tracks found (looking for Tone A/B/C/D).")
        return
    end

    -- Get the current index (1-based)
    local idx_str = reaper.GetExtState("SessionTemplate", "cycle_tone_idx")
    local current_idx = tonumber(idx_str) or 1

    -- Calculate the next index (wrap around)
    local next_idx = current_idx + 1
    if next_idx > #tone_tracks then
        next_idx = 1
    end

    -- Mute all tone tracks, then unmute the next one
    for i, entry in ipairs(tone_tracks) do
        local should_unmute = (i == next_idx)
        reaper.SetMediaTrackInfo_Value(entry.track, "B_MUTE", should_unmute and 0 or 1)
    end

    -- Save the new index
    reaper.SetExtState("SessionTemplate", "cycle_tone_idx", tostring(next_idx), false)

    utils.log("Cycle Tone: Active → " .. tone_tracks[next_idx].name
        .. " (" .. next_idx .. "/" .. #tone_tracks .. ")")
end)

reaper.defer(function() end)
