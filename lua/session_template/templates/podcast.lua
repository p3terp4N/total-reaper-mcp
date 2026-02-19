-- templates/podcast.lua — Podcast / Voiceover session template
--
-- Track layout (flat — no folders):
--   Host MV7X       (Tascam Ch 1)  → ReaGate → Comp VCA-65 → FabFilter Pro-Q 4 → de_esser → ReaFIR (bypassed)
--   Guest Condenser (Tascam Ch 4)  → ReaGate → Comp VCA-65 → FabFilter Pro-Q 4 → de_esser → ReaFIR (bypassed)
--   Soundboard/SFX  (no input)     → ReaGain
--   Reference       (no input)     → ReaGain (master send disabled)
--   Podcast Bus                    → Comp VCA-65 → FabFilter Pro-Q 4 → ReaLimit
--
-- Loudness target: -16 LUFS (podcast standard)

local config = require("config")
local tracks = require("tracks")
local fx = require("fx")
local project = require("project")

local podcast = {}

function podcast.build(session_name, bpm, time_sig, key, sample_rate)
    -- Apply project settings
    project.apply({
        name = session_name,
        type_key = "podcast",
        bpm = bpm,
        time_sig = time_sig,
        key = key,
        sample_rate = sample_rate,
    })

    tracks.reset()

    local tc = config.tascam.channels
    local colors = config.colors

    -- ============================
    -- Host MV7X
    -- ============================
    local host = tracks.create({
        name = "Host MV7X",
        color = colors.purple,
        input = tc.mic_mv7x,
        rec_arm = true,
        rec_mon = 1,
    })
    fx.add_named_chain(host, "podcast_mic") -- gate → comp → eq → deesser
    fx.smart_add_from_config(host, "noise_reduce", true) -- ReaFIR (bypassed)

    -- ============================
    -- Guest Condenser
    -- ============================
    local guest = tracks.create({
        name = "Guest Condenser",
        color = colors.purple,
        input = tc.mic_condenser,
        rec_arm = true,
        rec_mon = 1,
    })
    fx.add_named_chain(guest, "podcast_mic") -- gate → comp → eq → deesser
    fx.smart_add_from_config(guest, "noise_reduce", true) -- ReaFIR (bypassed)

    -- ============================
    -- Soundboard / SFX
    -- ============================
    local soundboard = tracks.create({
        name = "Soundboard/SFX",
        color = colors.orange,
    })
    fx.smart_add_from_config(soundboard, "gain")

    -- ============================
    -- Reference
    -- ============================
    local reference = tracks.create({
        name = "Reference",
        color = colors.white,
    })
    fx.smart_add_from_config(reference, "gain")
    tracks.disable_master_send(reference)

    -- ============================
    -- Podcast Bus
    -- ============================
    local podcast_bus = tracks.create_bus({
        name = "Podcast Bus",
        color = colors.gray,
    })
    fx.add_named_chain(podcast_bus, "podcast_bus") -- comp → eq → limit

    -- Send all mic tracks + soundboard to Podcast Bus
    tracks.create_sends_to_bus({ host, guest, soundboard }, podcast_bus, { volume = 1.0 })
end

return podcast
