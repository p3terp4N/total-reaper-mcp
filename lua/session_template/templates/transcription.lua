-- templates/transcription.lua — Transcription / Learning session template
--
-- Flat layout:
--   Source Audio   (no input, white)  → ReaGain (level control)
--   Guitar DI 1   (Ch 2, green)      → ReaTune (enabled for visual pitch)
--   Guitar QC L/R (Ch 7/8, green)    → (no FX)
--   Your Take     (receives DI 1)    → ReaEQ

local config = require("config")
local tracks = require("tracks")
local fx = require("fx")
local project = require("project")

local transcription = {}

function transcription.build(session_name, bpm, time_sig, key, sample_rate)
    project.apply({
        name = session_name,
        type_key = "transcription",
        bpm = bpm,
        time_sig = time_sig,
        key = key,
        sample_rate = sample_rate,
    })

    tracks.reset()

    local tc = config.tascam.channels
    local colors = config.colors

    -- Source Audio (user imports a song here)
    local source = tracks.create({
        name = "Source Audio",
        color = colors.white,
    })
    fx.smart_add_from_config(source, "gain")

    -- Guitar DI 1 (with ReaTune ENABLED for visual pitch feedback)
    local di1 = tracks.create({
        name = "Guitar DI 1",
        color = colors.green,
        input = tc.guitar_di_1,
        rec_arm = true,
        rec_mon = 1,
    })
    fx.smart_add_from_config(di1, "tuner", false) -- NOT bypassed — visual feedback

    -- Guitar QC L/R
    local qc = tracks.create({
        name = "Guitar QC L/R",
        color = colors.green,
        input = tc.qc_l,
        input_stereo = true,
        rec_arm = true,
        rec_mon = 1,
    })

    -- Your Take (receives from DI 1, for comparing against source)
    local your_take = tracks.create({
        name = "Your Take",
        color = colors.green,
    })
    fx.smart_add_from_config(your_take, "eq_surgical")
    tracks.create_send(di1, your_take, { volume = 1.0 })
end

return transcription
