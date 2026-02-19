-- templates/full_production.lua — Full Production session template
--
-- Track layout:
--   📁 GUITARS
--     ├── Guitar DI 1    (Tascam Ch 2)  → guitar_di chain (ReaTune bypassed)
--     ├── Guitar DI 2    (Tascam Ch 3)  → guitar_di chain (ReaTune bypassed)
--     ├── Guitar QC L/R  (Tascam Ch 7/8 stereo) → guitar_qc chain
--     └── Guitar Neural  (receives DI 1) → Neural DSP (muted)
--   📁 BASS
--     ├── Bass DI        (Tascam Ch 2)  → bass_di chain
--     ├── Bass QC        (Tascam Ch 7/8 stereo) → bass_qc chain
--     └── Bass Parallax  (receives Bass DI) → Parallax X (muted)
--   📁 DRUMS & SEQUENCES
--     ├── Drums-BSP      (BSP Ch 10)    → Addictive Drums 2
--     ├── Seq 1          (BSP Ch 1)     → Analog Lab V
--     └── Seq 2          (BSP Ch 2)     → Massive X
--   📁 KEYS
--     ├── Keys-Nektar    (Nektar Ch 1)  → Analog Lab V
--     └── Nektar Pads    (Nektar Ch 10) → Addictive Drums 2
--   📁 VOCALS
--     ├── Vocal MV7X     (Tascam Ch 1)  → vocal_dynamic chain
--     └── Vocal Condenser(Tascam Ch 4)  → vocal_condenser chain
--   QC Automation        (MIDI out to QC, Ch 1)
--   Reference            (no input, ReaGain, master send disabled)
--   📁 FX RETURNS
--     ├── Reverb Plate   → reverb_plate chain
--     ├── Reverb Hall    → reverb_hall chain
--     ├── Delay          → delay_main chain
--     └── Parallel Comp  → parallel_comp chain
--   Guitar Bus           → guitar_bus chain
--   Bass Bus             → eq_surgical
--   Drum Bus             → comp_vca65 + eq_surgical
--   Keys Bus             → eq_surgical
--   Vocal Bus            → comp_vca65 + eq_surgical
--   Mix Bus              → mix_bus chain (comp_vca65 → eq_surgical → ozone_imager → bus_peak)
--
-- Sidechains (bypassed): kick → bass comp, vocal → guitar comp

local config = require("config")
local tracks = require("tracks")
local fx = require("fx")
local project = require("project")
local utils = require("utils")

local full_production = {}

function full_production.build(session_name, bpm, time_sig, key, sample_rate)
    -- Apply project settings
    project.apply({
        name = session_name,
        type_key = "production",
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
    local qc_midi_idx = utils.find_midi_output(midi.quad_cortex.name)

    -- ============================
    -- GUITARS folder
    -- ============================
    local guitar_folder = tracks.create_folder({
        name = "GUITARS",
        color = colors.green,
    })

    -- Guitar DI 1
    local guitar_di1 = tracks.create({
        name = "Guitar DI 1",
        color = colors.green,
        input = tc.guitar_di_1,
        rec_arm = true,
        rec_mon = 1,
    })
    fx.add_named_chain(guitar_di1, "guitar_di", true) -- bypass ReaTune

    -- Guitar DI 2
    local guitar_di2 = tracks.create({
        name = "Guitar DI 2",
        color = colors.green,
        input = tc.guitar_di_2,
        rec_arm = true,
        rec_mon = 1,
    })
    fx.add_named_chain(guitar_di2, "guitar_di", true)

    -- Guitar QC L/R (stereo)
    local guitar_qc = tracks.create({
        name = "Guitar QC L/R",
        color = colors.green,
        input = tc.qc_l,
        input_stereo = true,
        rec_arm = true,
        rec_mon = 1,
    })
    fx.add_named_chain(guitar_qc, "guitar_qc")

    -- Guitar Neural (receives from DI 1, no direct input)
    local guitar_neural = tracks.create({
        name = "Guitar Neural",
        color = colors.green,
    })
    local neural_plugins = { "neural_petrucci", "neural_plini", "neural_gojira", "neural_mesa" }
    for _, pkey in ipairs(neural_plugins) do
        local name = fx.smart_add_from_config(guitar_neural, pkey, false)
        if name then break end
    end
    tracks.create_send(guitar_di1, guitar_neural, { volume = 1.0 })
    tracks.set_mute(guitar_neural, true)

    tracks.close_folder()

    -- ============================
    -- BASS folder
    -- ============================
    local bass_folder = tracks.create_folder({
        name = "BASS",
        color = colors.blue,
    })

    -- Bass DI (re-uses Guitar DI 1 channel — user patches cable)
    local bass_di = tracks.create({
        name = "Bass DI",
        color = colors.blue,
        input = tc.guitar_di_1,
        rec_arm = false,
        rec_mon = 1,
    })
    fx.add_named_chain(bass_di, "bass_di")

    -- Bass QC (stereo from QC outputs)
    local bass_qc = tracks.create({
        name = "Bass QC",
        color = colors.blue,
        input = tc.qc_l,
        input_stereo = true,
        rec_arm = false,
        rec_mon = 1,
    })
    fx.add_named_chain(bass_qc, "bass_qc")

    -- Bass Parallax (receives from Bass DI, Neural DSP Parallax X)
    local bass_parallax = tracks.create({
        name = "Bass Parallax",
        color = colors.blue,
    })
    fx.smart_add_from_config(bass_parallax, "neural_parallax", false)
    tracks.create_send(bass_di, bass_parallax, { volume = 1.0 })
    tracks.set_mute(bass_parallax, true)

    tracks.close_folder()

    -- ============================
    -- DRUMS & SEQUENCES folder
    -- ============================
    local drums_folder = tracks.create_folder({
        name = "DRUMS & SEQUENCES",
        color = colors.orange,
    })

    -- Drums-BSP (BeatStep Pro, Ch 10 → Addictive Drums 2)
    local drums_bsp = tracks.create({
        name = "Drums-BSP",
        color = colors.orange,
        midi_device = bsp_idx,
        midi_channel = midi.beatstep_pro.channels.drums,
        rec_arm = true,
        rec_mon = 1,
    })
    fx.smart_add_from_config(drums_bsp, "addictive_drums", false)

    -- Seq 1 (BeatStep Pro, Ch 1 → Analog Lab V)
    local seq1 = tracks.create({
        name = "Seq 1",
        color = colors.orange,
        midi_device = bsp_idx,
        midi_channel = midi.beatstep_pro.channels.seq1,
        rec_arm = true,
        rec_mon = 1,
    })
    fx.smart_add_from_config(seq1, "analog_lab", false)

    -- Seq 2 (BeatStep Pro, Ch 2 → Massive X)
    local seq2 = tracks.create({
        name = "Seq 2",
        color = colors.orange,
        midi_device = bsp_idx,
        midi_channel = midi.beatstep_pro.channels.seq2,
        rec_arm = true,
        rec_mon = 1,
    })
    fx.smart_add_from_config(seq2, "massive_x", false)

    tracks.close_folder()

    -- ============================
    -- KEYS folder
    -- ============================
    local keys_folder = tracks.create_folder({
        name = "KEYS",
        color = colors.yellow,
    })

    -- Keys-Nektar (Impact LX61+, Ch 1 → Analog Lab V)
    local keys_nektar = tracks.create({
        name = "Keys-Nektar",
        color = colors.yellow,
        midi_device = nektar_idx,
        midi_channel = midi.nektar.channels.keys,
        rec_arm = true,
        rec_mon = 1,
    })
    fx.smart_add_from_config(keys_nektar, "analog_lab", false)

    -- Nektar Pads (Impact LX61+, Ch 10 → Addictive Drums 2)
    local nektar_pads = tracks.create({
        name = "Nektar Pads",
        color = colors.yellow,
        midi_device = nektar_idx,
        midi_channel = midi.nektar.channels.pads,
        rec_arm = true,
        rec_mon = 1,
    })
    fx.smart_add_from_config(nektar_pads, "addictive_drums", false)

    tracks.close_folder()

    -- ============================
    -- VOCALS folder
    -- ============================
    local vocals_folder = tracks.create_folder({
        name = "VOCALS",
        color = colors.purple,
    })

    -- Vocal MV7X (Tascam Ch 1 — Shure MV7X dynamic mic)
    local vocal_mv7x = tracks.create({
        name = "Vocal MV7X",
        color = colors.purple,
        input = tc.mic_mv7x,
        rec_arm = true,
        rec_mon = 1,
    })
    fx.add_named_chain(vocal_mv7x, "vocal_dynamic")

    -- Vocal Condenser (Tascam Ch 4 — condenser mic)
    local vocal_condenser = tracks.create({
        name = "Vocal Condenser",
        color = colors.purple,
        input = tc.mic_condenser,
        rec_arm = false,
        rec_mon = 1,
    })
    fx.add_named_chain(vocal_condenser, "vocal_condenser")

    tracks.close_folder()

    -- ============================
    -- QC Automation (MIDI output to Quad Cortex)
    -- ============================
    local qc_auto = tracks.create({
        name = "QC Automation",
        color = colors.red,
        midi_device = qc_midi_idx,
        midi_channel = midi.quad_cortex.channels.main,
    })

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
    -- FX RETURNS folder
    -- ============================
    local fx_folder = tracks.create_folder({
        name = "FX RETURNS",
        color = colors.gray,
    })

    local reverb_plate = tracks.create_bus({
        name = "Reverb Plate",
        color = colors.gray,
        volume_db = -12,  -- FX returns sit well below dry signal
    })
    fx.add_named_chain(reverb_plate, "reverb_plate")

    local reverb_hall = tracks.create_bus({
        name = "Reverb Hall",
        color = colors.gray,
        volume_db = -12,
    })
    fx.add_named_chain(reverb_hall, "reverb_hall")

    local delay = tracks.create_bus({
        name = "Delay",
        color = colors.gray,
        volume_db = -12,
    })
    fx.add_named_chain(delay, "delay_main")

    local parallel_comp = tracks.create_bus({
        name = "Parallel Comp",
        color = colors.gray,
        volume_db = -12,
    })
    fx.add_named_chain(parallel_comp, "parallel_comp")

    tracks.close_folder()

    -- ============================
    -- Buses
    -- ============================

    -- Guitar Bus (4 guitar tracks summing)
    local guitar_bus = tracks.create_bus({
        name = "Guitar Bus",
        color = colors.gray,
        volume_db = -6,
    })
    fx.add_named_chain(guitar_bus, "guitar_bus")

    -- Bass Bus (3 bass tracks summing)
    local bass_bus = tracks.create_bus({
        name = "Bass Bus",
        color = colors.gray,
        volume_db = -4,
    })
    fx.smart_add_from_config(bass_bus, "eq_surgical")

    -- Drum Bus (3 tracks summing)
    local drum_bus = tracks.create_bus({
        name = "Drum Bus",
        color = colors.gray,
        volume_db = -4,
    })
    fx.smart_add_from_config(drum_bus, "comp_vca65")
    fx.smart_add_from_config(drum_bus, "eq_surgical")

    -- Keys Bus (2 tracks summing)
    local keys_bus = tracks.create_bus({
        name = "Keys Bus",
        color = colors.gray,
        volume_db = -3,
    })
    fx.smart_add_from_config(keys_bus, "eq_surgical")

    -- Vocal Bus (2 tracks summing)
    local vocal_bus = tracks.create_bus({
        name = "Vocal Bus",
        color = colors.gray,
        volume_db = -3,
    })
    fx.smart_add_from_config(vocal_bus, "comp_vca65")
    fx.smart_add_from_config(vocal_bus, "eq_surgical")

    -- Mix Bus (5 buses summing)
    local mix_bus = tracks.create_bus({
        name = "Mix Bus",
        color = colors.gray,
        volume_db = -6,
    })
    fx.add_named_chain(mix_bus, "mix_bus")

    -- ============================
    -- Bus routing — source tracks to their buses
    -- ============================
    tracks.create_sends_to_bus({ guitar_di1, guitar_di2, guitar_qc, guitar_neural }, guitar_bus, { volume = 1.0 })
    tracks.create_sends_to_bus({ bass_di, bass_qc, bass_parallax }, bass_bus, { volume = 1.0 })
    tracks.create_sends_to_bus({ drums_bsp, seq1, seq2 }, drum_bus, { volume = 1.0 })
    tracks.create_sends_to_bus({ keys_nektar, nektar_pads }, keys_bus, { volume = 1.0 })
    tracks.create_sends_to_bus({ vocal_mv7x, vocal_condenser }, vocal_bus, { volume = 1.0 })

    -- All buses feed into Mix Bus
    tracks.create_sends_to_bus({ guitar_bus, bass_bus, drum_bus, keys_bus, vocal_bus }, mix_bus, { volume = 1.0 })

    -- ============================
    -- FX sends — all audio tracks to FX returns (muted)
    -- ============================
    local all_audio = {
        guitar_di1, guitar_di2, guitar_qc, guitar_neural,
        bass_di, bass_qc, bass_parallax,
        drums_bsp, seq1, seq2,
        keys_nektar, nektar_pads,
        vocal_mv7x, vocal_condenser,
    }
    local fx_returns = { reverb_plate, reverb_hall, delay, parallel_comp }

    for _, fx_ret in ipairs(fx_returns) do
        tracks.create_sends_to_bus(all_audio, fx_ret, { volume = 0, mute = true })
    end

    -- ============================
    -- Sidechains (bypassed / muted for pre-wiring)
    -- ============================

    -- Kick (drums_bsp) → Bass Bus compressor sidechain (comp_vca65 is first FX on bass_bus)
    -- Bass Bus has eq_surgical at index 0, so comp is not present here — use bass_di comp instead
    -- Actually bass_di chain is { comp_tube_sta, eq_surgical } — comp at idx 0
    tracks.create_sidechain(drums_bsp, bass_di, 0, { volume = 1.0, mute = true })

    -- Vocal → Guitar Bus compressor sidechain (guitar_bus chain: eq_sitral=0, comp_vca65=1)
    tracks.create_sidechain(vocal_mv7x, guitar_bus, 1, { volume = 1.0, mute = true })
end

return full_production
