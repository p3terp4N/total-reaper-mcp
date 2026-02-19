# CLAUDE.md — total-reaper-mcp

## Project Overview

MCP server that exposes REAPER DAW functionality through Claude. Fork of [shiehn/total-reaper-mcp](https://github.com/shiehn/total-reaper-mcp) with session templates and backing track generation added.

**Architecture:** Hybrid Lua-Python. Lua runs inside REAPER (ReaScript API), Python provides the MCP interface. Communication via file-based JSON IPC through `~/Library/Application Support/REAPER/Scripts/mcp_bridge_data/`.

## Key Directories

```
server/                     # Python MCP server
  app.py                    # Entry point, profile selection, CATEGORY_REGISTRY
  bridge.py                 # File-based IPC bridge to REAPER
  tool_profiles.py          # Profile definitions (10 profiles)
  session_config.py         # Hardware/plugin config (static fallback)
  song_lookup.py            # Chord chart scraping + parsing
  tools/                    # MCP tool modules (38 categories)
  dsl/                      # Natural language wrappers
lua/
  mcp_bridge.lua            # Single bridge script for ALL profiles
  session_template/
    session_template.lua    # Standalone entry point (keybind target)
    lib/                    # Shared Lua modules (tracks, fx, config, etc.)
    lib/backing/            # Instrument pattern libraries (drums, bass, keys, guitar)
    templates/              # 9 session type templates
    actions/                # 28 action scripts (quick_tune, reamp, etc.)
tests/                      # pytest test suite
```

## Running Tests

REAPER is not installed. All tests run with mocks.

```bash
# Backing track + song lookup tests (48 tests, no REAPER needed)
python3.13 -m pytest tests/test_backing_tracks.py tests/test_song_lookup.py -v --noconftest

# Session template tests (20 tests, no REAPER needed)
python3.13 -m pytest tests/test_session_templates.py -v --noconftest
```

The `--noconftest` flag is required because `tests/conftest.py` imports `mcp` which isn't installed in the system Python. The venv at `.venv/` has a stale interpreter path (from upstream author). Use `python3.13` directly.

## Tool Profiles

Start with: `python -m server.app --profile <name>`

| Profile | Purpose |
|---------|---------|
| `dsl-production` | **Default.** DSL + essential tools |
| `session-template` | Session creation with hardware routing |
| `backing-track` | Backing track generation from chord charts |
| `full` | All 700+ tools |

## Session Templates (9 types)

guitar, production, songwriting, jam, podcast, mixing, tone, live, transcription

Hardware-specific routing for: Tascam Model 12, Quad Cortex, RC-600, BeatStep Pro, Nektar LX61+.

## Backing Track Generator

Scrapes chord charts from Ultimate Guitar, parses into normalized SongChart, generates MIDI patterns for drums/bass/keys/guitar across 10 genres (blues, country, funk, jazz, latin, metal, pop, r&b, reggae, rock).

**Data flow:** `lookup_song()` → search UG → scrape chords → `parse_chord_chart()` → bridge `GenerateBackingTrack` → Lua `generators.build()` → REAPER tracks with VSTi + MIDI.

## Conventions

- Tool modules return registration count from `register_*_tools(mcp)` functions
- Bridge functions go in `lua/mcp_bridge.lua` DSL_FUNCTIONS table
- Lua pattern libraries return `{pitch, start_beats, length_beats, velocity}` per bar
- Config source of truth: `lua/session_template/lib/config.lua`
- Python static fallback: `server/session_config.py`

## Git

- Remote `origin`: `p3terp4N/total-reaper-mcp` (fork, push here)
- Remote `upstream`: `shiehn/total-reaper-mcp` (original, read-only)
- `main` tracks `upstream` — always push with `git push origin main`
