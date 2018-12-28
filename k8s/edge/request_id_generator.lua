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
local _M = {}

function _M.reset_seed()
    local pod_uuid = os.getenv("POD_UID")
    if pod_uuid == Nil then
        pod_uuid = ""
    end

    local pid = ngx.worker.pid()
    local wid = ngx.worker.id()

    local seed_string = pod_uuid.."-pid-"..pid.."-wid-"..wid

    ngx.log(ngx.ERR, "Resetting UUID seed to "..seed_string)

    math.randomseed(seed_string)
end

function _M.generate_request_id()
    return uuid()
end

-- Reset seed on load
_M.reset_seed()
