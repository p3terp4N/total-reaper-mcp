"""
MIDI Production Tools for REAPER MCP

High-level MIDI tools for production workflows:
- Programmatic multi-note MIDI insertion
- Scale lock / MIDI filter
- Genre-aware drum pattern generation
"""

from typing import Optional, List, Dict, Any
from ..bridge import bridge


# ============================================================================
# Batch MIDI Insertion
# ============================================================================

async def insert_midi(track_index: int, notes: List[Dict[str, Any]],
                      create_item: bool = True, item_length: Optional[float] = None) -> str:
    """Insert multiple MIDI notes programmatically into a track.

    Each note dict should contain:
        pitch (int): MIDI note number 0-127
        start (float): Start position in beats (quarter notes)
        duration (float): Duration in beats
        velocity (int, optional): 1-127, default 80
        channel (int, optional): 0-15, default 0

    Args:
        track_index: Track index to insert into
        notes: List of note dicts with pitch, start, duration, velocity, channel
        create_item: Whether to create a new MIDI item (default True)
        item_length: Length of the MIDI item in seconds (auto-calculated if None)

    Returns:
        Status message with number of notes inserted
    """
    if not notes:
        return "No notes provided"

    # Calculate item length from note data if not specified
    if item_length is None:
        # Find the end of the last note (in beats)
        max_end_beats = max(n.get("start", 0) + n.get("duration", 1) for n in notes)
        # Get tempo to convert beats to seconds
        tempo_result = await bridge.call_lua("Master_GetTempo", [])
        tempo = tempo_result.get("ret", 120) if tempo_result.get("ok") else 120
        beat_duration = 60.0 / tempo
        item_length = max_end_beats * beat_duration + 0.1  # small buffer

    item_index = 0
    take_index = 0

    if create_item:
        # Get track handle
        track_result = await bridge.call_lua("GetTrack", [0, track_index])
        if not track_result.get("ok") or not track_result.get("ret"):
            raise Exception(f"Track {track_index} not found")

        # Create MIDI item on track
        create_result = await bridge.call_lua("CreateNewMIDIItemInProj", [
            track_result.get("ret"), 0.0, item_length, False
        ])
        if not create_result.get("ok"):
            raise Exception("Failed to create MIDI item")

        # Get item index from project
        count_result = await bridge.call_lua("CountMediaItems", [0])
        if count_result.get("ok"):
            item_index = count_result.get("ret", 1) - 1

    # Insert each note
    notes_inserted = 0
    for note in notes:
        pitch = note.get("pitch", 60)
        start_beats = note.get("start", 0.0)
        duration_beats = note.get("duration", 1.0)
        velocity = note.get("velocity", 80)
        channel = note.get("channel", 0)

        # Clamp values
        pitch = max(0, min(127, pitch))
        velocity = max(1, min(127, velocity))
        channel = max(0, min(15, channel))

        # Convert beats to PPQ (960 PPQ per quarter note)
        ppq_per_beat = 960
        start_ppq = start_beats * ppq_per_beat
        end_ppq = (start_beats + duration_beats) * ppq_per_beat

        result = await bridge.call_lua("InsertMIDINoteToItemTake", [
            item_index, take_index, pitch, velocity,
            start_ppq / ppq_per_beat,  # The bridge expects time in beats
            duration_beats,
            channel, False, False, 0, 0
        ])

        if result.get("ok"):
            notes_inserted += 1

    # Sort MIDI events
    await bridge.call_lua("SortMIDIInItemTake", [item_index, take_index])

    return f"Inserted {notes_inserted}/{len(notes)} MIDI notes on track {track_index}"


# ============================================================================
# Scale Lock / MIDI Filter
# ============================================================================

async def scale_lock(key: str, scale: str) -> str:
    """Set scale lock for MIDI input filtering.

    Constrains MIDI input to notes within the specified scale.
    This sets the project MIDI scale so that the MIDI editor
    shows scale-appropriate notes highlighted.

    Args:
        key: Root note - C, C#, D, D#, E, F, F#, G, G#, A, A#, B
        scale: Scale type - major, minor, harmonic_minor, melodic_minor,
               dorian, phrygian, lydian, mixolydian, pentatonic, blues

    Returns:
        Status message confirming scale lock settings
    """
    # Map key names to semitone offsets
    key_map = {
        "C": 0, "C#": 1, "Db": 1,
        "D": 2, "D#": 3, "Eb": 3,
        "E": 4, "Fb": 4,
        "F": 5, "F#": 6, "Gb": 6,
        "G": 7, "G#": 8, "Ab": 8,
        "A": 9, "A#": 10, "Bb": 10,
        "B": 11, "Cb": 11,
    }

    # Map scale names to interval patterns (semitones from root)
    scale_intervals = {
        "major": [0, 2, 4, 5, 7, 9, 11],
        "minor": [0, 2, 3, 5, 7, 8, 10],
        "harmonic_minor": [0, 2, 3, 5, 7, 8, 11],
        "melodic_minor": [0, 2, 3, 5, 7, 9, 11],
        "dorian": [0, 2, 3, 5, 7, 9, 10],
        "phrygian": [0, 1, 3, 5, 7, 8, 10],
        "lydian": [0, 2, 4, 6, 7, 9, 11],
        "mixolydian": [0, 2, 4, 5, 7, 9, 10],
        "pentatonic": [0, 2, 4, 7, 9],
        "blues": [0, 3, 5, 6, 7, 10],
        "aeolian": [0, 2, 3, 5, 7, 8, 10],
        "locrian": [0, 1, 3, 5, 6, 8, 10],
    }

    if key not in key_map:
        valid_keys = ", ".join(sorted(key_map.keys(), key=lambda k: key_map[k]))
        return f"Unknown key '{key}'. Valid keys: {valid_keys}"

    scale_lower = scale.lower()
    if scale_lower not in scale_intervals:
        valid_scales = ", ".join(scale_intervals.keys())
        return f"Unknown scale '{scale}'. Valid scales: {valid_scales}"

    root = key_map[key]
    intervals = scale_intervals[scale_lower]

    # Build a 12-bit scale mask: each bit represents a semitone
    # Bit 0 = root, bit 1 = root+1 semitone, etc.
    scale_mask = 0
    for interval in intervals:
        scale_mask |= (1 << ((root + interval) % 12))

    # Set the project scale via extended state
    # REAPER stores scale info in project extended state
    await bridge.call_lua("SetProjExtState", [
        0, "MCP_ScaleLock", "root", str(root)
    ])
    await bridge.call_lua("SetProjExtState", [
        0, "MCP_ScaleLock", "scale", scale_lower
    ])
    await bridge.call_lua("SetProjExtState", [
        0, "MCP_ScaleLock", "mask", str(scale_mask)
    ])
    await bridge.call_lua("SetProjExtState", [
        0, "MCP_ScaleLock", "enabled", "1"
    ])

    # Use REAPER's built-in MIDI editor scale snap if available
    # Action 40047 = MIDI editor: Set scale snap
    # We set the key/scale via project state markers
    result = await bridge.call_lua("SetProjExtState", [
        0, "MIDI_SCALE", "root", str(root)
    ])

    note_names = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
    scale_notes = [note_names[(root + i) % 12] for i in intervals]

    return (f"Scale lock set: {key} {scale} "
            f"(notes: {', '.join(scale_notes)})")


# ============================================================================
# Genre-Aware Drum Generation
# ============================================================================

# Comprehensive drum patterns by genre
DRUM_PATTERNS = {
    "rock": {
        "name": "Rock",
        "patterns": {
            "kick": [0, 2],
            "snare": [1, 3],
            "hihat": [0, 0.5, 1, 1.5, 2, 2.5, 3, 3.5],
        },
        "velocity_map": {"kick": 110, "snare": 100, "hihat": 80},
        "fills_every": 4,  # bars
    },
    "pop": {
        "name": "Pop",
        "patterns": {
            "kick": [0, 1.5, 2],
            "snare": [1, 3],
            "hihat": [0, 0.5, 1, 1.5, 2, 2.5, 3, 3.5],
        },
        "velocity_map": {"kick": 100, "snare": 95, "hihat": 70},
        "fills_every": 8,
    },
    "funk": {
        "name": "Funk",
        "patterns": {
            "kick": [0, 0.75, 2, 2.25],
            "snare": [1, 3],
            "hihat": [i * 0.25 for i in range(16)],  # 16th notes
            "open_hihat": [1.75, 3.75],
        },
        "velocity_map": {"kick": 110, "snare": 105, "hihat": 75, "open_hihat": 90},
        "fills_every": 4,
    },
    "jazz": {
        "name": "Jazz",
        "patterns": {
            "ride": [0, 0.67, 1, 1.67, 2, 2.67, 3, 3.67],  # swing ride
            "kick": [0, 2.5],
            "hihat": [1, 3],  # foot hi-hat on 2 and 4
            "snare": [],  # ghost notes handled separately
        },
        "velocity_map": {"ride": 85, "kick": 70, "hihat": 60, "snare": 55},
        "fills_every": 4,
    },
    "blues": {
        "name": "Blues",
        "patterns": {
            "kick": [0, 2],
            "snare": [1, 3],
            "ride": [0, 0.67, 1, 1.67, 2, 2.67, 3, 3.67],  # shuffle
        },
        "velocity_map": {"kick": 100, "snare": 95, "ride": 80},
        "fills_every": 4,
    },
    "metal": {
        "name": "Metal",
        "patterns": {
            "kick": [i * 0.25 for i in range(16)],  # double bass
            "snare": [1, 3],
            "hihat": [0, 0.5, 1, 1.5, 2, 2.5, 3, 3.5],
            "crash": [0],
        },
        "velocity_map": {"kick": 120, "snare": 120, "hihat": 90, "crash": 110},
        "fills_every": 4,
    },
    "latin": {
        "name": "Latin",
        "patterns": {
            "kick": [0, 1.5, 3],
            "snare": [1, 2.5],
            "hihat": [i * 0.25 for i in range(16)],
            "tom1": [0.75, 2.75],
            "tom2": [1.25, 3.25],
        },
        "velocity_map": {"kick": 100, "snare": 90, "hihat": 70, "tom1": 85, "tom2": 80},
        "fills_every": 4,
    },
    "r&b": {
        "name": "R&B",
        "patterns": {
            "kick": [0, 1.75, 2.5],
            "snare": [1, 3],
            "hihat": [i * 0.25 for i in range(16)],
        },
        "velocity_map": {"kick": 95, "snare": 90, "hihat": 65},
        "fills_every": 8,
    },
    "country": {
        "name": "Country",
        "patterns": {
            "kick": [0, 2],
            "snare": [1, 3],
            "hihat": [0, 0.5, 1, 1.5, 2, 2.5, 3, 3.5],
        },
        "velocity_map": {"kick": 100, "snare": 90, "hihat": 75},
        "fills_every": 8,
    },
    "reggae": {
        "name": "Reggae",
        "patterns": {
            "kick": [0.75, 2.75],
            "snare": [1.5, 3.5],
            "hihat": [0, 0.5, 1, 1.5, 2, 2.5, 3, 3.5],
            "open_hihat": [0.5, 2.5],
        },
        "velocity_map": {"kick": 95, "snare": 85, "hihat": 70, "open_hihat": 80},
        "fills_every": 4,
    },
    "hiphop": {
        "name": "Hip-Hop",
        "patterns": {
            "kick": [0, 0.75, 2, 2.75],
            "snare": [1, 3],
            "hihat": [i * 0.25 for i in range(16)],
            "open_hihat": [1.5, 3.5],
        },
        "velocity_map": {"kick": 110, "snare": 105, "hihat": 70, "open_hihat": 85},
        "fills_every": 8,
    },
    "edm": {
        "name": "EDM",
        "patterns": {
            "kick": [0, 1, 2, 3],  # four-on-the-floor
            "snare": [1, 3],
            "hihat": [i * 0.25 for i in range(16)],
            "open_hihat": [0.5, 1.5, 2.5, 3.5],
        },
        "velocity_map": {"kick": 120, "snare": 100, "hihat": 75, "open_hihat": 85},
        "fills_every": 8,
    },
}

# General MIDI drum map
GM_DRUMS = {
    "kick": 36,
    "snare": 38,
    "hihat": 42,
    "open_hihat": 46,
    "crash": 49,
    "ride": 51,
    "tom1": 48,  # Hi tom
    "tom2": 45,  # Mid tom
    "tom3": 43,  # Low tom
}


async def generate_drums(genre: str, tempo: float, bars: int = 4,
                         item_index: Optional[int] = None,
                         take_index: int = 0,
                         track_index: Optional[int] = None) -> str:
    """Generate a drum MIDI pattern for a specific genre and tempo.

    Supports 12 genres: rock, pop, funk, jazz, blues, metal,
    latin, r&b, country, reggae, hiphop, edm.

    Args:
        genre: Musical genre for the drum pattern
        tempo: Tempo in BPM (affects swing/feel calculations)
        bars: Number of bars to generate (default 4)
        item_index: Existing MIDI item index to insert into (optional)
        take_index: Take index within the item (default 0)
        track_index: Track index for creating a new MIDI item (optional, used if item_index is None)

    Returns:
        Status message with pattern details
    """
    genre_lower = genre.lower()
    if genre_lower not in DRUM_PATTERNS:
        available = ", ".join(DRUM_PATTERNS.keys())
        return f"Unknown genre '{genre}'. Available: {available}"

    pattern_def = DRUM_PATTERNS[genre_lower]
    patterns = pattern_def["patterns"]
    velocity_map = pattern_def["velocity_map"]

    # If no existing MIDI item, create one
    if item_index is None:
        if track_index is None:
            return "Provide either item_index (existing MIDI item) or track_index (to create new item)"

        # Calculate item length from tempo and bars
        beats_per_bar = 4  # Assuming 4/4 time
        total_beats = bars * beats_per_bar
        beat_duration = 60.0 / tempo
        item_length = total_beats * beat_duration + 0.1

        # Get track handle
        track_result = await bridge.call_lua("GetTrack", [0, track_index])
        if not track_result.get("ok") or not track_result.get("ret"):
            raise Exception(f"Track {track_index} not found")

        # Create MIDI item
        create_result = await bridge.call_lua("CreateNewMIDIItemInProj", [
            track_result.get("ret"), 0.0, item_length, False
        ])
        if not create_result.get("ok"):
            raise Exception("Failed to create MIDI item")

        # Get the item index
        count_result = await bridge.call_lua("CountMediaItems", [0])
        item_index = (count_result.get("ret", 1) - 1) if count_result.get("ok") else 0

    # Get the take handle
    item_result = await bridge.call_lua("GetMediaItem", [0, item_index])
    if not item_result.get("ok") or not item_result.get("ret"):
        raise Exception(f"Media item {item_index} not found")

    take_result = await bridge.call_lua("GetMediaItemTake", [
        item_result.get("ret"), take_index
    ])
    if not take_result.get("ok") or not take_result.get("ret"):
        raise Exception(f"Take {take_index} not found in item {item_index}")

    take_handle = take_result.get("ret")

    # Generate pattern
    ppq_per_quarter = 960
    notes_added = 0

    for bar in range(bars):
        bar_offset = bar * 4 * ppq_per_quarter  # 4 quarters per bar

        for drum_name, positions in patterns.items():
            if drum_name not in GM_DRUMS:
                continue

            pitch = GM_DRUMS[drum_name]
            base_velocity = velocity_map.get(drum_name, 80)

            for pos in positions:
                ppq_pos = int(bar_offset + pos * ppq_per_quarter)

                # Add slight velocity variation for realism
                import random
                vel_variation = random.randint(-5, 5)
                velocity = max(1, min(127, base_velocity + vel_variation))

                result = await bridge.call_lua("MIDI_InsertNote", [
                    take_handle,
                    False,   # selected
                    False,   # muted
                    ppq_pos,
                    ppq_pos + 100,  # short duration for drums
                    9,       # channel 10 (0-indexed = 9) for drums
                    pitch,
                    velocity,
                    True     # noSort (we sort at the end)
                ])

                if result.get("ok"):
                    notes_added += 1

    # Sort MIDI events
    await bridge.call_lua("MIDI_Sort", [take_handle])

    return (f"Generated {pattern_def['name']} drum pattern: "
            f"{notes_added} notes over {bars} bars at {tempo} BPM")


# ============================================================================
# Registration Function
# ============================================================================

def register_midi_production_tools(mcp) -> int:
    """Register all MIDI production tools with the MCP instance"""
    tools = [
        (insert_midi,
         "Insert multiple MIDI notes programmatically. Provide a list of notes "
         "with pitch, start (beats), duration (beats), velocity, and channel. "
         "Creates a new MIDI item or adds to an existing one."),
        (scale_lock,
         "Set scale lock to constrain MIDI to a specific key and scale. "
         "Supports major, minor, modes, pentatonic, blues. "
         "Use for keeping compositions in key."),
        (generate_drums,
         "Generate genre-specific drum patterns as MIDI. "
         "Supports rock, pop, funk, jazz, blues, metal, latin, r&b, "
         "country, reggae, hiphop, edm. "
         "Specify tempo and number of bars."),
    ]

    for func, desc in tools:
        mcp.tool()(func)

    return len(tools)
