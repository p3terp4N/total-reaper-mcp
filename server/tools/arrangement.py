"""
Arrangement Tools for REAPER MCP

Tools for song arrangement, structure, and form:
- Genre-based arrangement templates (markers/regions)
- Project structure analysis and suggestions
"""

from typing import Optional, Dict, List, Any
from ..bridge import bridge


# ============================================================================
# Arrangement Templates
# ============================================================================

# Genre arrangement templates define song structure with section names
# and bar counts. Uses 4/4 time signature.
ARRANGEMENT_TEMPLATES = {
    "pop": {
        "name": "Pop",
        "sections": [
            ("Intro", 4),
            ("Verse 1", 8),
            ("Pre-Chorus", 4),
            ("Chorus", 8),
            ("Verse 2", 8),
            ("Pre-Chorus", 4),
            ("Chorus", 8),
            ("Bridge", 8),
            ("Chorus", 8),
            ("Outro", 4),
        ],
    },
    "rock": {
        "name": "Rock",
        "sections": [
            ("Intro", 4),
            ("Verse 1", 8),
            ("Chorus", 8),
            ("Verse 2", 8),
            ("Chorus", 8),
            ("Solo", 8),
            ("Chorus", 8),
            ("Outro", 8),
        ],
    },
    "blues": {
        "name": "Blues (12-Bar)",
        "sections": [
            ("Intro", 4),
            ("Verse 1", 12),
            ("Verse 2", 12),
            ("Solo", 12),
            ("Verse 3", 12),
            ("Outro/Turnaround", 4),
        ],
    },
    "jazz": {
        "name": "Jazz (AABA)",
        "sections": [
            ("Intro", 4),
            ("A Section", 8),
            ("A Section (repeat)", 8),
            ("B Section (Bridge)", 8),
            ("A Section (final)", 8),
            ("Solo over A", 8),
            ("Solo over A", 8),
            ("Solo over B", 8),
            ("Solo over A", 8),
            ("Head Out A", 8),
            ("Head Out A", 8),
            ("Head Out B", 8),
            ("Head Out A", 8),
            ("Outro/Tag", 4),
        ],
    },
    "country": {
        "name": "Country",
        "sections": [
            ("Intro", 4),
            ("Verse 1", 8),
            ("Verse 2", 8),
            ("Chorus", 8),
            ("Verse 3", 8),
            ("Chorus", 8),
            ("Bridge", 8),
            ("Chorus", 8),
            ("Outro", 4),
        ],
    },
    "metal": {
        "name": "Metal",
        "sections": [
            ("Intro/Riff", 8),
            ("Verse 1", 8),
            ("Pre-Chorus", 4),
            ("Chorus", 8),
            ("Verse 2", 8),
            ("Pre-Chorus", 4),
            ("Chorus", 8),
            ("Breakdown", 8),
            ("Solo", 8),
            ("Chorus", 8),
            ("Outro", 8),
        ],
    },
    "funk": {
        "name": "Funk",
        "sections": [
            ("Intro/Groove", 4),
            ("Verse 1", 8),
            ("Chorus", 8),
            ("Verse 2", 8),
            ("Chorus", 8),
            ("Bridge/Breakdown", 8),
            ("Chorus", 8),
            ("Outro/Jam", 8),
        ],
    },
    "edm": {
        "name": "EDM",
        "sections": [
            ("Intro", 8),
            ("Build-Up", 8),
            ("Drop", 16),
            ("Break", 8),
            ("Build-Up 2", 8),
            ("Drop 2", 16),
            ("Outro", 8),
        ],
    },
    "hiphop": {
        "name": "Hip-Hop",
        "sections": [
            ("Intro", 4),
            ("Verse 1", 16),
            ("Hook", 8),
            ("Verse 2", 16),
            ("Hook", 8),
            ("Bridge", 8),
            ("Verse 3", 16),
            ("Hook", 8),
            ("Outro", 4),
        ],
    },
    "r&b": {
        "name": "R&B",
        "sections": [
            ("Intro", 4),
            ("Verse 1", 8),
            ("Pre-Chorus", 4),
            ("Chorus", 8),
            ("Verse 2", 8),
            ("Pre-Chorus", 4),
            ("Chorus", 8),
            ("Bridge", 8),
            ("Chorus", 8),
            ("Outro", 4),
        ],
    },
    "reggae": {
        "name": "Reggae",
        "sections": [
            ("Intro", 4),
            ("Verse 1", 8),
            ("Chorus", 8),
            ("Verse 2", 8),
            ("Chorus", 8),
            ("Bridge", 8),
            ("Chorus", 8),
            ("Outro/Dub", 8),
        ],
    },
    "latin": {
        "name": "Latin",
        "sections": [
            ("Intro", 4),
            ("Verse 1", 8),
            ("Chorus", 8),
            ("Verse 2", 8),
            ("Chorus", 8),
            ("Instrumental", 8),
            ("Chorus", 8),
            ("Montuno/Outro", 16),
        ],
    },
    "singer-songwriter": {
        "name": "Singer-Songwriter",
        "sections": [
            ("Intro", 4),
            ("Verse 1", 8),
            ("Verse 2", 8),
            ("Chorus", 8),
            ("Verse 3", 8),
            ("Chorus", 8),
            ("Bridge", 8),
            ("Chorus", 8),
            ("Outro", 4),
        ],
    },
    "podcast": {
        "name": "Podcast",
        "sections": [
            ("Intro Music", 4),
            ("Welcome/Topic Intro", 8),
            ("Segment 1", 32),
            ("Transition", 2),
            ("Segment 2", 32),
            ("Transition", 2),
            ("Segment 3", 32),
            ("Wrap-Up", 8),
            ("Outro Music", 4),
        ],
    },
}

# Section colors (REAPER native color format: 0x01BBGGRR)
SECTION_COLORS = {
    "Intro": 0x0100FF80,       # Green
    "Verse": 0x01FF8000,       # Blue-ish
    "Pre-Chorus": 0x0100CCFF,  # Orange
    "Chorus": 0x010000FF,      # Red
    "Bridge": 0x01FF00FF,      # Magenta
    "Solo": 0x0100FFFF,        # Yellow
    "Outro": 0x01808080,       # Gray
    "Drop": 0x010000FF,        # Red
    "Build": 0x010080FF,       # Orange
    "Break": 0x01FFCC00,       # Cyan-ish
    "Breakdown": 0x01FF00FF,   # Magenta
    "Hook": 0x010000FF,        # Red
    "Instrumental": 0x0100FFFF,  # Yellow
    "Jam": 0x0100FFFF,         # Yellow
    "Segment": 0x01FF8000,     # Blue-ish
    "Transition": 0x01808080,  # Gray
    "Welcome": 0x0100FF80,     # Green
    "Wrap": 0x01808080,        # Gray
}


def _get_section_color(section_name: str) -> int:
    """Get color for a section name based on keywords."""
    name_lower = section_name.lower()
    for keyword, color in SECTION_COLORS.items():
        if keyword.lower() in name_lower:
            return color
    return 0  # Default color (no specific color)


async def arrangement_template(genre: str, tempo: Optional[float] = None,
                                clear_existing: bool = False) -> str:
    """Apply a genre-specific arrangement template to the project.

    Creates markers/regions for each song section (intro, verse, chorus,
    bridge, outro, etc.) with appropriate bar counts.

    Args:
        genre: Musical genre for the arrangement template
        tempo: Tempo in BPM (uses current project tempo if not specified)
        clear_existing: Whether to clear existing markers/regions first

    Returns:
        Status message with arrangement details
    """
    genre_lower = genre.lower()
    if genre_lower not in ARRANGEMENT_TEMPLATES:
        available = ", ".join(ARRANGEMENT_TEMPLATES.keys())
        return f"Unknown genre '{genre}'. Available: {available}"

    template = ARRANGEMENT_TEMPLATES[genre_lower]
    sections = template["sections"]

    # Get or set tempo
    if tempo is not None:
        # Set project tempo using the safe method (SetTempoTimeSigMarker)
        count_result = await bridge.call_lua("CountTempoTimeSigMarkers", [0])
        marker_count = count_result.get("ret", 0) if count_result.get("ok") else 0

        if marker_count > 0:
            # Modify existing first tempo marker
            await bridge.call_lua("SetTempoTimeSigMarker", [
                0, 0, 0.0, -1, -1, tempo, 4, 4, False
            ])
        else:
            # Create first tempo marker
            await bridge.call_lua("SetTempoTimeSigMarker", [
                0, -1, 0.0, -1, -1, tempo, 4, 4, False
            ])
    else:
        # Get current tempo
        tempo_result = await bridge.call_lua("Master_GetTempo", [])
        tempo = tempo_result.get("ret", 120) if tempo_result.get("ok") else 120

    # Clear existing markers/regions if requested
    if clear_existing:
        # Count and delete all markers/regions in reverse
        count_result = await bridge.call_lua("CountProjectMarkers", [0])
        if count_result.get("ok"):
            total = count_result.get("ret", 0)
            if isinstance(total, list):
                total = total[0] + total[1] if len(total) >= 2 else 0
            for i in range(total - 1, -1, -1):
                await bridge.call_lua("DeleteProjectMarkerByIndex", [0, i])

    # Calculate section positions
    beat_duration = 60.0 / tempo  # seconds per beat
    bar_duration = beat_duration * 4  # 4/4 time

    current_pos = 0.0
    regions_created = 0

    for section_name, bar_count in sections:
        section_duration = bar_count * bar_duration
        section_end = current_pos + section_duration
        color = _get_section_color(section_name)

        # Create region with color
        result = await bridge.call_lua("AddProjectMarker2", [
            0,           # project
            True,        # is_region
            current_pos,
            section_end,
            section_name,
            -1,          # auto-number
            color
        ])

        if result.get("ok"):
            regions_created += 1
        else:
            # Fallback: try without color
            result = await bridge.call_lua("AddProjectMarker", [
                0, True, current_pos, section_end, section_name, -1
            ])
            if result.get("ok"):
                regions_created += 1

        current_pos = section_end

    # Calculate total duration
    total_bars = sum(bars for _, bars in sections)
    total_duration = current_pos
    total_minutes = int(total_duration // 60)
    total_seconds = total_duration % 60

    # Build section summary
    section_summary = " | ".join(
        f"{name} ({bars} bars)" for name, bars in sections
    )

    return (f"Applied {template['name']} arrangement template: "
            f"{regions_created} sections, {total_bars} bars total, "
            f"~{total_minutes}:{total_seconds:04.1f} at {tempo:.0f} BPM\n"
            f"Structure: {section_summary}")


# ============================================================================
# Form Analysis
# ============================================================================

async def analyze_form() -> str:
    """Analyze the current project structure and suggest improvements.

    Examines:
    - Existing regions/markers (song sections)
    - Track layout and content distribution
    - Tempo map
    - Overall length and pacing

    Returns:
        Detailed analysis with suggestions
    """
    analysis = []
    suggestions = []

    # --- 1. Get basic project info ---
    track_count_result = await bridge.call_lua("CountTracks", [0])
    track_count = track_count_result.get("ret", 0) if track_count_result.get("ok") else 0

    item_count_result = await bridge.call_lua("CountMediaItems", [0])
    item_count = item_count_result.get("ret", 0) if item_count_result.get("ok") else 0

    length_result = await bridge.call_lua("GetProjectLength", [0])
    project_length = length_result.get("ret", 0) if length_result.get("ok") else 0

    tempo_result = await bridge.call_lua("Master_GetTempo", [])
    tempo = tempo_result.get("ret", 120) if tempo_result.get("ok") else 120

    minutes = int(project_length // 60)
    seconds = project_length % 60
    beat_duration = 60.0 / tempo
    bar_duration = beat_duration * 4
    total_bars = project_length / bar_duration if bar_duration > 0 else 0

    analysis.append(
        f"Project Overview: {track_count} tracks, {item_count} items, "
        f"{minutes}:{seconds:04.1f} ({total_bars:.0f} bars at {tempo:.0f} BPM)"
    )

    # --- 2. Analyze existing markers/regions ---
    marker_count_result = await bridge.call_lua("CountProjectMarkers", [0])
    total_markers = 0
    num_markers = 0
    num_regions = 0

    if marker_count_result.get("ok"):
        ret = marker_count_result.get("ret", 0)
        if isinstance(ret, list) and len(ret) >= 2:
            num_markers = ret[0]
            num_regions = ret[1]
            total_markers = num_markers + num_regions
        elif isinstance(ret, (int, float)):
            total_markers = int(ret)

    regions = []
    markers_list = []

    # Enumerate all markers/regions
    for i in range(total_markers):
        enum_result = await bridge.call_lua("EnumProjectMarkers", [i])
        if enum_result.get("ok"):
            ret = enum_result.get("ret", [])
            if isinstance(ret, list) and len(ret) >= 5:
                idx, is_region, pos, rgn_end, name = ret[:5]
                if is_region:
                    regions.append({
                        "name": name, "start": pos,
                        "end": rgn_end, "length": rgn_end - pos
                    })
                else:
                    markers_list.append({"name": name, "pos": pos})

    if regions:
        analysis.append(f"\nSong Sections ({len(regions)} regions):")
        for r in regions:
            bars_in_region = r["length"] / bar_duration if bar_duration > 0 else 0
            analysis.append(
                f"  {r['name']}: {r['start']:.1f}s - {r['end']:.1f}s "
                f"({bars_in_region:.0f} bars)"
            )

        # Check for gaps between regions
        for i in range(1, len(regions)):
            gap = regions[i]["start"] - regions[i - 1]["end"]
            if gap > 0.5:  # More than half a second gap
                suggestions.append(
                    f"Gap of {gap:.1f}s between '{regions[i-1]['name']}' "
                    f"and '{regions[i]['name']}' - consider adding a transition section"
                )

        # Check for very long sections
        for r in regions:
            bars = r["length"] / bar_duration if bar_duration > 0 else 0
            if bars > 16:
                suggestions.append(
                    f"'{r['name']}' is {bars:.0f} bars - consider splitting "
                    f"into sub-sections for variety"
                )
    else:
        analysis.append("\nNo song sections defined (no regions)")
        suggestions.append(
            "Add arrangement regions to mark song sections. "
            "Use arrangement_template() to auto-generate from a genre template."
        )

    if markers_list:
        analysis.append(f"\nMarkers ({len(markers_list)}):")
        for m in markers_list[:10]:  # Limit display
            analysis.append(f"  '{m['name']}' at {m['pos']:.1f}s")

    # --- 3. Analyze track layout ---
    analysis.append(f"\nTrack Layout ({track_count} tracks):")

    tracks_with_content = 0
    empty_tracks = 0
    track_info = []

    for i in range(min(track_count, 20)):  # Limit to first 20
        track_result = await bridge.call_lua("GetTrack", [0, i])
        if not track_result.get("ok"):
            continue

        track = track_result.get("ret")

        # Get track name
        name_result = await bridge.call_lua("GetTrackName", [i])
        name = name_result.get("ret", f"Track {i+1}") if name_result.get("ok") else f"Track {i+1}"

        # Count items on track
        item_result = await bridge.call_lua("CountTrackMediaItems", [track])
        track_items = item_result.get("ret", 0) if item_result.get("ok") else 0

        # Check if muted
        mute_result = await bridge.call_lua("GetMediaTrackInfo_Value", [track, "B_MUTE"])
        is_muted = bool(mute_result.get("ret", 0)) if mute_result.get("ok") else False

        # Count FX
        fx_result = await bridge.call_lua("TrackFX_GetCount", [track])
        fx_count = fx_result.get("ret", 0) if fx_result.get("ok") else 0

        if track_items > 0:
            tracks_with_content += 1
        else:
            empty_tracks += 1

        status = ""
        if is_muted:
            status = " [MUTED]"
        if track_items == 0:
            status += " [EMPTY]"

        analysis.append(
            f"  {i}: '{name}' - {track_items} items, {fx_count} FX{status}"
        )

    if empty_tracks > 0:
        suggestions.append(
            f"{empty_tracks} empty tracks found - consider removing unused tracks"
        )

    # --- 4. Content density analysis ---
    if project_length > 0 and item_count > 0:
        items_per_minute = item_count / (project_length / 60)
        analysis.append(f"\nContent Density: {items_per_minute:.1f} items/minute")

        if items_per_minute < 2:
            suggestions.append(
                "Low content density - the project may be sparse. "
                "Consider adding more instruments or fills."
            )
    elif project_length == 0:
        suggestions.append("Project appears empty - add content to analyze form.")

    # --- 5. Duration analysis ---
    if project_length > 0:
        if project_length < 60:
            suggestions.append(
                f"Project is only {project_length:.0f}s - typical songs are 3-5 minutes. "
                "Consider extending with more sections."
            )
        elif project_length > 420:  # > 7 minutes
            suggestions.append(
                f"Project is {minutes}:{seconds:04.1f} - consider tightening the arrangement "
                "unless this is intentional (jam, prog, etc.)."
            )

    # --- 6. Tempo analysis ---
    tempo_count_result = await bridge.call_lua("CountTempoTimeSigMarkers", [0])
    tempo_changes = tempo_count_result.get("ret", 0) if tempo_count_result.get("ok") else 0

    if tempo_changes > 1:
        analysis.append(f"\nTempo Changes: {tempo_changes} markers")
    else:
        analysis.append(f"\nTempo: constant {tempo:.0f} BPM")

    # --- Build final output ---
    output = "\n".join(analysis)

    if suggestions:
        output += "\n\nSuggestions:"
        for i, suggestion in enumerate(suggestions, 1):
            output += f"\n  {i}. {suggestion}"
    else:
        output += "\n\nNo issues found - arrangement looks well-structured."

    return output


# ============================================================================
# Registration Function
# ============================================================================

def register_arrangement_tools(mcp) -> int:
    """Register all arrangement tools with the MCP instance"""
    tools = [
        (arrangement_template,
         "Apply a genre arrangement template. Creates colored regions for "
         "song sections (intro/verse/chorus/bridge/outro) with appropriate bar counts. "
         "Supports pop, rock, blues, jazz, country, metal, funk, edm, hiphop, "
         "r&b, reggae, latin, singer-songwriter, podcast."),
        (analyze_form,
         "Analyze the current project structure and suggest improvements. "
         "Examines regions, track layout, content density, pacing, and tempo. "
         "Provides actionable suggestions for arrangement improvements."),
    ]

    for func, desc in tools:
        mcp.tool()(func)

    return len(tools)
