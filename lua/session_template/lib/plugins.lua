-- lib/plugins.lua — Plugin auto-discovery via probe track
-- Scans installed plugins by attempting TrackFX_AddByName on a temp track.
-- Results cached per session to avoid repeated scanning.

local plugins = {}

-- Cache of scan results: { ["Plugin Name"] = true/false }
local _cache = {}
local _scanned = false

-- ============================================================================
-- Core Functions
-- ============================================================================

--- Check if a specific plugin is installed.
-- Uses a temporary track to probe TrackFX_AddByName.
-- Results are cached — subsequent calls for the same plugin are instant.
-- @param plugin_name string Exact plugin name as REAPER knows it
-- @return boolean True if plugin is available
function plugins.is_available(plugin_name)
    if plugin_name == nil or plugin_name == "" then
        return false
    end

    -- Check cache first
    if _cache[plugin_name] ~= nil then
        return _cache[plugin_name]
    end

    -- REAPER built-in plugins (ReaEQ, ReaComp, etc.) and JS effects are always available
    if plugin_name:match("^Rea") or plugin_name:match("^JS:") then
        _cache[plugin_name] = true
        return true
    end

    -- Probe using a temporary track
    local available = false
    reaper.PreventUIRefresh(1)

    -- Insert temp track at the end
    local track_count = reaper.CountTracks(0)
    reaper.InsertTrackAtIndex(track_count, false)
    local probe_track = reaper.GetTrack(0, track_count)

    if probe_track then
        -- Try to add the plugin (instantiate = false just checks availability)
        local fx_idx = reaper.TrackFX_AddByName(probe_track, plugin_name, false, -1)
        if fx_idx >= 0 then
            available = true
            -- Remove the FX we just added
            reaper.TrackFX_Delete(probe_track, fx_idx)
        end
        -- Remove the temp track
        reaper.DeleteTrack(probe_track)
    end

    reaper.PreventUIRefresh(-1)

    -- Cache result
    _cache[plugin_name] = available
    return available
end

--- Resolve a preferred/fallback plugin pair.
-- Returns the first available plugin name, or nil if neither is available.
-- @param preferred string Preferred plugin name
-- @param fallback string|nil Fallback plugin name
-- @return string|nil The plugin name to use, or nil
function plugins.resolve(preferred, fallback)
    if preferred and plugins.is_available(preferred) then
        return preferred
    end
    if fallback and plugins.is_available(fallback) then
        return fallback
    end
    return nil
end

--- Resolve a plugin pair from a config entry.
-- Config entries have the format { preferred = "Name", fallback = "Name" }.
-- @param entry table Config plugin entry with preferred/fallback keys
-- @return string|nil The plugin name to use
function plugins.resolve_entry(entry)
    if type(entry) ~= "table" then return nil end
    return plugins.resolve(entry.preferred, entry.fallback)
end

-- ============================================================================
-- Bulk Scanning
-- ============================================================================

--- Scan all plugins from a config table and return availability report.
-- @param plugin_config table The config.plugins table
-- @return table { available = {name=true, ...}, missing = {name=true, ...} }
function plugins.scan_all(plugin_config)
    local report = { available = {}, missing = {} }

    for key, entry in pairs(plugin_config) do
        if type(entry) == "table" and entry.preferred then
            local pref = entry.preferred
            if plugins.is_available(pref) then
                report.available[pref] = true
            else
                report.missing[pref] = true
            end
            -- Also check fallback
            if entry.fallback then
                if plugins.is_available(entry.fallback) then
                    report.available[entry.fallback] = true
                else
                    report.missing[entry.fallback] = true
                end
            end
        end
    end

    _scanned = true
    return report
end

--- Check if a full scan has been performed.
-- @return boolean
function plugins.has_scanned()
    return _scanned
end

--- Clear the plugin cache (force re-scan on next check).
function plugins.clear_cache()
    _cache = {}
    _scanned = false
end

return plugins
