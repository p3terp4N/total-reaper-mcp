-- actions/new_take_folder.lua — Create a new take/comp lane for the selected track
-- Switches selected items to the next take for comp lane workflows.
-- If no items are selected on the current track, shows a message.

dofile(debug.getinfo(1, "S").source:match("@?(.*/)") .. "init.lua")

local utils = require("utils")

utils.undo_block("New Take / Comp Lane", function()
    local sel_items = reaper.CountSelectedMediaItems(0)

    if sel_items == 0 then
        -- No items selected — check if there's a selected track
        local track = reaper.GetSelectedTrack(0, 0)
        if not track then
            utils.log("New Take: No track or items selected.")
            return
        end

        local _, name = reaper.GetSetMediaTrackInfo_String(track, "P_NAME", "", false)
        utils.log("New Take: No items selected on track '" .. (name or "Untitled") .. "'.")
        utils.log("  Select items first, then run this action to switch to the next take.")
        utils.log("  Record additional takes by recording over existing items.")
        return
    end

    -- Log context
    local first_item = reaper.GetSelectedMediaItem(0, 0)
    local track = reaper.GetMediaItem_Track(first_item)
    local _, track_name = reaper.GetSetMediaTrackInfo_String(track, "P_NAME", "", false)

    -- Report current take info before switching
    local num_takes = reaper.GetMediaItemNumTakes(first_item)

    -- Command 40435: Take: Switch items to next take
    reaper.Main_OnCommand(40435, 0)

    -- Report the new state
    local active_take = reaper.GetActiveTake(first_item)
    local take_name = ""
    if active_take then
        _, take_name = reaper.GetSetMediaItemTakeInfo_String(active_take, "P_NAME", "", false)
    end

    utils.log("Switched to next take on " .. sel_items .. " item(s)")
    utils.log("  Track: " .. (track_name or "Untitled"))
    utils.log("  Total takes: " .. num_takes)
    if take_name and take_name ~= "" then
        utils.log("  Active take: " .. take_name)
    end
    utils.log("  Tip: Use 'Take: Crop to active take' (40131) when you've chosen your comp.")
end)

reaper.defer(function() end)
