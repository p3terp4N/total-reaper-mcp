-- actions/chord_region.lua — Create chord region over time selection
-- Prompts for chord name, detects quality, and creates a colored region
-- (not a marker) spanning the current time selection.

dofile(debug.getinfo(1, "S").source:match("@?(.*/)") .. "init.lua")

local config = require("config")
local utils  = require("utils")

--- Detect chord quality from a chord name string.
-- @param chord string Chord name (e.g., "Am", "F", "G7", "Bdim")
-- @return string Quality key: "minor", "dominant", "diminished", or "major"
local function detect_quality(chord)
    if not chord or chord == "" then return "major" end

    if chord:find("dim") or chord:find("°") then
        return "diminished"
    end

    if chord:find("%d") and not chord:find("maj") then
        return "dominant"
    end

    local root_removed = chord:sub(2)
    if root_removed:find("^m") and not root_removed:find("^maj") then
        return "minor"
    end
    if root_removed:find("^%-") or root_removed:find("^min") then
        return "minor"
    end

    return "major"
end

utils.undo_block("Create Chord Region", function()
    -- Get the current time selection
    local ts_start, ts_end = reaper.GetSet_LoopTimeRange(false, false, 0, 0, false)

    if ts_start == ts_end then
        utils.log("Chord Region: No time selection set. Select a time range first.")
        return
    end

    local retval, retvals_csv = reaper.GetUserInputs(
        "Chord Region", 1,
        "Chord (e.g., Am, F, G7, Bdim):",
        ""
    )

    if not retval then
        utils.log("Chord region cancelled.")
        return
    end

    local chord = retvals_csv
    if chord == "" then
        utils.log("Chord Region: No chord name entered.")
        return
    end

    -- Detect quality and pick color
    local quality = detect_quality(chord)
    local chord_color = config.colors.chords[quality] or config.colors.chords.major

    -- Create a region (isrgn=true) over the time selection
    local color = utils.color(chord_color)
    reaper.AddProjectMarker2(0, true, ts_start, ts_end, chord, -1, color)

    utils.log("Created chord region: " .. chord .. " (" .. quality .. ") from "
        .. string.format("%.2f", ts_start) .. "s to "
        .. string.format("%.2f", ts_end) .. "s")
end)

reaper.defer(function() end)
