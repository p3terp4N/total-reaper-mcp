-- actions/song_structure_marker.lua — Drop color-coded song structure marker
-- Prompts the user to select a structure type (Intro, Verse, Chorus, Bridge,
-- Solo, Outro) and drops a color-coded marker at the cursor position using
-- colors from config.colors.markers.

dofile(debug.getinfo(1, "S").source:match("@?(.*/)") .. "init.lua")

local config = require("config")
local utils  = require("utils")

utils.undo_block("Song Structure Marker", function()
    local types = {
        { key = "intro",  label = "Intro" },
        { key = "verse",  label = "Verse" },
        { key = "chorus", label = "Chorus" },
        { key = "bridge", label = "Bridge" },
        { key = "solo",   label = "Solo" },
        { key = "outro",  label = "Outro" },
    }

    -- Build the prompt caption
    local choices = {}
    for i, t in ipairs(types) do
        choices[#choices + 1] = i .. "=" .. t.label
    end

    local retval, retvals_csv = reaper.GetUserInputs(
        "Song Structure Marker", 1,
        "Type (" .. table.concat(choices, ", ") .. "):",
        "1"
    )

    if not retval then
        utils.log("Song structure marker cancelled.")
        return
    end

    local selection = tonumber(retvals_csv)
    if not selection or selection < 1 or selection > #types then
        utils.log("Song Structure: Invalid selection '" .. retvals_csv .. "'. Use 1-" .. #types .. ".")
        return
    end

    local entry = types[selection]
    local marker_color = config.colors.markers[entry.key]

    if not marker_color then
        utils.log("Song Structure: No color defined for '" .. entry.key .. "'.")
        return
    end

    -- Drop marker at current cursor position
    local pos = reaper.GetCursorPosition()
    local name = entry.label
    local color = utils.color(marker_color)
    reaper.AddProjectMarker2(0, false, pos, 0, name, -1, color)

    utils.log("Dropped " .. entry.label .. " marker at " .. string.format("%.2f", pos) .. "s")
end)

reaper.defer(function() end)
