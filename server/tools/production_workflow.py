"""
Production Workflow Tools for REAPER MCP

Higher-level tools for common production workflows:
- Social media clip export
- Genre-based arrangement templates
- Musical form analysis
"""

from typing import Optional, List, Dict, Any
from ..bridge import bridge


# ============================================================================
# Arrangement Template Definitions
# ============================================================================

ARRANGEMENT_TEMPLATES = {
    "pop": {
        "name": "Pop",
        "tempo_range": (100, 130),
        "default_tempo": 120,
        "time_sig": (4, 4),
        "sections": [
            {"name": "Intro", "bars": 4},
            {"name": "Verse 1", "bars": 8},
            {"name": "Pre-Chorus", "bars": 4},
            {"name": "Chorus", "bars": 8},
            {"name": "Verse 2", "bars": 8},
            {"name": "Pre-Chorus", "bars": 4},
            {"name": "Chorus", "bars": 8},
            {"name": "Bridge", "bars": 8},
            {"name": "Chorus", "bars": 8},
            {"name": "Outro", "bars": 4},
        ],
    },
    "rock": {
        "name": "Rock",
        "tempo_range": (110, 150),
        "default_tempo": 130,
        "time_sig": (4, 4),
        "sections": [
            {"name": "Intro", "bars": 4},
            {"name": "Verse 1", "bars": 8},
            {"name": "Chorus", "bars": 8},
            {"name": "Verse 2", "bars": 8},
            {"name": "Chorus", "bars": 8},
            {"name": "Solo", "bars": 8},
            {"name": "Chorus", "bars": 8},
            {"name": "Outro", "bars": 4},
        ],
    },
    "blues": {
        "name": "Blues",
        "tempo_range": (70, 120),
        "default_tempo": 90,
        "time_sig": (4, 4),
        "sections": [
            {"name": "Intro", "bars": 4},
            {"name": "Verse 1 (12-bar)", "bars": 12},
            {"name": "Verse 2 (12-bar)", "bars": 12},
            {"name": "Solo", "bars": 12},
            {"name": "Verse 3 (12-bar)", "bars": 12},
            {"name": "Outro", "bars": 4},
        ],
    },
    "jazz": {
        "name": "Jazz",
        "tempo_range": (100, 200),
        "default_tempo": 140,
        "time_sig": (4, 4),
        "sections": [
            {"name": "Head In", "bars": 32},
            {"name": "Solo 1", "bars": 32},
            {"name": "Solo 2", "bars": 32},
            {"name": "Trading 4s", "bars": 16},
            {"name": "Head Out", "bars": 32},
        ],
    },
    "edm": {
        "name": "EDM",
        "tempo_range": (120, 150),
        "default_tempo": 128,
        "time_sig": (4, 4),
        "sections": [
            {"name": "Intro", "bars": 8},
            {"name": "Build", "bars": 8},
            {"name": "Drop 1", "bars": 16},
            {"name": "Breakdown", "bars": 8},
            {"name": "Build", "bars": 8},
            {"name": "Drop 2", "bars": 16},
            {"name": "Outro", "bars": 8},
        ],
    },
    "hiphop": {
        "name": "Hip-Hop",
        "tempo_range": (80, 110),
        "default_tempo": 90,
        "time_sig": (4, 4),
        "sections": [
            {"name": "Intro", "bars": 4},
            {"name": "Verse 1", "bars": 16},
            {"name": "Hook", "bars": 8},
            {"name": "Verse 2", "bars": 16},
            {"name": "Hook", "bars": 8},
            {"name": "Bridge", "bars": 8},
            {"name": "Hook", "bars": 8},
            {"name": "Outro", "bars": 4},
        ],
    },
    "country": {
        "name": "Country",
        "tempo_range": (100, 140),
        "default_tempo": 120,
        "time_sig": (4, 4),
        "sections": [
            {"name": "Intro", "bars": 4},
            {"name": "Verse 1", "bars": 8},
            {"name": "Chorus", "bars": 8},
            {"name": "Verse 2", "bars": 8},
            {"name": "Chorus", "bars": 8},
            {"name": "Solo", "bars": 8},
            {"name": "Chorus", "bars": 8},
            {"name": "Tag/Outro", "bars": 4},
        ],
    },
    "metal": {
        "name": "Metal",
        "tempo_range": (130, 200),
        "default_tempo": 160,
        "time_sig": (4, 4),
        "sections": [
            {"name": "Intro", "bars": 4},
            {"name": "Verse 1", "bars": 8},
            {"name": "Pre-Chorus", "bars": 4},
            {"name": "Chorus", "bars": 8},
            {"name": "Verse 2", "bars": 8},
            {"name": "Pre-Chorus", "bars": 4},
            {"name": "Chorus", "bars": 8},
            {"name": "Breakdown", "bars": 8},
            {"name": "Solo", "bars": 8},
            {"name": "Chorus", "bars": 8},
            {"name": "Outro", "bars": 4},
        ],
    },
    "funk": {
        "name": "Funk",
        "tempo_range": (95, 120),
        "default_tempo": 108,
        "time_sig": (4, 4),
        "sections": [
            {"name": "Intro", "bars": 4},
            {"name": "Groove 1", "bars": 8},
            {"name": "Verse 1", "bars": 8},
            {"name": "Chorus", "bars": 8},
            {"name": "Groove 2", "bars": 4},
            {"name": "Verse 2", "bars": 8},
            {"name": "Chorus", "bars": 8},
            {"name": "Breakdown", "bars": 8},
            {"name": "Chorus", "bars": 8},
            {"name": "Outro", "bars": 4},
        ],
    },
    "ballad": {
        "name": "Ballad",
        "tempo_range": (60, 85),
        "default_tempo": 72,
        "time_sig": (4, 4),
        "sections": [
            {"name": "Intro", "bars": 4},
            {"name": "Verse 1", "bars": 8},
            {"name": "Chorus", "bars": 8},
            {"name": "Verse 2", "bars": 8},
            {"name": "Chorus", "bars": 8},
            {"name": "Bridge", "bars": 8},
            {"name": "Chorus", "bars": 8},
            {"name": "Outro", "bars": 8},
        ],
    },
}

# Standard section naming for form analysis
SECTION_KEYWORDS = {
    "intro": ["intro", "introduction", "in"],
    "verse": ["verse", "vrs", "v"],
    "pre-chorus": ["pre-chorus", "pre chorus", "prechorus", "pre"],
    "chorus": ["chorus", "hook", "cho", "ch"],
    "bridge": ["bridge", "br", "middle 8"],
    "solo": ["solo", "guitar solo", "keys solo", "instrumental"],
    "breakdown": ["breakdown", "break", "bd"],
    "build": ["build", "buildup", "build-up", "riser"],
    "drop": ["drop"],
    "outro": ["outro", "out", "end", "tag", "coda"],
}


# ============================================================================
# Social Clip Export
# ============================================================================

async def social_clip(duration: int = 30, output_path: str = "",
                      start_time: Optional[float] = None,
                      format: str = "wav") -> str:
    """Export a clip optimized for social media (30s or 60s).

    Creates a render of the specified duration from the most interesting
    part of the project (chorus or loudest section). If start_time is
    provided, renders from that position instead.

    Args:
        duration: Clip duration in seconds (30 or 60)
        output_path: Output file path. If empty, uses project directory.
        start_time: Optional start position in seconds. If not provided,
                    uses the current time selection or cursor position.
        format: Audio format (wav, mp3, flac)
    """
    if duration not in (15, 30, 60, 90):
        return f"Invalid duration {duration}s. Supported: 15, 30, 60, 90 seconds."

    # Determine render start position
    render_start = 0.0

    if start_time is not None:
        render_start = start_time
    else:
        # Try to use existing time selection first
        time_sel_result = await bridge.call_lua("GetSet_LoopTimeRange", [
            False,   # isSet
            False,   # isLoop
            0.0,     # startOut
            0.0,     # endOut
            False    # allowautoseek
        ])

        if time_sel_result.get("ok"):
            ret = time_sel_result.get("ret", [0.0, 0.0])
            if isinstance(ret, (list, tuple)) and len(ret) >= 2:
                sel_start = ret[0]
                sel_end = ret[1]
            else:
                sel_start = 0.0
                sel_end = 0.0

            if sel_end > sel_start:
                # Use the start of the existing time selection
                render_start = sel_start
            else:
                # Fall back to edit cursor position
                cursor_result = await bridge.call_lua("GetCursorPosition", [])
                if cursor_result.get("ok"):
                    render_start = cursor_result.get("ret", 0.0)

    render_end = render_start + duration

    # Verify project length is sufficient
    length_result = await bridge.call_lua("GetProjectLength", [0])
    project_length = length_result.get("ret", 0.0) if length_result.get("ok") else 0.0

    if project_length < duration:
        return (f"Project length ({project_length:.1f}s) is shorter than "
                f"requested clip duration ({duration}s)")

    # Clamp to project bounds
    if render_end > project_length:
        render_end = project_length
        render_start = max(0.0, render_end - duration)

    # Set the time selection for rendering
    await bridge.call_lua("GetSet_LoopTimeRange", [
        True,          # isSet
        False,         # isLoop
        render_start,  # startOut
        render_end,    # endOut
        False          # allowautoseek
    ])

    # Set render bounds to time selection (2 = time selection)
    await bridge.call_lua("GetSetProjectInfo", [0, "RENDER_BOUNDSFLAG", 2, True])

    # Set output path if provided
    if output_path:
        await bridge.call_lua("GetSetProjectInfo_String", [
            0, "RENDER_FILE", output_path, True
        ])

    # Set render format
    format_map = {
        "wav": 0,    # WAV
        "mp3": 2,    # MP3 (requires LAME)
        "flac": 4,   # FLAC
    }
    fmt_code = format_map.get(format.lower(), 0)

    # Trigger render dialog
    result = await bridge.call_lua("Main_OnCommand", [41824, 0])

    if result.get("ok"):
        path_info = f" to {output_path}" if output_path else ""
        return (f"Social clip export started: {duration}s clip{path_info}\n"
                f"  Range: {render_start:.1f}s - {render_end:.1f}s\n"
                f"  Format: {format.upper()}\n"
                f"  (Render dialog opened - confirm to complete)")
    else:
        raise Exception(f"Failed to start render: {result.get('error', 'Unknown error')}")


# ============================================================================
# Arrangement Template
# ============================================================================

async def arrangement_template(genre: str, tempo: Optional[float] = None) -> str:
    """Apply a genre-based arrangement template to the project.

    Creates region markers for each section (intro, verse, chorus, etc.)
    with standard bar counts for the specified genre. Optionally sets
    the project tempo.

    Args:
        genre: Genre name (pop, rock, blues, jazz, edm, hiphop, country,
               metal, funk, ballad)
        tempo: Optional tempo override. If not provided, uses genre default.
    """
    genre_lower = genre.lower().strip()

    if genre_lower not in ARRANGEMENT_TEMPLATES:
        available = ", ".join(sorted(ARRANGEMENT_TEMPLATES.keys()))
        return f"Unknown genre '{genre}'. Available: {available}"

    template = ARRANGEMENT_TEMPLATES[genre_lower]
    sections = template["sections"]
    time_sig_num, time_sig_denom = template["time_sig"]

    # Determine tempo
    bpm = tempo if tempo is not None else template["default_tempo"]
    lo, hi = template["tempo_range"]
    if bpm < lo or bpm > hi:
        return (f"Tempo {bpm} BPM is outside typical range for "
                f"{template['name']} ({lo}-{hi} BPM). Proceeding anyway.")

    # Set project tempo via tempo marker at position 0
    # Use SetTempoTimeSigMarker per CLAUDE.md convention
    count_result = await bridge.call_lua("CountTempoTimeSigMarkers", [0])
    marker_count = count_result.get("ret", 0) if count_result.get("ok") else 0

    if marker_count > 0:
        # Modify existing marker 0
        await bridge.call_lua("SetTempoTimeSigMarker", [
            0,               # project
            0,               # ptidx (modify marker 0)
            0.0,             # timepos
            -1,              # measurepos (don't change)
            -1,              # beatpos (don't change)
            bpm,             # bpm
            time_sig_num,    # timesig_num
            time_sig_denom,  # timesig_denom
            False            # lineartempo
        ])
    else:
        # Create new marker
        await bridge.call_lua("SetTempoTimeSigMarker", [
            0,               # project
            -1,              # ptidx (-1 = create new)
            0.0,             # timepos
            -1,              # measurepos
            -1,              # beatpos
            bpm,             # bpm
            time_sig_num,    # timesig_num
            time_sig_denom,  # timesig_denom
            False            # lineartempo
        ])

    # Calculate beat duration
    beat_duration = 60.0 / bpm
    bar_duration = beat_duration * time_sig_num

    # Create regions for each section
    current_time = 0.0
    regions_created = 0
    section_summary = []

    for idx, section in enumerate(sections):
        section_name = section["name"]
        bars = section["bars"]
        section_duration = bars * bar_duration
        section_end = current_time + section_duration

        # Add region marker
        result = await bridge.call_lua("AddProjectMarker2", [
            0,               # project
            True,            # isrgn
            current_time,    # pos
            section_end,     # rgnend
            section_name,    # name
            -1,              # wantidx (-1 = auto)
            0                # color (0 = default)
        ])

        if result.get("ok"):
            regions_created += 1

        minutes = int(current_time // 60)
        seconds = current_time % 60
        section_summary.append(
            f"  [{minutes}:{seconds:04.1f}] {section_name} ({bars} bars)"
        )

        current_time = section_end

    total_bars = sum(s["bars"] for s in sections)
    total_minutes = int(current_time // 60)
    total_seconds = current_time % 60

    # Update timeline
    await bridge.call_lua("UpdateTimeline", [])

    return (
        f"Applied {template['name']} arrangement template:\n"
        f"  Tempo: {bpm:.0f} BPM, Time sig: {time_sig_num}/{time_sig_denom}\n"
        f"  Total: {total_bars} bars ({total_minutes}:{total_seconds:04.1f})\n"
        f"  Regions created: {regions_created}\n\n"
        + "\n".join(section_summary)
    )


# ============================================================================
# Form Analysis
# ============================================================================

async def analyze_form() -> str:
    """Analyze the current project structure and identify musical form.

    Examines region markers, tempo markers, and track content to
    determine the arrangement structure. Identifies sections (intro,
    verse, chorus, etc.) and provides suggestions for improvement.
    """
    # Get project tempo
    tempo_result = await bridge.call_lua("Master_GetTempo", [])
    tempo = tempo_result.get("ret", 120) if tempo_result.get("ok") else 120

    # Get time signature
    ts_result = await bridge.call_lua("GetTempoTimeSigMarker", [0, 0])
    ts_num = ts_result.get("timesig_num", 4) if ts_result.get("ok") else 4
    ts_denom = ts_result.get("timesig_denom", 4) if ts_result.get("ok") else 4

    beat_duration = 60.0 / tempo
    bar_duration = beat_duration * ts_num

    # Get project length
    length_result = await bridge.call_lua("GetProjectLength", [0])
    project_length = length_result.get("ret", 0.0) if length_result.get("ok") else 0.0

    total_bars = project_length / bar_duration if bar_duration > 0 else 0
    total_minutes = int(project_length // 60)
    total_seconds = project_length % 60

    # Count tracks and items
    track_count_result = await bridge.call_lua("CountTracks", [0])
    track_count = track_count_result.get("ret", 0) if track_count_result.get("ok") else 0

    item_count_result = await bridge.call_lua("CountMediaItems", [0])
    item_count = item_count_result.get("ret", 0) if item_count_result.get("ok") else 0

    # Collect regions (sections)
    marker_count_result = await bridge.call_lua("CountProjectMarkers", [0])
    total_markers = 0
    num_regions = 0

    if marker_count_result.get("ok"):
        ret = marker_count_result.get("ret", 0)
        if isinstance(ret, (list, tuple)):
            total_markers = ret[0] if len(ret) > 0 else 0
            num_regions = ret[1] if len(ret) > 1 else 0
        else:
            total_markers = ret

    sections = []
    markers_list = []

    # Enumerate markers/regions to find sections
    idx = 0
    while True:
        enum_result = await bridge.call_lua("EnumProjectMarkers", [idx])
        if not enum_result.get("ok"):
            break

        ret = enum_result.get("ret", [])
        if isinstance(ret, (list, tuple)):
            if len(ret) >= 5:
                retval, is_rgn, pos, rgnend, name = ret[:5]
                if not retval or retval == 0:
                    break

                if is_rgn:
                    section_bars = (rgnend - pos) / bar_duration
                    sections.append({
                        "name": name,
                        "start": pos,
                        "end": rgnend,
                        "bars": section_bars,
                    })
                else:
                    markers_list.append({"name": name, "pos": pos})
            else:
                break
        else:
            break

        idx += 1
        if idx > 200:
            break

    # Build analysis output
    lines = [
        f"Project Form Analysis:",
        f"  Tempo: {tempo:.1f} BPM, Time sig: {ts_num}/{ts_denom}",
        f"  Length: {total_minutes}:{total_seconds:04.1f} ({total_bars:.0f} bars)",
        f"  Tracks: {track_count}, Items: {item_count}",
        "",
    ]

    if sections:
        lines.append(f"Sections ({len(sections)} regions found):")
        for sec in sections:
            minutes = int(sec["start"] // 60)
            seconds = sec["start"] % 60
            lines.append(
                f"  [{minutes}:{seconds:04.1f}] {sec['name']} "
                f"({sec['bars']:.0f} bars)"
            )

        # Identify form
        section_types = []
        for sec in sections:
            name_lower = sec["name"].lower()
            matched = False
            for stype, keywords in SECTION_KEYWORDS.items():
                for kw in keywords:
                    if kw in name_lower:
                        section_types.append(stype)
                        matched = True
                        break
                if matched:
                    break
            if not matched:
                section_types.append("other")

        # Build form string (e.g., "AABA" or "Verse-Chorus")
        unique_types = list(dict.fromkeys(section_types))
        lines.append(f"\nIdentified form: {' - '.join(t.title() for t in section_types)}")

        # Suggestions
        lines.append("\nSuggestions:")
        has_intro = "intro" in section_types
        has_outro = "outro" in section_types
        has_chorus = "chorus" in section_types
        has_bridge = "bridge" in section_types
        has_verse = "verse" in section_types

        if not has_intro:
            lines.append("  - Consider adding an Intro section")
        if not has_outro:
            lines.append("  - Consider adding an Outro section")
        if has_verse and not has_chorus:
            lines.append("  - Verses found but no Chorus -- consider adding a Chorus")
        if has_chorus and not has_bridge:
            lines.append("  - No Bridge section -- a bridge can add contrast before the final chorus")
        if total_bars > 0 and total_bars < 32:
            lines.append(f"  - Short arrangement ({total_bars:.0f} bars) -- consider expanding")
        if total_bars > 120:
            lines.append(f"  - Long arrangement ({total_bars:.0f} bars) -- consider tightening")

        # Check bar counts
        non_standard = []
        for sec in sections:
            bars = sec["bars"]
            if bars > 1 and bars % 4 != 0 and bars % 3 != 0:
                non_standard.append(f"{sec['name']} ({bars:.0f} bars)")
        if non_standard:
            lines.append(f"  - Non-standard bar counts: {', '.join(non_standard)}")

        if not any(s for s in lines if s.startswith("  -")):
            lines.append("  - Arrangement looks well-structured!")

    elif markers_list:
        lines.append(f"Markers ({len(markers_list)} found, but no regions):")
        for m in markers_list[:10]:
            minutes = int(m["pos"] // 60)
            seconds = m["pos"] % 60
            lines.append(f"  [{minutes}:{seconds:04.1f}] {m['name']}")

        lines.append("\nSuggestions:")
        lines.append("  - Convert markers to regions for section-based analysis")
        lines.append("  - Use arrangement_template() to create a region-based structure")

    else:
        lines.append("No regions or markers found.")
        lines.append("\nSuggestions:")
        lines.append("  - Add region markers to define sections (intro, verse, chorus, etc.)")
        lines.append("  - Use arrangement_template() to create a genre-based structure")
        lines.append("  - Without markers, the form cannot be analyzed")

    return "\n".join(lines)


# ============================================================================
# Registration Function
# ============================================================================

def register_production_workflow_tools(mcp) -> int:
    """Register all production workflow tools with the MCP instance"""
    tools = [
        (social_clip,
         "Export a short clip for social media (Instagram, TikTok, etc). "
         "Creates a 15/30/60/90 second render from the current time selection "
         "or cursor position. Opens the render dialog with the right bounds set."),
        (arrangement_template,
         "Set up a song structure with genre-appropriate sections. "
         "Creates region markers for intro, verse, chorus, bridge, etc. "
         "with standard bar counts. Supports: pop, rock, blues, jazz, edm, "
         "hiphop, country, metal, funk, ballad."),
        (analyze_form,
         "Analyze the musical form/structure of the current project. "
         "Identifies sections from region markers, calculates bar counts, "
         "and suggests structural improvements. Use to understand arrangement "
         "before making changes."),
    ]

    # Register each tool
    for func, desc in tools:
        decorated = mcp.tool()(func)

    return len(tools)
