-- lib/config.lua — Hardware/MIDI/FX constants (source of truth)
-- All session template modules read from this config.
-- Python side mirrors this in server/session_config.py (static fallback).
-- Exposed to MCP via GetSessionConfig bridge function.

local config = {}

-- ============================================================================
-- Tascam Model 12 Channel Map
-- ============================================================================
-- Values are 1-based REAPER hardware input indices.
-- Tascam USB sends channels as stereo pairs: 1/2, 3/4, 5/6, 7/8, 9/10.
-- Mono channels map to individual inputs within pairs.

config.tascam = {
    channels = {
        mic_mv7x       = 1,   -- Ch 1: Shure MV7X (dynamic, vocal/podcast)
        guitar_di_1    = 2,   -- Ch 2: Guitar DI 1 (clean, via AUX1 → QC In 1)
        guitar_di_2    = 3,   -- Ch 3: Guitar DI 2 (clean, via AUX2 → QC In 2)
        mic_condenser  = 4,   -- Ch 4: Available (NT1-A or Beta 58A, 48V phantom)
        rc600_l        = 5,   -- Ch 5: Boss RC-600 Left
        rc600_r        = 6,   -- Ch 6: Boss RC-600 Right
        qc_l           = 7,   -- Ch 7: Quad Cortex Left (XLR out → TRS)
        qc_r           = 8,   -- Ch 8: Quad Cortex Right
        daw_return_l   = 9,   -- Ch 9: macOS audio return (monitoring only)
        daw_return_r   = 10,  -- Ch 10: macOS audio return
    },
    sample_rates = { 44100, 48000 },
    bit_depth = 24,
    -- AUX routing (hardware-level, documented for reference)
    aux = {
        aux1 = "QC Input 1 (default: Tascam Ch 2 / Guitar DI 1)",
        aux2 = "QC Input 2 (default: Tascam Ch 3 / Guitar DI 2)",
    },
}

-- ============================================================================
-- MIDI Devices
-- ============================================================================

config.midi = {
    devices = {
        beatstep_pro = {
            name = "Arturia BeatStep Pro",
            channels = {
                seq1 = 1,        -- Melodic → synth VSTi
                seq2 = 2,        -- Melodic → bass/synth VSTi
                controller = 3,  -- Encoders → mixer, pads → triggers
                drums = 10,      -- Drum seq → drum VSTi
            },
        },
        nektar = {
            name = "Impact LX61+",
            channels = {
                keys = 1,   -- Keys → instrument VSTi
                pads = 10,  -- Pads → drum triggers
            },
        },
        quad_cortex = {
            name = "Quad Cortex",
            channels = {
                main = 1,  -- PC for preset switching, CC for block control
            },
        },
        rc600 = {
            name = "RC-600",
            channels = {
                main = 4,  -- Unique channel, avoids Ch 1 conflict
            },
        },
    },
    -- REAPER is master clock; send to these devices
    clock_destinations = { "Arturia BeatStep Pro", "Quad Cortex", "RC-600" },
    transport_destinations = { "Arturia BeatStep Pro", "RC-600" },
    retrospective_recording = true,
}

-- ============================================================================
-- RC-600 Footswitch → REAPER Action Mapping
-- ============================================================================

config.rc600 = {
    -- Pedal Mode 1: Jam
    jam = {
        { switch = "REC/PLAY 1", cc = 20, press = "toggle_record",       hold = nil },
        { switch = "REC/PLAY 2", cc = 21, press = "idea_marker",         hold = "bounce_selection" },
        { switch = "REC/PLAY 3", cc = 22, press = "arm_next_track",      hold = "arm_all_di" },
        { switch = "STOP 1",     cc = 23, press = "stop",                hold = "undo_last_recording" },
        { switch = "STOP 2",     cc = 24, press = "toggle_metronome",    hold = "click_headphones_only" },
        { switch = "STOP 3",     cc = 25, press = "toggle_loop",         hold = "clear_loop_region" },
        { switch = "TRACK SEL",  cc = 26, press = "cycle_armed_tracks",  hold = nil },
        { switch = "UNDO/REDO",  cc = 27, press = "undo",                hold = "redo" },
        { switch = "ALL START",  cc = 28, press = "play_pause",          hold = "stop_return_start" },
    },
    -- Pedal Mode 3: Live
    live = {
        { switch = "REC/PLAY 1", cc = 30, press = "next_song_marker",    hold = "prev_song_marker" },
        { switch = "REC/PLAY 2", cc = 31, press = "toggle_backing_mute", hold = nil },
        { switch = "REC/PLAY 3", cc = 32, press = "toggle_live_capture", hold = nil },
        { switch = "STOP 1",     cc = 33, press = "stop",                hold = "stop_return_start" },
        { switch = "STOP 2",     cc = 34, press = "qc_preset_next",      hold = "qc_preset_prev" },
        { switch = "STOP 3",     cc = 35, press = "toggle_loop",         hold = "clear_loop_region" },
        { switch = "TRACK SEL",  cc = 36, press = "setlist_marker",      hold = nil },
        { switch = "UNDO/REDO",  cc = 37, press = "undo",                hold = "redo" },
        { switch = "ALL START",  cc = 38, press = "play_pause",          hold = "stop_return_start" },
    },
}

-- ============================================================================
-- BSP Encoder Mapping
-- ============================================================================

config.bsp_encoders = {
    -- Encoders 1-8: track volumes (first 8 visible tracks)
    -- Encoders 9-12: FX return levels (reverb plate, reverb hall, delay, parallel comp)
    -- Encoder 13: master volume
    -- Encoder 14: metronome volume
    -- Encoders 15-16: selected track EQ (hi shelf / lo shelf)
    track_volume_range = { 1, 8 },
    fx_return_range = { 9, 12 },
    master_volume = 13,
    metronome_volume = 14,
    eq_range = { 15, 16 },
}

-- ============================================================================
-- Colors (REAPER native format: OS-dependent, R|G|B|0x01000000)
-- ============================================================================
-- Use utils.rgb() to convert — these are just the RGB values.

config.colors = {
    green   = { 76, 175, 80 },   -- Guitar tracks
    blue    = { 33, 150, 243 },  -- Bass tracks
    orange  = { 255, 152, 0 },   -- Drum/sequence tracks
    yellow  = { 255, 235, 59 },  -- Keys tracks
    purple  = { 156, 39, 176 },  -- Vocal tracks
    cyan    = { 0, 188, 212 },   -- RC-600 / loop tracks
    red     = { 244, 67, 54 },   -- Automation tracks
    white   = { 245, 245, 245 }, -- Reference / capture tracks
    gray    = { 158, 158, 158 }, -- Buses / FX returns
    -- Song structure marker colors
    markers = {
        intro  = { 144, 202, 249 }, -- Light blue
        verse  = { 76, 175, 80 },   -- Green
        chorus = { 244, 67, 54 },   -- Red
        bridge = { 255, 235, 59 },  -- Yellow
        solo   = { 255, 152, 0 },   -- Orange
        outro  = { 156, 39, 176 },  -- Purple
    },
    -- Chord marker colors
    chords = {
        major      = { 33, 150, 243 },  -- Blue
        minor      = { 76, 175, 80 },   -- Green
        dominant   = { 255, 152, 0 },   -- Orange
        diminished = { 244, 67, 54 },   -- Red
    },
}

-- ============================================================================
-- Plugins — Preferred / Fallback pairs
-- ============================================================================
-- { preferred = "Exact Plugin Name", fallback = "REAPER Built-in" }
-- Plugin names must match what TrackFX_AddByName expects.

config.plugins = {
    -- EQ
    eq_surgical     = { preferred = "FabFilter Pro-Q 4", fallback = "ReaEQ" },
    eq_sitral       = { preferred = "EQ SITRAL-295", fallback = "ReaEQ" },

    -- Compressors
    comp_fet76      = { preferred = "Comp FET-76", fallback = "ReaComp" },
    comp_vca65      = { preferred = "Comp VCA-65", fallback = "ReaComp" },
    comp_tube_sta   = { preferred = "Comp TUBE-STA", fallback = "ReaComp" },
    comp_diode609   = { preferred = "Comp DIODE-609", fallback = "ReaComp" },

    -- Reverbs
    rev_plate140    = { preferred = "Rev PLATE-140", fallback = "ReaVerbate" },
    rev_lx24        = { preferred = "Rev LX-24", fallback = "ReaVerbate" },
    rev_vintage     = { preferred = "ValhallaVintageVerb", fallback = "ReaVerbate" },
    rev_supermassive = { preferred = "Valhalla Supermassive", fallback = "ReaVerbate" },

    -- Delays
    delay_replika   = { preferred = "Replika", fallback = "ReaDelay" },
    delay_tape201   = { preferred = "Delay TAPE-201", fallback = "ReaDelay" },

    -- Preamps / Channel strips
    pre_1973        = { preferred = "Pre 1973", fallback = nil },
    pre_v76         = { preferred = "Pre V76", fallback = nil },
    pre_trida       = { preferred = "Pre TridA", fallback = nil },

    -- Guitar amp sims (Neural DSP)
    neural_gojira   = { preferred = "Archetype: Gojira X", fallback = nil },
    neural_petrucci = { preferred = "Archetype: Petrucci X", fallback = nil },
    neural_plini    = { preferred = "Archetype: Plini X", fallback = nil },
    neural_mesa     = { preferred = "Mesa Boogie Mark IIC+ Suite", fallback = nil },
    neural_mantra   = { preferred = "Mantra", fallback = nil },
    neural_parallax = { preferred = "Parallax X", fallback = nil },

    -- Instruments
    analog_lab      = { preferred = "Analog Lab V", fallback = "ReaSynth" },
    massive_x       = { preferred = "Massive X", fallback = "ReaSynth" },
    kontakt         = { preferred = "Kontakt 8", fallback = nil },
    addictive_drums = { preferred = "Addictive Drums 2", fallback = nil },

    -- Mastering / Bus
    ozone_imager    = { preferred = "Ozone Imager 2", fallback = nil },
    bus_peak        = { preferred = "Bus PEAK", fallback = "ReaLimit" },
    bus_force       = { preferred = "Bus FORCE", fallback = nil },

    -- Monitoring
    soundid         = { preferred = "SoundID Reference", fallback = nil },

    -- Utility
    tuner           = { preferred = "ReaTune", fallback = nil },
    gate            = { preferred = "ReaGate", fallback = nil },
    gain            = { preferred = "ReaGain", fallback = nil },
    limit           = { preferred = "ReaLimit", fallback = nil },
    deesser         = { preferred = "JS: de_esser", fallback = nil },
    noise_reduce    = { preferred = "ReaFIR", fallback = nil },

    -- Arturia FX misc
    chorus_dim_d    = { preferred = "Chorus DIMENSION-D", fallback = nil },
    dist_coldfire   = { preferred = "Dist COLDFIRE", fallback = nil },
    tape_j37        = { preferred = "Tape J-37", fallback = nil },
    space_mod       = { preferred = "Valhalla SpaceModulator", fallback = nil },
    freq_echo       = { preferred = "Valhalla FreqEcho", fallback = nil },
}

-- ============================================================================
-- FX Chains — Named chains used by templates
-- ============================================================================
-- Each chain is an ordered list of plugin keys from config.plugins.

config.fx_chains = {
    -- Guitar Recording
    guitar_di       = { "tuner", "gate" },                  -- ReaTune (bypassed) → ReaGate
    guitar_qc       = { "eq_surgical" },                    -- FabFilter Pro-Q 4
    guitar_bus      = { "eq_sitral", "comp_vca65" },        -- EQ SITRAL-295 → Comp VCA-65

    -- FX Returns
    reverb_plate    = { "rev_plate140" },
    reverb_hall     = { "rev_lx24" },
    delay_main      = { "delay_replika" },
    parallel_comp   = { "comp_fet76" },

    -- Bass
    bass_di         = { "comp_tube_sta", "eq_surgical" },
    bass_qc         = { "eq_surgical" },

    -- Vocals
    vocal_dynamic   = { "gate", "pre_1973", "neural_mantra" },
    vocal_condenser = { "gate", "pre_v76", "comp_fet76", "eq_surgical" },
    podcast_mic     = { "gate", "comp_vca65", "eq_surgical", "deesser" },       -- Replaced ReaComp→ReaEQ

    -- Mix Bus
    mix_bus         = { "comp_vca65", "eq_surgical", "ozone_imager", "bus_peak" },

    -- Podcast Bus
    podcast_bus     = { "comp_vca65", "eq_surgical", "limit" },

    -- Mixing defaults (all REAPER built-in for generic stem mixing)
    mix_guitar_bus  = { "eq_surgical" },
    mix_bass_bus    = { "eq_surgical" },
    mix_drum_bus    = { "comp_vca65", "eq_surgical" },
    mix_keys_bus    = { "eq_surgical" },
    mix_vocal_bus   = { "comp_vca65", "eq_surgical" },
    mix_reverb_room = { "rev_plate140" },
    mix_reverb_hall = { "rev_lx24" },
    mix_delay       = { "delay_replika" },
    mix_parallel    = { "comp_fet76" },
    mix_master      = { "comp_vca65", "eq_surgical", "limit" },

    -- Live vocal
    live_vocal      = { "gate", "eq_surgical", "comp_vca65", "limit" },
}

-- ============================================================================
-- Session Types
-- ============================================================================

config.session_types = {
    guitar = {
        name = "Guitar Recording",
        description = "DI + QC + Neural DSP, FX returns, guitar bus",
        grid = 0.25,      -- 1/4 note
        snap = true,
        use_folders = true,
        screenset = "recording",
    },
    production = {
        name = "Full Production",
        description = "All instruments, vocals, full bus routing, mix bus",
        grid = 0.0625,    -- 1/16 note
        snap = true,
        use_folders = true,
        screenset = "recording",
    },
    songwriting = {
        name = "Songwriting / Sketch",
        description = "Minimal setup for quick ideas",
        grid = nil,        -- Off
        snap = false,
        use_folders = false,
        screenset = "recording",
    },
    jam = {
        name = "Jam / Loop",
        description = "RC-600 integration, loop capture, minimal FX",
        grid = 0.25,
        snap = true,
        use_folders = false,
        screenset = "recording",
    },
    podcast = {
        name = "Podcast / Voiceover",
        description = "Mic tracks with processing chain, loudness targeting",
        grid = nil,
        snap = false,
        use_folders = false,
        screenset = "recording",
    },
    mixing = {
        name = "Mixing (Import Stems)",
        description = "Empty folders with buses and FX returns, no inputs",
        grid = 0.25,
        snap = true,
        use_folders = true,
        screenset = "mixing",
    },
    tone = {
        name = "Tone Design",
        description = "DI → 4 Neural DSP amps for A/B comparison",
        grid = nil,
        snap = false,
        use_folders = false,
        screenset = "recording",
    },
    live = {
        name = "Live Performance",
        description = "Backing tracks, click, QC automation, live capture",
        grid = 0.25,
        snap = true,
        use_folders = false,
        screenset = "recording",
    },
    transcription = {
        name = "Transcription / Learning",
        description = "Source audio + playback rate control + practice tools",
        grid = nil,
        snap = false,
        use_folders = false,
        screenset = "recording",
    },
}

-- ============================================================================
-- Render Presets
-- ============================================================================

config.render = {
    master      = { format = "WAV", bits = 24, rate = 48000, dither = false, label = "Master" },
    master_cd   = { format = "WAV", bits = 16, rate = 44100, dither = true,  label = "Master CD" },
    mp3_preview = { format = "MP3", kbps = 320, label = "MP3 Preview" },
    stems       = { format = "WAV", bits = 24, rate = 48000, dither = false, label = "Stems", per_bus = true },
    di_only     = { format = "WAV", bits = 24, rate = 48000, dither = false, label = "DI Only" },
    podcast     = { format = "MP3", kbps = 192, mono = true, label = "Podcast" },
    podcast_hq  = { format = "WAV", bits = 24, rate = 48000, mono = true, label = "Podcast HQ" },
}

-- ============================================================================
-- Loudness Targets (LUFS)
-- ============================================================================

config.loudness = {
    spotify     = -14,
    apple_music = -16,
    youtube     = -14,
    cd_loud     = -9,
    podcast     = -16,
}

-- ============================================================================
-- Recording Defaults
-- ============================================================================

config.recording = {
    format = "WAV",
    bits = 24,
    rate = 48000,
    auto_save_minutes = 5,
    pre_roll_bars = 1,
    punch_pre_roll_bars = 2,
    punch_post_roll_bars = 1,
    path = "~/Music/REAPER Sessions/",
}

-- ============================================================================
-- Screensets
-- ============================================================================

config.screensets = {
    recording = { key = "F1", description = "Large timeline, track meters, transport bar" },
    mixing    = { key = "F2", description = "Mixer view, FX chains, metering" },
    editing   = { key = "F3", description = "Zoomed waveform, MIDI piano roll" },
}

-- ============================================================================
-- Monitoring
-- ============================================================================

config.monitoring = {
    soundid_profile = "DT 770 Pro 80 Ohm",
    -- Monitor FX chain order
    chain = { "soundid", "tuner", "eq_surgical" },  -- SoundID → Loudness Meter → Spectrum
    -- JS: Loudness Meter for LUFS metering (REAPER built-in JS)
    loudness_meter = "JS: Loudness Meter Peak/RMS/LUFS (Cockos)",
}

return config
