-- templates/tone_design.lua — Tone Design session template
--
-- Track layout (flat — no folders):
--   Guitar DI 1     (Tascam Ch 2)    → ReaTune (bypassed, visual pitch feedback)
--   Guitar QC L/R   (Tascam Ch 7/8)  → FabFilter Pro-Q 4 (hardware comparison)
--   Tone A — Plini X    (receives DI 1) → Archetype: Plini X
--   Tone B — Petrucci X (receives DI 1) → Archetype: Petrucci X (muted)
--   Tone C — Gojira X   (receives DI 1) → Archetype: Gojira X (muted)
--   Tone D — Mesa IIC+  (receives DI 1) → Mesa Boogie Mark IIC+ Suite (muted)
--
-- DI 1 sends to all 4 tone tracks for A/B/C/D comparison.
-- Only Tone A is unmuted; B/C/D start muted.
-- QC track lets user compare hardware vs software tones.

local config = require("config")
local tracks = require("tracks")
local fx = require("fx")
local project = require("project")

local tone_design = {}

function tone_design.build(session_name, bpm, time_sig, key, sample_rate)
    -- Apply project settings
    project.apply({
        name = session_name,
        type_key = "tone",
        bpm = bpm,
        time_sig = time_sig,
        key = key,
        sample_rate = sample_rate,
    })

    tracks.reset()

    local tc = config.tascam.channels
    local colors = config.colors

    -- ============================
    -- Guitar DI 1 (source for all tone tracks)
    -- ============================
    local di1 = tracks.create({
        name = "Guitar DI 1",
        color = colors.green,
        input = tc.guitar_di_1,
        rec_arm = true,
        rec_mon = 1,
    })
    fx.smart_add_from_config(di1, "tuner", true) -- ReaTune bypassed (visual pitch feedback)

    -- ============================
    -- Guitar QC L/R (hardware comparison)
    -- ============================
    local qc = tracks.create({
        name = "Guitar QC L/R",
        color = colors.green,
        input = tc.qc_l,
        input_stereo = true,
        rec_arm = true,
        rec_mon = 1,
    })
    fx.smart_add_from_config(qc, "eq_surgical")

    -- ============================
    -- Tone A — Plini X (active)
    -- ============================
    local tone_a = tracks.create({
        name = "Tone A - Plini X",
        color = colors.green,
    })
    fx.smart_add_from_config(tone_a, "neural_plini")
    tracks.create_send(di1, tone_a, { volume = 1.0 })

    -- ============================
    -- Tone B — Petrucci X (muted)
    -- ============================
    local tone_b = tracks.create({
        name = "Tone B - Petrucci X",
        color = colors.green,
    })
    fx.smart_add_from_config(tone_b, "neural_petrucci")
    tracks.create_send(di1, tone_b, { volume = 1.0 })
    tracks.set_mute(tone_b, true)

    -- ============================
    -- Tone C — Gojira X (muted)
    -- ============================
    local tone_c = tracks.create({
        name = "Tone C - Gojira X",
        color = colors.green,
    })
    fx.smart_add_from_config(tone_c, "neural_gojira")
    tracks.create_send(di1, tone_c, { volume = 1.0 })
    tracks.set_mute(tone_c, true)

    -- ============================
    -- Tone D — Mesa IIC+ (muted)
    -- ============================
    local tone_d = tracks.create({
        name = "Tone D - Mesa IIC+",
        color = colors.green,
    })
    fx.smart_add_from_config(tone_d, "neural_mesa")
    tracks.create_send(di1, tone_d, { volume = 1.0 })
    tracks.set_mute(tone_d, true)
end

return tone_design
