"""
Session Template DSL Wrappers — Natural language session creation

Provides high-level wrappers that map natural language descriptions
to session template tool calls. Registered as additional MCP tools
in the "Session Templates" category.
"""

from ..bridge import bridge
from ..session_config import STATIC_CONFIG


# Session type aliases for natural language matching
SESSION_ALIASES = {
    # Guitar
    "guitar": "guitar",
    "guitar recording": "guitar",
    "record guitar": "guitar",
    "guitar session": "guitar",
    # Production
    "production": "production",
    "full production": "production",
    "full session": "production",
    "produce": "production",
    "write music": "production",
    # Songwriting
    "songwriting": "songwriting",
    "sketch": "songwriting",
    "idea": "songwriting",
    "quick idea": "songwriting",
    "write a song": "songwriting",
    # Jam
    "jam": "jam",
    "loop": "jam",
    "jam session": "jam",
    "jam loop": "jam",
    "looping": "jam",
    # Podcast
    "podcast": "podcast",
    "voiceover": "podcast",
    "voice over": "podcast",
    "interview": "podcast",
    "recording podcast": "podcast",
    # Mixing
    "mixing": "mixing",
    "mix": "mixing",
    "mix stems": "mixing",
    "stem mixing": "mixing",
    "import stems": "mixing",
    # Tone design
    "tone": "tone",
    "tone design": "tone",
    "amp comparison": "tone",
    "compare amps": "tone",
    "dial in tone": "tone",
    # Live
    "live": "live",
    "live performance": "live",
    "gig": "live",
    "concert": "live",
    "perform": "live",
    # Transcription
    "transcription": "transcription",
    "learn": "transcription",
    "learning": "transcription",
    "practice": "transcription",
    "transcribe": "transcription",
    "learn a song": "transcription",
}


def resolve_session_type(description: str) -> str | None:
    """Resolve a natural language description to a session type key."""
    desc = description.lower().strip()
    # Exact match
    if desc in SESSION_ALIASES:
        return SESSION_ALIASES[desc]
    # Substring match
    for alias, session_type in SESSION_ALIASES.items():
        if alias in desc:
            return session_type
    return None


async def setup_session(
    description: str,
    session_name: str = "",
    bpm: int = 120,
) -> str:
    """Set up a REAPER session from a natural language description.

    Interprets descriptions like "set up for guitar recording" or
    "I want to mix some stems" and creates the appropriate session.

    Args:
        description: Natural language description of what you want to do
        session_name: Optional session name (auto-generated if empty)
        bpm: Tempo in BPM (default 120)
    """
    session_type = resolve_session_type(description)
    if not session_type:
        # List available types for the user
        types = STATIC_CONFIG.get("session_types", {})
        lines = [f"Could not determine session type from: '{description}'", "", "Available types:"]
        for key, info in types.items():
            lines.append(f"  {key}: {info['name']} — {info['description']}")
        return "\n".join(lines)

    type_info = STATIC_CONFIG.get("session_types", {}).get(session_type, {})
    if not session_name:
        import datetime
        session_name = f"{type_info.get('name', session_type)} {datetime.datetime.now().strftime('%Y-%m-%d %H%M')}"

    result = await bridge.call_lua("CreateSession", [
        session_type, session_name, bpm, "4/4", "", 48000
    ])

    if result.get("ok"):
        return f"Session '{session_name}' created ({type_info.get('name', session_type)}) at {bpm} BPM"
    else:
        return f"Failed: {result.get('error', 'Unknown error')}"


async def what_sessions_are_available() -> str:
    """List all available session types with descriptions.

    Returns a formatted list of session templates you can create.
    """
    types = STATIC_CONFIG.get("session_types", {})
    lines = ["Available session templates:", ""]
    for key, info in types.items():
        lines.append(f"  {key}: {info['name']}")
        lines.append(f"    {info['description']}")
        lines.append("")
    return "\n".join(lines)


def register_session_dsl_tools(mcp) -> int:
    """Register session DSL wrapper tools with the MCP instance."""
    tools = [
        (setup_session, "Set up a REAPER session from a natural language description"),
        (what_sessions_are_available, "List all available session template types"),
    ]

    for func, desc in tools:
        mcp.tool()(func)

    return len(tools)
