# REAPER API Reference Documentation

Scraped from official sources for use during development. These docs are consulted by Claude when adding new tools, fixing bugs, or understanding REAPER API behavior.

## Files

| File | Source | Size | Description |
|------|--------|------|-------------|
| `reascript-api-v7.60.md` | [reaper.fm](https://www.reaper.fm/sdk/reascript/reascripthelp.html) | ~580KB | Official ReaScript API reference (v7.60). Function signatures, parameters, return values for all ReaScript methods. |
| `reascript-api-full-v7.38.md` | [Ultraschall/Reaper Internals](https://mespotin.uber.space/Ultraschall/Reaper_Api_Documentation.html) | ~3.5MB | Comprehensive API docs including SWS extension functions, detailed descriptions, code examples, and cross-references. |
| `reascript-guide.md` | [reaper.fm](https://www.reaper.fm/sdk/reascript/reascript.php) | ~15KB | ReaScript overview: how to write scripts in EEL2, Lua, and Python. IDE setup, debugging, script distribution. |
| `reaper-config-variables.md` | [Ultraschall/Reaper Internals](https://mespotin.uber.space/Ultraschall/Reaper_Config_Variables.html) | ~600KB | REAPER configuration variables accessible via `SNM_GetIntConfigVar` / `SNM_SetIntConfigVar` (SWS extension). |

## When to Use

- **Adding new bridge functions**: Check `reascript-api-v7.60.md` for exact Lua function signatures
- **SWS extension functions**: Check `reascript-api-full-v7.38.md` (includes SWS/S&M functions)
- **Config variables** (grid, snap, project settings): Check `reaper-config-variables.md`
- **Understanding ReaScript conventions**: Check `reascript-guide.md`

## Freshness

Scraped 2026-02-19. Re-scrape after REAPER major version updates.
