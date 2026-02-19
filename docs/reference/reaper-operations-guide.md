# REAPER Operations Guide

Practical operational reference for working with REAPER from this project. Covers UI navigation, script loading, key bindings, and the concepts needed to deploy and test the MCP bridge and session templates.

**Source**: Official REAPER v7.61 documentation, SWS Extension docs, community guides. Scraped 2026-02-19.

---

## Key Paths (macOS)

| Path | Purpose |
|------|---------|
| `/Applications/REAPER.app` | Application |
| `~/Library/Application Support/REAPER/` | **Resource path** (all config, scripts, plugins) |
| `~/Library/Application Support/REAPER/Scripts/` | ReaScripts directory |
| `~/Library/Application Support/REAPER/Scripts/mcp_bridge_data/` | MCP bridge IPC directory |
| `~/Library/Application Support/REAPER/reaper.ini` | Main config file |
| `~/Library/Application Support/REAPER/reaper-kb.ini` | Keyboard shortcut bindings |
| `~/Library/Application Support/REAPER/UserPlugins/` | SWS extension DLL/dylib location |

To find the resource path from within REAPER: **Options > Show REAPER resource path in explorer/finder**.

---

## Actions Window

The Actions window is the central hub for running scripts, binding keys, and managing custom actions.

### Opening It

- **Menu**: Actions > Show action list
- **Default shortcut**: `?` (question mark key)
- **Action ID**: 40605

### Layout

The Actions window has:
- **Top**: Section filter dropdown (Main, MIDI Editor, Media Explorer, etc.) + search/filter bar
- **Middle**: Scrollable list of all actions (built-in + custom + scripts)
- **Bottom**: TWO separate button groups (this distinction is critical):

```
┌─────────────────────────────────────────────────────────────────────┐
│ Section: [Main ▼]    Filter: [________________] [x]                │
│                                                                     │
│  ID      Description                                                │
│  ─────── ───────────────────────────────────────────────────────     │
│  40001   File: New project                                          │
│  40002   File: Open project...                                      │
│  ...     ...                                                        │
│  _abc123 Script: mcp_bridge_file_v2.lua                             │
│                                                                     │
│                                                                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  [Run/Close]  [New...]  [Copy...]          ← Custom Action buttons  │
│                                                                     │
│  ReaScript: [New...] [Load...] [Edit...]   ← ReaScript buttons      │
│                                                                     │
│  Shortcut: [Add...] [Delete]               ← Key binding buttons    │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### CRITICAL: The Two "New..." Buttons

There are TWO buttons labeled "New..." in the Actions window:

1. **Top row "New..."** — Creates a **custom action** (macro that chains existing actions). This is NOT for scripts.
2. **"ReaScript: New..."** — Creates a **new ReaScript file** (.lua, .eel, .py). This IS for scripts.

The "ReaScript:" label is a group header for the three buttons: New..., Load..., Edit...

### Button Reference

| Button | Group | What It Does |
|--------|-------|-------------|
| Run/Close | Action | Runs selected action and closes window |
| New... | Custom Action | Creates a custom action (macro chaining existing actions) |
| Copy... | Custom Action | Duplicates selected custom action for editing |
| ReaScript: New... | ReaScript | Creates a new empty script file, prompts for save location |
| ReaScript: Load... | ReaScript | Loads existing .lua/.eel/.py file into action list |
| ReaScript: Edit... | ReaScript | Opens selected script in ReaScript IDE |
| Shortcut: Add... | Shortcuts | Assigns keyboard shortcut to selected action |
| Shortcut: Delete | Shortcuts | Removes keyboard shortcut from selected action |

---

## Loading a Script (e.g., the MCP Bridge)

### Method 1: Actions Window (Recommended)

1. Open REAPER
2. Open Actions window: **Actions > Show action list** (or press `?`)
3. Click **ReaScript: "Load..."** (bottom of window, in the ReaScript button group)
4. Navigate to the script file (e.g., `~/Library/Application Support/REAPER/Scripts/mcp_bridge_file_v2.lua`)
5. Select file and click **Open** — multiple selection is allowed
6. Script appears in the action list with prefix "Script: "
7. Select it and click **Run/Close** (or double-click) to run it

### Method 2: ReaScript Run Action

1. Open Actions window (`?`)
2. In the filter/search bar, type: `ReaScript: run`
3. Find the action **"ReaScript: run..."** (built-in action)
4. Double-click it — a file picker opens
5. Navigate to and select the script file
6. Script runs immediately (but is NOT permanently added to action list)

### Method 3: Run Last Script

After running a script once via Method 2, you can re-run it:
- Action: **"ReaScript: run last script"**
- No default shortcut — you can assign one

### After Loading

Once loaded, a script is permanently in the action list (persists across REAPER restarts). You can:
- **Run it**: Select in action list, click Run (or double-click)
- **Bind to key**: Select it, click **Shortcut: Add...**, press desired key combo
- **Bind to toolbar**: Right-click a toolbar, customize, add the script action
- **Run from ReaScript**: `reaper.Main_OnCommand(commandID, 0)` — get ID by right-clicking > "Copy selected action ID"

---

## Creating a New Script

1. Open Actions window (`?`)
2. Click **ReaScript: "New..."** (NOT the top "New..." button)
3. Choose save location — default is `~/Library/Application Support/REAPER/Scripts/`
4. Enter filename with extension: `.lua` for Lua, `.eel` for EEL2, `.py` for Python
5. The ReaScript IDE opens with an empty script
6. Write code, press **Ctrl+S** to save
7. Script is automatically added to the action list

---

## Editing/Debugging Scripts

1. Select the script in the Actions window
2. Click **ReaScript: "Edit..."**
3. The **ReaScript IDE** opens:
   - Left pane: code editor
   - Right pane: variable watch (built-in + user defined)
   - Bottom: output/console
4. **Ctrl+S**: Save and run the script
5. Error messages show line number and description

### ReaScript Console

To print debug output from Lua scripts:
```lua
reaper.ShowConsoleMsg("Debug: value = " .. tostring(value) .. "\n")
```

The console window appears automatically when `ShowConsoleMsg` is called. To clear it:
```lua
reaper.ShowConsoleMsg("")  -- does NOT clear
reaper.ClearConsole()      -- clears the console (REAPER v6.17+)
```

---

## Deferred (Background) Scripts

The MCP bridge runs as a **deferred script** — it stays running in the background using `reaper.defer()`.

### How Deferred Scripts Work

```lua
function main_loop()
    -- Do periodic work (check for bridge commands, etc.)
    reaper.defer(main_loop)  -- Schedule next iteration
end

function cleanup()
    -- Called when script terminates
end

reaper.atexit(cleanup)
reaper.defer(main_loop)  -- Start the loop
```

### Managing Running Scripts

- **View running scripts**: Actions menu shows currently running deferred scripts
- **Stop a script**: Click it in the Actions menu running scripts list
- **Note**: When a deferred script is running, running it again from the action list will start a SECOND instance (unless the script guards against this)

### Bridge-Specific Notes

The MCP bridge (`mcp_bridge_file_v2.lua`) runs as a deferred script:
- Polls `~/Library/Application Support/REAPER/Scripts/mcp_bridge_data/` for command files
- Writes response files to same directory
- Shows "REAPER MCP Bridge (File-based, Full API) started" in console on startup
- Stays running until manually stopped or REAPER closes

---

## Keyboard Shortcuts

### Default Shortcuts (Most Used)

| Shortcut | Action |
|----------|--------|
| `?` | Open Actions window |
| `Ctrl+N` | New project |
| `Ctrl+O` | Open project |
| `Ctrl+S` | Save project |
| `Space` | Play/Stop |
| `R` | Toggle record |
| `Ctrl+Z` | Undo |
| `Ctrl+Shift+Z` | Redo |
| `Ctrl+T` | Insert new track |
| `S` | Split items at cursor |
| `F5` | Toggle mixer |
| `Ctrl+M` | Toggle metronome |
| `Home` | Go to start of project |
| `End` | Go to end of project |
| `Tab` | Move to next transient |
| `Ctrl+L` | Set loop points to time selection |
| `N` | Toggle ripple editing |

### Assigning Custom Shortcuts

1. Open Actions window (`?`)
2. Find/select the action or script
3. Click **Shortcut: Add...**
4. Press the key combination you want to assign
5. Click **OK**
6. If the key is already assigned, REAPER warns you — you can reassign or cancel

### Shortcut Sections

Shortcuts are section-specific. The "Section" dropdown at the top of Actions window determines context:
- **Main**: General REAPER shortcuts
- **Main (alt recording)**: Alternative shortcuts during recording
- **MIDI Editor**: Shortcuts when MIDI editor has focus
- **MIDI Event List Editor**: Shortcuts in event list view
- **Media Explorer**: Shortcuts in media explorer

---

## Key Menu Items

### Options Menu

| Item | Purpose |
|------|---------|
| Options > Show REAPER resource path... | Opens resource directory in Finder |
| Options > Preferences (Ctrl+P) | Opens preferences dialog |
| Options > Preferences > Audio > Device | Audio interface selection (ASIO/CoreAudio) |
| Options > Preferences > Plug-Ins > VST | VST plugin scan paths |
| Options > Preferences > Plug-Ins > ReaScript | Python path config, enable/disable |
| Options > Preferences > Media > MIDI | MIDI device enable/disable |
| Options > Layouts | Window layout switching |

### View Menu

| Item | Purpose |
|------|---------|
| View > Screensets/Layouts > Screensets | Save/recall window arrangements (slots 1-10) |
| View > Routing Matrix | Visual I/O routing overview |
| View > Track Manager | Bulk track visibility/properties |
| View > Big Clock | Large transport time display |
| View > Performance Meter | CPU/disk monitoring |

### Insert Menu

| Item | Purpose |
|------|---------|
| Insert > New track (Ctrl+T) | Add track |
| Insert > Virtual instrument on new track | Add VSTi with routing |
| Insert > Media file... | Import audio/MIDI files |

### Extensions Menu

Only appears if SWS Extension is installed:

| Item | Purpose |
|------|---------|
| Extensions > About | SWS version info |
| Extensions > Command parameters... | SWS action search and parameter editing |

---

## Project Extended State

Used by the MCP bridge to persist data (like backing track chart data) within project files.

```lua
-- Store data (saved with project file)
reaper.SetProjExtState(0, "section", "key", "value")

-- Retrieve data
local retval, value = reaper.GetProjExtState(0, "section", "key")
-- retval: 0 = key not found, >0 = found

-- Global state (persists across projects, stored in reaper-extstate.ini)
reaper.SetExtState("section", "key", "value", true)  -- true = persist across sessions
local value = reaper.GetExtState("section", "key")
```

The MCP bridge uses `MCP_BackingTrack` section to store chart data for `RegeneratePart`.

---

## SWS Extension

The [SWS Extension](http://www.sws-extension.org/) adds ~900 additional actions and API functions to REAPER. Several bridge functions depend on it.

### Installation (macOS)

1. Download from https://www.sws-extension.org/
2. The installer places `reaper_sws-arm64.dylib` (or `reaper_sws64.dylib`) into `~/Library/Application Support/REAPER/UserPlugins/`
3. Restart REAPER
4. Verify: **Extensions** menu appears in menu bar

### Key SWS API Functions Used by This Project

| Function | Purpose |
|----------|---------|
| `SNM_GetIntConfigVar(name, errval)` | Read REAPER internal config variable |
| `SNM_SetIntConfigVar(name, value)` | Write REAPER internal config variable |
| `BR_GetMediaTrackByGUID(proj, guid)` | Find track by GUID |
| `CF_GetClipboard(buf)` | Read clipboard |

### Checking if SWS is Available

```lua
if reaper.SNM_GetIntConfigVar then
    -- SWS is installed
    local grid = reaper.SNM_GetIntConfigVar("projgridmin", -1)
else
    -- SWS not available, use fallback
end
```

---

## ReaPack (Package Manager)

[ReaPack](https://reapack.com/) is a package manager for REAPER scripts and extensions.

### Installation

1. Download from https://reapack.com/
2. Place `reaper_reapack-arm64.dylib` in `~/Library/Application Support/REAPER/UserPlugins/`
3. Restart REAPER
4. Access via **Extensions > ReaPack**

### Key Operations

| Action | How |
|--------|-----|
| Browse packages | Extensions > ReaPack > Browse packages |
| Sync repositories | Extensions > ReaPack > Synchronize packages |
| Import repository | Extensions > ReaPack > Import repositories... |
| Manage repos | Extensions > ReaPack > Manage repositories... |

---

## Audio Device Setup

### CoreAudio (macOS)

1. Options > Preferences > Audio > Device
2. Audio system: **CoreAudio**
3. Audio device: Select your interface (e.g., "Tascam Model 12")
4. Sample rate: Match your interface (e.g., 48000)
5. Block size: Lower = less latency, higher = more stable (256-512 typical)

### MIDI Devices

1. Options > Preferences > Media > MIDI Devices (macOS: MIDI > MIDI Devices)
2. Double-click a device to enable it
3. Check "Enable input" and/or "Enable output"
4. Device names may vary by OS

---

## Undo System

REAPER has a granular undo system. Scripts should use undo blocks:

```lua
reaper.Undo_BeginBlock()
-- ... do work ...
reaper.Undo_EndBlock("Description of what changed", -1)
```

Undo flags for `Undo_EndBlock()`:
- `1`: Track configurations (name, color, routing)
- `2`: Track FX
- `4`: Track items (media items, takes)
- `8`: Project states (tempo, time sig)
- `16`: Freeze states
- `-1`: All of the above (safest default)

---

## Common Troubleshooting

### Script Won't Load

- **"No such file"**: Check the file path. Use Options > Show resource path to verify Scripts directory.
- **"Unknown API function"**: Script requires newer REAPER version or SWS extension.
- **Lua error on line X**: Open in ReaScript IDE (Edit...) to debug.

### Bridge Not Starting

- Check REAPER console (View > Show console, or Ctrl+Alt+M on Mac) for error messages
- Verify file exists: `ls ~/Library/Application\ Support/REAPER/Scripts/mcp_bridge_file_v2.lua`
- Verify bridge data directory exists: `ls ~/Library/Application\ Support/REAPER/Scripts/mcp_bridge_data/`
- Try running from Actions window again

### No Audio

- Check Options > Preferences > Audio > Device — correct interface selected?
- Check track arm status (red button on track)
- Check track input (click input selector on track header)
- Check monitoring mode on track

### MIDI Not Working

- Options > Preferences > MIDI Devices — is your controller enabled?
- Check track input is set to correct MIDI device/channel
- Verify MIDI monitor shows activity (View > MIDI Input Monitor)

---

## External References

- **Official User Guide (PDF)**: https://www.reaper.fm/userguide/ReaperUserGuide761.pdf
- **Keyboard Shortcuts (PDF)**: https://user.cockos.com/~glazfolk/ReaperKeyboardShortcuts.pdf
- **ReaScript API Reference**: https://www.reaper.fm/sdk/reascript/reascripthelp.html
- **SWS Extension**: https://www.sws-extension.org/
- **ReaPack**: https://reapack.com/
- **REAPER Forum**: https://forum.cockos.com/forumdisplay.php?f=20
- **ReaScript Forum**: https://forum.cockos.com/forumdisplay.php?f=3
