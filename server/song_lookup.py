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
