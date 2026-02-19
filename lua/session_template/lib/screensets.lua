-- lib/screensets.lua — Window layouts (screensets)
-- REAPER screensets save/restore window arrangements.
-- We configure 3 presets: Recording (F1), Mixing (F2), Editing (F3).

local config = require("config")
local utils = require("utils")

local screensets = {}

-- REAPER screenset command IDs (built-in actions)
-- Screenset 1-10 load: 40454-40463
-- Screenset 1-10 save: 40464-40473
local LOAD_CMDS = { 40454, 40455, 40456, 40457, 40458, 40459, 40460, 40461, 40462, 40463 }
local SAVE_CMDS = { 40464, 40465, 40466, 40467, 40468, 40469, 40470, 40471, 40472, 40473 }

--- Save current window layout to a screenset slot.
-- @param slot number Screenset slot (1-10)
function screensets.save(slot)
    if slot >= 1 and slot <= 10 then
        reaper.Main_OnCommand(SAVE_CMDS[slot], 0)
    end
end

--- Load a screenset by slot number.
-- @param slot number Screenset slot (1-10)
function screensets.load(slot)
    if slot >= 1 and slot <= 10 then
        reaper.Main_OnCommand(LOAD_CMDS[slot], 0)
    end
end

--- Set up default screensets for a session.
-- Configures the window layout based on the session type's default screenset.
-- @param default_screenset string "recording", "mixing", or "editing"
function screensets.apply_default(default_screenset)
    -- Map screenset names to slots
    local slot_map = {
        recording = 1,
        mixing = 2,
        editing = 3,
    }

    local slot = slot_map[default_screenset]
    if slot then
        -- Load the default screenset for this session type
        screensets.load(slot)
        utils.log("Loaded screenset: " .. default_screenset .. " (F" .. slot .. ")")
    end
end

--- Show the mixer window.
function screensets.show_mixer()
    reaper.Main_OnCommand(40078, 0) -- View: Toggle mixer
end

--- Show the track manager.
function screensets.show_track_manager()
    reaper.Main_OnCommand(40906, 0) -- View: Show track manager window
end

--- Zoom to fit all tracks vertically.
function screensets.zoom_fit_tracks()
    reaper.Main_OnCommand(40110, 0) -- View: Toggle track zoom to maximum height
end

--- Zoom to show full project horizontally.
function screensets.zoom_fit_project()
    reaper.Main_OnCommand(40295, 0) -- View: Zoom to fit project in arrange view
end

return screensets
