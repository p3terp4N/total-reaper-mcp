-- actions/reference_ab.lua — A/B toggle between mix and reference track
-- Finds the "Reference" track by name. If reference is muted, unmute + solo it
-- (silencing the mix). If reference is unmuted, mute + unsolo it (restoring mix).

dofile(debug.getinfo(1, "S").source:match("@?(.*/)") .. "init.lua")

local utils  = require("utils")
local tracks = require("tracks")

utils.undo_block("A/B Reference Toggle", function()
    local ref_track = tracks.find_by_name("Reference")
    if not ref_track then
        utils.log("Reference track not found. Create a track named 'Reference' with your reference audio.")
        return
    end

    local is_muted = reaper.GetMediaTrackInfo_Value(ref_track, "B_MUTE")

    if is_muted == 1 then
        -- Reference is currently muted → switch TO reference
        tracks.set_mute(ref_track, false)
        tracks.set_solo(ref_track, true)
        utils.log("A/B: Listening to REFERENCE track.")
    else
        -- Reference is currently unmuted → switch BACK to mix
        tracks.set_mute(ref_track, true)
        tracks.set_solo(ref_track, false)
        utils.log("A/B: Listening to MIX.")
    end
end)

reaper.defer(function() end)
