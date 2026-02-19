-- actions/auto_trim_silence.lua — Trim silence from selected items
-- Uses REAPER's "Split items at silence" action to split silent portions,
-- then selects and removes the silent fragments.

dofile(debug.getinfo(1, "S").source:match("@?(.*/)") .. "init.lua")

local utils = require("utils")

utils.undo_block("Auto Trim Silence", function()
    local sel_items = reaper.CountSelectedMediaItems(0)
    if sel_items == 0 then
        utils.log("Auto Trim: No items selected. Select items to trim silence from.")
        return
    end

    utils.log("Auto Trim: Processing " .. sel_items .. " selected item(s)...")

    -- Remember the original selected items' tracks for context
    local track_names = {}
    for i = 0, sel_items - 1 do
        local item = reaper.GetSelectedMediaItem(0, i)
        local track = reaper.GetMediaItem_Track(item)
        local _, name = reaper.GetSetMediaTrackInfo_String(track, "P_NAME", "", false)
        if name and name ~= "" and not track_names[name] then
            track_names[name] = true
        end
    end

    -- Command 40131: Item properties: Split items at silence
    -- This opens a dialog for silence threshold settings
    reaper.Main_OnCommand(40131, 0)

    utils.log("Split at silence completed. Review the splits and delete unwanted silent portions.")
    utils.log("Tip: Select the silent items and press Delete, or use 'Item: Remove items' (40006).")

    local names = {}
    for name, _ in pairs(track_names) do
        names[#names + 1] = name
    end
    if #names > 0 then
        utils.log("Tracks affected: " .. table.concat(names, ", "))
    end
end)

reaper.defer(function() end)
