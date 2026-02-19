-- lib/backing/bass.lua — Bass line pattern library for backing track generation
-- Returns MIDI note data tables for 10 genres plus a simple fallback.
-- Each pattern function takes (chord_name, section_type, bar_in_phrase) and
-- returns a table of {pitch, start_beats, length_beats, velocity} for ONE bar.

local bass = {}

-- ============================================================================
-- Root Notes (octave 2, C2 = MIDI 36)
-- ============================================================================

local ROOT_NOTES = {
    C  = 36, Cs = 37, Db = 37,
    D  = 38, Ds = 39, Eb = 39,
    E  = 40,
    F  = 41, Fs = 42, Gb = 42,
    G  = 43, Gs = 44, Ab = 44,
    A  = 45, As = 46, Bb = 46,
    B  = 47,
}

-- ============================================================================
-- Intervals (semitone offsets from root)
-- ============================================================================

local INTERVALS = {
    unison     = 0,
    minor2     = 1,
    major2     = 2,
    minor3     = 3,
    major3     = 4,
    perfect4   = 5,
    tritone    = 6,
    perfect5   = 7,
    minor6     = 8,
    major6     = 9,
    minor7     = 10,
    major7     = 11,
    octave     = 12,
}

-- ============================================================================
-- Chord Parsing
-- ============================================================================

--- Parse a chord name into root MIDI pitch and quality string.
-- Handles: C, Cm, C7, Cmaj7, Cm7, Cdim, Caug, Csus4, C#m, Bb7, etc.
-- @param chord_name string e.g. "Am7", "F#dim", "Bb"
-- @return number root_pitch, string quality
local function parse_chord(chord_name)
    if not chord_name or chord_name == "" then
        return ROOT_NOTES.C, "major"
    end

    -- Extract root note (1-2 characters: letter + optional # or b)
    local root_str, quality_str
    local first = chord_name:sub(1, 1):upper()
    local second = chord_name:sub(2, 2)

    if second == "#" or second == "b" then
        root_str = first .. (second == "#" and "s" or "b")
        quality_str = chord_name:sub(3)
    else
        root_str = first
        quality_str = chord_name:sub(2)
    end

    local root = ROOT_NOTES[root_str] or ROOT_NOTES.C

    -- Determine quality from remaining string
    local quality = "major"
    if quality_str:find("^dim") then
        quality = "dim"
    elseif quality_str:find("^aug") then
        quality = "aug"
    elseif quality_str:find("^sus4") then
        quality = "sus4"
    elseif quality_str:find("^sus2") then
        quality = "sus2"
    elseif quality_str:find("^m") and not quality_str:find("^maj") then
        if quality_str:find("^m7") then
            quality = "m7"
        else
            quality = "minor"
        end
    elseif quality_str:find("^maj7") then
        quality = "maj7"
    elseif quality_str:find("^7") then
        quality = "dom7"
    end

    return root, quality
end

-- ============================================================================
-- Interval Helpers
-- ============================================================================

--- Get the fifth above a root.
-- @param root number MIDI pitch
-- @return number MIDI pitch of the fifth
local function fifth(root)
    return root + INTERVALS.perfect5
end

--- Get the third above a root, adjusted for chord quality.
-- @param root number MIDI pitch
-- @param quality string Chord quality
-- @return number MIDI pitch of the third
local function third(root, quality)
    if quality == "minor" or quality == "m7" or quality == "dim" then
        return root + INTERVALS.minor3
    elseif quality == "sus4" then
        return root + INTERVALS.perfect4
    elseif quality == "sus2" then
        return root + INTERVALS.major2
    else
        return root + INTERVALS.major3
    end
end

--- Get the seventh above a root, adjusted for chord quality.
-- @param root number MIDI pitch
-- @param quality string Chord quality
-- @return number MIDI pitch of the seventh
local function seventh(root, quality)
    if quality == "maj7" then
        return root + INTERVALS.major7
    elseif quality == "dim" then
        return root + INTERVALS.minor7 -- diminished 7th context, use m7
    else
        return root + INTERVALS.minor7 -- dominant 7th
    end
end

-- Export helpers for external use
bass.fifth = fifth
bass.third = third
bass.seventh = seventh

--- Create a single note entry.
local function note(pitch, start, len, vel)
    return { pitch = pitch, start_beats = start, length_beats = len, velocity = vel }
end

-- ============================================================================
-- Simple (default fallback)
-- ============================================================================

--- Root on 1, octave on 3.
-- @param chord_name string
-- @param section_type string
-- @param bar_in_phrase number
-- @return table Notes for one bar
function bass.simple(chord_name, section_type, bar_in_phrase)
    local root, _ = parse_chord(chord_name)
    return {
        note(root, 0, 1.5, 100),
        note(root + INTERVALS.octave, 2, 1.5, 90),
    }
end

-- ============================================================================
-- Rock — Root-fifth driving 8ths
-- ============================================================================

function bass.rock(chord_name, section_type, bar_in_phrase)
    local root, quality = parse_chord(chord_name)
    local f = fifth(root)
    local notes = {}

    -- Driving 8th-note pattern: root-root-fifth-root
    local pattern = { root, root, f, root, root, f, root, root }
    for i = 1, 8 do
        notes[#notes + 1] = note(pattern[i], (i - 1) * 0.5, 0.45, 100)
    end

    return notes
end

-- ============================================================================
-- Pop — Melodic, root-third-fifth movement
-- ============================================================================

function bass.pop(chord_name, section_type, bar_in_phrase)
    local root, quality = parse_chord(chord_name)
    local t = third(root, quality)
    local f = fifth(root)

    return {
        note(root, 0, 1.0, 95),
        note(t, 1, 0.75, 80),
        note(f, 2, 0.75, 85),
        note(t, 3, 0.75, 80),
    }
end

-- ============================================================================
-- Blues — Walking bass with approach notes
-- ============================================================================

function bass.blues(chord_name, section_type, bar_in_phrase)
    local root, quality = parse_chord(chord_name)
    local t = third(root, quality)
    local f = fifth(root)
    local sv = seventh(root, quality)

    -- Walking pattern with chromatic approach note leading to next bar
    local approach = root + INTERVALS.octave - 1 -- chromatic approach from below

    return {
        note(root, 0, 0.9, 100),
        note(t, 1, 0.9, 90),
        note(f, 2, 0.9, 95),
        note(approach, 3, 0.9, 85),
    }
end

-- ============================================================================
-- Jazz — Walking bass (root, passing tone, fifth, approach)
-- ============================================================================

function bass.jazz(chord_name, section_type, bar_in_phrase)
    local root, quality = parse_chord(chord_name)
    local t = third(root, quality)
    local f = fifth(root)
    local sv = seventh(root, quality)

    -- Vary the walking pattern by bar position
    local notes = {}
    if bar_in_phrase % 4 == 1 then
        notes[#notes + 1] = note(root, 0, 0.9, 95)
        notes[#notes + 1] = note(t, 1, 0.9, 85)
        notes[#notes + 1] = note(f, 2, 0.9, 90)
        notes[#notes + 1] = note(sv, 3, 0.9, 85)
    elseif bar_in_phrase % 4 == 2 then
        notes[#notes + 1] = note(root, 0, 0.9, 95)
        notes[#notes + 1] = note(root + INTERVALS.major2, 1, 0.9, 80)
        notes[#notes + 1] = note(t, 2, 0.9, 85)
        notes[#notes + 1] = note(f, 3, 0.9, 90)
    elseif bar_in_phrase % 4 == 3 then
        notes[#notes + 1] = note(f, 0, 0.9, 90)
        notes[#notes + 1] = note(t, 1, 0.9, 85)
        notes[#notes + 1] = note(root, 2, 0.9, 95)
        notes[#notes + 1] = note(root - 1, 3, 0.9, 80) -- chromatic approach below
    else
        notes[#notes + 1] = note(root, 0, 0.9, 95)
        notes[#notes + 1] = note(sv, 1, 0.9, 85)
        notes[#notes + 1] = note(f, 2, 0.9, 90)
        notes[#notes + 1] = note(root + INTERVALS.octave - 1, 3, 0.9, 80) -- leading tone
    end

    return notes
end

-- ============================================================================
-- Funk — Syncopated, percussive
-- ============================================================================

function bass.funk(chord_name, section_type, bar_in_phrase)
    local root, quality = parse_chord(chord_name)
    local f = fifth(root)
    local oct = root + INTERVALS.octave

    -- Syncopated funk pattern with rests (gaps = percussive feel)
    return {
        note(root, 0, 0.3, 110),       -- staccato hit on 1
        note(root, 0.75, 0.2, 90),     -- ghost
        note(oct, 1, 0.3, 100),        -- octave pop on 2
        note(root, 1.5, 0.2, 80),      -- ghost
        note(f, 2, 0.3, 105),          -- fifth on 3
        note(root, 2.25, 0.2, 85),     -- quick bounce
        note(root, 2.75, 0.2, 90),     -- syncopated push
        note(oct, 3.5, 0.3, 95),       -- octave anticipation
    }
end

-- ============================================================================
-- Country — Root-fifth alternating (boom-chick)
-- ============================================================================

function bass.country(chord_name, section_type, bar_in_phrase)
    local root, quality = parse_chord(chord_name)
    local f = fifth(root)

    -- Classic boom-chick bass: root on 1+3, fifth on 2+4
    return {
        note(root, 0, 0.9, 100),
        note(f, 1, 0.9, 85),
        note(root, 2, 0.9, 100),
        note(f, 3, 0.9, 85),
    }
end

-- ============================================================================
-- Ballad — Whole notes, sustained
-- ============================================================================

function bass.ballad(chord_name, section_type, bar_in_phrase)
    local root, quality = parse_chord(chord_name)

    -- Whole note root, maybe add fifth on chorus
    local notes = {
        note(root, 0, 3.5, 80),
    }

    if section_type == "chorus" then
        notes[#notes + 1] = note(fifth(root), 2, 1.5, 65)
    end

    return notes
end

-- ============================================================================
-- Reggae — Offbeat push
-- ============================================================================

function bass.reggae(chord_name, section_type, bar_in_phrase)
    local root, quality = parse_chord(chord_name)
    local f = fifth(root)
    local t = third(root, quality)

    -- Reggae bass: heavy on offbeats, pushes against the one-drop
    return {
        note(root, 0, 0.4, 95),        -- downbeat anchor
        note(root, 0.5, 0.8, 100),     -- offbeat push
        note(t, 1.5, 0.4, 85),         -- offbeat
        note(root, 2, 0.5, 95),        -- beat 3 (with one-drop kick)
        note(f, 2.5, 0.8, 90),         -- offbeat push
        note(root, 3.5, 0.4, 85),      -- anticipation
    }
end

-- ============================================================================
-- Metal — Driving 8th-note roots
-- ============================================================================

function bass.metal(chord_name, section_type, bar_in_phrase)
    local root, quality = parse_chord(chord_name)
    local notes = {}

    -- Relentless 8th-note roots, power-chord style
    for i = 0, 7 do
        local vel = (i % 2 == 0) and 110 or 100
        notes[#notes + 1] = note(root, i * 0.5, 0.45, vel)
    end

    -- In chorus, add occasional fifth hits for variation
    if section_type == "chorus" and bar_in_phrase % 2 == 0 then
        notes[5].pitch = fifth(root)
        notes[6].pitch = fifth(root)
    end

    return notes
end

-- ============================================================================
-- Latin — Syncopated bossa/samba
-- ============================================================================

function bass.latin(chord_name, section_type, bar_in_phrase)
    local root, quality = parse_chord(chord_name)
    local f = fifth(root)
    local t = third(root, quality)

    -- Bossa nova bass: root on 1, syncopated movement
    return {
        note(root, 0, 1.0, 90),        -- root on 1
        note(f, 1.5, 0.8, 80),         -- fifth on "and of 2"
        note(root, 2.5, 0.5, 85),      -- root pickup
        note(t, 3, 0.8, 80),           -- third leading out
    }
end

-- ============================================================================
-- Genre Lookup
-- ============================================================================

local genre_patterns = {
    rock    = bass.rock,
    pop     = bass.pop,
    blues   = bass.blues,
    jazz    = bass.jazz,
    funk    = bass.funk,
    country = bass.country,
    ballad  = bass.ballad,
    reggae  = bass.reggae,
    metal   = bass.metal,
    latin   = bass.latin,
}

--- Get the pattern function for a genre, falling back to simple.
-- @param genre string Genre name (lowercase)
-- @return function pattern_fn(chord_name, section_type, bar_in_phrase) -> notes
function bass.get_pattern(genre)
    return genre_patterns[genre] or bass.simple
end

return bass
