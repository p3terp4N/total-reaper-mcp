-- actions/clear_cache.lua — Clear cached Lua modules
-- Called via RunSessionAction("clear_cache") to force reload on next require()

local modules = {
    "config", "plugins", "tracks", "fx", "utils", "generators",
    "backing.drums", "backing.bass", "backing.keys", "backing.guitar",
    "guitar", "production", "songwriting", "jam", "podcast",
    "mixing", "tone", "live", "transcription",
    "guitar_recording", "full_production", "jam_loop",
    "tone_design", "live_performance",
}
for _, mod in ipairs(modules) do
    package.loaded[mod] = nil
end
