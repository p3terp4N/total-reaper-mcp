-- session_template.lua — Main entry point for standalone session creation
-- Bind this script to a REAPER keybind (e.g., Ctrl+Shift+N).
-- Shows a dialog to select session type, then builds the session.

-- Set up package path to find lib/ modules
local info = debug.getinfo(1, "S")
local script_path = info.source:match("@?(.*/)")
if script_path then
    package.path = script_path .. "lib/?.lua;" .. script_path .. "templates/?.lua;" .. package.path
else
    reaper.ShowConsoleMsg("ERROR: Could not determine script path\n")
    return
end

local config = require("config")
local dialog = require("dialog")
local project = require("project")
local utils = require("utils")

-- Template loaders (lazy-loaded on demand)
local template_map = {
    guitar        = "guitar_recording",
    production    = "full_production",
    songwriting   = "songwriting",
    jam           = "jam_loop",
    podcast       = "podcast",
    mixing        = "mixing",
    tone          = "tone_design",
    live          = "live_performance",
    transcription = "transcription",
}

local function load_template(type_key)
    local module_name = template_map[type_key]
    if not module_name then
        reaper.ShowConsoleMsg("ERROR: Unknown session type: " .. tostring(type_key) .. "\n")
        return nil
    end

    local ok, template = pcall(require, module_name)
    if not ok then
        reaper.ShowConsoleMsg("ERROR: Failed to load template '" .. module_name .. "': " .. tostring(template) .. "\n")
        return nil
    end

    if type(template.build) ~= "function" then
        reaper.ShowConsoleMsg("ERROR: Template '" .. module_name .. "' has no build() function\n")
        return nil
    end

    return template
end

-- Main execution
local function main()
    -- Show dialog
    local opts = dialog.show()
    if not opts then
        return -- User cancelled
    end

    -- Load template
    local template = load_template(opts.type_key)
    if not template then return end

    -- Build session
    local type_info = config.session_types[opts.type_key] or {}
    utils.log("Creating session: " .. opts.name .. " (" .. (type_info.name or opts.type_key) .. ")")

    reaper.Undo_BeginBlock()
    reaper.PreventUIRefresh(1)

    local ok, err = pcall(template.build, opts.name, opts.bpm, opts.time_sig, opts.key, opts.sample_rate)

    reaper.PreventUIRefresh(-1)
    reaper.Undo_EndBlock("Create Session: " .. opts.name, -1)
    reaper.TrackList_AdjustWindows(false)
    reaper.UpdateArrange()

    if ok then
        utils.log("Session created successfully: " .. opts.name)
    else
        reaper.ShowConsoleMsg("ERROR: Template build failed: " .. tostring(err) .. "\n")
    end
end

-- Run
main()
reaper.defer(function() end)
