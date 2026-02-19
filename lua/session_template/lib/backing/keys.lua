-- lib/backing/keys.lua — Keys/piano pattern library for backing track generation
-- Returns MIDI note data tables for 7 genres plus a simple fallback.
-- Each pattern function takes (chord_name, section_type, bar_in_phrase) and
-- returns a table of {pitch, start_beats, length_beats, velocity} for ONE bar.

local keys = {}

-- ============================================================================
-- Root Notes (octave 4, C4 = MIDI 60)
-- ============================================================================

local ROOT_NOTES = {
    C  = 60, Cs = 61, Db = 61,
    D  = 62, Ds = 63, Eb = 63,
    E  = 64,
    F  = 65, Fs = 66, Gb = 66,
    G  = 67, Gs = 68, Ab = 68,
    A  = 69, As = 70, Bb = 70,
    B  = 71,
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
-- @param chord_name string e.g. "Am7", "F#dim", "Bb"
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
-- Voicing Helpers
-- ============================================================================

--- Build a chord voicing (array of MIDI pitches) from root and quality.
-- Returns 3-4 note voicings appropriate for piano.
-- @param root number MIDI root pitch
-- @param quality string Chord quality
-- @return table Array of MIDI pitches
local function voicing(root, quality)
    if quality == "minor" then
        return { root, root + INTERVALS.minor3, root + INTERVALS.perfect5 }
    elseif quality == "m7" then
        return { root, root + INTERVALS.minor3, root + INTERVALS.perfect5, root + INTERVALS.minor7 }
    elseif quality == "dom7" then
        return { root, root + INTERVALS.major3, root + INTERVALS.perfect5, root + INTERVALS.minor7 }
    elseif quality == "maj7" then
        return { root, root + INTERVALS.major3, root + INTERVALS.perfect5, root + INTERVALS.major7 }
    elseif quality == "dim" then
        return { root, root + INTERVALS.minor3, root + INTERVALS.tritone }
    elseif quality == "aug" then
        return { root, root + INTERVALS.major3, root + INTERVALS.minor6 }
    elseif quality == "sus4" then
        return { root, root + INTERVALS.perfect4, root + INTERVALS.perfect5 }
    elseif quality == "sus2" then
        return { root, root + INTERVALS.major2, root + INTERVALS.perfect5 }
    else -- major
        return { root, root + INTERVALS.major3, root + INTERVALS.perfect5 }
    end
end

--- Play all notes of a chord simultaneously as a block.
-- @param pitches table Array of MIDI pitches
-- @param start number Beat position
-- @param len number Duration in beats
-- @param vel number Velocity
-- @return table Array of note entries
local function block_chord(pitches, start, len, vel)
    local notes = {}
    for i = 1, #pitches do
        notes[#notes + 1] = {
            pitch = pitches[i],
            start_beats = start,
            length_beats = len,
            velocity = vel,
        }
    end
    return notes
end

-- Export helpers
keys.voicing = voicing
keys.block_chord = block_chord

--- Helper to append notes from one table into another.
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

--- Block chords on beats 1 and 3.
-- @param chord_name string
-- @param section_type string
-- @param bar_in_phrase number
-- @return table Notes for one bar
function keys.simple(chord_name, section_type, bar_in_phrase)
    local root, quality = parse_chord(chord_name)
    local pitches = voicing(root, quality)
    local notes = {}
    append(notes, block_chord(pitches, 0, 1.5, 85))
    append(notes, block_chord(pitches, 2, 1.5, 80))
    return notes
end

-- ============================================================================
-- Rock — Sparse power chords (root + fifth)
-- ============================================================================

function keys.rock(chord_name, section_type, bar_in_phrase)
    local root, quality = parse_chord(chord_name)
    -- Power chord voicing: root + fifth + octave
    local pitches = { root, root + INTERVALS.perfect5, root + INTERVALS.octave }
    local notes = {}

    -- Hit on 1 and let ring, accent on chorus
    local vel = (section_type == "chorus") and 95 or 80
    append(notes, block_chord(pitches, 0, 3.5, vel))

    -- Add a push note on beat 4 for momentum in chorus
    if section_type == "chorus" then
        append(notes, block_chord(pitches, 3.5, 0.4, 85))
    end

    return notes
end

-- ============================================================================
-- Pop — Arpeggiated chord tones
-- ============================================================================

function keys.pop(chord_name, section_type, bar_in_phrase)
    local root, quality = parse_chord(chord_name)
    local pitches = voicing(root, quality)
    local notes = {}

    -- Arpeggiate through chord tones in 8th notes
    local arp_pattern
    if #pitches >= 4 then
        arp_pattern = { 1, 2, 3, 4, 3, 2, 1, 3 }
    else
        arp_pattern = { 1, 2, 3, 2, 1, 3, 2, 3 }
    end

    for i = 1, 8 do
        local idx = arp_pattern[i]
        local p = pitches[idx] or pitches[1]
        notes[#notes + 1] = note(p, (i - 1) * 0.5, 0.45, 70 + (i % 2) * 10)
    end

    return notes
end

-- ============================================================================
-- Blues — Shuffle comping (triplet-based stabs)
-- ============================================================================

function keys.blues(chord_name, section_type, bar_in_phrase)
    local root, quality = parse_chord(chord_name)
    local pitches = voicing(root, quality)
    local notes = {}

    -- Shuffle comping: hit on downbeat, hit on triplet "and"
    for beat = 0, 3 do
        append(notes, block_chord(pitches, beat, 0.5, 80))
        append(notes, block_chord(pitches, beat + 0.67, 0.3, 65))
    end

    return notes
end

-- ============================================================================
-- Jazz — Freddie Green voicings (rootless, smooth)
-- ============================================================================

function keys.jazz(chord_name, section_type, bar_in_phrase)
    local root, quality = parse_chord(chord_name)

    -- Freddie Green style: rootless voicings, let bass handle the root
    -- Use 3rd and 7th as the core, add color tones
    local third_interval = (quality == "minor" or quality == "m7" or quality == "dim")
        and INTERVALS.minor3 or INTERVALS.major3
    local seventh_interval = (quality == "maj7")
        and INTERVALS.major7 or INTERVALS.minor7

    local pitches
    if quality == "dom7" or quality == "m7" or quality == "maj7" then
        -- Rootless voicing: 3, 5, 7 (or 7, 3, 5 inversion)
        pitches = {
            root + third_interval,
            root + INTERVALS.perfect5,
            root + seventh_interval,
        }
    else
        -- Simple voicing for triads
        pitches = voicing(root, quality)
    end

    local notes = {}

    -- Comp pattern: quarter-note hits with swing feel
    -- Freddie Green style: steady quarters, dynamically varied
    local vels = { 70, 60, 70, 55 }
    for beat = 0, 3 do
        append(notes, block_chord(pitches, beat, 0.8, vels[beat + 1]))
    end

    return notes
end

-- ============================================================================
-- Funk — Clavinet stabs (sharp, percussive)
-- ============================================================================

function keys.funk(chord_name, section_type, bar_in_phrase)
    local root, quality = parse_chord(chord_name)
    local pitches = voicing(root, quality)
    local notes = {}

    -- Clavinet-style stabs: short, accented, syncopated
    -- 16th-note grid with specific hits
    local stab_positions = { 0, 0.75, 1.5, 2, 2.75, 3.5 }
    local stab_vels      = { 100, 85, 90, 100, 85, 95 }

    for i = 1, #stab_positions do
        append(notes, block_chord(pitches, stab_positions[i], 0.2, stab_vels[i]))
    end

    return notes
end

-- ============================================================================
-- Ballad — Whole-note pads, sustained
-- ============================================================================

function keys.ballad(chord_name, section_type, bar_in_phrase)
    local root, quality = parse_chord(chord_name)
    local pitches = voicing(root, quality)
    local notes = {}

    -- Whole-note sustained pad
    append(notes, block_chord(pitches, 0, 3.8, 65))

    -- In chorus, add an octave-up doubling for fullness
    if section_type == "chorus" then
        for i = 1, #pitches do
            notes[#notes + 1] = note(pitches[i] + INTERVALS.octave, 0, 3.8, 50)
        end
    end

    return notes
end

-- ============================================================================
-- Genre Lookup
-- ============================================================================

local genre_patterns = {
    rock    = keys.rock,
    pop     = keys.pop,
    blues   = keys.blues,
    jazz    = keys.jazz,
    funk    = keys.funk,
    ballad  = keys.ballad,
}

--- Get the pattern function for a genre, falling back to simple.
-- @param genre string Genre name (lowercase)
-- @return function pattern_fn(chord_name, section_type, bar_in_phrase) -> notes
function keys.get_pattern(genre)
    return genre_patterns[genre] or keys.simple
end

return keys
