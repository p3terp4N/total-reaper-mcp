-- actions/playback_rate.lua — Cycle playback rate: 50%, 70%, 80%, 90%, 100%
-- Useful for practice and transcription sessions.
-- Stores the current rate index in ExtState.

dofile(debug.getinfo(1, "S").source:match("@?(.*/)") .. "init.lua")

local utils = require("utils")

utils.undo_block("Cycle Playback Rate", function()
    local rates = { 0.5, 0.7, 0.8, 0.9, 1.0 }
    local labels = { "50%", "70%", "80%", "90%", "100%" }

    -- Get the current index (1-based)
    local idx_str = reaper.GetExtState("SessionTemplate", "playback_rate_idx")
    local current_idx = tonumber(idx_str) or #rates  -- default to 100%

    -- Advance to the next rate (wrap around)
    local next_idx = current_idx + 1
    if next_idx > #rates then
        next_idx = 1
    end

    -- Apply the new rate
    reaper.CSurf_OnPlayRateChange(rates[next_idx])

    -- Save the new index
    reaper.SetExtState("SessionTemplate", "playback_rate_idx", tostring(next_idx), false)

    utils.log("Playback rate: " .. labels[next_idx])
end)

reaper.defer(function() end)
