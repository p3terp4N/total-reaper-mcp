-- lib/dialog.lua — REAPER GetUserInputs dialog for session creation
-- Shows a dialog with session name, type selection, BPM, time sig, key, sample rate.

local config = require("config")

local dialog = {}

-- Build the type list string for the dialog
local function get_type_list()
    local types = {
        { key = "guitar",        num = 1 },
        { key = "production",    num = 2 },
        { key = "songwriting",   num = 3 },
        { key = "jam",           num = 4 },
        { key = "podcast",       num = 5 },
        { key = "mixing",        num = 6 },
        { key = "tone",          num = 7 },
        { key = "live",          num = 8 },
        { key = "transcription", num = 9 },
    }
    return types
end

--- Show the session creation dialog.
-- @return table|nil {name, type_key, bpm, time_sig, key, sample_rate} or nil if cancelled
function dialog.show()
    local types = get_type_list()

    -- Build description for type field
    local type_desc = {}
    for _, t in ipairs(types) do
        local info = config.session_types[t.key]
        type_desc[#type_desc + 1] = t.num .. ". " .. (info and info.name or t.key)
    end

    -- REAPER GetUserInputs: title, num_fields, captions (CSV), defaults (CSV)
    local title = "New Session"
    local num_fields = 6
    local captions = "Session Name:,"
        .. "Session Type (1-9)\\n" .. table.concat(type_desc, "\\n") .. ","
        .. "BPM:,"
        .. "Time Signature:,"
        .. "Key:,"
        .. "Sample Rate:"
    local defaults = ",1,120,4/4,Am,48000"

    local retval, retvals_csv = reaper.GetUserInputs(title, num_fields, captions, defaults)
    if not retval then return nil end

    -- Parse CSV response
    local fields = {}
    for field in retvals_csv:gmatch("([^,]*)") do
        fields[#fields + 1] = field
    end

    local session_name = fields[1] or ""
    local type_num = tonumber(fields[2]) or 1
    local bpm = tonumber(fields[3]) or 120
    local time_sig = fields[4] or "4/4"
    local key = fields[5] or ""
    local sample_rate = tonumber(fields[6]) or 48000

    -- Map type number to key
    local type_key = "guitar"  -- default
    for _, t in ipairs(types) do
        if t.num == type_num then
            type_key = t.key
            break
        end
    end

    -- Validate
    if session_name == "" then
        session_name = "Untitled " .. os.date("%Y-%m-%d %H%M")
    end

    return {
        name = session_name,
        type_key = type_key,
        bpm = bpm,
        time_sig = time_sig,
        key = key,
        sample_rate = sample_rate,
    }
end

return dialog
