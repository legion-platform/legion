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


function _M.push_data(_, time, name, endpoint)
    local host = _M.host
    local port = _M.port
    local namespace = _M.namespace

    ngx.log(ngx.DEBUG, "Connection to host="..host.." port="..port.." namespace="..namespace)

    local conn, err = Statsd({
        host = host,
        port = tonumber(port),
        namespace = namespace
    })

    local ok = false

    if conn ~= Nil then
        ok, err = conn:increment(name.."."..endpoint..".request.count", 1, 1)
        ok, err = conn:timer(name.."."..endpoint..".request.time", time)
    end

    if err ~= Nil then
        ngx.log(ngx.ERR, "Failed to send Statsd statistics to host="..host.." port="..port.." namespace="..namespace..":", err)
    end
end

function _M.send_request_statistics(name, latency)
    local request_http_headers = ngx.req.get_headers()
    local endpoint = request_http_headers["Model-Endpoint"]

    local ok, err = ngx.timer.at(0, _M.push_data, latency, name, endpoint)
    if not ok then
        ngx.log(ngx.ERR, "Failed to create Statsd reporting timer: ", err)
        return
    end
end

function _M.init(host, port, namespace)
    _M.host = host
    _M.port = port
    _M.namespace = namespace
    ngx.log(ngx.ERR, "statistics_sender.lua initialized with host="..host.." port="..port.." namespace="..namespace)
end

return _M
