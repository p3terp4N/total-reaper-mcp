-- actions/cleanup_session.lua — Remove empty takes, heal splits, consolidate
-- Performs a series of cleanup operations on the current project:
-- 1. Heal splits in selected items
-- 2. Remove active take from items (cleans up empty/unused takes)
-- Falls back to operating on all items if none are selected.

dofile(debug.getinfo(1, "S").source:match("@?(.*/)") .. "init.lua")

local utils = require("utils")

utils.undo_block("Cleanup Session", function()
    local sel_items = reaper.CountSelectedMediaItems(0)

    -- If no items selected, select all items first
    if sel_items == 0 then
        -- Command 40182: Item: Select all items
        reaper.Main_OnCommand(40182, 0)
        sel_items = reaper.CountSelectedMediaItems(0)

        if sel_items == 0 then
            utils.log("Cleanup: No items in project.")
            return
        end

        utils.log("Cleanup: No items selected — operating on all " .. sel_items .. " items.")
    else
        utils.log("Cleanup: Operating on " .. sel_items .. " selected item(s).")
    end

    -- Step 1: Heal splits in selected items
    -- Command 40548: Item: Heal splits in items
    utils.log("Step 1: Healing splits...")
    reaper.Main_OnCommand(40548, 0)

    -- Step 2: Remove empty takes
    -- Walk through items and remove takes that have no source
    local removed_takes = 0
    for i = reaper.CountSelectedMediaItems(0) - 1, 0, -1 do
        local item = reaper.GetSelectedMediaItem(0, i)
        if item then
            local num_takes = reaper.GetMediaItemNumTakes(item)
            -- Remove takes from the end to avoid index shifting
            for t = num_takes - 1, 0, -1 do
                local take = reaper.GetMediaItemTake(item, t)
                if take then
                    local source = reaper.GetMediaItemTake_Source(take)
                    if not source then
                        -- Empty take — activate it and remove
                        reaper.SetMediaItemInfo_Value(item, "I_CURTAKE", t)
                        -- Command 41588: Take: Remove active take from items
                        reaper.Main_OnCommand(41588, 0)
                        removed_takes = removed_takes + 1
                    end
                end
            end
        end
    end

    -- Step 3: Remove empty items (items with no takes left)
    local removed_items = 0
    for i = reaper.CountSelectedMediaItems(0) - 1, 0, -1 do
        local item = reaper.GetSelectedMediaItem(0, i)
        if item and reaper.GetMediaItemNumTakes(item) == 0 then
            local track = reaper.GetMediaItem_Track(item)
            reaper.DeleteTrackMediaItem(track, item)
            removed_items = removed_items + 1
        end
    end

    utils.log("Cleanup complete:")
    utils.log("  Splits healed")
    utils.log("  Empty takes removed: " .. removed_takes)
    utils.log("  Empty items removed: " .. removed_items)
end)

reaper.defer(function() end)
