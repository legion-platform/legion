--
--   Copyright 2018 EPAM Systems
--
--   Licensed under the Apache License, Version 2.0 (the "License");
--   you may not use this file except in compliance with the License.
--   You may obtain a copy of the License at
--
--       http://www.apache.org/licenses/LICENSE-2.0
--
--   Unless required by applicable law or agreed to in writing, software
--   distributed under the License is distributed on an "AS IS" BASIS,
--   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
--   See the License for the specific language governing permissions and
--   limitations under the License.
--
local os = require("os")
local uuid = require "resty.jit-uuid"
local bit = require 'bit'
local _M = {}


function _M.reset_seed()
    local pod_uuid = os.getenv("POD_UUID")
    if pod_uuid == nil then
        pod_uuid = ""
    end

    local pod_uuid_crc32 = ngx.crc32_short(pod_uuid) -- CRC32 of POD ID

    local pid = ngx.worker.pid() -- process ID
    local wid = ngx.worker.id() -- worker ID
    local time = ngx.time() -- timestamp

    --[[
    Seed structure:
    |      POD UID CRC 32 hash       | + | PID| WID|  TIMESTAMP's tail      | + |      Bytes from /dev/urandom   |
    |            32 bits             | + |4bts|4bts|          24bits        | + |            32 bytes            |
    |--------------------------------| + |---- ---- ------------------------| + |--------------------------------|
    |            1st string          | + |              2nd string          | + |            3rd string          |
    --]]

    -- Second seed string
    local seed_p2_pid = bit.lshift(28, bit.band(pid, 0xF)) -- (PID & 0xF) << 28
    local seed_p2_wid = bit.lshift(24, bit.band(wid, 0xF)) -- (WID & 0xF) << 24
    local seed_p2_time = bit.band(time, 0x0FFFFFFF)         -- TIMESTAMP & 0x0FFFFFFF
    local seed_p2 = bit.bor(bit.bor(seed_p2_pid, seed_p2_wid), seed_p2_time)
    -- Third seed string
    local random_stream = io.open("/dev/urandom", "r")
    local random_data = tostring(random_stream:read(32))
    random_stream:close()
    -- Entire seed
    local seed = ngx.crc32_short(tostring(pod_uuid_crc32)..tostring(seed_p2)..random_data)


    ngx.log(ngx.ERR, "Resetting UUID seed to 0x"..string.format("%x", seed)..": POD_UUID = "..pod_uuid..
            " (CRC32: "..pod_uuid_crc32.."); Time = "..time.."; PID = "..pid.."; WID = "..wid..
            "; Random = "..random_data.." (CRC32: "..ngx.crc32_short(random_data))

    math.randomseed(seed)
end

function _M.generate_request_id()
    return uuid()
end

-- Reset seed on load
_M.reset_seed()

return _M