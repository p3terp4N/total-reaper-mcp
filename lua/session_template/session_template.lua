-- session_template.lua — Main entry point for standalone session creation
-- Bound to a REAPER keybind. Shows dialog, loads template, executes.
-- This file is loaded by: actions/init.lua bootstrap OR directly via keybind.

local info = debug.getinfo(1, "S")
local script_path = info.source:match("@?(.*/)")
package.path = script_path .. "lib/?.lua;" .. package.path

-- Modules loaded after Phase 1+3 implementation
-- local config = require("config")
-- local dialog = require("dialog")
-- local project = require("project")

-- Placeholder: will show dialog → select template → execute
reaper.defer(function() end)
