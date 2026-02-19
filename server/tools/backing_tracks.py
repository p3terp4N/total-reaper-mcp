"""
Backing Track Tools for REAPER MCP

Tools for generating MIDI backing tracks from song chord charts.
Looks up chords online, parses them, and sends to REAPER via the bridge
for MIDI generation on instrument tracks (drums, bass, keys, guitar).
"""

from typing import Optional
from ..bridge import bridge
from ..song_lookup import lookup_song, parse_chord_chart


# ============================================================================
# Constants
# ============================================================================

AVAILABLE_GENRES = [
    "blues",
    "country",
    "funk",
    "jazz",
    "latin",
    "metal",
    "pop",
    "r&b",
    "reggae",
    "rock",
]

VALID_INSTRUMENTS = ["drums", "bass", "keys", "guitar"]

GENRE_DESCRIPTIONS = {
    "blues": "12-bar shuffle, swing feel, pentatonic bass lines",
    "country": "Two-beat feel, walking bass, train beat drums",
    "funk": "Syncopated 16th-note grooves, slap bass, tight hi-hats",
    "jazz": "Swing ride, walking bass, comping chords, brushes option",
    "latin": "Bossa nova / samba patterns, syncopated percussion",
    "metal": "Double kick, palm-muted power chords, aggressive bass",
    "pop": "Four-on-the-floor kick, simple bass, bright keys",
    "r&b": "Neo-soul grooves, ghost notes, smooth bass lines",
    "reggae": "One-drop drums, offbeat skank, dub bass",
    "rock": "Straight 8th-note feel, driving bass, power chords",
}


# ============================================================================
# Backing Track Tools
# ============================================================================

async def generate_backing_track(
    song: str,
    artist: str,
    instruments: str = "drums,bass",
    style: str = "genre",
    genre_override: str = "",
    bpm_override: int = 0,
) -> str:
    """Generate a MIDI backing track for a song.

    Looks up the chord chart online, parses it, then generates
    MIDI backing tracks in REAPER for the requested instruments.

    Args:
        song: Song title to look up
        artist: Artist name
        instruments: Comma-separated instruments (drums, bass, keys, guitar)
        style: Style approach — "genre" (match song genre) or a specific genre name
        genre_override: Force a specific genre instead of auto-detecting
        bpm_override: Force a specific BPM instead of using the chart's BPM
    """
    # Validate instruments
    inst_list = [i.strip().lower() for i in instruments.split(",")]
    invalid = [i for i in inst_list if i not in VALID_INSTRUMENTS]
    if invalid:
        return (
            f"Invalid instruments: {', '.join(invalid)}. "
            f"Valid options: {', '.join(VALID_INSTRUMENTS)}"
        )

    # Look up the song chart
    genre = genre_override or style if style != "genre" else ""
    chart = lookup_song(song, artist, bpm=bpm_override, genre=genre)
    if chart is None:
        return (
            f"Could not find chord chart for '{song}' by {artist}. "
            "Try manual_chart() to paste chords directly."
        )

    # Apply overrides
    if bpm_override:
        chart["bpm"] = bpm_override
    if genre_override:
        chart["genre"] = genre_override

    # Send to REAPER bridge for MIDI generation
    result = await bridge.call_lua("GenerateBackingTrack", [
        chart, inst_list, style, genre_override
    ])

    if result.get("ok"):
        ret = result.get("ret", {})
        tracks_created = ret.get("tracks", inst_list)
        return (
            f"Backing track generated for '{song}' by {artist} "
            f"({chart['key']}, {chart['bpm']} BPM). "
            f"Tracks: {', '.join(tracks_created)}"
        )
    else:
        raise Exception(f"Failed to generate backing track: {result.get('error', 'Unknown error')}")


async def regenerate_part(
    instrument: str,
    style: str = "genre",
    genre_override: str = "",
) -> str:
    """Regenerate a single instrument part with a different style.

    Re-generates one instrument track using the chart data already
    stored in the REAPER project from the initial backing track generation.

    Args:
        instrument: Instrument to regenerate (drums, bass, keys, guitar)
        style: New style to apply
        genre_override: Force a specific genre
    """
    instrument = instrument.lower().strip()
    if instrument not in VALID_INSTRUMENTS:
        return (
            f"Invalid instrument: '{instrument}'. "
            f"Valid options: {', '.join(VALID_INSTRUMENTS)}"
        )

    if genre_override and genre_override.lower() not in AVAILABLE_GENRES:
        return (
            f"Unknown genre: '{genre_override}'. "
            f"Available: {', '.join(AVAILABLE_GENRES)}"
        )

    result = await bridge.call_lua("RegeneratePart", [
        instrument, style, genre_override or ""
    ])

    if result.get("ok"):
        ret = result.get("ret", {})
        new_genre = ret.get("genre", genre_override or style)
        return (
            f"Regenerated {instrument} part with {new_genre} style. "
            f"Track updated in REAPER."
        )
    else:
        error = result.get("error", "Unknown error")
        if "no chart" in error.lower() or "no backing" in error.lower():
            return (
                "No backing track found in current project. "
                "Generate a backing track first with generate_backing_track()."
            )
        raise Exception(f"Failed to regenerate {instrument}: {error}")


async def list_backing_genres() -> str:
    """List all available backing track genres with descriptions.

    Returns a formatted list of supported genres and their musical characteristics.
    """
    lines = ["Available backing track genres:", ""]
    for genre in sorted(AVAILABLE_GENRES):
        desc = GENRE_DESCRIPTIONS.get(genre, "")
        lines.append(f"  {genre}: {desc}")
    return "\n".join(lines)


async def get_song_chart(
    song: str,
    artist: str,
) -> str:
    """Fetch and parse a chord chart without generating backing tracks.

    Useful for previewing what chords were found before committing
    to backing track generation.

    Args:
        song: Song title to look up
        artist: Artist name
    """
    chart = lookup_song(song, artist)
    if chart is None:
        return f"Could not find chord chart for '{song}' by {artist}."

    lines = [
        f"Chart: {chart['title']} by {chart['artist']}",
        f"Key: {chart['key']}  BPM: {chart['bpm']}  Time: {chart['time_sig']}",
        "",
    ]
    for section in chart["sections"]:
        lines.append(f"[{section['name']}] ({section['bars']} bars)")
        lines.append("  " + " | ".join(section["chords"]))
        lines.append("")

    return "\n".join(lines)


async def manual_chart(
    chord_text: str,
    title: str = "Untitled",
    artist: str = "Unknown",
    bpm: int = 120,
    key: str = "",
    instruments: str = "drums,bass",
    style: str = "genre",
) -> str:
    """Generate a backing track from manually pasted chord text.

    Use this when the online lookup fails or you have custom chords.
    Format: sections with [SectionName] headers, chords separated by spaces,
    dots (.) to repeat the previous chord.

    Args:
        chord_text: Chord chart text with [Section] headers
        title: Song title
        artist: Artist name
        bpm: Tempo in BPM
        key: Musical key (auto-detected if empty)
        instruments: Comma-separated instruments (drums, bass, keys, guitar)
        style: Style approach — "genre" or a specific genre name
    """
    # Validate instruments
    inst_list = [i.strip().lower() for i in instruments.split(",")]
    invalid = [i for i in inst_list if i not in VALID_INSTRUMENTS]
    if invalid:
        return (
            f"Invalid instruments: {', '.join(invalid)}. "
            f"Valid options: {', '.join(VALID_INSTRUMENTS)}"
        )

    chart = parse_chord_chart(chord_text, title=title, artist=artist, bpm=bpm, key=key)

    if not chart["sections"]:
        return "No sections found in chord text. Use [SectionName] headers and chord symbols."

    # Send to REAPER bridge
    result = await bridge.call_lua("GenerateBackingTrack", [
        chart, inst_list, style, ""
    ])

    if result.get("ok"):
        ret = result.get("ret", {})
        tracks_created = ret.get("tracks", inst_list)
        return (
            f"Backing track generated from manual chart '{title}' "
            f"({chart['key']}, {chart['bpm']} BPM). "
            f"Tracks: {', '.join(tracks_created)}"
        )
    else:
        raise Exception(f"Failed to generate backing track: {result.get('error', 'Unknown error')}")


# ============================================================================
# Registration
# ============================================================================

def register_backing_track_tools(mcp) -> int:
    """Register all backing track tools with the MCP instance."""
    from ..dsl.backing_wrappers import register_backing_dsl_tools

    tools = [
        (generate_backing_track, "Generate MIDI backing tracks from a song's chord chart"),
        (regenerate_part, "Regenerate a single instrument part with a different style/genre"),
        (list_backing_genres, "List all available backing track genres with descriptions"),
        (get_song_chart, "Fetch and parse a chord chart without generating tracks"),
        (manual_chart, "Generate backing tracks from manually pasted chord text"),
    ]

    for func, desc in tools:
        decorated = mcp.tool()(func)

    # Also register DSL wrappers (natural language backing track creation)
    dsl_count = register_backing_dsl_tools(mcp)

    return len(tools) + dsl_count
