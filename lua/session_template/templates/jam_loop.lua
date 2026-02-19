-- templates/jam_loop.lua — Jam / Loop session template
--
-- Flat layout for jamming and loop-based recording.
-- Jam Capture track receives pre-fader from all audio tracks, always armed.
--
-- Track layout:
--   Guitar DI 1   (Tascam Ch 2)         → guitar_di chain (bypass first)
--   Guitar QC L/R (Tascam Ch 7/8 stereo)→ eq_surgical
--   RC-600 L/R    (Tascam Ch 5/6 stereo)→ eq_surgical
--   Drum/Beat     (BSP Ch 10)           → Addictive Drums 2
--   Vocal         (Tascam Ch 1)         → comp_vca65
--   Jam Capture   (no input, receives all pre-fader, always armed)

local config = require("config")
local tracks = require("tracks")
local fx = require("fx")
local project = require("project")
local utils = require("utils")

local jam_loop = {}

function jam_loop.build(session_name, bpm, time_sig, key, sample_rate)
    -- Apply project settings
    project.apply({
        name = session_name,
        type_key = "jam",
        bpm = bpm,
        time_sig = time_sig,
        key = key,
        sample_rate = sample_rate,
    })

    tracks.reset()

    local tc = config.tascam.channels
    local colors = config.colors
    local midi = config.midi.devices

    -- Resolve MIDI device index
    local bsp_idx = utils.find_midi_input(midi.beatstep_pro.name)

    -- ============================
    -- Guitar DI 1 (guitar_di chain with bypass first — ReaTune bypassed)
    -- ============================
    local guitar_di1 = tracks.create({
        name = "Guitar DI 1",
        color = colors.green,
        input = tc.guitar_di_1,
        rec_arm = true,
        rec_mon = 1,
    })
    fx.add_named_chain(guitar_di1, "guitar_di", true) -- bypass first (ReaTune)

    -- ============================
    -- Guitar QC L/R (stereo from Quad Cortex)
    -- ============================
    local guitar_qc = tracks.create({
        name = "Guitar QC L/R",
        color = colors.green,
        input = tc.qc_l,
        input_stereo = true,
        rec_arm = true,
        rec_mon = 1,
    })
    fx.smart_add_from_config(guitar_qc, "eq_surgical")

    -- ============================
    -- RC-600 L/R (stereo from Boss RC-600)
    -- ============================
    local rc600 = tracks.create({
        name = "RC-600 L/R",
        color = colors.cyan,
        input = tc.rc600_l,
        input_stereo = true,
        rec_arm = true,
        rec_mon = 1,
    })
    fx.smart_add_from_config(rc600, "eq_surgical")

    -- ============================
    -- Drum/Beat (BeatStep Pro, Ch 10 → Addictive Drums 2)
    -- ============================
    local drum_beat = tracks.create({
        name = "Drum/Beat",
        color = colors.orange,
        midi_device = bsp_idx,
        midi_channel = midi.beatstep_pro.channels.drums,
        rec_arm = true,
        rec_mon = 1,
    })
    fx.smart_add_from_config(drum_beat, "addictive_drums", false)

    -- ============================
    -- Vocal (dynamic mic, light compression)
    -- ============================
    local vocal = tracks.create({
        name = "Vocal",
        color = colors.purple,
        input = tc.mic_mv7x,
        rec_arm = true,
        rec_mon = 1,
    })
    fx.smart_add_from_config(vocal, "comp_vca65")

    -- ============================
    -- Jam Capture (receives pre-fader from all audio tracks, always armed)
    -- ============================
    local jam_capture = tracks.create({
        name = "Jam Capture",
        color = colors.white,
        rec_arm = true,
    })
    tracks.setup_capture_bus(jam_capture, { guitar_di1, guitar_qc, rc600, drum_beat, vocal })
end

return jam_loop
