-- templates/songwriting.lua — Songwriting / Sketch session template
--
-- Minimal flat layout for quick ideas — no folders, no buses.
--
-- Track layout:
--   Guitar DI     (Tascam Ch 2)         → ReaTune (bypassed)
--   Guitar QC     (Tascam Ch 7/8 stereo)→ eq_surgical
--   Vocal         (Tascam Ch 1)         → comp_vca65
--   Keys          (Nektar Ch 1)         → Analog Lab V / ReaSynth
--   Loop/Beat     (BSP Ch 10)           → Addictive Drums 2
--   Reverb        (bus)                 → rev_vintage (ValhallaVintageVerb / ReaVerbate)
--   Reference     (no input)            → ReaGain, master send disabled
--
-- All tracks send to Reverb (muted).

local config = require("config")
local tracks = require("tracks")
local fx = require("fx")
local project = require("project")
local utils = require("utils")

local songwriting = {}

function songwriting.build(session_name, bpm, time_sig, key, sample_rate)
    -- Apply project settings
    project.apply({
        name = session_name,
        type_key = "songwriting",
        bpm = bpm,
        time_sig = time_sig,
        key = key,
        sample_rate = sample_rate,
    })

    tracks.reset()

    local tc = config.tascam.channels
    local colors = config.colors
    local midi = config.midi.devices

    -- Resolve MIDI device indices
    local bsp_idx = utils.find_midi_input(midi.beatstep_pro.name)
    local nektar_idx = utils.find_midi_input(midi.nektar.name)

    -- ============================
    -- Guitar DI (ReaTune bypassed for quick tuning check)
    -- ============================
    local guitar_di = tracks.create({
        name = "Guitar DI",
        color = colors.green,
        input = tc.guitar_di_1,
        rec_arm = true,
        rec_mon = 1,
    })
    fx.smart_add_from_config(guitar_di, "tuner", true) -- ReaTune bypassed

    -- ============================
    -- Guitar QC (stereo from Quad Cortex)
    -- ============================
    local guitar_qc = tracks.create({
        name = "Guitar QC",
        color = colors.green,
        input = tc.qc_l,
        input_stereo = true,
        rec_arm = true,
        rec_mon = 1,
    })
    fx.smart_add_from_config(guitar_qc, "eq_surgical")

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
    -- Keys (Nektar Impact LX61+, Ch 1 → Analog Lab V / ReaSynth)
    -- ============================
    local keys = tracks.create({
        name = "Keys",
        color = colors.yellow,
        midi_device = nektar_idx,
        midi_channel = midi.nektar.channels.keys,
        rec_arm = true,
        rec_mon = 1,
    })
    fx.smart_add_from_config(keys, "analog_lab", false)

    -- ============================
    -- Loop/Beat (BeatStep Pro, Ch 10 → Addictive Drums 2)
    -- ============================
    local loop_beat = tracks.create({
        name = "Loop/Beat",
        color = colors.orange,
        midi_device = bsp_idx,
        midi_channel = midi.beatstep_pro.channels.drums,
        rec_arm = true,
        rec_mon = 1,
    })
    fx.smart_add_from_config(loop_beat, "addictive_drums", false)

    -- ============================
    -- Reverb (ValhallaVintageVerb / ReaVerbate)
    -- ============================
    local reverb = tracks.create_bus({
        name = "Reverb",
        color = colors.gray,
    })
    fx.smart_add_from_config(reverb, "rev_vintage")

    -- ============================
    -- Reference track
    -- ============================
    local reference = tracks.create({
        name = "Reference",
        color = colors.white,
    })
    fx.smart_add_from_config(reference, "gain")
    tracks.disable_master_send(reference)

    -- ============================
    -- FX sends — all tracks to reverb (muted)
    -- ============================
    local all_audio = { guitar_di, guitar_qc, vocal, keys, loop_beat }
    tracks.create_sends_to_bus(all_audio, reverb, { volume = 0, mute = true })
end

return songwriting
