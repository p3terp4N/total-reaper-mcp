-- lib/render.lua — Render presets
-- Configures REAPER render settings for different output targets.
-- Presets: Master, Master CD, MP3 Preview, Stems, DI Only, Podcast, Podcast HQ.

local config = require("config")
local utils = require("utils")

local render = {}

-- REAPER render format codes
local FORMAT = {
    WAV = 0,   -- evaw (WAV)
    MP3 = 1,   -- l3pm (MP3/LAME)
}

-- ============================================================================
-- Render Settings via SWS
-- ============================================================================

--- Apply render settings using SWS SNM_SetIntConfigVar.
-- @param opts table Render options from config.render
function render.apply_settings(opts)
    if not utils.has_sws() then
        utils.log("SWS required for render preset configuration")
        return
    end

    -- Set render format
    if opts.format == "WAV" then
        -- WAV settings
        reaper.GetSetProjectInfo(0, "RENDER_FORMAT", FORMAT.WAV, true)
        if opts.bits then
            -- Bit depth: stored in render settings
            -- 16-bit = 1, 24-bit = 2, 32-bit float = 3
            local depth_map = { [16] = 1, [24] = 2, [32] = 3 }
            local depth = depth_map[opts.bits] or 2
            reaper.GetSetProjectInfo(0, "RENDER_FORMAT", depth, true)
        end
    elseif opts.format == "MP3" then
        reaper.GetSetProjectInfo(0, "RENDER_FORMAT", FORMAT.MP3, true)
    end

    -- Sample rate
    if opts.rate then
        reaper.GetSetProjectInfo(0, "RENDER_SRATE", opts.rate, true)
    end

    -- Channels (mono/stereo)
    if opts.mono then
        reaper.GetSetProjectInfo(0, "RENDER_CHANNELS", 1, true)
    else
        reaper.GetSetProjectInfo(0, "RENDER_CHANNELS", 2, true)
    end

    -- Dithering
    if opts.dither then
        reaper.GetSetProjectInfo(0, "RENDER_DITHER", 1, true)
    end
end

--- Set render bounds.
-- @param mode number 0=custom, 1=entire project, 2=time selection, 3=regions, 4=selected items, 5=selected regions
function render.set_bounds(mode)
    reaper.GetSetProjectInfo(0, "RENDER_BOUNDSFLAG", mode, true)
end

--- Set render directory.
-- @param path string Output directory
function render.set_directory(path)
    reaper.GetSetProjectInfo_String(0, "RENDER_FILE", path, true)
end

--- Set render filename pattern.
-- @param pattern string e.g., "$project - $track" for stem export
function render.set_filename(pattern)
    reaper.GetSetProjectInfo_String(0, "RENDER_PATTERN", pattern, true)
end

-- ============================================================================
-- Named Render Presets
-- ============================================================================

--- Apply a named render preset from config.
-- @param preset_name string Key from config.render (e.g., "master", "podcast")
function render.apply_preset(preset_name)
    local preset = config.render[preset_name]
    if not preset then
        utils.log("Unknown render preset: " .. tostring(preset_name))
        return
    end

    render.apply_settings(preset)
    utils.log("Render preset applied: " .. (preset.label or preset_name))
end

--- Get a summary of all available render presets.
-- @return table Array of {name, label, format, description}
function render.list_presets()
    local list = {}
    for name, preset in pairs(config.render) do
        list[#list + 1] = {
            name = name,
            label = preset.label or name,
            format = preset.format,
            bits = preset.bits,
            rate = preset.rate,
            mono = preset.mono or false,
        }
    end
    return list
end

return render
