# Backing Track Generator Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Generate MIDI backing tracks for any song by scraping chord data and producing genre-aware instrument parts in REAPER.

**Architecture:** Python scrapes chord charts (UG/Chordify) → parses into `SongChart` JSON → sends to Lua generators via bridge → Lua creates tracks with VSTi and inserts MIDI notes. Three generation modes: `simple` (deterministic), `genre` (pattern library), `ai` (Phase 2).

**Tech Stack:** Python (requests, BeautifulSoup4), Lua (ReaScript API), MCP tools (FastMCP)

**Design doc:** `docs/plans/2026-02-19-backing-track-generator-design.md`

---

## Phase 1: Chord Scraping & Parsing

### Task 1: Song Lookup — Chord Scraper

**Files:**
- Create: `server/song_lookup.py`
- Create: `tests/test_song_lookup.py`

**Step 1: Write the failing test**

```python
# tests/test_song_lookup.py
"""Tests for song lookup / chord parsing (no network required)."""

import pytest


class TestChordParser:
    """Test chord chart text parsing."""

    def test_parse_simple_chart(self):
        from server.song_lookup import parse_chord_chart
        raw = """[Verse]
Am . G .
F . E .

[Chorus]
C G Am F
"""
        chart = parse_chord_chart(raw, title="Test Song", artist="Test Artist", bpm=120, key="Am")
        assert chart["title"] == "Test Song"
        assert chart["key"] == "Am"
        assert chart["bpm"] == 120
        assert len(chart["sections"]) == 2
        assert chart["sections"][0]["name"] == "verse"
        assert chart["sections"][0]["chords"] == ["Am", "Am", "G", "G", "F", "F", "E", "E"]
        assert chart["sections"][1]["name"] == "chorus"
        assert chart["sections"][1]["chords"] == ["C", "G", "Am", "F"]

    def test_parse_repeats_with_dots(self):
        from server.song_lookup import parse_chord_chart
        raw = "[Verse]\nAm . . .\n"
        chart = parse_chord_chart(raw, title="T", artist="A")
        assert chart["sections"][0]["chords"] == ["Am", "Am", "Am", "Am"]

    def test_parse_section_names_normalized(self):
        from server.song_lookup import parse_chord_chart
        raw = "[Intro]\nAm\n[VERSE 1]\nG\n[Pre-Chorus]\nC\n[Chorus]\nF\n[Bridge]\nDm\n[Outro]\nAm\n"
        chart = parse_chord_chart(raw, title="T", artist="A")
        names = [s["name"] for s in chart["sections"]]
        assert names == ["intro", "verse", "pre-chorus", "chorus", "bridge", "outro"]

    def test_parse_extended_chords(self):
        from server.song_lookup import parse_chord_chart
        raw = "[Verse]\nCmaj7 Dm7b5 G13 Asus4\n"
        chart = parse_chord_chart(raw, title="T", artist="A")
        assert chart["sections"][0]["chords"] == ["Cmaj7", "Dm7b5", "G13", "Asus4"]

    def test_parse_slash_chords(self):
        from server.song_lookup import parse_chord_chart
        raw = "[Verse]\nC/E G/B Am\n"
        chart = parse_chord_chart(raw, title="T", artist="A")
        assert chart["sections"][0]["chords"] == ["C/E", "G/B", "Am"]

    def test_parse_empty_chart_returns_empty_sections(self):
        from server.song_lookup import parse_chord_chart
        chart = parse_chord_chart("", title="T", artist="A")
        assert chart["sections"] == []

    def test_bars_calculated_from_chords(self):
        from server.song_lookup import parse_chord_chart
        raw = "[Verse]\nAm G F E Am G F E\n"
        chart = parse_chord_chart(raw, title="T", artist="A", time_sig="4/4")
        # 8 chords at 1 chord per bar = 8 bars
        assert chart["sections"][0]["bars"] == 8


class TestChordSimplifier:
    """Test chord simplification for unknown types."""

    def test_simplify_known_chord(self):
        from server.song_lookup import simplify_chord
        assert simplify_chord("Am") == "Am"
        assert simplify_chord("C") == "C"

    def test_simplify_extended_chord(self):
        from server.song_lookup import simplify_chord
        assert simplify_chord("Cmaj7") == "Cmaj7"
        assert simplify_chord("Dm7") == "Dm7"

    def test_simplify_complex_to_triad(self):
        from server.song_lookup import simplify_chord
        # Unknown extensions fall back to root triad
        assert simplify_chord("Gadd9#11b13") == "G"

    def test_simplify_slash_extracts_bass(self):
        from server.song_lookup import simplify_chord, extract_bass_note
        assert extract_bass_note("C/E") == "E"
        assert extract_bass_note("Am") is None


class TestKeyDetection:
    """Test key detection from chord set."""

    def test_detect_key_from_chords(self):
        from server.song_lookup import detect_key
        assert detect_key(["Am", "G", "F", "E"]) == "Am"
        assert detect_key(["C", "G", "Am", "F"]) == "C"

    def test_detect_key_empty(self):
        from server.song_lookup import detect_key
        assert detect_key([]) == "C"  # default


class TestTempoEstimation:
    """Test genre-based tempo estimation."""

    def test_estimate_tempo_by_genre(self):
        from server.song_lookup import estimate_tempo
        assert estimate_tempo("rock") == 120
        assert estimate_tempo("ballad") == 72
        assert estimate_tempo("funk") == 100

    def test_estimate_tempo_unknown_genre(self):
        from server.song_lookup import estimate_tempo
        assert estimate_tempo("unknown") == 120  # default
```

**Step 2: Run test to verify it fails**

Run: `.venv-session/bin/python3 -m pytest tests/test_song_lookup.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'server.song_lookup'`

**Step 3: Write implementation**

```python
# server/song_lookup.py
"""
Song Lookup — Chord chart scraping and parsing.

Scrapes chord charts from Ultimate Guitar and Chordify,
parses them into normalized SongChart dicts for backing track generation.
"""

import re
from typing import Optional


# ============================================================================
# Chord Parsing
# ============================================================================

# Regex for valid chord tokens: root + optional quality + optional slash bass
CHORD_RE = re.compile(
    r'^[A-G][b#]?'                  # root note
    r'(?:m|min|maj|dim|aug|sus)?'   # basic quality
    r'(?:\d+)?'                      # extension (7, 9, 11, 13)
    r'(?:[b#]\d+)*'                  # alterations (b5, #9)
    r'(?:add\d+)?'                   # add extensions
    r'(?:/[A-G][b#]?)?$'            # slash bass
)

SECTION_RE = re.compile(r'^\[([^\]]+)\]')

# Known chord qualities we can voice (everything else gets simplified)
KNOWN_QUALITIES = {
    "", "m", "min", "maj", "dim", "aug", "sus2", "sus4",
    "7", "m7", "maj7", "min7", "dim7", "aug7",
    "9", "m9", "maj9", "11", "m11", "13", "m13",
    "6", "m6", "add9", "add11",
    "7b5", "7#5", "m7b5", "7b9", "7#9",
    "sus", "7sus4",
}

GENRE_TEMPOS = {
    "rock": 120, "pop": 115, "blues": 90, "jazz": 140,
    "funk": 100, "country": 110, "ballad": 72, "reggae": 80,
    "latin": 105, "metal": 140, "punk": 170, "r&b": 95,
}

# Common key signatures based on chord frequency
KEY_WEIGHTS = {
    "C": ["C", "Dm", "Em", "F", "G", "Am"],
    "G": ["G", "Am", "Bm", "C", "D", "Em"],
    "D": ["D", "Em", "F#m", "G", "A", "Bm"],
    "A": ["A", "Bm", "C#m", "D", "E", "F#m"],
    "E": ["E", "F#m", "G#m", "A", "B", "C#m"],
    "F": ["F", "Gm", "Am", "Bb", "C", "Dm"],
    "Bb": ["Bb", "Cm", "Dm", "Eb", "F", "Gm"],
    "Am": ["Am", "Bdim", "C", "Dm", "Em", "F", "G", "E"],
    "Em": ["Em", "F#dim", "G", "Am", "Bm", "C", "D", "B"],
    "Dm": ["Dm", "Edim", "F", "Gm", "Am", "Bb", "C", "A"],
}


def _normalize_section_name(raw: str) -> str:
    """Normalize section name: '[VERSE 1]' -> 'verse', '[Pre-Chorus]' -> 'pre-chorus'."""
    name = raw.strip().lower()
    name = re.sub(r'\s*\d+$', '', name)  # strip trailing numbers
    name = name.replace(' ', '-')
    return name


def _is_chord_token(token: str) -> bool:
    """Check if a token looks like a chord."""
    if not token or token == ".":
        return False
    return bool(CHORD_RE.match(token))


def parse_chord_chart(
    raw_text: str,
    title: str = "",
    artist: str = "",
    bpm: int = 0,
    key: str = "",
    time_sig: str = "4/4",
) -> dict:
    """Parse a chord chart text into a normalized SongChart dict."""
    sections = []
    current_section = None
    current_chords = []

    for line in raw_text.split("\n"):
        line = line.strip()
        if not line:
            continue

        # Section header
        section_match = SECTION_RE.match(line)
        if section_match:
            # Save previous section
            if current_section and current_chords:
                sections.append({
                    "name": current_section,
                    "chords": current_chords,
                    "bars": len(current_chords),
                })
            current_section = _normalize_section_name(section_match.group(1))
            current_chords = []
            continue

        # Chord line
        if current_section is not None:
            tokens = line.split()
            prev_chord = None
            for token in tokens:
                if token == ".":
                    if prev_chord:
                        current_chords.append(prev_chord)
                elif _is_chord_token(token):
                    current_chords.append(token)
                    prev_chord = token

    # Save last section
    if current_section and current_chords:
        sections.append({
            "name": current_section,
            "chords": current_chords,
            "bars": len(current_chords),
        })

    # Detect key from chords if not provided
    all_chords = [c for s in sections for c in s["chords"]]
    if not key:
        key = detect_key(all_chords)

    return {
        "title": title,
        "artist": artist,
        "key": key,
        "bpm": bpm or 120,
        "time_sig": time_sig,
        "sections": sections,
    }


def simplify_chord(chord: str) -> str:
    """Simplify a chord to the nearest known voicing.

    Returns the chord as-is if known, otherwise strips to root triad.
    """
    if "/" in chord:
        chord = chord.split("/")[0]

    # Extract root
    root_match = re.match(r'^([A-G][b#]?)(.*)', chord)
    if not root_match:
        return chord
    root, quality = root_match.group(1), root_match.group(2)

    if quality in KNOWN_QUALITIES:
        return chord
    # Try shorter suffixes
    for length in range(len(quality), 0, -1):
        if quality[:length] in KNOWN_QUALITIES:
            return root + quality[:length]
    return root


def extract_bass_note(chord: str) -> Optional[str]:
    """Extract the bass note from a slash chord, or None."""
    if "/" in chord:
        return chord.split("/")[1]
    return None


def detect_key(chords: list[str]) -> str:
    """Detect the most likely key from a list of chords."""
    if not chords:
        return "C"

    # Strip extensions for matching
    roots = []
    for c in chords:
        root_match = re.match(r'^([A-G][b#]?m?)', c)
        if root_match:
            roots.append(root_match.group(1))

    # Score each key by how many chords belong to it
    best_key = "C"
    best_score = 0
    for key, scale_chords in KEY_WEIGHTS.items():
        score = sum(1 for r in roots if r in scale_chords)
        if score > best_score:
            best_score = score
            best_key = key

    return best_key


def estimate_tempo(genre: str) -> int:
    """Estimate tempo from genre. Returns 120 as default."""
    return GENRE_TEMPOS.get(genre.lower(), 120)
```

**Step 4: Run test to verify it passes**

Run: `.venv-session/bin/python3 -m pytest tests/test_song_lookup.py -v`
Expected: All PASS

**Step 5: Commit**

```bash
git add server/song_lookup.py tests/test_song_lookup.py
git commit -m "feat: add chord chart parser and song lookup module"
```

---

### Task 2: Ultimate Guitar Scraper

**Files:**
- Modify: `server/song_lookup.py`
- Modify: `tests/test_song_lookup.py`

**Dependencies:** `pip install requests beautifulsoup4` (should already be installed; check first)

**Step 1: Write the failing test**

Add to `tests/test_song_lookup.py`:

```python
from unittest.mock import patch, MagicMock


class TestUGScraper:
    """Test Ultimate Guitar scraping (mocked network)."""

    def test_search_returns_url(self):
        from server.song_lookup import search_ultimate_guitar
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = '''
        <div class="js-store" data-content='{"store":{"page":{"data":{"results":[
            {"tab_url":"https://tabs.ultimate-guitar.com/tab/eagles/hotel-california-chords-46190",
             "song_name":"Hotel California","artist_name":"Eagles","rating":4.8,"type":"Chords"}
        ]}}}}'>
        '''
        with patch("server.song_lookup.requests.get", return_value=mock_response):
            result = search_ultimate_guitar("Hotel California", "Eagles")
            assert result is not None
            assert "hotel-california" in result

    def test_search_no_results(self):
        from server.song_lookup import search_ultimate_guitar
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = '<div class="js-store" data-content=\'{"store":{"page":{"data":{"results":[]}}}}\'>'
        with patch("server.song_lookup.requests.get", return_value=mock_response):
            result = search_ultimate_guitar("Nonexistent Song", "Nobody")
            assert result is None

    def test_scrape_chord_page(self):
        from server.song_lookup import scrape_ug_chord_page
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = '''
        <div class="js-store" data-content='{"store":{"page":{"data":{"tab_view":{"wiki_tab":{"content":"[Verse]\\nAm G F E\\n\\n[Chorus]\\nC G Am F\\n"},"meta":{"tonality":"Am","bpm":null}}}}}}'>
        '''
        with patch("server.song_lookup.requests.get", return_value=mock_response):
            chart_text, meta = scrape_ug_chord_page("https://tabs.ultimate-guitar.com/fake")
            assert "[Verse]" in chart_text
            assert "Am" in chart_text

    def test_full_lookup_pipeline(self):
        from server.song_lookup import lookup_song
        mock_search = MagicMock(return_value="https://tabs.ultimate-guitar.com/fake")
        mock_scrape = MagicMock(return_value=("[Verse]\nAm G\n[Chorus]\nC F\n", {"tonality": "Am"}))
        with patch("server.song_lookup.search_ultimate_guitar", mock_search), \
             patch("server.song_lookup.scrape_ug_chord_page", mock_scrape):
            chart = lookup_song("Test", "Artist")
            assert chart is not None
            assert chart["title"] == "Test"
            assert len(chart["sections"]) == 2
```

**Step 2: Run test to verify it fails**

Run: `.venv-session/bin/python3 -m pytest tests/test_song_lookup.py::TestUGScraper -v`
Expected: FAIL — `ImportError: cannot import name 'search_ultimate_guitar'`

**Step 3: Add scraper functions to `server/song_lookup.py`**

Append to `server/song_lookup.py`:

```python
import json
import requests


# ============================================================================
# Web Scraping — Ultimate Guitar
# ============================================================================

UG_SEARCH_URL = "https://www.ultimate-guitar.com/search.php"
UG_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
}


def search_ultimate_guitar(song: str, artist: str) -> Optional[str]:
    """Search Ultimate Guitar for a chord chart. Returns tab URL or None."""
    try:
        resp = requests.get(UG_SEARCH_URL, params={
            "search_type": "title",
            "value": f"{artist} {song}",
        }, headers=UG_HEADERS, timeout=10)
        resp.raise_for_status()
    except Exception:
        return None

    # UG stores data in a js-store div
    match = re.search(r'class="js-store"\s+data-content="([^"]*)"', resp.text)
    if not match:
        # Try single-quote variant
        match = re.search(r"class=\"js-store\"\s+data-content='([^']*)'", resp.text)
    if not match:
        return None

    try:
        data = json.loads(match.group(1).replace("&quot;", '"'))
        results = data["store"]["page"]["data"]["results"]
    except (json.JSONDecodeError, KeyError):
        return None

    # Filter for chord tabs, pick highest rated
    chord_tabs = [r for r in results if r.get("type") == "Chords"]
    if not chord_tabs:
        return None

    chord_tabs.sort(key=lambda r: r.get("rating", 0), reverse=True)
    return chord_tabs[0].get("tab_url")


def scrape_ug_chord_page(url: str) -> tuple[Optional[str], dict]:
    """Scrape a UG chord page. Returns (chord_text, metadata_dict)."""
    try:
        resp = requests.get(url, headers=UG_HEADERS, timeout=10)
        resp.raise_for_status()
    except Exception:
        return None, {}

    match = re.search(r'class="js-store"\s+data-content="([^"]*)"', resp.text)
    if not match:
        match = re.search(r"class=\"js-store\"\s+data-content='([^']*)'", resp.text)
    if not match:
        return None, {}

    try:
        data = json.loads(match.group(1).replace("&quot;", '"'))
        tab_view = data["store"]["page"]["data"]["tab_view"]
        content = tab_view["wiki_tab"]["content"]
        meta = tab_view.get("meta", {})
    except (json.JSONDecodeError, KeyError):
        return None, {}

    # Clean up content: strip HTML tags, decode entities
    content = re.sub(r'<[^>]+>', '', content)
    content = content.replace("&amp;", "&").replace("\\n", "\n")

    return content, meta


def lookup_song(
    song: str,
    artist: str,
    bpm: int = 0,
    genre: str = "",
) -> Optional[dict]:
    """Full lookup pipeline: search → scrape → parse. Returns SongChart or None."""
    url = search_ultimate_guitar(song, artist)
    if not url:
        return None

    chart_text, meta = scrape_ug_chord_page(url)
    if not chart_text:
        return None

    key = meta.get("tonality", "")
    detected_bpm = bpm or (meta.get("bpm") and int(meta["bpm"])) or 0
    if not detected_bpm and genre:
        detected_bpm = estimate_tempo(genre)

    return parse_chord_chart(
        chart_text,
        title=song,
        artist=artist,
        bpm=detected_bpm,
        key=key,
    )
```

**Step 4: Run test to verify it passes**

Run: `.venv-session/bin/python3 -m pytest tests/test_song_lookup.py -v`
Expected: All PASS

**Step 5: Commit**

```bash
git add server/song_lookup.py tests/test_song_lookup.py
git commit -m "feat: add Ultimate Guitar scraper with mocked tests"
```

---

## Phase 2: Lua Pattern Libraries

### Task 3: Drum Pattern Library

**Files:**
- Create: `lua/session_template/lib/backing/drums.lua`

**Step 1: Write the module**

```lua
-- backing/drums.lua — Drum pattern generators
--
-- Each pattern function returns a table of {pitch, start_beats, length_beats, velocity}
-- for one bar of drums. Generators take (section_type, bar_number) for variation.

local drums = {}

-- GM drum map
drums.GM = {
    kick = 36, snare = 38, rimshot = 37,
    hihat = 42, hihat_open = 46, hihat_pedal = 44,
    crash = 49, crash2 = 57, ride = 51, ride_bell = 53,
    tom_hi = 48, tom_mid = 45, tom_lo = 43, tom_floor = 41,
    clap = 39, cowbell = 56, tambourine = 54,
}

-- Note length for drums (short hits)
local HIT = 0.1

-- Helper: create a note entry
local function note(pitch, start, vel)
    return { pitch = pitch, start_beats = start, length_beats = HIT, velocity = vel or 100 }
end

-- Helper: repeat a pattern for N bars
function drums.repeat_bars(pattern_fn, bars, section_type)
    local notes = {}
    for bar = 0, bars - 1 do
        local bar_notes = pattern_fn(section_type or "verse", bar)
        for _, n in ipairs(bar_notes) do
            notes[#notes + 1] = {
                pitch = n.pitch,
                start_beats = n.start_beats + (bar * 4),
                length_beats = n.length_beats,
                velocity = n.velocity,
            }
        end
    end
    return notes
end

-- Helper: add a fill on the last bar of a phrase
local function add_fill(notes, bar, style)
    style = style or "basic"
    local gm = drums.GM
    if style == "basic" then
        -- Simple snare roll into crash
        for i = 0, 3 do
            notes[#notes + 1] = note(gm.snare, 2 + i * 0.25, 90 + i * 3)
        end
        notes[#notes + 1] = note(gm.tom_hi, 3, 100)
        notes[#notes + 1] = note(gm.tom_mid, 3.25, 100)
        notes[#notes + 1] = note(gm.tom_lo, 3.5, 105)
        notes[#notes + 1] = note(gm.tom_floor, 3.75, 110)
    end
    return notes
end

-- ============================================================================
-- Simple mode — basic patterns that always work
-- ============================================================================

function drums.simple(section_type, bar_in_phrase)
    local gm = drums.GM
    local notes = {}
    local is_fill_bar = (bar_in_phrase % 4 == 3)

    -- Kick on 1 and 3
    notes[#notes + 1] = note(gm.kick, 0, 110)
    notes[#notes + 1] = note(gm.kick, 2, 100)
    -- Snare on 2 and 4
    notes[#notes + 1] = note(gm.snare, 1, 105)
    notes[#notes + 1] = note(gm.snare, 3, 100)
    -- 8th note hi-hats
    for i = 0, 7 do
        notes[#notes + 1] = note(gm.hihat, i * 0.5, 80)
    end

    if is_fill_bar then
        notes = add_fill(notes, bar_in_phrase, "basic")
    end

    return notes
end

-- ============================================================================
-- Genre mode — genre-specific patterns
-- ============================================================================

-- Rock: driving 8ths, strong kick/snare
function drums.rock(section_type, bar_in_phrase)
    local gm = drums.GM
    local notes = {}
    local is_chorus = (section_type == "chorus")
    local is_fill = (bar_in_phrase % 4 == 3)

    -- Kick pattern
    notes[#notes + 1] = note(gm.kick, 0, 115)
    notes[#notes + 1] = note(gm.kick, 2, 105)
    if is_chorus then
        notes[#notes + 1] = note(gm.kick, 2.5, 90) -- extra kick in chorus
    end

    -- Snare on 2 and 4
    notes[#notes + 1] = note(gm.snare, 1, 110)
    notes[#notes + 1] = note(gm.snare, 3, 105)

    -- Hi-hat 8ths (ride in chorus)
    local hat = is_chorus and gm.ride or gm.hihat
    for i = 0, 7 do
        notes[#notes + 1] = note(hat, i * 0.5, 85)
    end

    -- Crash on beat 1 of first bar in phrase
    if bar_in_phrase % 4 == 0 and is_chorus then
        notes[#notes + 1] = note(gm.crash, 0, 110)
    end

    if is_fill then notes = add_fill(notes, bar_in_phrase, "basic") end
    return notes
end

-- Pop: lighter, 8th hat, ghost notes
function drums.pop(section_type, bar_in_phrase)
    local gm = drums.GM
    local notes = {}
    local is_chorus = (section_type == "chorus")
    local is_fill = (bar_in_phrase % 8 == 7)

    notes[#notes + 1] = note(gm.kick, 0, 100)
    notes[#notes + 1] = note(gm.kick, 2.5, 85)
    notes[#notes + 1] = note(gm.snare, 1, 95)
    notes[#notes + 1] = note(gm.snare, 3, 90)

    -- Ghost note on snare
    notes[#notes + 1] = note(gm.snare, 1.75, 45)

    for i = 0, 7 do
        notes[#notes + 1] = note(gm.hihat, i * 0.5, 70 + (i % 2 == 0 and 10 or 0))
    end

    if is_fill then notes = add_fill(notes, bar_in_phrase, "basic") end
    return notes
end

-- Blues: shuffle feel (swing 8ths approximated as triplets)
function drums.blues(section_type, bar_in_phrase)
    local gm = drums.GM
    local notes = {}
    local is_fill = (bar_in_phrase % 4 == 3)

    notes[#notes + 1] = note(gm.kick, 0, 100)
    notes[#notes + 1] = note(gm.kick, 2, 90)
    notes[#notes + 1] = note(gm.snare, 1, 100)
    notes[#notes + 1] = note(gm.snare, 3, 95)

    -- Shuffle hi-hat: triplet feel (1, 1.67, 2, 2.67, 3, 3.67)
    local shuffle_positions = {0, 0.67, 1, 1.67, 2, 2.67, 3, 3.67}
    for _, pos in ipairs(shuffle_positions) do
        notes[#notes + 1] = note(gm.hihat, pos, 80)
    end

    if is_fill then notes = add_fill(notes, bar_in_phrase, "basic") end
    return notes
end

-- Jazz: ride pattern, kick comping
function drums.jazz(section_type, bar_in_phrase)
    local gm = drums.GM
    local notes = {}

    -- Ride pattern: 1, 2-and, 3, 4-and (swing)
    notes[#notes + 1] = note(gm.ride, 0, 90)
    notes[#notes + 1] = note(gm.ride, 1.67, 75)
    notes[#notes + 1] = note(gm.ride, 2, 85)
    notes[#notes + 1] = note(gm.ride, 3.67, 75)

    -- Hi-hat on 2 and 4
    notes[#notes + 1] = note(gm.hihat_pedal, 1, 60)
    notes[#notes + 1] = note(gm.hihat_pedal, 3, 60)

    -- Light kick comping (varies by bar)
    if bar_in_phrase % 2 == 0 then
        notes[#notes + 1] = note(gm.kick, 0, 70)
        notes[#notes + 1] = note(gm.kick, 2.67, 55)
    else
        notes[#notes + 1] = note(gm.kick, 0.67, 60)
        notes[#notes + 1] = note(gm.kick, 2, 65)
    end

    return notes
end

-- Funk: syncopated kick, ghost notes, 16th hats
function drums.funk(section_type, bar_in_phrase)
    local gm = drums.GM
    local notes = {}
    local is_fill = (bar_in_phrase % 4 == 3)

    -- Syncopated kick
    notes[#notes + 1] = note(gm.kick, 0, 110)
    notes[#notes + 1] = note(gm.kick, 0.75, 85)
    notes[#notes + 1] = note(gm.kick, 2, 100)
    notes[#notes + 1] = note(gm.kick, 2.25, 80)

    -- Snare on 2 and 4 with ghost notes
    notes[#notes + 1] = note(gm.snare, 1, 110)
    notes[#notes + 1] = note(gm.snare, 3, 105)
    notes[#notes + 1] = note(gm.snare, 0.5, 40)   -- ghost
    notes[#notes + 1] = note(gm.snare, 1.5, 35)   -- ghost
    notes[#notes + 1] = note(gm.snare, 2.75, 40)  -- ghost

    -- 16th hi-hats
    for i = 0, 15 do
        local vel = 70
        if i % 4 == 0 then vel = 90
        elseif i % 2 == 0 then vel = 80 end
        notes[#notes + 1] = note(gm.hihat, i * 0.25, vel)
    end

    if is_fill then notes = add_fill(notes, bar_in_phrase, "basic") end
    return notes
end

-- Country: train beat
function drums.country(section_type, bar_in_phrase)
    local gm = drums.GM
    local notes = {}

    notes[#notes + 1] = note(gm.kick, 0, 100)
    notes[#notes + 1] = note(gm.kick, 2, 90)
    notes[#notes + 1] = note(gm.snare, 1, 95)
    notes[#notes + 1] = note(gm.snare, 3, 90)

    -- Train beat: alternating closed/open hat
    for i = 0, 7 do
        local h = (i % 2 == 0) and gm.hihat or gm.hihat_open
        notes[#notes + 1] = note(h, i * 0.5, 80)
    end

    return notes
end

-- Ballad: sparse, gentle
function drums.ballad(section_type, bar_in_phrase)
    local gm = drums.GM
    local notes = {}
    local is_chorus = (section_type == "chorus")

    notes[#notes + 1] = note(gm.kick, 0, 75)
    if is_chorus then
        notes[#notes + 1] = note(gm.kick, 2, 65)
    end
    notes[#notes + 1] = note(gm.snare, 2, is_chorus and 80 or 70)

    -- Gentle ride or cross-stick
    local hat = is_chorus and gm.ride or gm.rimshot
    for i = 0, 3 do
        notes[#notes + 1] = note(hat, i, 55)
    end

    return notes
end

-- Reggae: one-drop
function drums.reggae(section_type, bar_in_phrase)
    local gm = drums.GM
    local notes = {}

    -- One drop: kick + snare on 3, no beat 1
    notes[#notes + 1] = note(gm.kick, 2, 100)
    notes[#notes + 1] = note(gm.snare, 2, 95)

    -- Cross-stick on offbeats
    notes[#notes + 1] = note(gm.rimshot, 0.5, 70)
    notes[#notes + 1] = note(gm.rimshot, 1.5, 65)
    notes[#notes + 1] = note(gm.rimshot, 2.5, 70)
    notes[#notes + 1] = note(gm.rimshot, 3.5, 65)

    -- Hi-hat on beats
    for i = 0, 3 do
        notes[#notes + 1] = note(gm.hihat, i, 75)
    end

    return notes
end

-- Metal: double kick, aggressive
function drums.metal(section_type, bar_in_phrase)
    local gm = drums.GM
    local notes = {}
    local is_chorus = (section_type == "chorus")
    local is_fill = (bar_in_phrase % 4 == 3)

    -- Double kick 16ths (chorus) or 8ths (verse)
    if is_chorus then
        for i = 0, 15 do
            notes[#notes + 1] = note(gm.kick, i * 0.25, 115)
        end
    else
        for i = 0, 7 do
            notes[#notes + 1] = note(gm.kick, i * 0.5, 110)
        end
    end

    -- Snare on 2 and 4
    notes[#notes + 1] = note(gm.snare, 1, 120)
    notes[#notes + 1] = note(gm.snare, 3, 115)

    -- Ride or china
    for i = 0, 7 do
        notes[#notes + 1] = note(gm.ride, i * 0.5, 95)
    end

    if is_fill then notes = add_fill(notes, bar_in_phrase, "basic") end
    return notes
end

-- Latin: basic bossa nova
function drums.latin(section_type, bar_in_phrase)
    local gm = drums.GM
    local notes = {}

    -- Cross-stick pattern
    notes[#notes + 1] = note(gm.rimshot, 1, 80)
    notes[#notes + 1] = note(gm.rimshot, 3, 75)

    -- Kick on 1 and the "and" of 2
    notes[#notes + 1] = note(gm.kick, 0, 85)
    notes[#notes + 1] = note(gm.kick, 1.5, 70)

    -- Hi-hat 8ths
    for i = 0, 7 do
        notes[#notes + 1] = note(gm.hihat, i * 0.5, 65)
    end

    return notes
end

--- Get the pattern function for a genre. Falls back to simple.
function drums.get_pattern(genre)
    local patterns = {
        rock = drums.rock, pop = drums.pop, blues = drums.blues,
        jazz = drums.jazz, funk = drums.funk, country = drums.country,
        ballad = drums.ballad, reggae = drums.reggae, metal = drums.metal,
        latin = drums.latin,
    }
    return patterns[genre] or drums.simple
end

return drums
```

**Step 2: Verify syntax**

Run: `lua -c lua/session_template/lib/backing/drums.lua` (or `luac -p` if available)
If no lua installed: skip syntax check, will be validated when running in REAPER.

**Step 3: Commit**

```bash
git add lua/session_template/lib/backing/drums.lua
git commit -m "feat: add drum pattern library (10 genres + simple mode)"
```

---

### Task 4: Bass Line Library

**Files:**
- Create: `lua/session_template/lib/backing/bass.lua`

**Step 1: Write the module**

```lua
-- backing/bass.lua — Bass line generators
--
-- Takes chord names + section info, produces MIDI notes.
-- Uses music theory to voice bass lines appropriately per genre.

local bass = {}

-- Note name → MIDI pitch (octave 2, bass register)
local ROOT_NOTES = {
    C = 36, ["C#"] = 37, Db = 37, D = 38, ["D#"] = 39, Eb = 39,
    E = 40, F = 41, ["F#"] = 42, Gb = 42, G = 43, ["G#"] = 44,
    Ab = 44, A = 45, ["A#"] = 46, Bb = 46, B = 47,
}

-- Intervals from root
local INTERVALS = {
    unison = 0, min2 = 1, maj2 = 2, min3 = 3, maj3 = 4,
    p4 = 5, tritone = 6, p5 = 7, min6 = 8, maj6 = 9,
    min7 = 10, maj7 = 11, octave = 12,
}

local function note(pitch, start, length, vel)
    return { pitch = pitch, start_beats = start, length_beats = length, velocity = vel or 95 }
end

--- Parse a chord name into root MIDI pitch and quality.
local function parse_chord(chord_name)
    if not chord_name then return 36, "" end
    -- Handle slash chords: use bass note
    local slash_bass = chord_name:match("/([A-G][b#]?)")
    local root_str = chord_name:match("^([A-G][b#]?)")
    if slash_bass then
        root_str = slash_bass
    end
    local quality = chord_name:match("^[A-G][b#]?(.*)")
    if slash_bass then
        quality = chord_name:match("^[A-G][b#]?(.-)/")
    end
    local pitch = ROOT_NOTES[root_str] or 36
    return pitch, quality or ""
end

--- Get the fifth above a root pitch.
local function fifth(root)
    return root + INTERVALS.p5
end

--- Get the third (major or minor based on quality).
local function third(root, quality)
    if quality:match("m") and not quality:match("maj") then
        return root + INTERVALS.min3
    end
    return root + INTERVALS.maj3
end

--- Get the seventh if chord quality implies it.
local function seventh(root, quality)
    if quality:match("maj7") then return root + INTERVALS.maj7 end
    if quality:match("7") then return root + INTERVALS.min7 end
    return nil
end

-- ============================================================================
-- Simple mode
-- ============================================================================

--- Simple: root on 1, octave on 3.
function bass.simple(chord_name, section_type, bar_in_phrase)
    local root, _ = parse_chord(chord_name)
    return {
        note(root, 0, 1.5, 100),
        note(root + 12, 2, 1.5, 85),
    }
end

-- ============================================================================
-- Genre patterns
-- ============================================================================

-- Rock: root-fifth driving pattern
function bass.rock(chord_name, section_type, bar_in_phrase)
    local root, q = parse_chord(chord_name)
    local f = fifth(root)
    local notes = {}
    local is_chorus = (section_type == "chorus")

    notes[#notes + 1] = note(root, 0, 0.75, 105)
    notes[#notes + 1] = note(root, 1, 0.75, 95)
    notes[#notes + 1] = note(f, 2, 0.75, 100)
    notes[#notes + 1] = note(root, 3, 0.75, 90)

    if is_chorus then
        notes[#notes + 1] = note(root, 0.5, 0.25, 70)
        notes[#notes + 1] = note(f, 2.5, 0.25, 70)
    end

    return notes
end

-- Pop: root-focused, melodic
function bass.pop(chord_name, section_type, bar_in_phrase)
    local root, q = parse_chord(chord_name)
    local t = third(root, q)
    local f = fifth(root)

    return {
        note(root, 0, 1, 95),
        note(f, 1.5, 0.5, 80),
        note(root, 2, 1, 90),
        note(t, 3.5, 0.5, 75),
    }
end

-- Blues: walking approach notes
function bass.blues(chord_name, section_type, bar_in_phrase)
    local root, q = parse_chord(chord_name)
    local t = third(root, q)
    local f = fifth(root)
    local s = seventh(root, q) or (root + INTERVALS.min7)

    return {
        note(root, 0, 0.67, 95),
        note(t, 0.67, 0.67, 85),
        note(f, 1.33, 0.67, 90),
        note(s, 2, 0.67, 85),
        note(f, 2.67, 0.67, 90),
        note(t, 3.33, 0.67, 80),
    }
end

-- Jazz: walking bass
function bass.jazz(chord_name, section_type, bar_in_phrase)
    local root, q = parse_chord(chord_name)
    local t = third(root, q)
    local f = fifth(root)
    local s = seventh(root, q) or (root + INTERVALS.min7)

    -- Classic walking: root, third, fifth, approach note
    local approach = root + 11  -- half step below next root
    return {
        note(root, 0, 0.9, 90),
        note(t, 1, 0.9, 80),
        note(f, 2, 0.9, 85),
        note(approach, 3, 0.9, 75),
    }
end

-- Funk: syncopated, percussive
function bass.funk(chord_name, section_type, bar_in_phrase)
    local root, q = parse_chord(chord_name)
    local f = fifth(root)
    local oct = root + 12

    return {
        note(root, 0, 0.25, 110),
        note(root, 0.75, 0.25, 95),
        note(oct, 1, 0.25, 100),
        note(root, 1.5, 0.5, 90),
        note(f, 2, 0.25, 100),
        note(root, 2.5, 0.25, 85),
        note(root, 3, 0.5, 95),
        note(f, 3.75, 0.25, 80),
    }
end

-- Country: root-fifth alternating
function bass.country(chord_name, section_type, bar_in_phrase)
    local root, _ = parse_chord(chord_name)
    local f = fifth(root)

    return {
        note(root, 0, 0.9, 95),
        note(f, 1, 0.9, 85),
        note(root, 2, 0.9, 90),
        note(f, 3, 0.9, 80),
    }
end

-- Ballad: whole notes, sparse
function bass.ballad(chord_name, section_type, bar_in_phrase)
    local root, _ = parse_chord(chord_name)
    local is_chorus = (section_type == "chorus")

    if is_chorus then
        return {
            note(root, 0, 2, 80),
            note(root + 12, 2, 2, 65),
        }
    end
    return {
        note(root, 0, 3.5, 70),
    }
end

-- Reggae: offbeat push
function bass.reggae(chord_name, section_type, bar_in_phrase)
    local root, q = parse_chord(chord_name)
    local f = fifth(root)

    return {
        note(root, 0.5, 1, 95),
        note(f, 2, 0.5, 85),
        note(root, 2.5, 1, 90),
    }
end

-- Metal: palm-mute 8ths on root
function bass.metal(chord_name, section_type, bar_in_phrase)
    local root, _ = parse_chord(chord_name)
    local notes = {}

    for i = 0, 7 do
        notes[#notes + 1] = note(root, i * 0.5, 0.4, 110)
    end

    return notes
end

-- Latin: syncopated root-fifth
function bass.latin(chord_name, section_type, bar_in_phrase)
    local root, _ = parse_chord(chord_name)
    local f = fifth(root)

    return {
        note(root, 0, 1, 90),
        note(f, 1.5, 0.5, 80),
        note(root, 2, 0.5, 85),
        note(root, 3, 0.5, 80),
        note(f, 3.5, 0.5, 75),
    }
end

--- Get pattern function for a genre.
function bass.get_pattern(genre)
    local patterns = {
        rock = bass.rock, pop = bass.pop, blues = bass.blues,
        jazz = bass.jazz, funk = bass.funk, country = bass.country,
        ballad = bass.ballad, reggae = bass.reggae, metal = bass.metal,
        latin = bass.latin,
    }
    return patterns[genre] or bass.simple
end

return bass
```

**Step 2: Commit**

```bash
git add lua/session_template/lib/backing/bass.lua
git commit -m "feat: add bass line pattern library (10 genres + simple mode)"
```

---

### Task 5: Keys & Guitar Pattern Libraries

**Files:**
- Create: `lua/session_template/lib/backing/keys.lua`
- Create: `lua/session_template/lib/backing/guitar.lua`

**Step 1: Write `keys.lua`**

```lua
-- backing/keys.lua — Piano/organ comping generators

local keys = {}

-- Note name → MIDI pitch (octave 4, middle register)
local ROOT_NOTES = {
    C = 60, ["C#"] = 61, Db = 61, D = 62, ["D#"] = 63, Eb = 63,
    E = 64, F = 65, ["F#"] = 66, Gb = 66, G = 67, ["G#"] = 68,
    Ab = 68, A = 69, ["A#"] = 70, Bb = 70, B = 71,
}

local INTERVALS = {
    min3 = 3, maj3 = 4, p5 = 7, min7 = 10, maj7 = 11,
}

local function note(pitch, start, length, vel)
    return { pitch = pitch, start_beats = start, length_beats = length, velocity = vel or 80 }
end

--- Build chord voicing from root + quality.
local function voicing(chord_name)
    local root_str = chord_name:match("^([A-G][b#]?)")
    local quality = chord_name:match("^[A-G][b#]?(.*)") or ""
    -- Strip slash
    if quality:find("/") then quality = quality:match("(.-)/" ) or quality end
    local root = ROOT_NOTES[root_str] or 60

    local notes = { root }
    -- Third
    if quality:match("m") and not quality:match("maj") then
        notes[#notes + 1] = root + INTERVALS.min3
    else
        notes[#notes + 1] = root + INTERVALS.maj3
    end
    -- Fifth
    notes[#notes + 1] = root + INTERVALS.p5
    -- Seventh
    if quality:match("maj7") then
        notes[#notes + 1] = root + INTERVALS.maj7
    elseif quality:match("7") then
        notes[#notes + 1] = root + INTERVALS.min7
    end

    return notes
end

--- Play a block chord at given position.
local function block_chord(chord_name, start, length, vel)
    local pitches = voicing(chord_name)
    local result = {}
    for _, p in ipairs(pitches) do
        result[#result + 1] = note(p, start, length, vel)
    end
    return result
end

-- ============================================================================
-- Patterns
-- ============================================================================

function keys.simple(chord_name, section_type, bar_in_phrase)
    local notes = {}
    -- Block chords on 1 and 3
    for _, n in ipairs(block_chord(chord_name, 0, 1.5, 80)) do
        notes[#notes + 1] = n
    end
    for _, n in ipairs(block_chord(chord_name, 2, 1.5, 70)) do
        notes[#notes + 1] = n
    end
    return notes
end

function keys.rock(chord_name, section_type, bar_in_phrase)
    -- Power chord style, sparse
    local notes = {}
    for _, n in ipairs(block_chord(chord_name, 0, 1, 85)) do
        notes[#notes + 1] = n
    end
    if section_type == "chorus" then
        for _, n in ipairs(block_chord(chord_name, 2, 1, 75)) do
            notes[#notes + 1] = n
        end
    end
    return notes
end

function keys.pop(chord_name, section_type, bar_in_phrase)
    local notes = {}
    -- Arpeggiated feel
    local pitches = voicing(chord_name)
    for i, p in ipairs(pitches) do
        notes[#notes + 1] = note(p, (i - 1) * 0.5, 1, 75)
    end
    for _, n in ipairs(block_chord(chord_name, 2, 1.5, 70)) do
        notes[#notes + 1] = n
    end
    return notes
end

function keys.blues(chord_name, section_type, bar_in_phrase)
    -- Comping with shuffle feel
    local notes = {}
    for _, n in ipairs(block_chord(chord_name, 0, 0.5, 85)) do
        notes[#notes + 1] = n
    end
    for _, n in ipairs(block_chord(chord_name, 0.67, 0.5, 70)) do
        notes[#notes + 1] = n
    end
    for _, n in ipairs(block_chord(chord_name, 2, 0.5, 80)) do
        notes[#notes + 1] = n
    end
    for _, n in ipairs(block_chord(chord_name, 2.67, 0.5, 70)) do
        notes[#notes + 1] = n
    end
    return notes
end

function keys.jazz(chord_name, section_type, bar_in_phrase)
    -- Voicings with gaps (Freddie Green style)
    local notes = {}
    for _, n in ipairs(block_chord(chord_name, 0, 0.3, 75)) do
        notes[#notes + 1] = n
    end
    for _, n in ipairs(block_chord(chord_name, 1, 0.3, 65)) do
        notes[#notes + 1] = n
    end
    for _, n in ipairs(block_chord(chord_name, 2, 0.3, 70)) do
        notes[#notes + 1] = n
    end
    for _, n in ipairs(block_chord(chord_name, 3, 0.3, 65)) do
        notes[#notes + 1] = n
    end
    return notes
end

function keys.funk(chord_name, section_type, bar_in_phrase)
    -- Clavinet-style stabs
    local notes = {}
    for _, n in ipairs(block_chord(chord_name, 0, 0.2, 95)) do
        notes[#notes + 1] = n
    end
    for _, n in ipairs(block_chord(chord_name, 0.75, 0.2, 80)) do
        notes[#notes + 1] = n
    end
    for _, n in ipairs(block_chord(chord_name, 2, 0.2, 90)) do
        notes[#notes + 1] = n
    end
    for _, n in ipairs(block_chord(chord_name, 2.5, 0.2, 75)) do
        notes[#notes + 1] = n
    end
    for _, n in ipairs(block_chord(chord_name, 3.25, 0.2, 85)) do
        notes[#notes + 1] = n
    end
    return notes
end

function keys.ballad(chord_name, section_type, bar_in_phrase)
    -- Whole note pads
    local notes = {}
    for _, n in ipairs(block_chord(chord_name, 0, 3.5, 60)) do
        notes[#notes + 1] = n
    end
    return notes
end

function keys.get_pattern(genre)
    local patterns = {
        rock = keys.rock, pop = keys.pop, blues = keys.blues,
        jazz = keys.jazz, funk = keys.funk, ballad = keys.ballad,
    }
    return patterns[genre] or keys.simple
end

return keys
```

**Step 2: Write `guitar.lua`**

```lua
-- backing/guitar.lua — Rhythm guitar generators

local guitar = {}

-- Note name → MIDI pitch (octave 3, guitar register)
local ROOT_NOTES = {
    C = 48, ["C#"] = 49, Db = 49, D = 50, ["D#"] = 51, Eb = 51,
    E = 52, F = 53, ["F#"] = 54, Gb = 54, G = 55, ["G#"] = 56,
    Ab = 56, A = 57, ["A#"] = 58, Bb = 58, B = 59,
}

local INTERVALS = { min3 = 3, maj3 = 4, p5 = 7, min7 = 10, maj7 = 11, octave = 12 }

local function note(pitch, start, length, vel)
    return { pitch = pitch, start_beats = start, length_beats = length, velocity = vel or 80 }
end

local function voicing(chord_name)
    local root_str = chord_name:match("^([A-G][b#]?)")
    local quality = chord_name:match("^[A-G][b#]?(.*)") or ""
    if quality:find("/") then quality = quality:match("(.-)/" ) or quality end
    local root = ROOT_NOTES[root_str] or 48

    local notes = { root }
    if quality:match("m") and not quality:match("maj") then
        notes[#notes + 1] = root + INTERVALS.min3
    else
        notes[#notes + 1] = root + INTERVALS.maj3
    end
    notes[#notes + 1] = root + INTERVALS.p5
    notes[#notes + 1] = root + INTERVALS.octave
    return notes
end

local function strum(chord_name, start, length, vel, direction)
    local pitches = voicing(chord_name)
    local result = {}
    local strum_offset = 0.02  -- slight strum delay between strings
    if direction == "up" then
        for i = #pitches, 1, -1 do
            result[#result + 1] = note(pitches[i], start + (4 - i) * strum_offset, length, vel)
        end
    else
        for i, p in ipairs(pitches) do
            result[#result + 1] = note(p, start + (i - 1) * strum_offset, length, vel)
        end
    end
    return result
end

-- ============================================================================
-- Patterns
-- ============================================================================

function guitar.simple(chord_name, section_type, bar_in_phrase)
    local notes = {}
    -- Down strums on each beat
    for beat = 0, 3 do
        for _, n in ipairs(strum(chord_name, beat, 0.8, 75, "down")) do
            notes[#notes + 1] = n
        end
    end
    return notes
end

function guitar.rock(chord_name, section_type, bar_in_phrase)
    local notes = {}
    -- Down-up 8th strumming
    for i = 0, 7 do
        local dir = (i % 2 == 0) and "down" or "up"
        local vel = (i % 2 == 0) and 85 or 65
        for _, n in ipairs(strum(chord_name, i * 0.5, 0.4, vel, dir)) do
            notes[#notes + 1] = n
        end
    end
    return notes
end

function guitar.pop(chord_name, section_type, bar_in_phrase)
    -- Arpeggiated picking
    local pitches = voicing(chord_name)
    local notes = {}
    local pattern = {1, 3, 2, 4, 1, 3, 2, 4}  -- picking pattern
    for i, idx in ipairs(pattern) do
        if pitches[idx] then
            notes[#notes + 1] = note(pitches[idx], (i - 1) * 0.5, 0.5, 70)
        end
    end
    return notes
end

function guitar.blues(chord_name, section_type, bar_in_phrase)
    -- Shuffle strum
    local notes = {}
    local positions = {0, 0.67, 1, 1.67, 2, 2.67, 3, 3.67}
    for i, pos in ipairs(positions) do
        local dir = (i % 2 == 1) and "down" or "up"
        local vel = (i % 2 == 1) and 80 or 60
        for _, n in ipairs(strum(chord_name, pos, 0.3, vel, dir)) do
            notes[#notes + 1] = n
        end
    end
    return notes
end

function guitar.funk(chord_name, section_type, bar_in_phrase)
    -- Muted 16th strumming with accents
    local notes = {}
    local accents = {true, false, false, true, false, true, false, false,
                     true, false, false, true, false, false, true, false}
    for i = 0, 15 do
        if accents[i + 1] then
            for _, n in ipairs(strum(chord_name, i * 0.25, 0.2, 90, "down")) do
                notes[#notes + 1] = n
            end
        end
    end
    return notes
end

function guitar.country(chord_name, section_type, bar_in_phrase)
    -- Boom-chicka pattern
    local root_str = chord_name:match("^([A-G][b#]?)")
    local root = ROOT_NOTES[root_str] or 48
    local notes = {}

    -- Bass note on 1 and 3
    notes[#notes + 1] = note(root, 0, 0.5, 90)
    notes[#notes + 1] = note(root + 7, 2, 0.5, 80)
    -- Strum on 2 and 4
    for _, n in ipairs(strum(chord_name, 1, 0.4, 70, "down")) do
        notes[#notes + 1] = n
    end
    for _, n in ipairs(strum(chord_name, 3, 0.4, 65, "down")) do
        notes[#notes + 1] = n
    end
    -- Upstrum on and-of-2, and-of-4
    for _, n in ipairs(strum(chord_name, 1.5, 0.3, 55, "up")) do
        notes[#notes + 1] = n
    end
    for _, n in ipairs(strum(chord_name, 3.5, 0.3, 50, "up")) do
        notes[#notes + 1] = n
    end

    return notes
end

function guitar.reggae(chord_name, section_type, bar_in_phrase)
    -- Offbeat skank
    local notes = {}
    for i = 0, 3 do
        for _, n in ipairs(strum(chord_name, i + 0.5, 0.3, 80, "down")) do
            notes[#notes + 1] = n
        end
    end
    return notes
end

function guitar.ballad(chord_name, section_type, bar_in_phrase)
    -- Gentle arpeggios
    local pitches = voicing(chord_name)
    local notes = {}
    for i, p in ipairs(pitches) do
        notes[#notes + 1] = note(p, (i - 1) * 0.75, 1.5, 55)
    end
    return notes
end

function guitar.get_pattern(genre)
    local patterns = {
        rock = guitar.rock, pop = guitar.pop, blues = guitar.blues,
        funk = guitar.funk, country = guitar.country, reggae = guitar.reggae,
        ballad = guitar.ballad,
    }
    return patterns[genre] or guitar.simple
end

return guitar
```

**Step 3: Commit**

```bash
git add lua/session_template/lib/backing/keys.lua lua/session_template/lib/backing/guitar.lua
git commit -m "feat: add keys and rhythm guitar pattern libraries"
```

---

### Task 6: Lua Generator Orchestrator

**Files:**
- Create: `lua/session_template/lib/backing/generators.lua`

**Step 1: Write the orchestrator**

```lua
-- backing/generators.lua — Orchestrator
--
-- Takes a SongChart (JSON-decoded table) and generates MIDI notes
-- for each requested instrument. Creates tracks, inserts notes.

local generators = {}

local tracks = require("tracks")
local fx = require("fx")
local utils = require("utils")
local config = require("config")

-- Lazy-load instrument modules
local function get_module(instrument)
    if instrument == "drums" then return require("backing.drums") end
    if instrument == "bass" then return require("backing.bass") end
    if instrument == "keys" then return require("backing.keys") end
    if instrument == "guitar" then return require("backing.guitar") end
    return nil
end

-- Instrument config: VSTi, color, MIDI channel
local INSTRUMENT_CONFIG = {
    drums = {
        name_prefix = "BT - Drums",
        preferred = "Addictive Drums 2",
        fallback = "MT-PowerDrumKit",
        color = config.colors.purple or {128, 0, 255},
        midi_channel = 9,  -- GM drums (0-indexed = ch 10)
    },
    bass = {
        name_prefix = "BT - Bass",
        preferred = "Kontakt",
        fallback = "ReaSynth",
        color = config.colors.red or {255, 0, 0},
        midi_channel = 0,
    },
    keys = {
        name_prefix = "BT - Keys",
        preferred = "Analog Lab V",
        fallback = "ReaSynth",
        color = config.colors.blue or {0, 128, 255},
        midi_channel = 1,
    },
    guitar = {
        name_prefix = "BT - Rhythm Guitar",
        preferred = "Ample Guitar",
        fallback = "ReaSynth",
        color = config.colors.orange or {255, 128, 0},
        midi_channel = 3,
    },
}

--- Convert beat position to PPQ (pulses per quarter note).
local function beats_to_ppq(beats)
    -- REAPER default: 960 PPQ per quarter note
    return math.floor(beats * 960)
end

--- Insert MIDI notes into a take.
local function insert_notes(take, notes, bar_offset_beats, channel)
    for _, n in ipairs(notes) do
        local start_ppq = beats_to_ppq(bar_offset_beats + n.start_beats)
        local end_ppq = start_ppq + beats_to_ppq(n.length_beats)
        reaper.MIDI_InsertNote(
            take,
            false,        -- selected
            false,        -- muted
            start_ppq,    -- startppqpos
            end_ppq,      -- endppqpos
            channel,      -- channel
            n.pitch,      -- pitch
            n.velocity,   -- velocity
            false         -- noSort
        )
    end
end

--- Generate all notes for one instrument across the full song chart.
-- Returns a flat list of {pitch, start_beats, length_beats, velocity}.
function generators.generate_instrument(instrument, chart, style)
    local mod = get_module(instrument)
    if not mod then return nil, "Unknown instrument: " .. tostring(instrument) end

    local genre = style
    if style == "simple" then
        genre = nil  -- force simple pattern
    end

    local pattern_fn = genre and mod.get_pattern(genre) or mod.simple
    local all_notes = {}
    local beat_cursor = 0

    for _, section in ipairs(chart.sections) do
        local bars = section.bars or #section.chords
        local chords = section.chords or {}

        for bar = 0, bars - 1 do
            -- Which chord is active for this bar?
            local chord_idx = (bar % #chords) + 1
            local chord_name = chords[chord_idx] or "C"

            -- Generate one bar of notes
            local bar_notes
            if instrument == "drums" then
                bar_notes = pattern_fn(section.name, bar)
            else
                bar_notes = pattern_fn(chord_name, section.name, bar)
            end

            -- Offset to absolute position
            for _, n in ipairs(bar_notes) do
                all_notes[#all_notes + 1] = {
                    pitch = n.pitch,
                    start_beats = beat_cursor + n.start_beats,
                    length_beats = n.length_beats,
                    velocity = n.velocity,
                }
            end

            beat_cursor = beat_cursor + 4  -- 4 beats per bar (4/4 assumed)
        end
    end

    return all_notes
end

--- Create tracks and insert MIDI for a full backing track.
-- @param chart table The SongChart (decoded from JSON)
-- @param instruments table Array of instrument names {"drums", "bass", ...}
-- @param style string "simple", or a genre name like "rock", "jazz"
-- @return table {ok=true, tracks_created=N, notes_inserted=N}
function generators.build(chart, instruments, style)
    instruments = instruments or {"drums", "bass"}
    style = style or "rock"

    -- Calculate total song length in beats
    local total_beats = 0
    for _, section in ipairs(chart.sections) do
        total_beats = total_beats + (section.bars or #section.chords) * 4
    end
    local total_seconds = total_beats / (chart.bpm or 120) * 60

    -- Set project tempo
    reaper.SetCurrentBPM(0, chart.bpm or 120, true)

    -- Create folder track
    local folder = tracks.create_folder({
        name = "Backing Track",
        color = config.colors.grey or {128, 128, 128},
    })

    local tracks_created = 0
    local notes_inserted = 0

    for _, instrument in ipairs(instruments) do
        local inst_config = INSTRUMENT_CONFIG[instrument]
        if not inst_config then goto continue end

        -- Generate notes
        local all_notes, err = generators.generate_instrument(instrument, chart, style)
        if not all_notes then
            utils.log("WARN: " .. (err or "generation failed for " .. instrument))
            goto continue
        end

        -- Create track
        local track = tracks.create({
            name = inst_config.name_prefix,
            color = inst_config.color,
        })
        tracks_created = tracks_created + 1

        -- Add VSTi
        fx.smart_add(track, inst_config.preferred, inst_config.fallback)

        -- Create MIDI item spanning the full song
        local item_idx = reaper.GetMediaTrackInfo_Value(track, "IP_TRACKNUMBER") - 1
        local item = reaper.CreateNewMIDIItemInProj(track, 0, total_seconds, false)
        if item then
            local take = reaper.GetActiveTake(item)
            if take then
                insert_notes(take, all_notes, 0, inst_config.midi_channel)
                reaper.MIDI_Sort(take)
                notes_inserted = notes_inserted + #all_notes
            end
        end

        ::continue::
    end

    -- Close folder
    tracks.close_folder()

    -- Create backing track bus
    local bus = tracks.create_bus({
        name = "BT - Bus",
        color = config.colors.grey or {128, 128, 128},
    })
    -- Add limiter on bus
    fx.smart_add(bus, "ReaLimit", "ReaComp")

    return {
        ok = true,
        tracks_created = tracks_created,
        notes_inserted = notes_inserted,
        total_bars = total_beats / 4,
        total_seconds = total_seconds,
    }
end

return generators
```

**Step 2: Commit**

```bash
git add lua/session_template/lib/backing/generators.lua
git commit -m "feat: add backing track generator orchestrator"
```

---

## Phase 3: MCP Integration

### Task 7: Bridge Functions

**Files:**
- Modify: `lua/mcp_bridge.lua` (add `GenerateBackingTrack` and `RegeneratePart` to DSL_FUNCTIONS)

**Step 1: Add bridge functions**

Add before the DSL_FUNCTIONS table (around line 850):

```lua
-- ============================================================================
-- Backing Track Generation
-- ============================================================================

local function GenerateBackingTrack(chart_json, instruments, style)
    local old_path = package.path
    package.path = session_template_path .. "lib/?.lua;" .. session_template_path .. "lib/backing/?.lua;" .. package.path

    local ok_gen, generators_mod = pcall(require, "generators")
    package.path = old_path

    if not ok_gen then
        return {ok = false, error = "Failed to load generators: " .. tostring(generators_mod)}
    end

    -- Decode chart from JSON string if needed
    local chart = chart_json
    if type(chart_json) == "string" then
        -- Simple JSON decode (use cjson if available, else minimal parser)
        local ok_json, decoded = pcall(function()
            return load("return " .. chart_json:gsub("%[", "{"):gsub("%]", "}"):gsub(":", "="):gsub('"(%w+)"=', "%1="))()
        end)
        if ok_json and decoded then
            chart = decoded
        else
            return {ok = false, error = "Failed to parse chart JSON"}
        end
    end

    reaper.Undo_BeginBlock()
    reaper.PreventUIRefresh(1)

    local ok_build, result = pcall(generators_mod.build, chart, instruments, style)

    reaper.PreventUIRefresh(-1)
    reaper.Undo_EndBlock("Generate Backing Track", -1)
    reaper.TrackList_AdjustWindows(false)
    reaper.UpdateArrange()

    if not ok_build then
        return {ok = false, error = "Generation failed: " .. tostring(result)}
    end

    return {ok = true, ret = result}
end
```

Add to DSL_FUNCTIONS table:

```lua
    -- Backing Tracks
    GenerateBackingTrack = GenerateBackingTrack,
```

**Step 2: Commit**

```bash
git add lua/mcp_bridge.lua
git commit -m "feat: add GenerateBackingTrack bridge function"
```

---

### Task 8: Python MCP Tools

**Files:**
- Create: `server/tools/backing_tracks.py`
- Create: `tests/test_backing_tracks.py`

**Step 1: Write the failing test**

```python
# tests/test_backing_tracks.py
"""Tests for Backing Track generation tools (no REAPER required)."""

import pytest
from unittest.mock import MagicMock


class TestBackingTrackToolRegistration:
    """Test that backing track tools register correctly."""

    def test_register_backing_track_tools(self):
        from server.tools.backing_tracks import register_backing_track_tools
        mock_mcp = MagicMock()
        mock_mcp.tool.return_value = lambda f: f

        count = register_backing_track_tools(mock_mcp)
        assert count == 5  # generate, regenerate, list_genres, get_chart, manual_chart


class TestGenreList:
    """Test genre listing."""

    def test_available_genres(self):
        from server.tools.backing_tracks import AVAILABLE_GENRES
        expected = {"rock", "pop", "blues", "jazz", "funk", "country",
                    "ballad", "reggae", "latin", "metal"}
        assert set(AVAILABLE_GENRES) == expected


class TestInstrumentValidation:
    """Test instrument validation."""

    def test_valid_instruments(self):
        from server.tools.backing_tracks import VALID_INSTRUMENTS
        expected = {"drums", "bass", "keys", "guitar"}
        assert set(VALID_INSTRUMENTS) == expected
```

**Step 2: Run test to verify it fails**

Run: `.venv-session/bin/python3 -m pytest tests/test_backing_tracks.py -v`
Expected: FAIL

**Step 3: Write implementation**

```python
# server/tools/backing_tracks.py
"""
Backing Track Tools for REAPER MCP

Tools for generating MIDI backing tracks from song chord charts.
Supports scraping from Ultimate Guitar, manual chord input, and
genre-aware pattern generation.
"""

import json
from typing import Optional
from ..bridge import bridge


AVAILABLE_GENRES = [
    "rock", "pop", "blues", "jazz", "funk",
    "country", "ballad", "reggae", "latin", "metal",
]

VALID_INSTRUMENTS = ["drums", "bass", "keys", "guitar"]


async def generate_backing_track(
    song: str,
    artist: str,
    instruments: str = "drums,bass",
    style: str = "genre",
    genre_override: str = "",
    bpm_override: int = 0,
) -> str:
    """Generate a MIDI backing track for a song.

    Scrapes chord data from Ultimate Guitar, generates MIDI parts
    for each instrument, and inserts them into REAPER as tracks with VSTi.

    Args:
        song: Song title (e.g. "Hotel California")
        artist: Artist name (e.g. "Eagles")
        instruments: Comma-separated instruments: drums, bass, keys, guitar (default: "drums,bass")
        style: Generation style: "simple", "genre", or a specific genre name (default: "genre")
        genre_override: Force a specific genre (e.g. "rock", "jazz") instead of auto-detect
        bpm_override: Override the scraped BPM (0 = use scraped value)
    """
    from ..song_lookup import lookup_song, estimate_tempo

    # Validate instruments
    inst_list = [i.strip() for i in instruments.split(",")]
    invalid = [i for i in inst_list if i not in VALID_INSTRUMENTS]
    if invalid:
        return f"Invalid instruments: {invalid}. Valid: {VALID_INSTRUMENTS}"

    # Lookup song
    chart = lookup_song(song, artist, bpm=bpm_override, genre=genre_override)
    if not chart:
        return (
            f"Could not find chords for '{song}' by '{artist}'.\n"
            f"Try manual_chart() to provide chords directly."
        )

    # Override BPM if specified
    if bpm_override:
        chart["bpm"] = bpm_override

    # Determine style
    actual_style = genre_override or style
    if actual_style == "genre" and not genre_override:
        actual_style = "rock"  # default genre

    # Send to REAPER
    result = await bridge.call_lua("GenerateBackingTrack", [
        json.dumps(chart), inst_list, actual_style
    ])

    if result.get("ok"):
        ret = result.get("ret", {})
        return (
            f"Backing track generated for '{song}' by '{artist}':\n"
            f"  Tracks: {ret.get('tracks_created', 0)}\n"
            f"  Notes: {ret.get('notes_inserted', 0)}\n"
            f"  Bars: {ret.get('total_bars', 0)}\n"
            f"  Style: {actual_style}\n"
            f"  Instruments: {', '.join(inst_list)}"
        )
    else:
        return f"Generation failed: {result.get('error', 'Unknown error')}"


async def regenerate_part(
    instrument: str,
    style: str = "genre",
) -> str:
    """Regenerate a single instrument part of the current backing track.

    Args:
        instrument: Which instrument to regenerate: drums, bass, keys, or guitar
        style: Generation style or genre name
    """
    if instrument not in VALID_INSTRUMENTS:
        return f"Invalid instrument: '{instrument}'. Valid: {VALID_INSTRUMENTS}"

    # TODO: Phase 2 — requires storing current chart in session state
    return f"regenerate_part is not yet implemented (Phase 2). Re-run generate_backing_track with different style."


async def list_backing_genres() -> str:
    """List all available genre patterns for backing track generation."""
    lines = ["Available genres for backing track generation:", ""]
    genre_descriptions = {
        "rock": "Driving 8ths, strong kick/snare, root-fifth bass",
        "pop": "Light groove, ghost notes, melodic bass, arpeggiated keys",
        "blues": "Shuffle feel, walking bass, comping keys",
        "jazz": "Swing ride, walking bass, voiced chords",
        "funk": "Syncopated 16ths, ghost notes, slap bass, clavinet stabs",
        "country": "Train beat, alternating bass, boom-chicka guitar",
        "ballad": "Sparse, gentle, whole-note pads",
        "reggae": "One-drop, offbeat skank guitar, push bass",
        "latin": "Bossa nova, cross-stick, syncopated bass",
        "metal": "Double kick, aggressive, palm-mute bass 8ths",
    }
    for genre in sorted(AVAILABLE_GENRES):
        desc = genre_descriptions.get(genre, "")
        lines.append(f"  {genre}: {desc}")
    return "\n".join(lines)


async def get_song_chart(
    song: str,
    artist: str,
) -> str:
    """Fetch and parse a chord chart without generating a backing track.

    Useful for previewing what chords were found before generating.

    Args:
        song: Song title
        artist: Artist name
    """
    from ..song_lookup import lookup_song

    chart = lookup_song(song, artist)
    if not chart:
        return f"Could not find chords for '{song}' by '{artist}'."

    lines = [
        f"Song: {chart['title']} by {chart['artist']}",
        f"Key: {chart['key']}  BPM: {chart['bpm']}  Time: {chart['time_sig']}",
        "",
    ]
    for section in chart["sections"]:
        lines.append(f"[{section['name'].title()}] ({section['bars']} bars)")
        lines.append(f"  {' '.join(section['chords'])}")
        lines.append("")

    return "\n".join(lines)


async def manual_chart(
    chord_text: str,
    title: str = "Manual Chart",
    artist: str = "",
    bpm: int = 120,
    key: str = "",
    instruments: str = "drums,bass",
    style: str = "rock",
) -> str:
    """Generate a backing track from a manually provided chord chart.

    Use this when automatic lookup fails. Provide chords in section format:
    [Verse]
    Am G F E

    [Chorus]
    C G Am F

    Args:
        chord_text: Chord chart text with [Section] headers and chord lines
        title: Song title for the project
        artist: Artist name (optional)
        bpm: Tempo in BPM
        key: Musical key (auto-detected if empty)
        instruments: Comma-separated instruments (default: "drums,bass")
        style: Genre name or "simple" (default: "rock")
    """
    from ..song_lookup import parse_chord_chart

    chart = parse_chord_chart(chord_text, title=title, artist=artist, bpm=bpm, key=key)

    if not chart["sections"]:
        return "No chord sections found. Use [Section] headers and chord lines."

    inst_list = [i.strip() for i in instruments.split(",")]
    invalid = [i for i in inst_list if i not in VALID_INSTRUMENTS]
    if invalid:
        return f"Invalid instruments: {invalid}. Valid: {VALID_INSTRUMENTS}"

    import json
    result = await bridge.call_lua("GenerateBackingTrack", [
        json.dumps(chart), inst_list, style
    ])

    if result.get("ok"):
        ret = result.get("ret", {})
        return (
            f"Backing track generated from manual chart:\n"
            f"  Tracks: {ret.get('tracks_created', 0)}\n"
            f"  Notes: {ret.get('notes_inserted', 0)}\n"
            f"  Style: {style}\n"
            f"  Instruments: {', '.join(inst_list)}"
        )
    else:
        return f"Generation failed: {result.get('error', 'Unknown error')}"


def register_backing_track_tools(mcp) -> int:
    """Register all backing track tools with the MCP instance."""
    tools = [
        (generate_backing_track, "Generate a MIDI backing track for a song by scraping chords"),
        (regenerate_part, "Regenerate a single instrument part"),
        (list_backing_genres, "List all available genre patterns"),
        (get_song_chart, "Fetch and display a chord chart without generating"),
        (manual_chart, "Generate a backing track from a manually provided chord chart"),
    ]

    for func, desc in tools:
        mcp.tool()(func)

    return len(tools)
```

**Step 4: Run test to verify it passes**

Run: `.venv-session/bin/python3 -m pytest tests/test_backing_tracks.py -v`
Expected: All PASS

**Step 5: Commit**

```bash
git add server/tools/backing_tracks.py tests/test_backing_tracks.py
git commit -m "feat: add backing track MCP tools with tests"
```

---

### Task 9: Register in app.py + tool_profiles.py

**Files:**
- Modify: `server/app.py` (~line 84 for import, ~line 135 for registry)
- Modify: `server/tool_profiles.py` (add "backing-track" profile)

**Step 1: Add import to `server/app.py`**

Near line 84, add:
```python
from .tools.backing_tracks import register_backing_track_tools
```

**Step 2: Add to CATEGORY_REGISTRY**

Near line 135 (after Session Templates):
```python
    "Backing Tracks": register_backing_track_tools,
```

**Step 3: Add profile to `server/tool_profiles.py`**

Add to TOOL_PROFILES dict:
```python
    "backing-track": {
        "name": "Backing Track Generation",
        "description": "Generate MIDI backing tracks from song chord charts",
        "categories": [
            "Backing Tracks",
            "MIDI",
            "Tracks",
            "FX",
            "Transport",
            "Project",
        ],
    },
```

**Step 4: Verify MCP server starts**

Run: `.venv-session/bin/python3 -c "from server.tools.backing_tracks import register_backing_track_tools; print('OK')"`
Expected: `OK`

**Step 5: Commit**

```bash
git add server/app.py server/tool_profiles.py
git commit -m "feat: register backing track tools in MCP server"
```

---

### Task 10: DSL Wrappers for Natural Language

**Files:**
- Create: `server/dsl/backing_wrappers.py`
- Modify: `server/tools/backing_tracks.py` (call register from here)

**Step 1: Write DSL wrappers**

```python
# server/dsl/backing_wrappers.py
"""
Backing Track DSL Wrappers — Natural language backing track generation.

Maps descriptions like "make a backing track for Wonderwall" to
the generate_backing_track tool.
"""

import re
from ..bridge import bridge


# Pattern: "backing track for <song> by <artist>"
BACKING_TRACK_RE = re.compile(
    r'(?:backing\s+track|jam\s+track|play\s+along|accompaniment)\s+'
    r'(?:for|of|to)\s+'
    r'["\']?(.+?)["\']?\s+'
    r'(?:by|from)\s+'
    r'["\']?(.+?)["\']?\s*$',
    re.IGNORECASE,
)


def parse_backing_request(description: str) -> dict | None:
    """Parse a natural language backing track request.

    Returns {song, artist} or None.
    """
    match = BACKING_TRACK_RE.match(description.strip())
    if match:
        return {"song": match.group(1).strip(), "artist": match.group(2).strip()}

    # Simpler pattern: just "song by artist"
    simple = re.match(
        r'["\']?(.+?)["\']?\s+(?:by|from)\s+["\']?(.+?)["\']?\s*$',
        description.strip(),
        re.IGNORECASE,
    )
    if simple:
        return {"song": simple.group(1).strip(), "artist": simple.group(2).strip()}

    return None


async def make_backing_track(
    description: str,
    instruments: str = "drums,bass",
    style: str = "genre",
) -> str:
    """Generate a backing track from a natural language description.

    Examples:
        "backing track for Hotel California by Eagles"
        "jam track for Wonderwall by Oasis"
        "Billie Jean by Michael Jackson"

    Args:
        description: Natural language description containing song and artist
        instruments: Comma-separated instruments (default: "drums,bass")
        style: Generation style or genre name (default: "genre")
    """
    parsed = parse_backing_request(description)
    if not parsed:
        return (
            "Could not parse song/artist from description.\n"
            "Try: 'backing track for <song> by <artist>'\n"
            "Or use generate_backing_track(song, artist) directly."
        )

    from ..tools.backing_tracks import generate_backing_track
    return await generate_backing_track(
        song=parsed["song"],
        artist=parsed["artist"],
        instruments=instruments,
        style=style,
    )


def register_backing_dsl_tools(mcp) -> int:
    """Register backing track DSL tools."""
    tools = [
        (make_backing_track, "Generate a backing track from natural language"),
    ]
    for func, desc in tools:
        mcp.tool()(func)
    return len(tools)
```

**Step 2: Wire into registration**

In `server/tools/backing_tracks.py`, modify `register_backing_track_tools` to also register DSL:

```python
def register_backing_track_tools(mcp) -> int:
    """Register all backing track tools with the MCP instance."""
    from ..dsl.backing_wrappers import register_backing_dsl_tools

    tools = [
        (generate_backing_track, "Generate a MIDI backing track for a song by scraping chords"),
        (regenerate_part, "Regenerate a single instrument part"),
        (list_backing_genres, "List all available genre patterns"),
        (get_song_chart, "Fetch and display a chord chart without generating"),
        (manual_chart, "Generate a backing track from a manually provided chord chart"),
    ]

    for func, desc in tools:
        mcp.tool()(func)

    dsl_count = register_backing_dsl_tools(mcp)

    return len(tools) + dsl_count
```

**Step 3: Write test for DSL parsing**

Add to `tests/test_backing_tracks.py`:

```python
class TestDSLParsing:
    """Test natural language parsing."""

    def test_parse_backing_track_request(self):
        from server.dsl.backing_wrappers import parse_backing_request
        result = parse_backing_request("backing track for Hotel California by Eagles")
        assert result == {"song": "Hotel California", "artist": "Eagles"}

    def test_parse_jam_track(self):
        from server.dsl.backing_wrappers import parse_backing_request
        result = parse_backing_request("jam track for Wonderwall by Oasis")
        assert result == {"song": "Wonderwall", "artist": "Oasis"}

    def test_parse_simple_format(self):
        from server.dsl.backing_wrappers import parse_backing_request
        result = parse_backing_request("Billie Jean by Michael Jackson")
        assert result == {"song": "Billie Jean", "artist": "Michael Jackson"}

    def test_parse_with_quotes(self):
        from server.dsl.backing_wrappers import parse_backing_request
        result = parse_backing_request('backing track for "Stairway to Heaven" by "Led Zeppelin"')
        assert result == {"song": "Stairway to Heaven", "artist": "Led Zeppelin"}

    def test_parse_unknown_returns_none(self):
        from server.dsl.backing_wrappers import parse_backing_request
        assert parse_backing_request("make a sandwich") is None

    def test_registration_count_includes_dsl(self):
        from server.tools.backing_tracks import register_backing_track_tools
        mock_mcp = MagicMock()
        mock_mcp.tool.return_value = lambda f: f
        count = register_backing_track_tools(mock_mcp)
        assert count == 6  # 5 direct + 1 DSL
```

**Step 4: Run all tests**

Run: `.venv-session/bin/python3 -m pytest tests/test_backing_tracks.py tests/test_song_lookup.py -v`
Expected: All PASS

**Step 5: Commit**

```bash
git add server/dsl/backing_wrappers.py server/tools/backing_tracks.py tests/test_backing_tracks.py
git commit -m "feat: add natural language DSL wrappers for backing track generation"
```

---

### Task 11: Install Dependencies + VSTi Config

**Files:**
- Modify: `server/session_config.py` (add VSTi entries for backing track instruments)
- Check: `requirements.txt` or `pyproject.toml` for requests + beautifulsoup4

**Step 1: Check if requests/bs4 are already dependencies**

Run: `.venv-session/bin/pip list | grep -i -E "requests|beautifulsoup"`

If not present:
Run: `.venv-session/bin/pip install requests beautifulsoup4`

**Step 2: Add VSTi plugin entries to `server/session_config.py`**

In the `"plugins"` dict, add:

```python
        # Backing Track VSTi
        "drums_vsti": {"preferred": "Addictive Drums 2", "fallback": "MT-PowerDrumKit"},
        "bass_vsti": {"preferred": "Kontakt", "fallback": "ReaSynth"},
        "keys_vsti": {"preferred": "Analog Lab V", "fallback": "ReaSynth"},
        "guitar_vsti": {"preferred": "Ample Guitar", "fallback": "ReaSynth"},
```

**Step 3: Commit**

```bash
git add server/session_config.py
git commit -m "feat: add backing track VSTi entries to session config"
```

---

## Phase 4: Integration & Polish

### Task 12: Full Integration Test

**Files:**
- Modify: `tests/test_backing_tracks.py`

**Step 1: Add integration test (mocked bridge)**

```python
class TestFullPipeline:
    """Test the full pipeline with mocked bridge."""

    @pytest.mark.asyncio
    async def test_manual_chart_pipeline(self):
        from server.tools.backing_tracks import manual_chart
        from unittest.mock import patch, AsyncMock

        mock_result = {"ok": True, "ret": {
            "tracks_created": 2, "notes_inserted": 100,
            "total_bars": 8, "total_seconds": 16.0
        }}
        with patch("server.tools.backing_tracks.bridge") as mock_bridge:
            mock_bridge.call_lua = AsyncMock(return_value=mock_result)
            result = await manual_chart(
                chord_text="[Verse]\nAm G F E\n[Chorus]\nC G Am F\n",
                title="Test Song",
                bpm=120,
                style="rock",
            )
            assert "Backing track generated" in result
            assert "rock" in result
            mock_bridge.call_lua.assert_called_once()
            call_args = mock_bridge.call_lua.call_args[0]
            assert call_args[0] == "GenerateBackingTrack"

    @pytest.mark.asyncio
    async def test_generate_with_lookup_failure(self):
        from server.tools.backing_tracks import generate_backing_track
        from unittest.mock import patch

        with patch("server.tools.backing_tracks.lookup_song", return_value=None):
            result = await generate_backing_track("Nonexistent", "Nobody")
            assert "Could not find" in result

    @pytest.mark.asyncio
    async def test_invalid_instruments_rejected(self):
        from server.tools.backing_tracks import generate_backing_track
        from unittest.mock import patch

        with patch("server.tools.backing_tracks.lookup_song"):
            result = await generate_backing_track("Test", "Test", instruments="drums,tuba")
            assert "Invalid instruments" in result
```

**Step 2: Run all tests**

Run: `.venv-session/bin/python3 -m pytest tests/test_backing_tracks.py tests/test_song_lookup.py -v`
Expected: All PASS

**Step 3: Commit**

```bash
git add tests/test_backing_tracks.py
git commit -m "test: add integration tests for backing track pipeline"
```

---

### Task 13: Push Phase + Final Verification

**Step 1: Run all project tests**

Run: `.venv-session/bin/python3 -m pytest tests/test_session_templates.py tests/test_song_lookup.py tests/test_backing_tracks.py -v`
Expected: All PASS

**Step 2: Verify server import**

Run: `.venv-session/bin/python3 -c "from server.tools.backing_tracks import register_backing_track_tools; from server.song_lookup import parse_chord_chart, lookup_song; print('All imports OK')"`
Expected: `All imports OK`

**Step 3: Push to GitHub**

```bash
git push -u origin feature/backing-track-generator
```

**Step 4: Use superpowers:finishing-a-development-branch to complete**

---

## Summary

| Phase | Tasks | What it delivers |
|-------|-------|-----------------|
| 1: Scraping | 1-2 | Chord chart parser + UG scraper |
| 2: Patterns | 3-6 | Lua pattern libraries (drums, bass, keys, guitar) + orchestrator |
| 3: MCP | 7-11 | Bridge functions, MCP tools, DSL wrappers, config |
| 4: Polish | 12-13 | Integration tests, verification, push |

**13 tasks total.** Phase 1 deliverable: chord parsing works. Phase 2: Lua generators ready. Phase 3: full MCP integration. Phase 4: tested and pushed.
