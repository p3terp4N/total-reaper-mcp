-- lib/utils.lua — Colors, helpers, wrappers
-- Shared utility functions for all session template modules.

local utils = {}

-- ============================================================================
-- Color Helpers
-- ============================================================================

--- Convert RGB (0-255) to REAPER native color format.
-- REAPER uses OS-dependent color encoding with a flag bit.
-- @param r number Red (0-255)
-- @param g number Green (0-255)
-- @param b number Blue (0-255)
-- @return number REAPER native color value
function utils.rgb(r, g, b)
    -- REAPER native: R | (G << 8) | (B << 16) | 0x01000000
    return r + (g * 256) + (b * 65536) + 0x01000000
end

--- Convert a color table {r, g, b} to REAPER native color.
-- @param color_table table {r, g, b} values 0-255
-- @return number REAPER native color value
function utils.color(color_table)
    return utils.rgb(color_table[1], color_table[2], color_table[3])
end

-- ============================================================================
-- MIDI Device Helpers
-- ============================================================================

--- Find a MIDI input device index by name substring.
-- @param name_part string Part of the device name to match
-- @return number|nil Device index (0-based) or nil if not found
function utils.find_midi_input(name_part)
    local count = reaper.GetNumMIDIInputs()
    for i = 0, count - 1 do
        local retval, name = reaper.GetMIDIInputName(i, "")
        if retval and name and name:find(name_part, 1, true) then
            return i
        end
    end
    return nil
end

--- Find a MIDI output device index by name substring.
-- @param name_part string Part of the device name to match
-- @return number|nil Device index (0-based) or nil if not found
function utils.find_midi_output(name_part)
    local count = reaper.GetNumMIDIOutputs()
    for i = 0, count - 1 do
        local retval, name = reaper.GetMIDIOutputName(i, "")
        if retval and name and name:find(name_part, 1, true) then
            return i
        end
    end
    return nil
end

-- ============================================================================
-- REAPER Input Encoding
-- ============================================================================

--- Encode a hardware audio input for I_RECINPUT.
-- @param channel number 1-based hardware input channel
-- @param stereo boolean If true, use stereo pair starting at channel
-- @return number I_RECINPUT value
function utils.encode_audio_input(channel, stereo)
    -- REAPER I_RECINPUT encoding for audio:
    -- Mono: channel_index (0-based)
    -- Stereo: channel_index (0-based) + 1024
    local idx = channel - 1  -- Convert to 0-based
    if stereo then
        return idx + 1024
    end
    return idx
end

--- Encode a MIDI input for I_RECINPUT.
-- @param device_idx number 0-based MIDI device index
-- @param channel number 1-based MIDI channel (1-16), or 0 for all channels
-- @return number I_RECINPUT value
function utils.encode_midi_input(device_idx, channel)
    -- REAPER I_RECINPUT encoding for MIDI:
    -- 4096 + device_idx * 32 + channel (0 = all channels, 1-16 = specific)
    return 4096 + (device_idx * 32) + (channel or 0)
end

-- ============================================================================
-- Undo Block Wrapper
-- ============================================================================

--- Execute a function wrapped in an undo block.
-- @param label string Undo label shown in REAPER's Edit → Undo
-- @param fn function The function to execute
-- @param ... any Arguments passed to fn
-- @return any Return value of fn
function utils.undo_block(label, fn, ...)
    reaper.Undo_BeginBlock()
    reaper.PreventUIRefresh(1)
    local result = fn(...)
    reaper.PreventUIRefresh(-1)
    reaper.Undo_EndBlock(label, -1)
    return result
end

-- ============================================================================
-- SWS Extension Guard
-- ============================================================================

--- Check if SWS extension is available.
-- @return boolean
function utils.has_sws()
    return reaper.SNM_SetIntConfigVar ~= nil
end

--- Call an SWS function safely, returning nil if SWS is not installed.
-- @param fn_name string Name of the reaper.SNM_* function
-- @param ... any Arguments
-- @return any|nil Result or nil if SWS unavailable
function utils.sws_call(fn_name, ...)
    local fn = reaper[fn_name]
    if fn then
        return fn(...)
    end
    return nil
end

-- ============================================================================
-- Table Utilities
-- ============================================================================

--- Shallow copy a table.
-- @param t table
-- @return table
function utils.shallow_copy(t)
    local copy = {}
    for k, v in pairs(t) do
        copy[k] = v
    end
    return copy
end

--- Merge table b into table a (a is modified in place).
-- @param a table Target
-- @param b table Source
-- @return table Modified a
function utils.merge(a, b)
    for k, v in pairs(b) do
        a[k] = v
    end
    return a
end

-- ============================================================================
-- String Utilities
-- ============================================================================

--- Pad a string to a minimum length.
-- @param str string
-- @param len number Minimum length
-- @param char string Padding character (default space)
-- @return string
function utils.pad(str, len, char)
    char = char or " "
    while #str < len do
        str = str .. char
    end
    return str
end

-- ============================================================================
-- Console / Debug
-- ============================================================================

--- Print a message to REAPER's console.
-- @param ... any Values to print (concatenated with space)
function utils.log(...)
    local parts = {}
    for i = 1, select("#", ...) do
        parts[#parts + 1] = tostring(select(i, ...))
    end
    reaper.ShowConsoleMsg(table.concat(parts, " ") .. "\n")
end

-- ============================================================================
-- JSON Encoding (minimal, for bridge communication)
-- ============================================================================

--- Encode a Lua value as JSON string.
-- Supports strings, numbers, booleans, nil, and tables (arrays and objects).
-- @param val any
-- @return string JSON string
function utils.to_json(val)
    if val == nil then return "null" end
    local t = type(val)
    if t == "string" then
        return '"' .. val:gsub('\\', '\\\\'):gsub('"', '\\"'):gsub('\n', '\\n'):gsub('\r', '\\r'):gsub('\t', '\\t') .. '"'
    elseif t == "number" then
        return tostring(val)
    elseif t == "boolean" then
        return val and "true" or "false"
    elseif t == "table" then
        -- Check if array (sequential integer keys starting at 1)
        local is_array = true
        local max_idx = 0
        for k, _ in pairs(val) do
            if type(k) == "number" and k == math.floor(k) and k > 0 then
                if k > max_idx then max_idx = k end
            else
                is_array = false
                break
            end
        end
        if is_array and max_idx == #val then
            local parts = {}
            for i = 1, #val do
                parts[i] = utils.to_json(val[i])
            end
            return "[" .. table.concat(parts, ",") .. "]"
        else
            local parts = {}
            for k, v in pairs(val) do
                parts[#parts + 1] = utils.to_json(tostring(k)) .. ":" .. utils.to_json(v)
            end
            return "{" .. table.concat(parts, ",") .. "}"
        end
    end
    return "null"
end

return utils
