-- lib/backing/drums.lua — Drum pattern library for backing track generation
-- Returns MIDI note data tables for 10 genres plus a simple fallback.
-- Each pattern function takes (section_type, bar_in_phrase) and returns a
-- table of {pitch, start_beats, length_beats, velocity} for ONE bar (4 beats).

local drums = {}

-- ============================================================================
-- General MIDI Drum Map
-- ============================================================================

drums.GM = {
    kick        = 36,
    snare       = 38,
    hihat       = 42,   -- closed
    hihat_open  = 46,
    hihat_pedal = 44,
    crash       = 49,
    ride        = 51,
    ride_bell   = 53,
    tom_hi      = 48,
    tom_mid     = 45,
    tom_lo      = 43,
    tom_floor   = 41,
    rimshot     = 37,   -- side stick / cross stick
    clap        = 39,
    cowbell     = 56,
    tambourine  = 54,
}

local GM = drums.GM

-- ============================================================================
-- Helpers
-- ============================================================================

--- Append all entries from src into dest.
local function append(dest, src)
    for i = 1, #src do
        dest[#dest + 1] = src[i]
    end
end

--- Create a single note entry.
-- @param pitch number MIDI note
-- @param start number Beat position (0-based within bar)
-- @param len number Duration in beats
-- @param vel number Velocity 1-127
-- @return table {pitch, start_beats, length_beats, velocity}
local function note(pitch, start, len, vel)
    return { pitch = pitch, start_beats = start, length_beats = len, velocity = vel }
end

--- Repeat a pattern function over multiple bars, offsetting start times.
-- @param pattern_fn function(section_type, bar_in_phrase) -> notes table
-- @param bars number How many bars to generate
-- @param section_type string "verse", "chorus", "bridge", etc.
-- @return table Combined notes with adjusted start_beats
function drums.repeat_bars(pattern_fn, bars, section_type)
    local result = {}
    for bar = 1, bars do
        local notes = pattern_fn(section_type, bar)
        for i = 1, #notes do
            local n = notes[i]
            result[#result + 1] = note(
                n.pitch,
                n.start_beats + (bar - 1) * 4,
                n.length_beats,
                n.velocity
            )
        end
    end
    return result
end

--- Generate a basic 4-bar drum fill (descending toms).
-- @return table Notes for a fill bar
local function fill_bar()
    local notes = {}
    -- 16th-note tom fill across the last bar
    local toms = { GM.tom_hi, GM.tom_hi, GM.tom_mid, GM.tom_mid,
                   GM.tom_lo, GM.tom_lo, GM.tom_floor, GM.tom_floor }
    for i = 1, 8 do
        notes[#notes + 1] = note(toms[i], 2 + (i - 1) * 0.25, 0.2, 90 + i)
    end
    -- Kick + crash at beat 0 and 1 for groove continuity
    notes[#notes + 1] = note(GM.kick, 0, 0.5, 100)
    notes[#notes + 1] = note(GM.snare, 1, 0.5, 100)
    return notes
end

--- Standard 8th-note hi-hat pattern.
-- @param vel number Base velocity
-- @return table Notes
local function eighth_hihats(vel)
    local notes = {}
    for i = 0, 7 do
        -- Accent downbeats slightly
        local v = (i % 2 == 0) and vel or (vel - 15)
        notes[#notes + 1] = note(GM.hihat, i * 0.5, 0.4, v)
    end
    return notes
end

--- Standard 16th-note hi-hat pattern.
-- @param vel number Base velocity
-- @return table Notes
local function sixteenth_hihats(vel)
    local notes = {}
    for i = 0, 15 do
        local v = vel
        if i % 4 == 0 then v = vel
        elseif i % 2 == 0 then v = vel - 10
        else v = vel - 20
        end
        notes[#notes + 1] = note(GM.hihat, i * 0.25, 0.2, v)
    end
    return notes
end

-- ============================================================================
-- Simple (default fallback)
-- ============================================================================

--- Basic pattern: kick 1+3, snare 2+4, 8th hi-hat, fills every 4 bars.
-- @param section_type string
-- @param bar_in_phrase number 1-based bar within phrase
-- @return table Notes for one bar
function drums.simple(section_type, bar_in_phrase)
    -- Fill on every 4th bar
    if bar_in_phrase % 4 == 0 then
        local notes = {}
        -- Keep basic kick/snare for first 2 beats
        notes[#notes + 1] = note(GM.kick, 0, 0.5, 100)
        notes[#notes + 1] = note(GM.snare, 1, 0.5, 100)
        append(notes, fill_bar())
        return notes
    end

    local notes = eighth_hihats(85)
    -- Kick on 1 and 3
    notes[#notes + 1] = note(GM.kick, 0, 0.5, 100)
    notes[#notes + 1] = note(GM.kick, 2, 0.5, 100)
    -- Snare on 2 and 4
    notes[#notes + 1] = note(GM.snare, 1, 0.5, 100)
    notes[#notes + 1] = note(GM.snare, 3, 0.5, 100)
    return notes
end

-- ============================================================================
-- Rock
-- ============================================================================

--- Driving 8ths, crash on chorus downbeat, extra kick on 2.5 in chorus.
function drums.rock(section_type, bar_in_phrase)
    if bar_in_phrase % 4 == 0 then
        return fill_bar()
    end

    local notes = eighth_hihats(90)

    -- Kick on 1 and 3
    notes[#notes + 1] = note(GM.kick, 0, 0.5, 110)
    notes[#notes + 1] = note(GM.kick, 2, 0.5, 110)
    -- Snare on 2 and 4
    notes[#notes + 1] = note(GM.snare, 1, 0.5, 110)
    notes[#notes + 1] = note(GM.snare, 3, 0.5, 110)

    if section_type == "chorus" then
        -- Extra kick on the "and" of 2
        notes[#notes + 1] = note(GM.kick, 2.5, 0.4, 95)
        -- Crash on bar 1 downbeat
        if bar_in_phrase == 1 then
            notes[#notes + 1] = note(GM.crash, 0, 1.0, 110)
        end
    end

    return notes
end

-- ============================================================================
-- Pop
-- ============================================================================

--- Ghost notes on snare, fills every 8 bars.
function drums.pop(section_type, bar_in_phrase)
    if bar_in_phrase % 8 == 0 then
        return fill_bar()
    end

    local notes = eighth_hihats(80)

    -- Kick pattern: 1, 2.5
    notes[#notes + 1] = note(GM.kick, 0, 0.5, 100)
    notes[#notes + 1] = note(GM.kick, 2.5, 0.5, 90)
    -- Snare on 2 and 4
    notes[#notes + 1] = note(GM.snare, 1, 0.5, 100)
    notes[#notes + 1] = note(GM.snare, 3, 0.5, 100)
    -- Ghost notes (quiet snare hits)
    notes[#notes + 1] = note(GM.snare, 0.75, 0.2, 40)
    notes[#notes + 1] = note(GM.snare, 1.75, 0.2, 35)
    notes[#notes + 1] = note(GM.snare, 2.75, 0.2, 40)
    notes[#notes + 1] = note(GM.snare, 3.75, 0.2, 35)

    if section_type == "chorus" and bar_in_phrase == 1 then
        notes[#notes + 1] = note(GM.crash, 0, 1.0, 100)
    end

    return notes
end

-- ============================================================================
-- Blues
-- ============================================================================

--- Shuffle feel: triplet hi-hat (0, 0.67, 1, 1.67, 2, 2.67, 3, 3.67).
function drums.blues(section_type, bar_in_phrase)
    if bar_in_phrase % 4 == 0 then
        return fill_bar()
    end

    local notes = {}
    -- Shuffle triplet hi-hat: beat, skip, beat (positions: 0, 0.67, 1, 1.67...)
    for beat = 0, 3 do
        notes[#notes + 1] = note(GM.hihat, beat, 0.5, 85)
        notes[#notes + 1] = note(GM.hihat, beat + 0.67, 0.3, 70)
    end

    -- Kick on 1 and 3
    notes[#notes + 1] = note(GM.kick, 0, 0.5, 100)
    notes[#notes + 1] = note(GM.kick, 2, 0.5, 100)
    -- Snare on 2 and 4
    notes[#notes + 1] = note(GM.snare, 1, 0.5, 95)
    notes[#notes + 1] = note(GM.snare, 3, 0.5, 95)

    return notes
end

-- ============================================================================
-- Jazz
-- ============================================================================

--- Ride pattern (swing), hi-hat pedal on 2+4, light kick comping.
function drums.jazz(section_type, bar_in_phrase)
    local notes = {}

    -- Ride: classic swing pattern (1, 2-and, 3, 4-and) with triplet feel
    for beat = 0, 3 do
        notes[#notes + 1] = note(GM.ride, beat, 0.5, 80)
        if beat % 2 == 0 then
            -- Swing "skip" note on triplet position
            notes[#notes + 1] = note(GM.ride, beat + 0.67, 0.3, 65)
        end
    end

    -- Hi-hat pedal on 2 and 4
    notes[#notes + 1] = note(GM.hihat_pedal, 1, 0.3, 70)
    notes[#notes + 1] = note(GM.hihat_pedal, 3, 0.3, 70)

    -- Light kick comping (sparse, varies by bar)
    if bar_in_phrase % 2 == 1 then
        notes[#notes + 1] = note(GM.kick, 0, 0.5, 60)
        notes[#notes + 1] = note(GM.kick, 2.67, 0.3, 50)
    else
        notes[#notes + 1] = note(GM.kick, 0.67, 0.3, 55)
        notes[#notes + 1] = note(GM.kick, 2, 0.5, 60)
    end

    -- Occasional cross-stick for color
    if bar_in_phrase % 4 == 3 then
        notes[#notes + 1] = note(GM.rimshot, 3, 0.3, 55)
    end

    return notes
end

-- ============================================================================
-- Funk
-- ============================================================================

--- Syncopated kick (0, 0.75, 2, 2.25), ghost notes, 16th hi-hats.
function drums.funk(section_type, bar_in_phrase)
    if bar_in_phrase % 4 == 0 then
        return fill_bar()
    end

    local notes = sixteenth_hihats(80)

    -- Open hi-hat accents
    notes[#notes + 1] = note(GM.hihat_open, 1.5, 0.2, 85)
    notes[#notes + 1] = note(GM.hihat_open, 3.5, 0.2, 85)

    -- Syncopated kick: 0, 0.75, 2, 2.25
    notes[#notes + 1] = note(GM.kick, 0, 0.4, 110)
    notes[#notes + 1] = note(GM.kick, 0.75, 0.3, 95)
    notes[#notes + 1] = note(GM.kick, 2, 0.4, 110)
    notes[#notes + 1] = note(GM.kick, 2.25, 0.3, 90)

    -- Snare on 2 and 4
    notes[#notes + 1] = note(GM.snare, 1, 0.5, 110)
    notes[#notes + 1] = note(GM.snare, 3, 0.5, 110)

    -- Ghost notes (very soft snare taps)
    notes[#notes + 1] = note(GM.snare, 0.5, 0.15, 35)
    notes[#notes + 1] = note(GM.snare, 1.25, 0.15, 30)
    notes[#notes + 1] = note(GM.snare, 1.75, 0.15, 35)
    notes[#notes + 1] = note(GM.snare, 2.75, 0.15, 30)
    notes[#notes + 1] = note(GM.snare, 3.25, 0.15, 35)
    notes[#notes + 1] = note(GM.snare, 3.75, 0.15, 30)

    return notes
end

-- ============================================================================
-- Country
-- ============================================================================

--- Train beat: alternating closed/open hi-hat.
function drums.country(section_type, bar_in_phrase)
    if bar_in_phrase % 4 == 0 then
        return fill_bar()
    end

    local notes = {}

    -- Train beat: alternating closed and open hi-hat on 8ths
    for i = 0, 7 do
        if i % 2 == 0 then
            notes[#notes + 1] = note(GM.hihat, i * 0.5, 0.4, 85)
        else
            notes[#notes + 1] = note(GM.hihat_open, i * 0.5, 0.3, 75)
        end
    end

    -- Kick on 1 and 3
    notes[#notes + 1] = note(GM.kick, 0, 0.5, 100)
    notes[#notes + 1] = note(GM.kick, 2, 0.5, 100)
    -- Snare on 2 and 4
    notes[#notes + 1] = note(GM.snare, 1, 0.5, 95)
    notes[#notes + 1] = note(GM.snare, 3, 0.5, 95)

    return notes
end

-- ============================================================================
-- Ballad
-- ============================================================================

--- Sparse: kick on 1, snare on 3, ride or rimshot quarters.
function drums.ballad(section_type, bar_in_phrase)
    local notes = {}

    -- Ride or rimshot quarters depending on section
    local cymbal = (section_type == "chorus") and GM.ride or GM.rimshot
    local cymbal_vel = (section_type == "chorus") and 70 or 55
    for beat = 0, 3 do
        notes[#notes + 1] = note(cymbal, beat, 0.8, cymbal_vel)
    end

    -- Sparse kick and snare
    notes[#notes + 1] = note(GM.kick, 0, 0.8, 80)
    notes[#notes + 1] = note(GM.snare, 2, 0.8, 75)

    -- Add subtle hi-hat pedal on 2+4 for timekeeping
    notes[#notes + 1] = note(GM.hihat_pedal, 1, 0.3, 45)
    notes[#notes + 1] = note(GM.hihat_pedal, 3, 0.3, 45)

    -- Crash on chorus downbeat
    if section_type == "chorus" and bar_in_phrase == 1 then
        notes[#notes + 1] = note(GM.crash, 0, 1.5, 85)
    end

    return notes
end

-- ============================================================================
-- Reggae
-- ============================================================================

--- One-drop: kick+snare on 3 only, cross-stick offbeats.
function drums.reggae(section_type, bar_in_phrase)
    local notes = {}

    -- One-drop: kick and snare together on beat 3
    notes[#notes + 1] = note(GM.kick, 2, 0.5, 100)
    notes[#notes + 1] = note(GM.snare, 2, 0.5, 95)

    -- Cross-stick on offbeats (and of each beat)
    notes[#notes + 1] = note(GM.rimshot, 0.5, 0.3, 70)
    notes[#notes + 1] = note(GM.rimshot, 1.5, 0.3, 70)
    notes[#notes + 1] = note(GM.rimshot, 2.5, 0.3, 65)
    notes[#notes + 1] = note(GM.rimshot, 3.5, 0.3, 70)

    -- Hi-hat: steady 8ths, quieter
    for i = 0, 7 do
        notes[#notes + 1] = note(GM.hihat, i * 0.5, 0.3, 60)
    end

    return notes
end

-- ============================================================================
-- Metal
-- ============================================================================

--- Double kick 16ths in chorus, 8ths in verse, aggressive snare.
function drums.metal(section_type, bar_in_phrase)
    if bar_in_phrase % 4 == 0 then
        return fill_bar()
    end

    local notes = {}

    -- Hi-hat: driving 8ths (or ride in chorus)
    local cymbal = (section_type == "chorus") and GM.ride_bell or GM.hihat
    for i = 0, 7 do
        notes[#notes + 1] = note(cymbal, i * 0.5, 0.4, 100)
    end

    -- Snare on 2 and 4 (aggressive)
    notes[#notes + 1] = note(GM.snare, 1, 0.5, 120)
    notes[#notes + 1] = note(GM.snare, 3, 0.5, 120)

    if section_type == "chorus" then
        -- Double kick: 16th notes throughout
        for i = 0, 15 do
            notes[#notes + 1] = note(GM.kick, i * 0.25, 0.2, 110)
        end
        -- Crash on downbeat
        if bar_in_phrase == 1 then
            notes[#notes + 1] = note(GM.crash, 0, 1.0, 120)
        end
    else
        -- Verse: 8th-note kick
        for i = 0, 7 do
            notes[#notes + 1] = note(GM.kick, i * 0.5, 0.4, 105)
        end
    end

    return notes
end

-- ============================================================================
-- Latin (Bossa Nova)
-- ============================================================================

--- Bossa nova: cross-stick 2+4, kick on 1 and "and of 2".
function drums.latin(section_type, bar_in_phrase)
    local notes = {}

    -- Cross-stick on 2 and 4
    notes[#notes + 1] = note(GM.rimshot, 1, 0.3, 75)
    notes[#notes + 1] = note(GM.rimshot, 3, 0.3, 75)

    -- Kick on 1 and "and of 2" (beat 1.5)
    notes[#notes + 1] = note(GM.kick, 0, 0.5, 90)
    notes[#notes + 1] = note(GM.kick, 1.5, 0.4, 80)

    -- Hi-hat: light 8ths
    for i = 0, 7 do
        local v = (i % 2 == 0) and 65 or 50
        notes[#notes + 1] = note(GM.hihat, i * 0.5, 0.3, v)
    end

    -- Subtle shaker / tambourine 16ths for bossa feel
    for i = 0, 15 do
        local v = 30 + (i % 4 == 0 and 15 or 0)
        notes[#notes + 1] = note(GM.tambourine, i * 0.25, 0.15, v)
    end

    return notes
end

-- ============================================================================
-- R&B (Neo-Soul)
-- ============================================================================

--- Laid-back groove: ghost-note-heavy snare, syncopated kick, open hi-hat accents.
function drums.r_b(section_type, bar_in_phrase)
    if bar_in_phrase % 8 == 0 then
        return fill_bar()
    end

    local notes = {}

    -- Hi-hat: 8ths with open hat accents on "and" of 2 and 4
    for i = 0, 7 do
        local v = (i % 2 == 0) and 70 or 55
        notes[#notes + 1] = note(GM.hihat, i * 0.5, 0.35, v)
    end
    notes[#notes + 1] = note(GM.hihat_open, 1.5, 0.3, 75)
    notes[#notes + 1] = note(GM.hihat_open, 3.5, 0.3, 75)

    -- Kick: syncopated (1, "and of 2", 3.5)
    notes[#notes + 1] = note(GM.kick, 0, 0.5, 90)
    notes[#notes + 1] = note(GM.kick, 1.5, 0.4, 80)
    notes[#notes + 1] = note(GM.kick, 3.5, 0.4, 75)

    -- Snare on 2 and 4 (softer than rock)
    notes[#notes + 1] = note(GM.snare, 1, 0.5, 85)
    notes[#notes + 1] = note(GM.snare, 3, 0.5, 85)

    -- Heavy ghost notes (signature neo-soul feel)
    notes[#notes + 1] = note(GM.snare, 0.25, 0.15, 30)
    notes[#notes + 1] = note(GM.snare, 0.75, 0.15, 35)
    notes[#notes + 1] = note(GM.snare, 1.25, 0.15, 25)
    notes[#notes + 1] = note(GM.snare, 1.75, 0.15, 30)
    notes[#notes + 1] = note(GM.snare, 2.25, 0.15, 30)
    notes[#notes + 1] = note(GM.snare, 2.75, 0.15, 35)
    notes[#notes + 1] = note(GM.snare, 3.25, 0.15, 25)
    notes[#notes + 1] = note(GM.snare, 3.75, 0.15, 30)

    if section_type == "chorus" and bar_in_phrase == 1 then
        notes[#notes + 1] = note(GM.crash, 0, 1.0, 85)
    end

    return notes
end

-- ============================================================================
-- Genre Lookup
-- ============================================================================

local genre_patterns = {
    rock    = drums.rock,
    pop     = drums.pop,
    blues   = drums.blues,
    jazz    = drums.jazz,
    funk    = drums.funk,
    country = drums.country,
    ballad  = drums.ballad,
    reggae  = drums.reggae,
    metal   = drums.metal,
    latin   = drums.latin,
    ["r&b"] = drums.r_b,
}

--- Get the pattern function for a genre, falling back to simple.
-- @param genre string Genre name (lowercase)
-- @return function pattern_fn(section_type, bar_in_phrase) -> notes table
function drums.get_pattern(genre)
    return genre_patterns[genre] or drums.simple
end

return drums
