-- actions/register_keybinds.lua — One-time keybind registration
-- Run this script ONCE to register all session template action scripts
-- as named REAPER actions and optionally bind them to keys.
--
-- After running: Actions → Show action list → filter "SessionTemplate"
-- to see all registered actions and modify keybinds as desired.

dofile(debug.getinfo(1, "S").source:match("@?(.*/)") .. "init.lua")

local utils = require("utils")

local script_dir = debug.getinfo(1, "S").source:match("@?(.*/)") or ""

-- Action scripts to register (filename → descriptive name)
local actions = {
    -- Core actions
    { file = "quick_tune.lua",           name = "SessionTemplate: Quick Tune Toggle",           key = "T" },
    { file = "reference_ab.lua",         name = "SessionTemplate: Reference A/B Toggle",        key = "B" },
    { file = "reamp.lua",               name = "SessionTemplate: Reamp Workflow",              key = "Ctrl+R" },
    { file = "arm_all_di.lua",          name = "SessionTemplate: Arm All DI Tracks",           key = "Shift+R" },
    { file = "tap_tempo.lua",           name = "SessionTemplate: Tap Tempo",                   key = "Ctrl+T" },

    -- Markers
    { file = "song_structure_marker.lua", name = "SessionTemplate: Song Structure Marker",      key = "M" },
    { file = "chord_marker.lua",         name = "SessionTemplate: Chord Marker",               key = "Ctrl+K" },
    { file = "chord_region.lua",         name = "SessionTemplate: Chord Region",               key = "Ctrl+Shift+K" },
    { file = "idea_marker.lua",          name = "SessionTemplate: Idea Marker",                key = "Ctrl+I" },
    { file = "setlist_marker.lua",       name = "SessionTemplate: Setlist Marker",             key = "Ctrl+L" },
    { file = "chapter_marker.lua",       name = "SessionTemplate: Chapter Marker",             key = "Ctrl+Shift+C" },

    -- Session-specific
    { file = "bounce_selection.lua",     name = "SessionTemplate: Bounce Selection",           key = "Ctrl+B" },
    { file = "arm_next_track.lua",       name = "SessionTemplate: Arm Next Track",             key = "Ctrl+J" },
    { file = "cycle_tone.lua",           name = "SessionTemplate: Cycle Tone",                 key = "Ctrl+G" },
    { file = "tone_snapshot.lua",        name = "SessionTemplate: Tone Snapshot",              key = "Ctrl+Shift+S" },
    { file = "tone_browser.lua",         name = "SessionTemplate: Tone Browser",               key = "Ctrl+Shift+N" },
    { file = "playback_rate.lua",        name = "SessionTemplate: Playback Rate Cycle",        key = "Ctrl+Shift+R" },
    { file = "practice_mode.lua",        name = "SessionTemplate: Practice Mode",              key = "Ctrl+P" },

    -- Utility
    { file = "noise_capture.lua",        name = "SessionTemplate: Noise Capture",              key = nil },
    { file = "session_backup.lua",       name = "SessionTemplate: Session Backup",             key = "Ctrl+Shift+B" },
    { file = "auto_trim_silence.lua",    name = "SessionTemplate: Auto-Trim Silence",          key = "Ctrl+Shift+T" },
    { file = "toggle_meters.lua",        name = "SessionTemplate: Toggle Meters",              key = nil },
    { file = "add_guitar_od.lua",        name = "SessionTemplate: Add Guitar Overdub",         key = nil },
    { file = "add_vocal.lua",            name = "SessionTemplate: Add Vocal Track",            key = nil },
    { file = "new_take_folder.lua",      name = "SessionTemplate: New Take Folder",            key = nil },
    { file = "cleanup_session.lua",      name = "SessionTemplate: Cleanup Session",            key = nil },
}

-- Register each action script
local registered = 0
for _, action in ipairs(actions) do
    local path = script_dir .. action.file
    -- Check file exists
    local f = io.open(path, "r")
    if f then
        f:close()
        -- AddRemoveReaScript: adds the script as a REAPER action
        -- Returns the command ID (>0 on success)
        local cmd_id = reaper.AddRemoveReaScript(true, 0, path, true)
        if cmd_id > 0 then
            registered = registered + 1
            utils.log("Registered: " .. action.name .. " (ID: " .. cmd_id .. ")")
        else
            utils.log("WARN: Could not register: " .. action.file)
        end
    else
        utils.log("SKIP: File not found: " .. action.file)
    end
end

utils.log("")
utils.log("Registered " .. registered .. "/" .. #actions .. " action scripts.")
utils.log("Open Actions → Show action list → filter 'SessionTemplate' to see them.")
utils.log("Keybinds listed in comments above — assign manually via Actions list.")
utils.log("")
utils.log("Suggested keybinds:")
for _, action in ipairs(actions) do
    if action.key then
        utils.log("  " .. action.key .. " → " .. action.name)
    end
end

reaper.defer(function() end)
