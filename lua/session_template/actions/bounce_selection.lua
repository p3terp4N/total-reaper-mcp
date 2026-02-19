-- actions/bounce_selection.lua — Render time selection to new track
-- Uses REAPER's built-in "Render items to new take" action on selected items
-- within the time selection, then adds a note about the source range.

dofile(debug.getinfo(1, "S").source:match("@?(.*/)") .. "init.lua")

local utils = require("utils")

utils.undo_block("Bounce Selection", function()
    -- Get the current time selection
    local ts_start, ts_end = reaper.GetSet_LoopTimeRange(false, false, 0, 0, false)

    if ts_start == ts_end then
        utils.log("Bounce: No time selection set. Select a time range first.")
        return
    end

    local range_str = string.format("%.2fs - %.2fs", ts_start, ts_end)

    -- Check that there are selected items
    local sel_items = reaper.CountSelectedMediaItems(0)
    if sel_items == 0 then
        utils.log("Bounce: No items selected. Select items within the time selection.")
        return
    end

    -- Render items to new take (applies any FX processing)
    -- Command 40601: Item: Render items to new take (in place)
    reaper.Main_OnCommand(40601, 0)

    utils.log("Bounced " .. sel_items .. " item(s) from [" .. range_str .. "]")
    utils.log("New takes created in place. Use 'Take: Switch items to next take' to compare.")
end)

reaper.defer(function() end)
