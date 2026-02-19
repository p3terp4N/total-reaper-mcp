-- actions/add_guitar_od.lua — Add a guitar overdub track
-- Creates a new track named "Guitar OD [N]" (auto-numbered), sets input to
-- Tascam Ch 2 (guitar DI), arms for recording, and applies green color.
-- If a GUITARS folder track exists, inserts the new track inside it.

dofile(debug.getinfo(1, "S").source:match("@?(.*/)") .. "init.lua")

local config = require("config")
local utils  = require("utils")
local tracks = require("tracks")

utils.undo_block("Add Guitar Overdub Track", function()
    -- Count existing Guitar OD tracks to determine the next number
    local count = reaper.CountTracks(0)
    local od_count = 0
    local guitars_folder_idx = nil
    local last_child_idx = nil

    for i = 0, count - 1 do
        local track = reaper.GetTrack(0, i)
        local _, name = reaper.GetSetMediaTrackInfo_String(track, "P_NAME", "", false)

        if name and name:find("^Guitar OD") then
            od_count = od_count + 1
        end

        -- Find the GUITARS folder track
        if name and (name == "GUITARS" or name == "Guitars") then
            local depth = reaper.GetMediaTrackInfo_Value(track, "I_FOLDERDEPTH")
            if depth == 1 then
                guitars_folder_idx = i
            end
        end
    end

    local new_num = od_count + 1
    local new_name = "Guitar OD " .. new_num

    -- Determine insertion index
    local insert_idx
    if guitars_folder_idx then
        -- Find the last child of the GUITARS folder
        last_child_idx = guitars_folder_idx
        local folder_depth = 1
        for i = guitars_folder_idx + 1, count - 1 do
            local track = reaper.GetTrack(0, i)
            local depth = reaper.GetMediaTrackInfo_Value(track, "I_FOLDERDEPTH")
            folder_depth = folder_depth + depth
            last_child_idx = i
            if folder_depth <= 0 then
                break
            end
        end
        -- Insert before the last child (which closes the folder) or after it
        insert_idx = last_child_idx
    else
        -- No folder found — insert at the end
        insert_idx = count
    end

    -- Insert the new track
    reaper.InsertTrackAtIndex(insert_idx, false)
    local new_track = reaper.GetTrack(0, insert_idx)

    if not new_track then
        utils.log("Add Guitar OD: Failed to create track.")
        return
    end

    -- Set track properties
    reaper.GetSetMediaTrackInfo_String(new_track, "P_NAME", new_name, true)
    reaper.SetMediaTrackInfo_Value(new_track, "I_CUSTOMCOLOR", utils.color(config.colors.green))

    -- Set input to Tascam Ch 2 (guitar DI)
    local input_val = utils.encode_audio_input(config.tascam.channels.guitar_di_1, false)
    reaper.SetMediaTrackInfo_Value(new_track, "I_RECINPUT", input_val)

    -- Arm for recording
    reaper.SetMediaTrackInfo_Value(new_track, "I_RECARM", 1)

    -- Input monitoring (normal)
    reaper.SetMediaTrackInfo_Value(new_track, "I_RECMON", 1)

    utils.log("Created: " .. new_name)
    utils.log("  Input: Tascam Ch " .. config.tascam.channels.guitar_di_1 .. " (Guitar DI)")
    utils.log("  Color: Green | Armed: Yes | Monitoring: On")
    if guitars_folder_idx then
        utils.log("  Added to GUITARS folder.")
    end
end)

reaper.defer(function() end)
