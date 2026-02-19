-- actions/tone_browser.lua — Cycle through Neural DSP plugins on selected track
-- Removes the current Neural DSP plugin and adds the next one in the cycle.
-- Cycle order: Plini X → Petrucci X → Gojira X → Mesa IIC+
-- Stores the current plugin index in ExtState per track.

dofile(debug.getinfo(1, "S").source:match("@?(.*/)") .. "init.lua")

local config = require("config")
local utils  = require("utils")
local fx     = require("fx")

utils.undo_block("Cycle Neural DSP Plugin", function()
    -- Neural DSP plugins to cycle through (config keys)
    local neural_keys = {
        "neural_plini",
        "neural_petrucci",
        "neural_gojira",
        "neural_mesa",
    }

    -- Get selected track
    local track = reaper.GetSelectedTrack(0, 0)
    if not track then
        utils.log("Tone Browser: No track selected. Select a track first.")
        return
    end

    local _, track_name = reaper.GetSetMediaTrackInfo_String(track, "P_NAME", "", false)
    if not track_name or track_name == "" then
        track_name = "Untitled"
    end

    -- Use a per-track ExtState key based on track GUID
    local guid = reaper.GetTrackGUID(track)
    local ext_key = "tone_browser_idx_" .. guid

    -- Get the current index (1-based)
    local idx_str = reaper.GetExtState("SessionTemplate", ext_key)
    local current_idx = tonumber(idx_str) or 0

    -- Advance to the next plugin (wrap around)
    local next_idx = current_idx + 1
    if next_idx > #neural_keys then
        next_idx = 1
    end

    -- Remove any existing Neural DSP plugins from the track
    local plugin_names = {}
    for _, key in ipairs(neural_keys) do
        local entry = config.plugins[key]
        if entry then
            plugin_names[#plugin_names + 1] = entry.preferred
        end
    end

    -- Remove from the end to avoid index shifting
    for fx_idx = reaper.TrackFX_GetCount(track) - 1, 0, -1 do
        local _, name = reaper.TrackFX_GetFXName(track, fx_idx, "")
        if name then
            for _, pname in ipairs(plugin_names) do
                if name:find(pname, 1, true) then
                    reaper.TrackFX_Delete(track, fx_idx)
                    break
                end
            end
        end
    end

    -- Add the next Neural DSP plugin
    local next_key = neural_keys[next_idx]
    local added = fx.smart_add_from_config(track, next_key, false)

    -- Save the new index
    reaper.SetExtState("SessionTemplate", ext_key, tostring(next_idx), false)

    if added then
        utils.log("Tone Browser [" .. track_name .. "]: " .. added
            .. " (" .. next_idx .. "/" .. #neural_keys .. ")")
    else
        local entry = config.plugins[next_key]
        local pref_name = entry and entry.preferred or next_key
        utils.log("Tone Browser: " .. pref_name .. " not available.")
        utils.log("  Install the plugin or skip to the next one by running this action again.")
    end
end)

reaper.defer(function() end)
