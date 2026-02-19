-- actions/idea_marker.lua — Drop "IDEA" marker at cursor with auto-incrementing number
-- Stores the running count in ExtState "SessionTemplate/idea_count" so numbering
-- persists across script invocations within the same REAPER session.

dofile(debug.getinfo(1, "S").source:match("@?(.*/)") .. "init.lua")

local config = require("config")
local utils  = require("utils")

utils.undo_block("Drop Idea Marker", function()
    -- Read and increment the idea counter
    local count_str = reaper.GetExtState("SessionTemplate", "idea_count")
    local count = tonumber(count_str) or 0
    count = count + 1
    reaper.SetExtState("SessionTemplate", "idea_count", tostring(count), false)

    -- Drop marker at current cursor position
    local pos = reaper.GetCursorPosition()
    local name = "IDEA " .. count
    local color = utils.color(config.colors.yellow)
    reaper.AddProjectMarker2(0, false, pos, 0, name, -1, color)

    utils.log("Dropped marker: " .. name .. " at " .. string.format("%.2f", pos) .. "s")
end)

reaper.defer(function() end)
