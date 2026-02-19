-- actions/practice_mode.lua — Set up practice loop with playback rate control
-- Gets the current time selection (or full project), enables loop mode,
-- and sets an initial slow playback rate for practice. The user can then
-- use playback_rate.lua to gradually increase tempo.

dofile(debug.getinfo(1, "S").source:match("@?(.*/)") .. "init.lua")

local utils = require("utils")

utils.undo_block("Practice Mode", function()
    -- Get the current time selection
    local ts_start, ts_end = reaper.GetSet_LoopTimeRange(false, false, 0, 0, false)

    if ts_start == ts_end then
        utils.log("Practice Mode: No time selection. Select a region to practice.")
        utils.log("Tip: Select a passage, then run this action to loop it at reduced speed.")
        return
    end

    -- Enable loop mode
    -- Command 1068: Transport: Toggle repeat
    local loop_state = reaper.GetSetRepeat(-1) -- -1 = query
    if loop_state == 0 then
        reaper.GetSetRepeat(1) -- Enable loop
    end

    -- Set the loop points to match the time selection
    reaper.GetSet_LoopTimeRange(true, true, ts_start, ts_end, false)

    -- Set playback rate to 50% for initial practice
    reaper.CSurf_OnPlayRateChange(0.5)
    reaper.SetExtState("SessionTemplate", "playback_rate_idx", "1", false)

    -- Move cursor to the start of the selection
    reaper.SetEditCurPos(ts_start, true, true)

    -- Get tempo for display
    local bpm = reaper.Master_GetTempo()
    local effective_bpm = bpm * 0.5

    local duration = ts_end - ts_start

    utils.log("--- PRACTICE MODE ACTIVE ---")
    utils.log("Loop: " .. string.format("%.2f", ts_start) .. "s - "
        .. string.format("%.2f", ts_end) .. "s ("
        .. string.format("%.1f", duration) .. "s)")
    utils.log("Playback rate: 50% (" .. string.format("%.0f", effective_bpm) .. " BPM effective)")
    utils.log("")
    utils.log("Use 'Cycle Playback Rate' action to gradually increase speed:")
    utils.log("  50% → 70% → 80% → 90% → 100%")
    utils.log("Press Play (Space) to start practicing.")
    utils.log("----------------------------")
end)

reaper.defer(function() end)
