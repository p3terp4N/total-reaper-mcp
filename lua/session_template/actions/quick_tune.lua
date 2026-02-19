-- actions/quick_tune.lua — Toggle ReaTune on DI track
-- Phase 5 implementation

dofile(debug.getinfo(1, "S").source:match("@?(.*/)") .. "init.lua")
reaper.defer(function() end)
