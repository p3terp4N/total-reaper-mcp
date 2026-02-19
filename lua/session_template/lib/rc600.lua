-- lib/rc600.lua — RC-600 footswitch → REAPER action mapping
-- Maps CC messages from RC-600 footswitches to REAPER actions.
-- Three pedal modes: Jam (Mode 1), Loop (Mode 2, internal), Live (Mode 3).

local config = require("config")
local utils = require("utils")

local rc600 = {}

-- ============================================================================
-- Action Registration
-- ============================================================================

-- Map of action names to REAPER command IDs or custom action script paths.
-- These get resolved at registration time to actual command IDs.
local action_handlers = {}

--- Register an action handler for a footswitch action name.
-- @param action_name string Name from config.rc600 (e.g., "toggle_record")
-- @param command_id number|string REAPER command ID or named command
function rc600.register_action(action_name, command_id)
    action_handlers[action_name] = command_id
end

--- Get the command ID for an action name.
-- @param action_name string
-- @return number|string|nil Command ID
function rc600.get_action(action_name)
    return action_handlers[action_name]
end

-- ============================================================================
-- Built-in Action Mappings
-- ============================================================================

-- Register default REAPER built-in actions
local function register_defaults()
    -- Transport
    rc600.register_action("toggle_record", 1013)  -- Transport: Record
    rc600.register_action("stop", 1016)            -- Transport: Stop
    rc600.register_action("play_pause", 40073)     -- Transport: Play/pause
    rc600.register_action("stop_return_start", 40042) -- Transport: Go to start
    rc600.register_action("undo", 40029)           -- Edit: Undo
    rc600.register_action("redo", 40030)           -- Edit: Redo
    rc600.register_action("toggle_metronome", 40364) -- Options: Toggle metronome
    rc600.register_action("toggle_loop", 1068)     -- Transport: Toggle repeat

    -- The following are custom action scripts — registered when action scripts
    -- are loaded. Their command IDs are resolved via NamedCommandLookup.
    -- rc600.register_action("idea_marker", "_RS...") -- filled by actions/
    -- rc600.register_action("bounce_selection", "_RS...")
    -- rc600.register_action("arm_next_track", "_RS...")
    -- rc600.register_action("arm_all_di", "_RS...")
    -- etc.
end

register_defaults()

-- ============================================================================
-- CC → Action Dispatch
-- ============================================================================

--- Process a CC message and trigger the corresponding REAPER action.
-- Called from the MIDI monitor or CC-to-action mapping.
-- @param cc_number number MIDI CC number (0-127)
-- @param value number CC value (0-127)
-- @param mode string "jam" or "live"
-- @return boolean True if action was triggered
function rc600.dispatch(cc_number, value, mode)
    mode = mode or "jam"
    local mapping = config.rc600[mode]
    if not mapping then return false end

    for _, entry in ipairs(mapping) do
        if entry.cc == cc_number then
            -- CC value > 64 = press, value 0 = release
            -- For hold detection, the caller handles timing
            local action_name = entry.press
            if action_name then
                local cmd = action_handlers[action_name]
                if cmd then
                    if type(cmd) == "number" then
                        reaper.Main_OnCommand(cmd, 0)
                    elseif type(cmd) == "string" then
                        local id = reaper.NamedCommandLookup(cmd)
                        if id > 0 then
                            reaper.Main_OnCommand(id, 0)
                        end
                    end
                    return true
                end
            end
        end
    end
    return false
end

--- Get a human-readable mapping table for a pedal mode.
-- @param mode string "jam" or "live"
-- @return table Array of {switch, cc, press_action, hold_action, press_cmd, hold_cmd}
function rc600.get_mapping(mode)
    mode = mode or "jam"
    local mapping = config.rc600[mode]
    if not mapping then return {} end

    local result = {}
    for _, entry in ipairs(mapping) do
        result[#result + 1] = {
            switch = entry.switch,
            cc = entry.cc,
            press_action = entry.press,
            hold_action = entry.hold,
            press_cmd = action_handlers[entry.press],
            hold_cmd = entry.hold and action_handlers[entry.hold] or nil,
        }
    end
    return result
end

return rc600
