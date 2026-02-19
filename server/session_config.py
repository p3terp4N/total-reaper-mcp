"""
Session Template Configuration — Python-side static fallback

Mirrors lua/session_template/lib/config.lua structure.
Used when REAPER is not running (testing, config queries without bridge).
The Lua config is the source of truth; this is a read-only fallback.
"""

STATIC_CONFIG = {
    "session_types": {
        "guitar": {
            "name": "Guitar Recording",
            "description": "DI + QC + Neural DSP, FX returns, guitar bus",
            "grid": 0.25,
            "snap": True,
            "use_folders": True,
        },
        "production": {
            "name": "Full Production",
            "description": "All instruments, vocals, full bus routing, mix bus",
            "grid": 0.0625,
            "snap": True,
            "use_folders": True,
        },
        "songwriting": {
            "name": "Songwriting / Sketch",
            "description": "Minimal setup for quick ideas — guitar, vocal, keys, beat",
            "grid": None,
            "snap": False,
            "use_folders": False,
        },
        "jam": {
            "name": "Jam / Loop",
            "description": "RC-600 integration, loop capture, minimal FX",
            "grid": 0.25,
            "snap": True,
            "use_folders": False,
        },
        "podcast": {
            "name": "Podcast / Voiceover",
            "description": "Mic tracks with processing chain, loudness targeting",
            "grid": None,
            "snap": False,
            "use_folders": False,
        },
        "mixing": {
            "name": "Mixing (Import Stems)",
            "description": "Empty folders with buses and FX returns, no inputs",
            "grid": 0.25,
            "snap": True,
            "use_folders": True,
        },
        "tone": {
            "name": "Tone Design",
            "description": "DI → 4 Neural DSP amps for A/B comparison",
            "grid": None,
            "snap": False,
            "use_folders": False,
        },
        "live": {
            "name": "Live Performance",
            "description": "Backing tracks, click, QC automation, live capture",
            "grid": 0.25,
            "snap": True,
            "use_folders": False,
        },
        "transcription": {
            "name": "Transcription / Learning",
            "description": "Source audio + playback rate control + practice tools",
            "grid": None,
            "snap": False,
            "use_folders": False,
        },
    },
    "tascam": {
        "channels": {
            "mic_mv7x": 1,
            "guitar_di_1": 2,
            "guitar_di_2": 3,
            "mic_condenser": 4,
            "rc600_l": 5,
            "rc600_r": 6,
            "qc_l": 7,
            "qc_r": 8,
            "daw_return_l": 9,
            "daw_return_r": 10,
        },
        "sample_rates": [44100, 48000],
        "bit_depth": 24,
    },
    "midi": {
        "devices": {
            "beatstep_pro": {
                "name": "Arturia BeatStep Pro",
                "channels": {"seq1": 1, "seq2": 2, "controller": 3, "drums": 10},
            },
            "nektar": {
                "name": "Impact LX61+",
                "channels": {"keys": 1, "pads": 10},
            },
            "quad_cortex": {
                "name": "Quad Cortex",
                "channels": {"main": 1},
            },
            "rc600": {
                "name": "RC-600",
                "channels": {"main": 4},
            },
        },
        "clock_destinations": ["Arturia BeatStep Pro", "Quad Cortex", "RC-600"],
        "transport_destinations": ["Arturia BeatStep Pro", "RC-600"],
    },
    "plugins": {
        "eq_surgical": {"preferred": "FabFilter Pro-Q 4", "fallback": "ReaEQ"},
        "eq_sitral": {"preferred": "EQ SITRAL-295", "fallback": "ReaEQ"},
        "comp_fet76": {"preferred": "Comp FET-76", "fallback": "ReaComp"},
        "comp_vca65": {"preferred": "Comp VCA-65", "fallback": "ReaComp"},
        "comp_tube_sta": {"preferred": "Comp TUBE-STA", "fallback": "ReaComp"},
        "rev_plate140": {"preferred": "Rev PLATE-140", "fallback": "ReaVerbate"},
        "rev_lx24": {"preferred": "Rev LX-24", "fallback": "ReaVerbate"},
        "delay_replika": {"preferred": "Replika", "fallback": "ReaDelay"},
        "neural_gojira": {"preferred": "Archetype: Gojira X", "fallback": None},
        "neural_petrucci": {"preferred": "Archetype: Petrucci X", "fallback": None},
        "neural_plini": {"preferred": "Archetype: Plini X", "fallback": None},
        "neural_mesa": {"preferred": "Mesa Boogie Mark IIC+ Suite", "fallback": None},
        "analog_lab": {"preferred": "Analog Lab V", "fallback": "ReaSynth"},
        "massive_x": {"preferred": "Massive X", "fallback": "ReaSynth"},
        "soundid": {"preferred": "SoundID Reference", "fallback": None},
        "tuner": {"preferred": "ReaTune", "fallback": None},
        "gate": {"preferred": "ReaGate", "fallback": None},
        "gain": {"preferred": "ReaGain", "fallback": None},
    },
    "colors": {
        "green": [76, 175, 80],
        "blue": [33, 150, 243],
        "orange": [255, 152, 0],
        "yellow": [255, 235, 59],
        "purple": [156, 39, 176],
        "cyan": [0, 188, 212],
        "red": [244, 67, 54],
        "white": [245, 245, 245],
        "gray": [158, 158, 158],
    },
    "loudness": {
        "spotify": -14,
        "apple_music": -16,
        "youtube": -14,
        "podcast": -16,
    },
}
