-- actions/toggle_meters.lua — Toggle master track metering visibility
-- Uses REAPER's "View: Toggle master track visible" action to show or hide
-- the master track and its metering in the mixer/arrange view.

dofile(debug.getinfo(1, "S").source:match("@?(.*/)") .. "init.lua")

local utils = require("utils")

utils.undo_block("Toggle Master Meters", function()
    -- Command 40075: View: Toggle master track visible
    reaper.Main_OnCommand(40075, 0)

    -- Check the new state to report it
    local master = reaper.GetMasterTrack(0)
    local visible = reaper.GetMasterTrackVisibility()
    -- GetMasterTrackVisibility returns a bitmask: bit 0 = TCP, bit 1 = MCP
    local tcp_visible = (visible & 1) == 1
    local mcp_visible = (visible & 2) == 2

    local state_parts = {}
    if tcp_visible then state_parts[#state_parts + 1] = "TCP" end
    if mcp_visible then state_parts[#state_parts + 1] = "MCP" end

    if #state_parts > 0 then
        utils.log("Master track visible in: " .. table.concat(state_parts, ", "))
    else
        utils.log("Master track hidden.")
    end
end)

reaper.defer(function() end)
