-- actions/tone_snapshot.lua — Drop a marker with current FX settings noted
-- Gets the selected track, lists all FX plugin names, and stores the
-- information in a marker name at the current cursor position.

dofile(debug.getinfo(1, "S").source:match("@?(.*/)") .. "init.lua")

local config = require("config")
local utils  = require("utils")

utils.undo_block("Tone Snapshot Marker", function()
    -- Get selected track
    local track = reaper.GetSelectedTrack(0, 0)
    if not track then
        utils.log("Tone Snapshot: No track selected. Select a track first.")
        return
    end

    local _, track_name = reaper.GetSetMediaTrackInfo_String(track, "P_NAME", "", false)
    if not track_name or track_name == "" then
        track_name = "Untitled"
    end

    -- Collect FX names on the selected track
    local fx_count = reaper.TrackFX_GetCount(track)
    local fx_names = {}

    for i = 0, fx_count - 1 do
        local _, name = reaper.TrackFX_GetFXName(track, i, "")
        if name and name ~= "" then
            local enabled = reaper.TrackFX_GetEnabled(track, i)
            local prefix = enabled and "" or "[OFF] "
            fx_names[#fx_names + 1] = prefix .. name
        end
    end

    if #fx_names == 0 then
        utils.log("Tone Snapshot: No FX on track '" .. track_name .. "'.")
        return
    end

    -- Build the marker name
    local fx_list = table.concat(fx_names, " > ")
    local marker_name = "TONE [" .. track_name .. "] " .. fx_list

    -- Drop marker at current cursor position
    local pos = reaper.GetCursorPosition()
    local color = utils.color(config.colors.orange)
    reaper.AddProjectMarker2(0, false, pos, 0, marker_name, -1, color)

    utils.log("Tone snapshot at " .. string.format("%.2f", pos) .. "s:")
    utils.log("  Track: " .. track_name)
    for i, name in ipairs(fx_names) do
        utils.log("  FX " .. i .. ": " .. name)
    end
end)

reaper.defer(function() end)
