# CLAUDE.md — total-reaper-mcp

## Project Overview

MCP server that exposes REAPER DAW functionality through Claude. Fork of [shiehn/total-reaper-mcp](https://github.com/shiehn/total-reaper-mcp) with session templates and backing track generation added.

**Architecture:** Hybrid Lua-Python. Lua runs inside REAPER (ReaScript API), Python provides the MCP interface. Communication via file-based JSON IPC through `~/Library/Application Support/REAPER/Scripts/mcp_bridge_data/`.

## Key Directories

```
server/                     # Python MCP server
  app.py                    # Entry point, profile selection, CATEGORY_REGISTRY
  bridge.py                 # File-based IPC bridge to REAPER
  tool_profiles.py          # Profile definitions (10 profiles, including dsl-production default)
  session_config.py         # Hardware/plugin config (static fallback)
  song_lookup.py            # Chord chart scraping + parsing
  tools/                    # MCP tool modules (50 categories)
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
docs/reference/             # REAPER API docs (scraped, for development use)
```

## REAPER API Reference

Full API docs are in `docs/reference/`. Use these when adding bridge functions or tools:

- **`reascript-api-v7.60.md`** — Official ReaScript API (function signatures, parameters)
- **`reascript-api-full-v7.38.md`** — Comprehensive docs including SWS extension functions
- **`reaper-config-variables.md`** — Config vars for `SNM_GetIntConfigVar`/`SNM_SetIntConfigVar`
- **`reascript-guide.md`** — ReaScript overview (Lua/EEL2/Python conventions)
- **`reaper-operations-guide.md`** — Practical REAPER operations (Actions window UI, loading scripts, key bindings, menus, SWS/ReaPack, troubleshooting)

## Running Tests

The `--noconftest` flag is required because `tests/conftest.py` imports `mcp` which isn't installed in the system Python. The venv at `.venv/` has a stale interpreter path (from upstream author). Use `python3.13` directly.

### Mock tests (no REAPER needed, 68 tests)

```bash
python3.13 -m pytest tests/test_backing_tracks.py tests/test_song_lookup.py tests/test_session_templates.py -v --noconftest
```

### Live tests (require REAPER running with bridge, 268 tests)

Run **one suite at a time** — the file bridge can only handle one test suite's requests. Never run live suites in parallel.

```bash
# Bridge integration — 39 tests, DSL functions + raw REAPER API
python3.13 -m pytest tests/test_bridge_integration_live.py -v --noconftest

# DSL comprehensive — 66 tests, all 46 DSL tools
python3.13 -m pytest tests/test_dsl_comprehensive.py -v --noconftest

# Actions — 57 tests, all 21+ action scripts
python3.13 -m pytest tests/test_actions_live.py -v --noconftest

# Session templates — 80 tests, all 9 templates with detail assertions
python3.13 -m pytest tests/test_templates_live.py -v --noconftest

# Backing tracks — 26 tests, all genres × instruments + regeneration
python3.13 -m pytest tests/test_backing_live.py -v --noconftest
```

## Tool Profiles

Start with: `python -m server.app --profile <name>`

| Profile | Purpose |
|---------|---------|
| `dsl-production` | **Default.** DSL + essential tools + production workflow, render/export, MIDI production, arrangement |
| `session-template` | Session creation with hardware-specific routing |
| `backing-track` | Backing track generation from chord charts |
| `midi-production` | MIDI-focused workflows (editor, advanced MIDI, production) |
| `mixing` | Mixing and mastering (FX, routing, bus workflows, render) |
| `full` | All 700+ tools |
| `minimal` | Bare minimum (tracks, transport, project) |
| `dsl` | DSL tools only |
| `groq-essential` | Core REAPER for Groq (max 128 tools) |
| `groq-extended` | Extended Groq profile |

## Session Templates (9 types)

guitar, production, songwriting, jam, podcast, mixing, tone, live, transcription

Hardware-specific routing for: Tascam Model 12, Quad Cortex, RC-600, BeatStep Pro, Nektar LX61+.

## Backing Track Generator

Scrapes chord charts from Ultimate Guitar, parses into normalized SongChart, generates MIDI patterns for drums/bass/keys/guitar across 10 genres (blues, country, funk, jazz, latin, metal, pop, r&b, reggae, rock). All 4 instruments have full coverage of all 10 genres plus a "ballad" bonus pattern.

**Data flow:** `lookup_song()` → search UG → scrape chords → `parse_chord_chart()` → bridge `GenerateBackingTrack` → Lua `generators.build()` → REAPER tracks with VSTi + MIDI.

`regenerate_part()` re-generates a single instrument via `RegeneratePart` bridge function. Chart data is stored in REAPER project extended state (`MCP_BackingTrack` section) after initial generation.

## New Tool Categories (added post-fork)

These categories extend the original upstream toolset:

- **Production Workflow** (`production_workflow.py`): Arrangement templates, social media clip export, form analysis
- **Render & Export** (`render_export.py`): Format-aware rendering, stem export, social clip dimensions
- **MIDI Production** (`midi_production.py`): Batch MIDI insertion, scale lock, genre-specific drum patterns
- **Arrangement** (`arrangement.py`): Song structure templates, section management, form analysis
- **Neural DSP** (`neural_dsp.py`): Quad Cortex plugin parameter control within REAPER
- **Advanced MIDI Generation** (`advanced_midi_generation.py`): Algorithmic MIDI generation
- **Groove & Quantization** (`groove_quantization.py`): Groove templates, swing, humanize
- **Bus Routing & Mixing** (`bus_routing.py`): Bus creation, mixing workflows, routing helpers
- **Bounce & Render** (`bounce_render.py`): Bounce-in-place, render queue, freeze operations

## Conventions

- Tool modules return registration count from `register_*_tools(mcp)` functions
- Bridge functions go in `lua/mcp_bridge.lua` DSL_FUNCTIONS table
- Lua pattern libraries return `{pitch, start_beats, length_beats, velocity}` per bar
- Config source of truth: `lua/session_template/lib/config.lua`
- Python static fallback: `server/session_config.py`
- **Tempo**: NEVER use `CSurf_OnTempoChange` — doesn't persist in defer loop. Use `SetTempoTimeSigMarker` with marker count check (modify marker 0 if exists, create with ptidx=-1 if not)
- Bridge top-level DSL functions only reload on REAPER restart. Lua modules reload via `clear_module_cache()`

## Git

- Remote `origin`: `p3terp4N/total-reaper-mcp` (fork, push here)
- Remote `upstream`: `shiehn/total-reaper-mcp` (original, read-only)
- `main` tracks `upstream` — always push with `git push origin main`
