-- actions/chord_marker.lua — Drop chord marker at cursor with quality-based color
-- Prompts for chord name (e.g., "Am", "F", "C7", "Bdim"). Detects quality
-- (major/minor/dominant/diminished) from the name and applies the matching
-- color from config.colors.chords.

dofile(debug.getinfo(1, "S").source:match("@?(.*/)") .. "init.lua")

local config = require("config")
local utils  = require("utils")

--- Detect chord quality from a chord name string.
-- @param chord string Chord name (e.g., "Am", "F", "G7", "Bdim")
-- @return string Quality key: "minor", "dominant", "diminished", or "major"
local function detect_quality(chord)
    if not chord or chord == "" then return "major" end

    -- Check for diminished (dim, o)
    if chord:find("dim") or chord:find("°") then
        return "diminished"
    end

    -- Check for dominant (7, 9, 11, 13 without "maj" prefix)
    -- e.g., "G7" is dominant, "Cmaj7" is major
    if chord:find("%d") and not chord:find("maj") then
        return "dominant"
    end

    -- Check for minor (m, min, -)
    -- Must check after diminished since "dim" contains no 'm' conflict,
    -- but we need to avoid matching "m" in "maj"
    local root_removed = chord:sub(2) -- remove root note letter
    if root_removed:find("^m") and not root_removed:find("^maj") then
        return "minor"
    end
    if root_removed:find("^%-") or root_removed:find("^min") then
        return "minor"
    end

    return "major"
end

utils.undo_block("Drop Chord Marker", function()
    local retval, retvals_csv = reaper.GetUserInputs(
        "Chord Marker", 1,
        "Chord (e.g., Am, F, G7, Bdim):",
        ""
    )

    if not retval then
        utils.log("Chord marker cancelled.")
        return
    end

    local chord = retvals_csv
    if chord == "" then
        utils.log("Chord Marker: No chord name entered.")
        return
    end

    -- Detect quality and pick color
    local quality = detect_quality(chord)
    local chord_color = config.colors.chords[quality]

    if not chord_color then
        chord_color = config.colors.chords.major
    end

    -- Drop marker at current cursor position
    local pos = reaper.GetCursorPosition()
    local color = utils.color(chord_color)
    reaper.AddProjectMarker2(0, false, pos, 0, chord, -1, color)

    utils.log("Dropped chord marker: " .. chord .. " (" .. quality .. ") at "
        .. string.format("%.2f", pos) .. "s")
end)

reaper.defer(function() end)
