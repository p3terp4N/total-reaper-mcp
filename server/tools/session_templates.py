"""
Session Template Tools for REAPER MCP

Tools for creating pre-configured REAPER sessions from templates.
Supports 9 session types with hardware-specific routing for
Tascam Model 12, Quad Cortex, RC-600, BeatStep Pro, and Nektar LX61+.
"""

from typing import Optional
from ..bridge import bridge


# ============================================================================
# Session Management Tools
# ============================================================================

async def create_session(
    session_type: str,
    session_name: str,
    bpm: int = 120,
    time_signature: str = "4/4",
    key: str = "",
    sample_rate: int = 48000
) -> str:
    """Create a new REAPER session from a template.

    Args:
        session_type: One of: guitar, production, songwriting, jam, podcast, mixing, tone, live, transcription
        session_name: Name for the session/project
        bpm: Tempo in BPM (default 120)
        time_signature: Time signature as "n/d" (default "4/4")
        key: Musical key (e.g. "Am", "C", "F#m") — optional
        sample_rate: Sample rate in Hz (default 48000)
    """
    result = await bridge.call_lua("CreateSession", [
        session_type, session_name, bpm, time_signature, key, sample_rate
    ])

    if result.get("ok"):
        return f"Session '{session_name}' created with template '{session_type}' at {bpm} BPM"
    else:
        raise Exception(f"Failed to create session: {result.get('error', 'Unknown error')}")


async def list_session_types() -> str:
    """List all available session template types with descriptions."""
    result = await bridge.call_lua("GetSessionConfig", ["session_types"])

    if result.get("ok"):
        return str(result.get("ret", {}))
    else:
        # Fallback to static config when REAPER is not running
        from ..session_config import STATIC_CONFIG
        types = STATIC_CONFIG.get("session_types", {})
        lines = ["Available session types:"]
        for key, info in types.items():
            lines.append(f"  {key}: {info.get('name', key)} — {info.get('description', '')}")
        return "\n".join(lines)


async def get_session_config(section: str = "all") -> str:
    """Get session template configuration.

    Args:
        section: Config section to retrieve: 'tascam', 'midi', 'plugins', 'colors', 'session_types', or 'all'
    """
    result = await bridge.call_lua("GetSessionConfig", [section])

    if result.get("ok"):
        return str(result.get("ret", {}))
    else:
        from ..session_config import STATIC_CONFIG
        if section == "all":
            return str(STATIC_CONFIG)
        return str(STATIC_CONFIG.get(section, f"Unknown section: {section}"))


async def smart_add_fx(
    track_index: int,
    preferred: str,
    fallback: str = "",
    bypassed: bool = False
) -> str:
    """Add an FX plugin to a track with automatic fallback.

    Tries the preferred plugin first. If not installed, uses the fallback.

    Args:
        track_index: 0-based track index
        preferred: Preferred plugin name (e.g. "FabFilter Pro-Q 4")
        fallback: Fallback plugin name (e.g. "ReaEQ") — uses REAPER built-in if empty
        bypassed: Whether to add the plugin in bypassed state
    """
    result = await bridge.call_lua("SmartAddFX", [
        track_index, preferred, fallback, bypassed
    ])

    if result.get("ok"):
        ret = result.get("ret", {})
        plugin_used = ret.get("plugin", preferred)
        return f"Added '{plugin_used}' to track {track_index}" + (" (bypassed)" if bypassed else "")
    else:
        raise Exception(f"Failed to add FX: {result.get('error', 'Unknown error')}")


async def scan_plugins() -> str:
    """Scan for installed plugins and return availability report.

    Uses a probe track to test which plugins from the session template
    config are actually installed. Returns a categorized report.
    """
    result = await bridge.call_lua("ScanPlugins", [])

    if result.get("ok"):
        return str(result.get("ret", {}))
    else:
        raise Exception(f"Failed to scan plugins: {result.get('error', 'Unknown error')}")


# ============================================================================
# Action Script Tools
# ============================================================================

# All available action scripts
SESSION_ACTIONS = {
    "quick_tune": "Toggle ReaTune bypass on all DI tracks",
    "reference_ab": "A/B toggle between mix and reference track",
    "reamp": "Create a reamp track from selected DI with Neural DSP",
    "arm_all_di": "Toggle arm state on all DI tracks",
    "tap_tempo": "Tap tempo (call twice within 3 seconds)",
    "idea_marker": "Drop auto-numbered IDEA marker at cursor",
    "bounce_selection": "Bounce time selection to new track",
    "chapter_marker": "Drop numbered chapter marker at cursor",
    "tone_snapshot": "Drop marker with current FX settings",
    "cycle_tone": "Cycle through tone tracks (A/B/C/D)",
    "playback_rate": "Cycle playback rate (50/70/80/90/100%)",
    "setlist_marker": "Drop SONG marker at cursor",
    "arm_next_track": "Disarm current track, arm next",
    "noise_capture": "Toggle noise capture mode on vocal tracks",
    "song_structure_marker": "Drop color-coded song structure marker",
    "chord_marker": "Drop chord marker at cursor",
    "chord_region": "Create chord region over time selection",
    "session_backup": "Save timestamped backup of current project",
    "auto_trim_silence": "Split and trim silence from selected items",
    "toggle_meters": "Toggle master track metering visibility",
    "add_guitar_od": "Add a new guitar overdub track",
    "add_vocal": "Add a new vocal track with FX chain",
    "new_take_folder": "Switch to next take for comp workflow",
    "cleanup_session": "Remove empty takes and heal splits",
    "practice_mode": "Set up practice loop with slowed playback",
    "tone_browser": "Cycle Neural DSP plugins on selected track",
}


async def run_session_action(action_name: str) -> str:
    """Run a session template action script.

    Args:
        action_name: Name of the action to run (e.g., "quick_tune", "reference_ab")
    """
    if action_name not in SESSION_ACTIONS:
        lines = [f"Unknown action: '{action_name}'", "", "Available actions:"]
        for name, desc in sorted(SESSION_ACTIONS.items()):
            lines.append(f"  {name}: {desc}")
        return "\n".join(lines)

    result = await bridge.call_lua("RunSessionAction", [action_name])

    if result.get("ok"):
        return f"Action '{action_name}' executed: {SESSION_ACTIONS[action_name]}"
    else:
        raise Exception(f"Action failed: {result.get('error', 'Unknown error')}")


async def list_session_actions() -> str:
    """List all available session template action scripts."""
    lines = ["Available session actions:", ""]
    for name, desc in sorted(SESSION_ACTIONS.items()):
        lines.append(f"  {name}: {desc}")
    return "\n".join(lines)


# ============================================================================
# Registration Function
# ============================================================================

def register_session_template_tools(mcp) -> int:
    """Register all session template tools with the MCP instance"""
    from ..dsl.session_wrappers import register_session_dsl_tools

    tools = [
        (create_session, "Create a new REAPER session from a template type"),
        (list_session_types, "List all available session template types"),
        (get_session_config, "Get session template configuration values"),
        (smart_add_fx, "Add an FX plugin with automatic preferred/fallback resolution"),
        (scan_plugins, "Scan for installed plugins and report availability"),
        (run_session_action, "Run a session template action script by name"),
        (list_session_actions, "List all available session template action scripts"),
    ]

    for func, desc in tools:
        decorated = mcp.tool()(func)

    # Also register DSL wrappers (natural language session creation)
    dsl_count = register_session_dsl_tools(mcp)

    return len(tools) + dsl_count
