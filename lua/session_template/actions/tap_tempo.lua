-- actions/tap_tempo.lua — Tap tempo via repeated script invocation
-- Stores last tap time in REAPER ExtState. If called again within 3 seconds,
-- calculates BPM from the interval and sets the project tempo. Tap twice (or
-- more) to dial in the tempo. Resets if more than 3 seconds elapse between taps.

dofile(debug.getinfo(1, "S").source:match("@?(.*/)") .. "init.lua")

local utils = require("utils")

local EXT_SECTION = "SessionTemplate"
local EXT_KEY     = "last_tap_time"
local TAP_TIMEOUT = 3.0  -- seconds; reset if gap exceeds this
local MIN_BPM     = 30
local MAX_BPM     = 300

reaper.Undo_BeginBlock()

local now = os.clock()
local last_tap_str = reaper.GetExtState(EXT_SECTION, EXT_KEY)
local last_tap = tonumber(last_tap_str)

if last_tap and (now - last_tap) < TAP_TIMEOUT and (now - last_tap) > 0 then
    -- Calculate BPM from interval between taps
    local interval = now - last_tap
    local bpm = 60.0 / interval

    -- Clamp to sane range
    if bpm < MIN_BPM then bpm = MIN_BPM end
    if bpm > MAX_BPM then bpm = MAX_BPM end

    -- Round to 1 decimal place for cleanliness
    bpm = math.floor(bpm * 10 + 0.5) / 10

    reaper.SetCurrentBPM(0, bpm, true)
    utils.log("Tap tempo: " .. bpm .. " BPM (interval: " .. string.format("%.3f", interval) .. "s)")
else
    utils.log("Tap tempo: first tap registered. Tap again within " .. TAP_TIMEOUT .. "s.")
end

-- Store this tap time for the next invocation
reaper.SetExtState(EXT_SECTION, EXT_KEY, tostring(now), false)

reaper.Undo_EndBlock("Tap Tempo", -1)

reaper.defer(function() end)
