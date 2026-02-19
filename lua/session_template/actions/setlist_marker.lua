-- actions/setlist_marker.lua — Drop a "SONG: [name]" marker at cursor
-- Prompts for the song name via GetUserInputs.

dofile(debug.getinfo(1, "S").source:match("@?(.*/)") .. "init.lua")

local config = require("config")
local utils  = require("utils")

utils.undo_block("Drop Setlist Marker", function()
    -- Prompt for song name
    local retval, retvals_csv = reaper.GetUserInputs(
        "Setlist Marker", 1,
        "Song Name:",
        ""
    )

    if not retval then
        utils.log("Setlist marker cancelled.")
        return
    end

    local song_name = retvals_csv
    if song_name == "" then
        song_name = "Untitled Song"
    end

    -- Drop marker at current cursor position
    local pos = reaper.GetCursorPosition()
    local name = "SONG: " .. song_name
    local color = utils.color(config.colors.red)
    reaper.AddProjectMarker2(0, false, pos, 0, name, -1, color)

    utils.log("Dropped setlist marker: " .. name .. " at " .. string.format("%.2f", pos) .. "s")
end)

reaper.defer(function() end)
