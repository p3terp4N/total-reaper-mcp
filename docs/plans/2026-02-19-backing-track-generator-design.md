# Backing Track Generator — Design

## Purpose

Generate MIDI backing tracks for any song inside REAPER. User provides a song name and artist, the system scrapes chord data, generates instrument parts, and inserts them as MIDI tracks with VSTi plugins.

## Input / Output

**Input**: `generate_backing_track("Hotel California", "Eagles", instruments=["drums", "bass", "keys"])`

**Output**: REAPER folder with MIDI tracks per instrument, each with appropriate VSTi, routed to a backing track bus.

## Data Pipeline

1. **Song Lookup** — Python scrapes chord chart from web sources
2. **Normalize** — Parse raw chords into structured `SongChart` (sections, chords, tempo, key, time signature)
3. **Generate** — Per-instrument generators produce MIDI note arrays from the chart
4. **Insert** — Bridge creates tracks, inserts MIDI, loads VSTi

## Chord Sources (free only)

| Priority | Source | Method |
|----------|--------|--------|
| 1 | Ultimate Guitar | Web scrape (community tabs) |
| 2 | Chordify | Web scrape (AI-analyzed) |
| 3 | Manual input | User pastes chord chart |
| Phase 2 | ChordMini | Local audio analysis (open-source) |

### Chord Parser

Handles standard (`Am`, `F#m`), extended (`Cmaj7`, `Dm7b5`), slash (`C/E`), and repeat (`. . .`) notation. Outputs normalized `SongChart` JSON:

```json
{
  "title": "Hotel California",
  "artist": "Eagles",
  "key": "Bm",
  "bpm": 74,
  "time_sig": "4/4",
  "sections": [
    {"name": "intro", "bars": 8, "chords": ["Bm", "F#7", "A", "E7", "G", "D", "Em", "F#7"]},
    {"name": "verse", "bars": 16, "chords": ["Bm", "F#7", "A", "E7", "..."]}
  ]
}
```

## Generation Modes

### `simple` — Deterministic pattern templates (Phase 1)

- Drums: straight 8th hi-hat, kick 1+3, snare 2+4, fills every 4/8 bars
- Bass: root on beat 1, octave on beat 3, follows chord changes
- Keys: block chord voicings on beats 1 and 3
- Rhythm guitar: arpeggiated chord strumming pattern

### `genre` — Genre-aware pattern library (Phase 1)

Genres: rock, pop, blues, jazz, funk, country, ballad, reggae, latin, metal.

Each genre provides ~3-4 variations per instrument (verse/chorus/bridge/fill). Patterns are Lua tables. Falls back to `simple` for unknown genres.

### `ai` — Claude-composed (Phase 2)

Sends chord chart + genre + instrument to Claude. Returns note data as JSON. User can regenerate individual parts.

## Track Structure

```
Backing Track (folder)
   BT - Drums        (VSTi, MIDI ch 10)
   BT - Bass          (VSTi, MIDI ch 1)
   BT - Keys          (VSTi, MIDI ch 2)   [if requested]
   BT - Rhythm Guitar (VSTi, MIDI ch 4)   [if requested]
   BT - Bus           (receives from all, limiter on master send)
```

### VSTi Mapping

| Instrument | Preferred | Fallback | MIDI Ch |
|-----------|-----------|----------|---------|
| Drums | Addictive Drums 2 | MT-PowerDrumKit (free) | 10 |
| Bass | Scarbee Bass (Kontakt) | ReaSynth | 1 |
| Keys | Keyscape / Analog Lab V | ReaSynth | 2 |
| Organ | Analog Lab V | ReaSynth | 3 |
| Rhythm Guitar | Ample Guitar / Heavier7Strings | ReaSynth | 4 |

Uses `fx.smart_add()` from session template system.

## MIDI Insertion

Each generator outputs `{pitch, start_beats, length_beats, velocity}` arrays. Bridge converts beats to PPQ using project tempo. One MIDI item per song section for easy rearrangement.

## Architecture

```
server/
   tools/backing_tracks.py       # MCP tools
   song_lookup.py                # Scraper + chord parser
   dsl/backing_wrappers.py       # Natural language wrappers

lua/session_template/lib/backing/
   generators.lua                # Orchestrator: chart -> MIDI per instrument
   drums.lua                     # Drum pattern library
   bass.lua                      # Bass line generators
   keys.lua                      # Piano/organ comping
   guitar.lua                    # Rhythm guitar patterns
   patterns/
      rock.lua, jazz.lua, funk.lua, ...   # Genre data tables
```

### MCP Tools

- `generate_backing_track(song, artist, instruments, style, genre_override)` — main tool
- `regenerate_part(instrument, style)` — redo one instrument
- `list_backing_genres()` — show available genres
- `get_song_chart(song, artist)` — fetch/parse chord chart only

### Bridge Functions

- `GenerateBackingTrack(chart_json, instruments, style)` — orchestrates Lua generators
- `RegeneratePart(instrument, chart_json, style)` — regenerate single instrument

## Error Handling

| Scenario | Behavior |
|----------|----------|
| Song not found | Try UG -> Chordify -> prompt for manual input |
| Ambiguous results | Pick highest-rated version, user can override key/capo |
| Missing tempo | Estimate from genre defaults |
| Missing key | Detect from chord set |
| Missing sections | Treat as single repeating section |
| Unknown chord type | Simplify to nearest known chord + log warning |
| No VSTi installed | Fall back to ReaSynth (ships with REAPER) |

## Phasing

**Phase 1**: `simple` + `genre` modes, UG + Chordify scraping, manual input, full track creation pipeline.

**Phase 2**: `ai` mode (Claude-composed MIDI), ChordMini local audio analysis.
