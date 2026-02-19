-- templates/mixing.lua — Mixing (Import Stems) session template
--
-- Track layout (full folder structure, NO inputs armed):
--   📁 GUITARS       (empty folder — user imports stems)
--   📁 BASS          (empty folder)
--   📁 DRUMS         (empty folder)
--   📁 KEYS          (empty folder)
--   📁 VOCALS        (empty folder)
--   Reference        (no input) → ReaGain (master send disabled)
--   📁 FX RETURNS
--     ├── Reverb Room    → Rev PLATE-140
--     ├── Reverb Hall    → Rev LX-24
--     ├── Delay          → Replika
--     └── Parallel Comp  → Comp FET-76
--   Guitar Bus       → FabFilter Pro-Q 4
--   Bass Bus         → FabFilter Pro-Q 4
--   Drum Bus         → Comp VCA-65 → FabFilter Pro-Q 4
--   Keys Bus         → FabFilter Pro-Q 4
--   Vocal Bus        → Comp VCA-65 → FabFilter Pro-Q 4
--   Mix Bus          → Comp VCA-65 → FabFilter Pro-Q 4 → ReaLimit
--
-- Sidechain: Drum Bus → Bass Bus compressor (bypassed/muted)

local config = require("config")
local tracks = require("tracks")
local fx = require("fx")
local project = require("project")

local mixing = {}

function mixing.build(session_name, bpm, time_sig, key, sample_rate)
    -- Apply project settings
    project.apply({
        name = session_name,
        type_key = "mixing",
        bpm = bpm,
        time_sig = time_sig,
        key = key,
        sample_rate = sample_rate,
    })

    tracks.reset()

    local colors = config.colors

    -- ============================
    -- Empty stem folders (user imports audio into these)
    -- ============================

    -- GUITARS folder
    tracks.create_folder({
        name = "GUITARS",
        color = colors.green,
    })
    tracks.close_folder()

    -- BASS folder
    tracks.create_folder({
        name = "BASS",
        color = colors.blue,
    })
    tracks.close_folder()

    -- DRUMS folder
    tracks.create_folder({
        name = "DRUMS",
        color = colors.orange,
    })
    tracks.close_folder()

    -- KEYS folder
    tracks.create_folder({
        name = "KEYS",
        color = colors.yellow,
    })
    tracks.close_folder()

    -- VOCALS folder
    tracks.create_folder({
        name = "VOCALS",
        color = colors.purple,
    })
    tracks.close_folder()

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
    tracks.create_folder({
        name = "FX RETURNS",
        color = colors.gray,
    })

    local reverb_room = tracks.create({
        name = "Reverb Room",
        color = colors.gray,
        volume_db = -12,  -- FX returns sit well below dry signal
    })
    fx.add_named_chain(reverb_room, "mix_reverb_room")

    local reverb_hall = tracks.create({
        name = "Reverb Hall",
        color = colors.gray,
        volume_db = -12,
    })
    fx.add_named_chain(reverb_hall, "mix_reverb_hall")

    local delay = tracks.create({
        name = "Delay",
        color = colors.gray,
        volume_db = -12,
    })
    fx.add_named_chain(delay, "mix_delay")

    local parallel_comp = tracks.create({
        name = "Parallel Comp",
        color = colors.gray,
        volume_db = -12,
    })
    fx.add_named_chain(parallel_comp, "mix_parallel")

    tracks.close_folder()

    -- ============================
    -- Instrument Buses
    -- ============================
    local guitar_bus = tracks.create_bus({
        name = "Guitar Bus",
        color = colors.gray,
        volume_db = -6,  -- Headroom for multiple guitar stems
    })
    fx.add_named_chain(guitar_bus, "mix_guitar_bus")

    local bass_bus = tracks.create_bus({
        name = "Bass Bus",
        color = colors.gray,
        volume_db = -4,
    })
    fx.add_named_chain(bass_bus, "mix_bass_bus")

    local drum_bus = tracks.create_bus({
        name = "Drum Bus",
        color = colors.gray,
        volume_db = -4,
    })
    fx.add_named_chain(drum_bus, "mix_drum_bus")

    local keys_bus = tracks.create_bus({
        name = "Keys Bus",
        color = colors.gray,
        volume_db = -3,
    })
    fx.add_named_chain(keys_bus, "mix_keys_bus")

    local vocal_bus = tracks.create_bus({
        name = "Vocal Bus",
        color = colors.gray,
        volume_db = -3,
    })
    fx.add_named_chain(vocal_bus, "mix_vocal_bus")

    -- ============================
    -- Mix Bus (master)
    -- ============================
    local mix_bus = tracks.create_bus({
        name = "Mix Bus",
        color = colors.gray,
        volume_db = -6,  -- Headroom for 5 buses summing
    })
    fx.add_named_chain(mix_bus, "mix_master")

    -- ============================
    -- Sidechain: Drum Bus → Bass Bus compressor (bypassed/muted)
    -- ============================
    -- Bass Bus chain is mix_bass_bus = { "eq_surgical" }, comp is index 0
    -- if the chain has a compressor. Since mix_bass_bus only has EQ,
    -- the sidechain targets the first FX slot (index 0) for future use.
    tracks.create_sidechain(drum_bus, bass_bus, 0, { volume = 1.0, mute = true })
end

return mixing
