-- actions/init.lua — Shared bootstrap for action scripts
-- Sets package.path so action scripts can require() lib modules

local info = debug.getinfo(1, "S")
local script_path = info.source:match("@?(.*/)") or ""
local base_path = script_path:match("(.*/session_template/)")
if base_path then
  package.path = base_path .. "lib/?.lua;" .. package.path
end
