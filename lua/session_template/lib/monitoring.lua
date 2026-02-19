-- lib/monitoring.lua — Monitor FX (SoundID Reference, metering)
-- Monitor FX chain is placed in REAPER's monitoring path (View > Monitoring FX).
-- These FX are excluded from all renders automatically.

local config = require("config")
local plugins = require("plugins")
local utils = require("utils")

local monitoring = {}

-- ============================================================================
-- Monitor FX Helpers
-- ============================================================================

--- Add an FX to the Monitor FX chain on the master track.
-- Monitor FX uses the 0x1000000 offset with TrackFX_AddByName.
-- @param plugin_name string Plugin name
-- @param bypassed boolean Add in bypassed state
-- @return number FX index in monitor chain, or -1 on failure
function monitoring.add_monitor_fx(plugin_name, bypassed)
    local master = reaper.GetMasterTrack(0)
    if not master then return -1 end

    -- 0x1000000 flag = add to monitor FX chain (not regular FX chain)
    local fx_idx = reaper.TrackFX_AddByName(master, plugin_name, false, -1 + 0x1000000)
    if fx_idx >= 0 and bypassed then
        -- Monitor FX uses 0x1000000 offset for get/set operations too
        reaper.TrackFX_SetEnabled(master, fx_idx + 0x1000000, false)
    end
    return fx_idx
end

--- Add a preferred/fallback plugin to Monitor FX chain.
-- @param preferred string Preferred plugin name
-- @param fallback string|nil Fallback plugin name
-- @param bypassed boolean
-- @return string|nil Plugin name that was added
function monitoring.smart_add_monitor_fx(preferred, fallback, bypassed)
    local name = plugins.resolve(preferred, fallback)
    if not name then return nil end

    local idx = monitoring.add_monitor_fx(name, bypassed)
    if idx >= 0 then
        return name
    end
    return nil
end

-- ============================================================================
-- Standard Monitor Chain Setup
-- ============================================================================

--- Set up the standard monitoring chain: SoundID Reference + metering.
-- Called during session creation for templates that need calibrated monitoring.
function monitoring.setup_standard()
    -- 1. SoundID Reference (room correction / headphone profile)
    local soundid = config.plugins.soundid
    if soundid then
        local added = monitoring.smart_add_monitor_fx(soundid.preferred, soundid.fallback, false)
        if added then
            utils.log("Monitor FX: " .. added .. " (SoundID Reference)")
        else
            utils.log("Monitor FX: SoundID Reference not available, skipping")
        end
    end

    -- 2. Loudness meter (REAPER built-in JS)
    local meter_name = config.monitoring.loudness_meter
    if meter_name then
        local idx = monitoring.add_monitor_fx(meter_name, false)
        if idx >= 0 then
            utils.log("Monitor FX: " .. meter_name)
        end
    end

    -- 3. Spectrum analyzer (ReaEQ in analyzer mode)
    local eq_entry = config.plugins.eq_surgical
    if eq_entry then
        local eq_name = plugins.resolve(eq_entry.preferred, eq_entry.fallback)
        if eq_name then
            monitoring.add_monitor_fx(eq_name, true) -- Bypassed by default
            utils.log("Monitor FX: " .. eq_name .. " (spectrum analyzer, bypassed)")
        end
    end
end

--- Set up minimal monitoring (just SoundID, no metering).
-- For session types where metering isn't needed.
function monitoring.setup_minimal()
    local soundid = config.plugins.soundid
    if soundid then
        monitoring.smart_add_monitor_fx(soundid.preferred, soundid.fallback, false)
    end
end

-- ============================================================================
-- Monitor FX Utility
-- ============================================================================

--- Get the count of Monitor FX on the master track.
-- @return number
function monitoring.get_count()
    local master = reaper.GetMasterTrack(0)
    if not master then return 0 end
    return reaper.TrackFX_GetRecCount(master)
end

--- Clear all Monitor FX.
function monitoring.clear()
    local master = reaper.GetMasterTrack(0)
    if not master then return end
    local count = reaper.TrackFX_GetRecCount(master)
    for i = count - 1, 0, -1 do
        reaper.TrackFX_Delete(master, i + 0x1000000)
    end
end

return monitoring
