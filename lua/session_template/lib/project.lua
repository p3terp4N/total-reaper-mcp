-- lib/project.lua — Project settings (BPM, grid, paths, auto-save, recording)
-- Configures REAPER project properties for a session template.

local config = require("config")
local utils = require("utils")

local project = {}

--- Set project BPM.
-- @param bpm number Tempo in BPM
function project.set_bpm(bpm)
    reaper.SetTempoTimeSigMarker(0, -1, -1, -1, -1, bpm, 0, 0, false)
end

--- Set project time signature.
-- @param num number Numerator (e.g., 4)
-- @param denom number Denominator (e.g., 4)
function project.set_time_sig(num, denom)
    -- Set via the initial tempo/time sig marker
    local bpm = reaper.Master_GetTempo()
    reaper.SetTempoTimeSigMarker(0, -1, -1, -1, -1, bpm, num, denom, false)
end

--- Set project grid division and snap.
-- @param division number|nil Grid division (0.25 = 1/4, 0.0625 = 1/16, nil = off)
-- @param snap boolean Enable snap to grid
function project.set_grid(division, snap)
    if division then
        reaper.GetSetProjectGrid(0, true, division)
    end

    -- Snap on/off via SWS if available
    if utils.has_sws() then
        reaper.SNM_SetIntConfigVar("projgridsnap", snap and 1 or 0)
    end
end

--- Set project sample rate.
-- @param rate number Sample rate in Hz (44100 or 48000)
function project.set_sample_rate(rate)
    if utils.has_sws() then
        reaper.SNM_SetIntConfigVar("projsrate", rate)
        reaper.SNM_SetIntConfigVar("projsrateuse", 1) -- Use project sample rate
    end
end

--- Set recording format to WAV 24-bit.
function project.set_recording_format()
    if utils.has_sws() then
        -- recfmt: 1 = WAV
        reaper.SNM_SetIntConfigVar("recfmt", 1)
    end
end

--- Set project recording path.
-- @param session_name string Session name (used as subdirectory)
function project.set_recording_path(session_name)
    local base = config.recording.path:gsub("^~", os.getenv("HOME") or "~")
    local path = base .. session_name .. "/"

    -- Create directory
    reaper.RecursiveCreateDirectory(path, 0)

    -- Set as project recording path
    reaper.GetSetProjectInfo_String(0, "RECORD_PATH", path, true)
end

--- Set auto-save interval.
-- @param minutes number Interval in minutes
function project.set_autosave(minutes)
    if utils.has_sws() then
        reaper.SNM_SetIntConfigVar("autosaveint", minutes)
        reaper.SNM_SetIntConfigVar("autosavemode", 1) -- Enable auto-save
    end
end

--- Set metronome pre-roll.
-- @param bars number Number of bars for count-in
function project.set_preroll(bars)
    if utils.has_sws() then
        reaper.SNM_SetIntConfigVar("preroll", bars)
        reaper.SNM_SetIntConfigVar("prerollmeas", 1) -- Enable pre-roll
    end
end

--- Configure project notes with session metadata.
-- @param opts table {name, type_name, bpm, key, time_sig}
function project.set_notes(opts)
    local notes = string.format(
        "SESSION: %s\nDATE: %s\nBPM: %d | KEY: %s | TIME SIG: %s\nTYPE: %s\n",
        opts.name or "Untitled",
        os.date("%Y-%m-%d"),
        opts.bpm or 120,
        opts.key or "—",
        opts.time_sig or "4/4",
        opts.type_name or "—"
    )
    reaper.GetSetProjectNotes(0, true, notes)
end

--- Apply all project settings for a session template.
-- @param session_opts table From dialog: {name, type_key, bpm, time_sig, key, sample_rate}
function project.apply(session_opts)
    local type_config = config.session_types[session_opts.type_key] or {}

    -- Parse time signature
    local ts_num, ts_denom = 4, 4
    if type(session_opts.time_sig) == "string" and session_opts.time_sig:find("/") then
        ts_num, ts_denom = session_opts.time_sig:match("(%d+)/(%d+)")
        ts_num = tonumber(ts_num) or 4
        ts_denom = tonumber(ts_denom) or 4
    elseif type(session_opts.time_sig) == "table" then
        ts_num = session_opts.time_sig[1] or 4
        ts_denom = session_opts.time_sig[2] or 4
    end

    project.set_bpm(session_opts.bpm or 120)
    project.set_time_sig(ts_num, ts_denom)
    project.set_grid(type_config.grid, type_config.snap)
    project.set_sample_rate(session_opts.sample_rate or config.recording.rate)
    project.set_recording_format()
    project.set_recording_path(session_opts.name or "Untitled")
    project.set_autosave(config.recording.auto_save_minutes)
    project.set_preroll(config.recording.pre_roll_bars)
    project.set_notes({
        name = session_opts.name,
        type_name = type_config.name or session_opts.type_key,
        bpm = session_opts.bpm,
        key = session_opts.key,
        time_sig = session_opts.time_sig,
    })
end

return project
