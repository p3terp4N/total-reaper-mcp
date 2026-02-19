-- lib/backing/guitar.lua — Rhythm guitar pattern library for backing track generation
-- Returns MIDI note data tables for 8 genres plus a simple fallback.
-- Each pattern function takes (chord_name, section_type, bar_in_phrase) and
-- returns a table of {pitch, start_beats, length_beats, velocity} for ONE bar.

local guitar = {}

-- ============================================================================
-- Root Notes (octave 3, C3 = MIDI 48)
-- ============================================================================

local ROOT_NOTES = {
    C  = 48, Cs = 49, Db = 49,
    D  = 50, Ds = 51, Eb = 51,
    E  = 52,
    F  = 53, Fs = 54, Gb = 54,
    G  = 55, Gs = 56, Ab = 56,
    A  = 57, As = 58, Bb = 58,
    B  = 59,
}

-- ============================================================================
-- Intervals
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
-- @param chord_name string
-- @return number root_pitch, string quality
local function parse_chord(chord_name)
    if not chord_name or chord_name == "" then
        return ROOT_NOTES.C, "major"
    end

    local first = chord_name:sub(1, 1):upper()
    local second = chord_name:sub(2, 2)
    local root_str, quality_str

    if second == "#" or second == "b" then
        root_str = first .. (second == "#" and "s" or "b")
        quality_str = chord_name:sub(3)
    else
        root_str = first
        quality_str = chord_name:sub(2)
    end

    local root = ROOT_NOTES[root_str] or ROOT_NOTES.C

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
-- Voicing & Strum Helpers
-- ============================================================================

--- Build a guitar chord voicing (4-6 notes, open/barre style).
-- @param root number MIDI root pitch
-- @param quality string Chord quality
-- @return table Array of MIDI pitches (low to high, like strings)
local function voicing(root, quality)
    if quality == "minor" then
        return {
            root,
            root + INTERVALS.perfect5,
            root + INTERVALS.octave,
            root + INTERVALS.octave + INTERVALS.minor3,
            root + INTERVALS.octave + INTERVALS.perfect5,
        }
    elseif quality == "m7" then
        return {
            root,
            root + INTERVALS.perfect5,
            root + INTERVALS.minor7,
            root + INTERVALS.octave + INTERVALS.minor3,
            root + INTERVALS.octave + INTERVALS.perfect5,
        }
    elseif quality == "dom7" then
        return {
            root,
            root + INTERVALS.major3,
            root + INTERVALS.minor7,
            root + INTERVALS.octave,
            root + INTERVALS.octave + INTERVALS.major3,
        }
    elseif quality == "maj7" then
        return {
            root,
            root + INTERVALS.major3,
            root + INTERVALS.major7,
            root + INTERVALS.octave,
            root + INTERVALS.octave + INTERVALS.major3,
        }
    elseif quality == "dim" then
        return {
            root,
            root + INTERVALS.minor3,
            root + INTERVALS.tritone,
            root + INTERVALS.octave,
        }
    elseif quality == "aug" then
        return {
            root,
            root + INTERVALS.major3,
            root + INTERVALS.minor6,
            root + INTERVALS.octave,
        }
    elseif quality == "sus4" then
        return {
            root,
            root + INTERVALS.perfect5,
            root + INTERVALS.octave,
            root + INTERVALS.octave + INTERVALS.perfect4,
            root + INTERVALS.octave + INTERVALS.perfect5,
        }
    elseif quality == "sus2" then
        return {
            root,
            root + INTERVALS.perfect5,
            root + INTERVALS.octave,
            root + INTERVALS.octave + INTERVALS.major2,
            root + INTERVALS.octave + INTERVALS.perfect5,
        }
    else -- major
        return {
            root,
            root + INTERVALS.perfect5,
            root + INTERVALS.octave,
            root + INTERVALS.octave + INTERVALS.major3,
            root + INTERVALS.octave + INTERVALS.perfect5,
        }
    end
end

--- Strum a chord with slight delay between strings (simulates pick movement).
-- @param pitches table Array of MIDI pitches (low to high)
-- @param start number Beat position
-- @param len number Duration in beats
-- @param vel number Base velocity
-- @param direction string "down" (low to high) or "up" (high to low)
-- @return table Array of note entries
local function strum(pitches, start, len, vel, direction)
    local notes = {}
    local strum_delay = 0.02  -- delay between each string (beats)
    local count = #pitches

    for i = 1, count do
        local idx = (direction == "up") and (count - i + 1) or i
        local offset = (i - 1) * strum_delay
        -- Slight velocity variation across strings
        local v = vel + math.floor((i - 1) * 2 - count)
        if v < 1 then v = 1 end
        if v > 127 then v = 127 end
        notes[#notes + 1] = {
            pitch = pitches[idx],
            start_beats = start + offset,
            length_beats = math.max(len - offset, 0.1),
            velocity = v,
        }
    end

    return notes
end

-- Export helpers
guitar.voicing = voicing
guitar.strum = strum

--- Helper to append notes.
local function append(dest, src)
    for i = 1, #src do
        dest[#dest + 1] = src[i]
    end
end

--- Create a single note entry.
local function note(pitch, start, len, vel)
    return { pitch = pitch, start_beats = start, length_beats = len, velocity = vel }
end

-- ============================================================================
-- Simple (default fallback)
-- ============================================================================

--- Quarter-note downstrums on each beat.
-- @param chord_name string
-- @param section_type string
-- @param bar_in_phrase number
-- @return table Notes for one bar
function guitar.simple(chord_name, section_type, bar_in_phrase)
    local root, quality = parse_chord(chord_name)
    local pitches = voicing(root, quality)
    local notes = {}

    for beat = 0, 3 do
        append(notes, strum(pitches, beat, 0.9, 80, "down"))
    end

    return notes
end

-- ============================================================================
-- Rock — Down-up 8th-note strumming
-- ============================================================================

function guitar.rock(chord_name, section_type, bar_in_phrase)
    local root, quality = parse_chord(chord_name)
    local pitches = voicing(root, quality)
    local notes = {}

    -- Alternating down-up 8ths
    for i = 0, 7 do
        local dir = (i % 2 == 0) and "down" or "up"
        local vel = (i % 2 == 0) and 95 or 80
        append(notes, strum(pitches, i * 0.5, 0.45, vel, dir))
    end

    return notes
end

-- ============================================================================
-- Pop — Arpeggiated picking pattern
-- ============================================================================

function guitar.pop(chord_name, section_type, bar_in_phrase)
    local root, quality = parse_chord(chord_name)
    local pitches = voicing(root, quality)
    local notes = {}
    local count = #pitches

    -- Fingerpicking arpeggio: bass, mid, high, mid pattern in 8ths
    -- Pick individual strings rather than strumming
    local pick_order
    if count >= 5 then
        pick_order = { 1, 3, 5, 4, 2, 4, 5, 3 }
    elseif count >= 4 then
        pick_order = { 1, 3, 4, 3, 2, 3, 4, 3 }
    else
        pick_order = { 1, 2, 3, 2, 1, 3, 2, 3 }
    end

    for i = 1, 8 do
        local idx = pick_order[i]
        if idx > count then idx = count end
        notes[#notes + 1] = note(pitches[idx], (i - 1) * 0.5, 0.7, 70 + (i % 3) * 5)
    end

    return notes
end

-- ============================================================================
-- Blues — Shuffle strum pattern
-- ============================================================================

function guitar.blues(chord_name, section_type, bar_in_phrase)
    local root, quality = parse_chord(chord_name)
    local pitches = voicing(root, quality)
    local notes = {}

    -- Shuffle strum: downbeat + triplet "and" (same feel as blues drums)
    for beat = 0, 3 do
        append(notes, strum(pitches, beat, 0.5, 85, "down"))
        append(notes, strum(pitches, beat + 0.67, 0.3, 70, "up"))
    end

    return notes
end

-- ============================================================================
-- Funk — Muted 16th-note accents (scratch/chick rhythm)
-- ============================================================================

function guitar.funk(chord_name, section_type, bar_in_phrase)
    local root, quality = parse_chord(chord_name)
    local pitches = voicing(root, quality)
    local notes = {}

    -- 16th-note grid: some hits are full chords, others are muted (very short + low vel)
    -- Classic funk: accented on "e" and "a" positions (syncopated)
    local accents = {
        -- beat subdivisions: 1 e & a 2 e & a 3 e & a 4 e & a
        true, false, false, true,   -- beat 1
        false, true, false, true,   -- beat 2
        true, false, false, true,   -- beat 3
        false, true, false, true,   -- beat 4
    }

    for i = 0, 15 do
        local pos = i * 0.25
        local dir = (i % 2 == 0) and "down" or "up"
        if accents[i + 1] then
            -- Full chord stab
            append(notes, strum(pitches, pos, 0.2, 95, dir))
        else
            -- Muted scratch: very short, low velocity (single note)
            notes[#notes + 1] = note(pitches[1], pos, 0.08, 35)
        end
    end

    return notes
end

-- ============================================================================
-- Country — Boom-chicka (bass note + up-strum alternating)
-- ============================================================================

function guitar.country(chord_name, section_type, bar_in_phrase)
    local root, quality = parse_chord(chord_name)
    local pitches = voicing(root, quality)
    local notes = {}

    -- Only top strings for the "chicka" (skip the bass note)
    local treble = {}
    for i = 3, #pitches do
        treble[#treble + 1] = pitches[i]
    end
    if #treble == 0 then treble = pitches end

    for beat = 0, 3 do
        -- "Boom" — bass note on the beat
        notes[#notes + 1] = note(pitches[1], beat, 0.4, 90)
        -- "Chicka" — treble strum on the "and"
        append(notes, strum(treble, beat + 0.5, 0.35, 75, "down"))
    end

    return notes
end

-- ============================================================================
-- Reggae — Offbeat skank (chords on the "and" of each beat)
-- ============================================================================

function guitar.reggae(chord_name, section_type, bar_in_phrase)
    local root, quality = parse_chord(chord_name)
    local pitches = voicing(root, quality)
    local notes = {}

    -- Skank: short, sharp stabs on offbeats only
    for beat = 0, 3 do
        append(notes, strum(pitches, beat + 0.5, 0.3, 90, "down"))
    end

    return notes
end

-- ============================================================================
-- Ballad — Gentle arpeggios
-- ============================================================================

function guitar.ballad(chord_name, section_type, bar_in_phrase)
    local root, quality = parse_chord(chord_name)
    local pitches = voicing(root, quality)
    local notes = {}
    local count = #pitches

    -- Slow, gentle arpeggio spread across the bar
    -- Each note gets roughly a half beat, overlapping for a sustained feel
    local pick_order
    if count >= 5 then
        pick_order = { 1, 2, 3, 4, 5, 4, 3, 2 }
    elseif count >= 4 then
        pick_order = { 1, 2, 3, 4, 3, 2, 3, 4 }
    else
        pick_order = { 1, 2, 3, 2, 1, 2, 3, 2 }
    end

    for i = 1, 8 do
        local idx = pick_order[i]
        if idx > count then idx = count end
        -- Long sustain (notes overlap) for a lush sound
        notes[#notes + 1] = note(pitches[idx], (i - 1) * 0.5, 1.5, 55 + (i % 3) * 5)
    end

    return notes
end

-- ============================================================================
-- Genre Lookup
-- ============================================================================

local genre_patterns = {
    rock    = guitar.rock,
    pop     = guitar.pop,
    blues   = guitar.blues,
    funk    = guitar.funk,
    country = guitar.country,
    reggae  = guitar.reggae,
    ballad  = guitar.ballad,
}

--- Get the pattern function for a genre, falling back to simple.
-- @param genre string Genre name (lowercase)
-- @return function pattern_fn(chord_name, section_type, bar_in_phrase) -> notes
function guitar.get_pattern(genre)
    return genre_patterns[genre] or guitar.simple
end

return guitar
