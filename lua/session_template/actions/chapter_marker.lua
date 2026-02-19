-- actions/chapter_marker.lua — Drop numbered chapter marker at cursor
-- Format: "Chapter N: [title]". Prompts for title via GetUserInputs.
-- Auto-increments chapter number via ExtState.

dofile(debug.getinfo(1, "S").source:match("@?(.*/)") .. "init.lua")

local config = require("config")
local utils  = require("utils")

utils.undo_block("Drop Chapter Marker", function()
    -- Read and increment the chapter counter
    local count_str = reaper.GetExtState("SessionTemplate", "chapter_count")
    local count = tonumber(count_str) or 0
    count = count + 1

    -- Prompt for chapter title
    local retval, retvals_csv = reaper.GetUserInputs(
        "Chapter Marker", 1,
        "Chapter " .. count .. " Title:",
        ""
    )

    if not retval then
        utils.log("Chapter marker cancelled.")
        return
    end

    local title = retvals_csv
    if title == "" then
        title = "Untitled"
    end

    -- Persist the counter
    reaper.SetExtState("SessionTemplate", "chapter_count", tostring(count), false)

    -- Drop marker at current cursor position
    local pos = reaper.GetCursorPosition()
    local name = "Chapter " .. count .. ": " .. title
    local color = utils.color(config.colors.cyan)
    reaper.AddProjectMarker2(0, false, pos, 0, name, -1, color)

    utils.log("Dropped marker: " .. name .. " at " .. string.format("%.2f", pos) .. "s")
end)

reaper.defer(function() end)
