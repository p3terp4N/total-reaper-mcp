"""
Neural DSP Plugin Tools for REAPER MCP

Tools for detecting, controlling, and managing Neural DSP guitar plugins
(Archetype series, etc.) loaded in REAPER. Uses REAPER's TrackFX API
to enumerate parameters, switch presets, snapshot/restore settings,
and toggle signal chain blocks.
"""

import json
from typing import Optional
from ..bridge import bridge


# ============================================================================
# Neural DSP Tools
# ============================================================================

async def neural_dsp_find() -> str:
    """Find all Neural DSP plugins loaded in the current REAPER session.

    Scans all tracks for Neural DSP plugins (Archetype, Darkglass,
    Parallax, Soldano, etc.) and returns their locations and status.
    """
    result = await bridge.call_lua("NeuralDSP_FindPlugins", [])

    if not result.get("ok"):
        raise Exception(f"Failed to scan for plugins: {result.get('error', 'Unknown error')}")

    plugins = result.get("ret", [])
    if not plugins:
        return "No Neural DSP plugins found in the current session."

    lines = [f"Found {len(plugins)} Neural DSP plugin(s):\n"]
    for p in plugins:
        status = "ON" if p.get("enabled") else "BYPASSED"
        lines.append(
            f"  Track {p['track_idx']} ({p['track_name']}) → "
            f"FX {p['fx_idx']}: {p['fx_name']} [{status}]"
        )
    return "\n".join(lines)


async def neural_dsp_params(
    track: int,
    fx: int,
) -> str:
    """List all parameters for a Neural DSP plugin instance.

    Args:
        track: Track index (0-based)
        fx: FX index on the track (0-based)
    """
    result = await bridge.call_lua("NeuralDSP_GetParams", [track, fx])

    if not result.get("ok"):
        raise Exception(result.get("error", "Unknown error"))

    ret = result["ret"]
    lines = [f"{ret['fx_name']} — {ret['param_count']} parameters:\n"]
    for p in ret["params"]:
        lines.append(f"  [{p['idx']:3d}] {p['name']}: {p['value']:.4f} (range {p['min']:.2f}–{p['max']:.2f})")
    return "\n".join(lines)


async def neural_dsp_get(
    track: int,
    fx: int,
    param: str,
) -> str:
    """Get a Neural DSP plugin parameter value by name (fuzzy match).

    Args:
        track: Track index (0-based)
        fx: FX index on the track (0-based)
        param: Parameter name to search for (e.g. "gain", "bass", "treble")
    """
    result = await bridge.call_lua("NeuralDSP_GetParamByName", [track, fx, param])

    if not result.get("ok"):
        raise Exception(result.get("error", "Unknown error"))

    ret = result["ret"]
    return (
        f"{ret['name']} (#{ret['idx']}): {ret['value']:.4f} "
        f"(range {ret['min']:.2f}–{ret['max']:.2f}, match: {ret['match_score']}%)"
    )


async def neural_dsp_set(
    track: int,
    fx: int,
    param: str,
    value: float,
) -> str:
    """Set a Neural DSP plugin parameter by name (fuzzy match).

    Args:
        track: Track index (0-based)
        fx: FX index on the track (0-based)
        param: Parameter name to search for (e.g. "gain", "bass", "treble")
        value: New value (0.0–1.0 normalized range)
    """
    result = await bridge.call_lua("NeuralDSP_SetParamByName", [track, fx, param, value])

    if not result.get("ok"):
        raise Exception(result.get("error", "Unknown error"))

    ret = result["ret"]
    return (
        f"{ret['name']} (#{ret['idx']}): {ret['old_value']:.4f} → {ret['new_value']:.4f} "
        f"(match: {ret['match_score']}%)"
    )


async def neural_dsp_preset(
    track: int,
    fx: int,
    preset: str = "",
) -> str:
    """Get or switch Neural DSP plugin presets.

    Args:
        track: Track index (0-based)
        fx: FX index on the track (0-based)
        preset: Preset name to switch to (leave empty to get current preset)
    """
    if preset:
        result = await bridge.call_lua("NeuralDSP_SetPreset", [track, fx, preset])
        if not result.get("ok"):
            raise Exception(result.get("error", "Unknown error"))
        return f"Switched to preset: {result['ret']['preset_name']}"
    else:
        result = await bridge.call_lua("NeuralDSP_GetPreset", [track, fx])
        if not result.get("ok"):
            raise Exception(result.get("error", "Unknown error"))
        ret = result["ret"]
        return f"{ret['fx_name']} — Current preset: {ret['preset_name']}"


async def neural_dsp_snapshot(
    track: int,
    fx: int,
    action: str = "save",
    snapshot_json: str = "",
) -> str:
    """Save or restore a full parameter snapshot for A/B comparison.

    Args:
        track: Track index (0-based)
        fx: FX index on the track (0-based)
        action: "save" to capture current state, "restore" to apply a saved snapshot
        snapshot_json: JSON snapshot data (required for restore)
    """
    if action == "save":
        result = await bridge.call_lua("NeuralDSP_Snapshot", [track, fx])
        if not result.get("ok"):
            raise Exception(result.get("error", "Unknown error"))
        ret = result["ret"]
        snapshot_str = json.dumps(ret["snapshot"])
        return (
            f"Snapshot saved for {ret['fx_name']} (preset: {ret['preset_name']}, "
            f"{ret['param_count']} params).\n\n"
            f"Snapshot data (use with action='restore'):\n{snapshot_str}"
        )
    elif action == "restore":
        if not snapshot_json:
            return "snapshot_json is required for restore action."
        try:
            snapshot = json.loads(snapshot_json)
        except json.JSONDecodeError as e:
            return f"Invalid snapshot JSON: {e}"
        result = await bridge.call_lua("NeuralDSP_RestoreSnapshot", [track, fx, snapshot])
        if not result.get("ok"):
            raise Exception(result.get("error", "Unknown error"))
        return f"Restored {result['ret']['params_restored']} parameters."
    else:
        return f"Unknown action: '{action}'. Use 'save' or 'restore'."


async def neural_dsp_chain(
    track: int,
    fx: int,
) -> str:
    """Show the signal chain state of a Neural DSP plugin.

    Lists which blocks (stomp, amp, cab, effects) are enabled or bypassed.

    Args:
        track: Track index (0-based)
        fx: FX index on the track (0-based)
    """
    result = await bridge.call_lua("NeuralDSP_GetSignalChain", [track, fx])

    if not result.get("ok"):
        raise Exception(result.get("error", "Unknown error"))

    ret = result["ret"]
    plugin_status = "ON" if ret["fx_enabled"] else "BYPASSED"
    lines = [f"{ret['fx_name']} [{plugin_status}]\n"]

    blocks = ret.get("blocks", [])
    if blocks:
        lines.append("Signal chain blocks:")
        for b in blocks:
            status = "ON" if b["enabled"] else "OFF"
            lines.append(f"  [{status:3s}] {b['name']} (#{b['idx']})")
    else:
        lines.append("No bypass/enable parameters detected. Use neural_dsp_params to see all parameters.")

    return "\n".join(lines)


async def neural_dsp_toggle(
    track: int,
    fx: int,
    block: str,
) -> str:
    """Toggle a signal chain block on/off in a Neural DSP plugin.

    Use "plugin" or "fx" to toggle the overall plugin bypass.
    Use a block name (e.g. "gate", "delay", "reverb") to toggle a specific block.

    Args:
        track: Track index (0-based)
        fx: FX index on the track (0-based)
        block: Block name to toggle (or "plugin"/"fx" for overall bypass)
    """
    result = await bridge.call_lua("NeuralDSP_ToggleBlock", [track, fx, block])

    if not result.get("ok"):
        raise Exception(result.get("error", "Unknown error"))

    ret = result["ret"]
    old = "ON" if ret["was_enabled"] else "OFF"
    new = "ON" if ret["now_enabled"] else "OFF"
    return f"{ret['name']}: {old} → {new}"


# ============================================================================
# Registration
# ============================================================================

def register_neural_dsp_tools(mcp) -> int:
    """Register all Neural DSP tools with the MCP instance."""
    tools = [
        neural_dsp_find,
        neural_dsp_params,
        neural_dsp_get,
        neural_dsp_set,
        neural_dsp_preset,
        neural_dsp_snapshot,
        neural_dsp_chain,
        neural_dsp_toggle,
    ]

    for func in tools:
        mcp.tool()(func)

    return len(tools)
