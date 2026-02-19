-- lib/fx.lua — FX engine: smart_add with preferred/fallback
-- Uses plugins.lua for availability checks, config.lua for chain definitions.

local config = require("config")
local plugins = require("plugins")

local fx = {}

-- ============================================================================
-- Core FX Functions
-- ============================================================================

--- Add a single FX plugin to a track by name.
-- @param track MediaTrack Target track
-- @param plugin_name string Plugin name (as REAPER knows it)
-- @param bypassed boolean If true, add in bypassed state
-- @return number FX index (0-based), or -1 on failure
function fx.add(track, plugin_name, bypassed)
    if not track or not plugin_name then return -1 end

    local fx_idx = reaper.TrackFX_AddByName(track, plugin_name, false, -1)
    if fx_idx >= 0 and bypassed then
        reaper.TrackFX_SetEnabled(track, fx_idx, false)
    end
    return fx_idx
end

--- Smart-add: try preferred plugin, fall back if not available.
-- @param track MediaTrack Target track
-- @param preferred string Preferred plugin name
-- @param fallback string|nil Fallback plugin name
-- @param bypassed boolean If true, add in bypassed state
-- @return string|nil Plugin name that was added, or nil on failure
function fx.smart_add(track, preferred, fallback, bypassed)
    local resolved = plugins.resolve(preferred, fallback)
    if not resolved then return nil end

    local idx = fx.add(track, resolved, bypassed)
    if idx >= 0 then
        return resolved
    end
    return nil
end

--- Smart-add from a config plugin entry.
-- Config entries: { preferred = "Name", fallback = "Name" }
-- @param track MediaTrack Target track
-- @param plugin_key string Key in config.plugins (e.g., "eq_surgical")
-- @param bypassed boolean If true, add in bypassed state
-- @return string|nil Plugin name that was added
function fx.smart_add_from_config(track, plugin_key, bypassed)
    local entry = config.plugins[plugin_key]
    if not entry then return nil end
    return fx.smart_add(track, entry.preferred, entry.fallback, bypassed)
end

-- ============================================================================
-- FX Chain Functions
-- ============================================================================

--- Add an ordered chain of FX to a track.
-- Each entry is a config plugin key. Plugins are added in order.
-- @param track MediaTrack Target track
-- @param chain table Array of config.plugins keys (e.g., {"tuner", "gate"})
-- @param bypass_list table|nil Array of booleans — true to bypass that slot
-- @return table Array of {key, plugin_name, fx_index} for each added FX
function fx.add_chain(track, chain, bypass_list)
    local results = {}
    for i, plugin_key in ipairs(chain) do
        local bypassed = bypass_list and bypass_list[i] or false
        local entry = config.plugins[plugin_key]
        if entry then
            local name = fx.smart_add(track, entry.preferred, entry.fallback, bypassed)
            results[#results + 1] = {
                key = plugin_key,
                plugin = name,
                fx_index = name and (reaper.TrackFX_GetCount(track) - 1) or -1,
            }
        end
    end
    return results
end

--- Add a named FX chain from config.fx_chains.
-- @param track MediaTrack Target track
-- @param chain_name string Key in config.fx_chains (e.g., "guitar_di")
-- @param bypass_first boolean If true, bypass the first plugin in chain
-- @return table Array of {key, plugin_name, fx_index}
function fx.add_named_chain(track, chain_name, bypass_first)
    local chain = config.fx_chains[chain_name]
    if not chain then return {} end

    local bypass_list = nil
    if bypass_first then
        bypass_list = {}
        for i = 1, #chain do
            bypass_list[i] = (i == 1)
        end
    end

    return fx.add_chain(track, chain, bypass_list)
end

-- ============================================================================
-- FX Parameter Control
-- ============================================================================

--- Set a named FX parameter value.
-- @param track MediaTrack
-- @param fx_idx number 0-based FX index
-- @param param_name string Parameter name to search for
-- @param value number Normalized value (0.0 to 1.0)
-- @return boolean Success
function fx.set_param_by_name(track, fx_idx, param_name, value)
    local param_count = reaper.TrackFX_GetNumParams(track, fx_idx)
    for i = 0, param_count - 1 do
        local _, name = reaper.TrackFX_GetParamName(track, fx_idx, i, "")
        if name and name:lower():find(param_name:lower(), 1, true) then
            reaper.TrackFX_SetParam(track, fx_idx, i, value)
            return true
        end
    end
    return false
end

--- Bypass/enable an FX on a track.
-- @param track MediaTrack
-- @param fx_idx number 0-based FX index
-- @param bypassed boolean True to bypass
function fx.set_bypass(track, fx_idx, bypassed)
    reaper.TrackFX_SetEnabled(track, fx_idx, not bypassed)
end

-- ============================================================================
-- FX Utility
-- ============================================================================

--- Get the FX index of a plugin by name on a track.
-- @param track MediaTrack
-- @param plugin_name string Plugin name to search for
-- @return number FX index (0-based), or -1 if not found
function fx.find_on_track(track, plugin_name)
    local count = reaper.TrackFX_GetCount(track)
    for i = 0, count - 1 do
        local _, name = reaper.TrackFX_GetFXName(track, i, "")
        if name and name:find(plugin_name, 1, true) then
            return i
        end
    end
    return -1
end

--- Remove all FX from a track.
-- @param track MediaTrack
function fx.clear_all(track)
    while reaper.TrackFX_GetCount(track) > 0 do
        reaper.TrackFX_Delete(track, 0)
    end
end

return fx
