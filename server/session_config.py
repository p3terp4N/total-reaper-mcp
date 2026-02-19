"""
Session Template Configuration — Python-side static fallback

This config mirrors the structure of lua/session_template/lib/config.lua.
Used when REAPER is not running (testing, config queries without bridge).
The Lua config is the source of truth; this is a fallback.
"""

STATIC_CONFIG = {
    "session_types": {
        "guitar": {
            "name": "Guitar Recording",
            "description": "DI + QC + Neural DSP, FX returns, guitar bus",
        },
        "production": {
            "name": "Full Production",
            "description": "All instruments, vocals, full bus routing, mix bus",
        },
        "songwriting": {
            "name": "Songwriting / Sketch",
            "description": "Minimal setup for quick ideas — guitar, vocal, keys, beat",
        },
        "jam": {
            "name": "Jam / Loop",
            "description": "RC-600 integration, loop capture, minimal FX",
        },
        "podcast": {
            "name": "Podcast / Voiceover",
            "description": "Mic tracks with processing chain, loudness targeting",
        },
        "mixing": {
            "name": "Mixing (Import Stems)",
            "description": "Empty folders with buses and FX returns, no inputs",
        },
        "tone": {
            "name": "Tone Design",
            "description": "DI → 4 Neural DSP amps for A/B comparison",
        },
        "live": {
            "name": "Live Performance",
            "description": "Backing tracks, click, QC automation, live capture",
        },
        "transcription": {
            "name": "Transcription / Learning",
            "description": "Source audio + playback rate control + practice tools",
        },
    },
    # Placeholder sections — filled in Phase 1
    "tascam": {},
    "midi": {},
    "plugins": {},
    "colors": {},
}
