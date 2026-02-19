-- templates/live_performance.lua — Live Performance session template
--
-- Flat layout:
--   Guitar DI 1    (Ch 2)          → ReaGate
--   Guitar QC L/R  (Ch 7/8 stereo) → (no FX, low latency)
--   RC-600 L/R     (Ch 5/6 stereo) → (no FX)
--   Vocal          (Ch 1)          → ReaGate → ReaEQ (HPF 80Hz) → ReaComp → ReaLimit
--   Backing Tracks (no input)      → ReaGain
--   Click          (no input)      → routed to headphones only
--   QC Automation  (MIDI out, Ch 1, red)
--   Live Capture   (receives all, white, always armed)

local config = require("config")
local tracks = require("tracks")
local fx = require("fx")
local project = require("project")

local live_performance = {}

function live_performance.build(session_name, bpm, time_sig, key, sample_rate)
    project.apply({
        name = session_name,
        type_key = "live",
        bpm = bpm,
        time_sig = time_sig,
        key = key,
        sample_rate = sample_rate,
    })

    tracks.reset()

    local tc = config.tascam.channels
    local colors = config.colors

    -- Guitar DI 1
    local di1 = tracks.create({
        name = "Guitar DI 1",
        color = colors.green,
        input = tc.guitar_di_1,
        rec_arm = true,
        rec_mon = 1,
    })
    fx.smart_add_from_config(di1, "gate")

    -- Guitar QC L/R
    local qc = tracks.create({
        name = "Guitar QC L/R",
        color = colors.green,
        input = tc.qc_l,
        input_stereo = true,
        rec_arm = true,
        rec_mon = 1,
    })

    -- RC-600 L/R
    local rc600 = tracks.create({
        name = "RC-600 L/R",
        color = colors.cyan,
        input = tc.rc600_l,
        input_stereo = true,
        rec_arm = true,
        rec_mon = 1,
    })

    -- Vocal
    local vocal = tracks.create({
        name = "Vocal",
        color = colors.purple,
        input = tc.mic_mv7x,
        rec_arm = true,
        rec_mon = 1,
    })
    fx.add_named_chain(vocal, "live_vocal")

    -- Backing Tracks
    local backing = tracks.create({
        name = "Backing Tracks",
        color = colors.yellow,
    })
    fx.smart_add_from_config(backing, "gain")

    -- Click (routed to headphones only — no master send)
    local click = tracks.create({
        name = "Click",
        color = colors.gray,
    })
    tracks.disable_master_send(click)
    -- Note: Click routing to headphone output requires hardware-specific
    -- channel routing set up after REAPER is running. The track is created
    -- with master send disabled so it won't go to monitors.

    -- QC Automation (MIDI CC/PC track for preset switching)
    local qc_auto = tracks.create({
        name = "QC Automation",
        color = colors.red,
    })

    -- Live Capture (receives from all, always armed)
    local live_capture = tracks.create({
        name = "Live Capture",
        color = colors.white,
        rec_arm = true,
    })
    local audio_tracks = { di1, qc, rc600, vocal, backing }
    tracks.setup_capture_bus(live_capture, audio_tracks)
end

return live_performance
