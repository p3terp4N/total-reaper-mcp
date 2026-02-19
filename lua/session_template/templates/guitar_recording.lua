-- templates/guitar_recording.lua — Guitar Recording session template
--
-- Track layout (from design doc):
--   📁 GUITARS
--     ├── Guitar DI 1    (Tascam Ch 2)  → ReaTune (bypassed) → ReaGate
--     ├── Guitar DI 2    (Tascam Ch 3)  → ReaTune (bypassed) → ReaGate
--     ├── Guitar QC L/R  (Tascam Ch 7/8) → FabFilter Pro-Q 4
--     └── Guitar Neural  (receives DI 1) → Neural DSP (inactive)
--   Reference           (no input)       → ReaGain
--   Guitar Bus                           → EQ SITRAL-295 → Comp VCA-65
--   Reverb Plate                         → Rev PLATE-140
--   Reverb Hall                          → Rev LX-24
--   Delay                                → Replika
--   Parallel Comp                        → Comp FET-76

local config = require("config")
local tracks = require("tracks")
local fx = require("fx")
local project = require("project")

local guitar_recording = {}

function guitar_recording.build(session_name, bpm, time_sig, key, sample_rate)
    -- Apply project settings
    project.apply({
        name = session_name,
        type_key = "guitar",
        bpm = bpm,
        time_sig = time_sig,
        key = key,
        sample_rate = sample_rate,
    })

    tracks.reset()

    local tc = config.tascam.channels
    local colors = config.colors

    -- ============================
    -- GUITARS folder
    -- ============================
    local folder = tracks.create_folder({
        name = "GUITARS",
        color = colors.green,
    })

    -- Guitar DI 1
    local di1 = tracks.create({
        name = "Guitar DI 1",
        color = colors.green,
        input = tc.guitar_di_1,
        rec_arm = true,
        rec_mon = 1,
    })
    fx.add_named_chain(di1, "guitar_di", true) -- bypass first (ReaTune)

    -- Guitar DI 2
    local di2 = tracks.create({
        name = "Guitar DI 2",
        color = colors.green,
        input = tc.guitar_di_2,
        rec_arm = true,
        rec_mon = 1,
    })
    fx.add_named_chain(di2, "guitar_di", true)

    -- Guitar QC L/R (stereo)
    local qc = tracks.create({
        name = "Guitar QC L/R",
        color = colors.green,
        input = tc.qc_l,
        input_stereo = true,
        rec_arm = true,
        rec_mon = 1,
    })
    fx.add_named_chain(qc, "guitar_qc")

    -- Guitar Neural (receives from DI 1, no direct input)
    local neural = tracks.create({
        name = "Guitar Neural",
        color = colors.green,
    })
    -- Add first available Neural DSP plugin
    local neural_plugins = { "neural_petrucci", "neural_plini", "neural_gojira", "neural_mesa" }
    for _, key in ipairs(neural_plugins) do
        local name = fx.smart_add_from_config(neural, key, false)
        if name then break end
    end
    -- Receive from DI 1
    tracks.create_send(di1, neural, { volume = 1.0 })
    tracks.set_mute(neural, true) -- Start muted (activate when needed)

    -- Close GUITARS folder
    tracks.close_folder()

    -- ============================
    -- Reference track
    -- ============================
    local reference = tracks.create({
        name = "Reference",
        color = colors.white,
    })
    fx.smart_add_from_config(reference, "gain")
    tracks.disable_master_send(reference) -- Excluded from master bus

    -- ============================
    -- Guitar Bus
    -- ============================
    local guitar_bus = tracks.create_bus({
        name = "Guitar Bus",
        color = colors.gray,
    })
    fx.add_named_chain(guitar_bus, "guitar_bus")

    -- Send all guitar tracks to bus
    tracks.create_sends_to_bus({ di1, di2, qc, neural }, guitar_bus, { volume = 1.0 })

    -- ============================
    -- FX Returns
    -- ============================
    local reverb_plate = tracks.create_bus({
        name = "Reverb Plate",
        color = colors.gray,
    })
    fx.add_named_chain(reverb_plate, "reverb_plate")

    local reverb_hall = tracks.create_bus({
        name = "Reverb Hall",
        color = colors.gray,
    })
    fx.add_named_chain(reverb_hall, "reverb_hall")

    local delay = tracks.create_bus({
        name = "Delay",
        color = colors.gray,
    })
    fx.add_named_chain(delay, "delay_main")

    local parallel_comp = tracks.create_bus({
        name = "Parallel Comp",
        color = colors.gray,
    })
    fx.add_named_chain(parallel_comp, "parallel_comp")

    -- Send from guitar bus to all FX returns (muted by default)
    local fx_returns = { reverb_plate, reverb_hall, delay, parallel_comp }
    tracks.create_sends_to_bus({ guitar_bus }, reverb_plate, { volume = 0, mute = true })
    tracks.create_sends_to_bus({ guitar_bus }, reverb_hall, { volume = 0, mute = true })
    tracks.create_sends_to_bus({ guitar_bus }, delay, { volume = 0, mute = true })
    tracks.create_sends_to_bus({ guitar_bus }, parallel_comp, { volume = 0, mute = true })
end

return guitar_recording
