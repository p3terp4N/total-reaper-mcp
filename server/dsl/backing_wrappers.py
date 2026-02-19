"""
Backing Track DSL Wrappers — Natural language backing track generation

Provides high-level wrappers that parse natural language descriptions
like "backing track for Wonderwall by Oasis" into structured tool calls.
Registered as an additional MCP tool in the "Backing Tracks" category.
"""

import re
from typing import Optional


# Regex patterns for natural language backing track requests
_BACKING_PATTERNS = [
    # "backing track for Song by Artist"
    re.compile(
        r'(?:backing|jam)\s+track\s+(?:for\s+)?["\']?(.+?)["\']?\s+by\s+["\']?(.+?)["\']?$',
        re.IGNORECASE,
    ),
    # "Song by Artist" (simple format)
    re.compile(
        r'^["\']?(.+?)["\']?\s+by\s+["\']?(.+?)["\']?$',
        re.IGNORECASE,
    ),
]


def parse_backing_request(description: str) -> Optional[dict]:
    """Parse a natural language backing track request.

    Accepts formats like:
    - "backing track for Wonderwall by Oasis"
    - "jam track for All Along the Watchtower by Jimi Hendrix"
    - "Hotel California by Eagles"
    - '"Bohemian Rhapsody" by "Queen"'

    Returns:
        dict with "song" and "artist" keys, or None if not parseable.
    """
    desc = description.strip()
    for pattern in _BACKING_PATTERNS:
        match = pattern.match(desc)
        if match:
            return {
                "song": match.group(1).strip().strip("'\""),
                "artist": match.group(2).strip().strip("'\""),
            }
    return None


async def make_backing_track(
    description: str,
    instruments: str = "drums,bass",
    style: str = "genre",
) -> str:
    """Generate a backing track from a natural language description.

    Parses descriptions like "backing track for Wonderwall by Oasis"
    and generates MIDI backing tracks in REAPER.

    Args:
        description: Natural language description (e.g. "backing track for Song by Artist")
        instruments: Comma-separated instruments (drums, bass, keys, guitar)
        style: Style approach — "genre" or a specific genre name
    """
    parsed = parse_backing_request(description)
    if not parsed:
        return (
            f"Could not parse backing track request: '{description}'. "
            "Try formats like:\n"
            "  - 'backing track for Wonderwall by Oasis'\n"
            "  - 'Hotel California by Eagles'\n"
            "  - 'jam track for Superstition by Stevie Wonder'"
        )

    from ..tools.backing_tracks import generate_backing_track
    return await generate_backing_track(
        song=parsed["song"],
        artist=parsed["artist"],
        instruments=instruments,
        style=style,
    )


def register_backing_dsl_tools(mcp) -> int:
    """Register backing track DSL wrapper tools with the MCP instance."""
    tools = [
        (make_backing_track, "Generate a backing track from a natural language description"),
    ]

    for func, desc in tools:
        mcp.tool()(func)

    return len(tools)
