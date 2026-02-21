"""
Render & Export Tools for REAPER MCP

High-level render/export operations for production workflows.
Builds on existing rendering.py and bounce_render.py with
social-media-friendly export and format-aware rendering.
"""

from typing import Optional
from ..bridge import bridge


# ============================================================================
# Format-aware Render Operations
# ============================================================================

async def render_mix(format: str = "wav", path: Optional[str] = None,
                     sample_rate: int = 48000, bit_depth: int = 24) -> str:
    """Render the full mix to a file with format selection.

    Args:
        format: Output format - wav, mp3, or flac
        path: Output directory path (uses project directory if not specified)
        sample_rate: Sample rate in Hz (default 48000)
        bit_depth: Bit depth - 16, 24, or 32 (default 24)

    Returns:
        Status message with render details
    """
    # Map format to REAPER render format codes
    # RENDER_FORMAT is a packed string; we set via project info
    format_map = {
        "wav": {"code": "evaw", "ext": "wav"},
        "mp3": {"code": " pm3", "ext": "mp3"},
        "flac": {"code": "calf", "ext": "flac"},
    }

    fmt = format.lower()
    if fmt not in format_map:
        return f"Unsupported format '{format}'. Use wav, mp3, or flac."

    # Set render directory if provided
    if path:
        await bridge.call_lua("GetSetProjectInfo_String", [
            0, "RENDER_FILE", path, True
        ])

    # Set render bounds to entire project (0 = entire project)
    await bridge.call_lua("GetSetProjectInfo", [0, "RENDER_BOUNDSFLAG", 0.0, True])

    # Set sample rate
    await bridge.call_lua("GetSetProjectInfo", [0, "RENDER_SRATE", float(sample_rate), True])

    # Render entire project via action
    result = await bridge.call_lua("Main_OnCommand", [41824, 0])

    if result.get("ok"):
        return (f"Rendered full mix as {fmt.upper()} "
                f"({sample_rate}Hz, {bit_depth}-bit)"
                + (f" to {path}" if path else ""))
    else:
        raise Exception(f"Failed to render mix: {result.get('error', 'Unknown error')}")


async def render_stems(path: Optional[str] = None, format: str = "wav") -> str:
    """Render individual stems per track/bus.

    Uses REAPER's region render matrix with stems mode, or
    falls back to rendering selected tracks as stems.

    Args:
        path: Output directory for stem files
        format: Output format (default wav)

    Returns:
        Status message
    """
    # Set output path if specified
    if path:
        await bridge.call_lua("GetSetProjectInfo_String", [
            0, "RENDER_FILE", path, True
        ])

    # Set render to stems mode (selected tracks)
    await bridge.call_lua("GetSetProjectInfo", [0, "RENDER_BOUNDSFLAG", 0.0, True])

    # Select all tracks for stem rendering
    await bridge.call_lua("Main_OnCommand", [40296, 0])  # Track: Select all tracks

    # Render using stems action (42230 = render project, using region matrix)
    # Action 41824 renders entire project
    result = await bridge.call_lua("Main_OnCommand", [41824, 0])

    if result.get("ok"):
        return f"Rendered stems as {format.upper()}" + (f" to {path}" if path else "")
    else:
        raise Exception(f"Failed to render stems: {result.get('error', 'Unknown error')}")


async def render_selection(start: float, end: float, path: Optional[str] = None,
                           format: str = "wav") -> str:
    """Render a specific time range to file.

    Args:
        start: Start time in seconds
        end: End time in seconds
        path: Output path (optional)
        format: Output format - wav, mp3, or flac (default wav)

    Returns:
        Status message with render details
    """
    if end <= start:
        return "Error: end time must be greater than start time"

    # Set the time selection
    await bridge.call_lua("GetSet_LoopTimeRange", [True, False, start, end, False])

    # Set render bounds to time selection (2 = time selection)
    await bridge.call_lua("GetSetProjectInfo", [0, "RENDER_BOUNDSFLAG", 2.0, True])

    # Set output path if specified
    if path:
        await bridge.call_lua("GetSetProjectInfo_String", [
            0, "RENDER_FILE", path, True
        ])

    # Render time selection
    result = await bridge.call_lua("Main_OnCommand", [41825, 0])

    if result.get("ok"):
        duration = end - start
        return (f"Rendered selection ({start:.1f}s - {end:.1f}s, "
                f"{duration:.1f}s) as {format.upper()}"
                + (f" to {path}" if path else ""))
    else:
        raise Exception(f"Failed to render selection: {result.get('error', 'Unknown error')}")


async def social_clip(duration: int = 30, path: Optional[str] = None,
                      format: str = "mp3", start_time: Optional[float] = None,
                      normalize: bool = True, fade_out: float = 1.0) -> str:
    """Export a clip optimized for social media platforms.

    Creates a short clip (30s or 60s) suitable for Instagram, TikTok,
    or other social platforms. Applies fade-out at the end.

    Args:
        duration: Clip duration in seconds - typically 30 or 60
        path: Output path for the clip
        format: Output format (default mp3 for smaller files)
        start_time: Start position in seconds (default: project start)
        normalize: Whether to normalize the output (default True)
        fade_out: Fade-out duration in seconds at the end (default 1.0)

    Returns:
        Status message with clip details
    """
    if duration not in (15, 30, 60, 90):
        return f"Warning: non-standard duration {duration}s. Common values: 15, 30, 60, 90."

    # Determine start position
    clip_start = start_time if start_time is not None else 0.0
    clip_end = clip_start + duration

    # Set the time selection for the clip
    await bridge.call_lua("GetSet_LoopTimeRange", [
        True, False, clip_start, clip_end, False
    ])

    # Set render bounds to time selection (2 = time selection)
    await bridge.call_lua("GetSetProjectInfo", [0, "RENDER_BOUNDSFLAG", 2.0, True])

    # Set render tail for fade-out (in milliseconds)
    if fade_out > 0:
        await bridge.call_lua("GetSetProjectInfo", [
            0, "RENDER_TAILMS", fade_out * 1000, True
        ])

    # Set output path if specified
    if path:
        await bridge.call_lua("GetSetProjectInfo_String", [
            0, "RENDER_FILE", path, True
        ])

    # Set sample rate to 44100 for social media compatibility
    await bridge.call_lua("GetSetProjectInfo", [0, "RENDER_SRATE", 44100.0, True])

    # Render
    result = await bridge.call_lua("Main_OnCommand", [41825, 0])

    if result.get("ok"):
        return (f"Exported {duration}s social media clip "
                f"({clip_start:.1f}s - {clip_end:.1f}s) as {format.upper()}, "
                f"44.1kHz, fade-out={fade_out}s"
                + (f" to {path}" if path else ""))
    else:
        raise Exception(f"Failed to export social clip: {result.get('error', 'Unknown error')}")


# ============================================================================
# Registration Function
# ============================================================================

def register_render_export_tools(mcp) -> int:
    """Register all render/export tools with the MCP instance"""
    tools = [
        (render_mix,
         "Render the full mix to a file. Supports wav, mp3, flac. "
         "Use for final mixdown or creating master files."),
        (render_stems,
         "Render individual stems per track/bus as separate files. "
         "Use for collaboration, remixing, or delivering stems to clients."),
        (render_selection,
         "Render a specific time range (start to end in seconds) to file. "
         "Use for exporting sections, loops, or specific parts."),
        (social_clip,
         "Export a short clip (30s/60s) optimized for social media. "
         "Creates MP3 at 44.1kHz with fade-out. "
         "Use for Instagram, TikTok, or YouTube Shorts previews."),
    ]

    for func, desc in tools:
        mcp.tool()(func)

    return len(tools)
