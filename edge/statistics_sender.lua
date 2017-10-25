--
--   Copyright 2017 EPAM Systems
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
local _M = {}
local Statsd = require("resty_statsd")
local os = require("os")

function _M.get_config(_, name, default)
    local value = os.getenv(name)
    if value ~= Nil then
        return value
    else
        return default
    end
end

function _M.push_data(_, time, name)
    local host = _M:get_config("STATSD_HOST", "graphite")
    local port = _M:get_config("STATSD_PORT", "8125")
    local namespace = _M:get_config("STATSD_NAMESPACE", "legion.model")

    ngx.log(ngx.DEBUG, "Connection to host="..host.." port="..port.." namespace="..namespace)

    local conn, err = Statsd({
        host = host,
        port = tonumber(port),
        namespace = namespace
    })

    local ok = false

    if conn ~= Nil then
        ok, err = conn:increment(name..".request.count", 1, 1)
        ok, err = conn:timer(name..".request.time", time)
    end

    if err ~= Nil then
        ngx.log(ngx.ERR, "Failed to send Statsd statistics to host="..host.." port="..port.." namespace="..namespace..":", err)
    end
end

function _M.send_request_statistics(name, latency)
    local ok, err = ngx.timer.at(0, _M.push_data, latency, name)
    if not ok then
        ngx.log(ngx.ERR, "Failed to create Statsd reporting timer: ", err)
        return
    end
end

function _M.init()
    ngx.log(ngx.INFO, "statistics_sender.lua initialized!")
end

return _M
