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
local cmsgpack = require "cmsgpack"

local _M = {}

function _M.new(host, port)
    _M.host = host
    _M.port = port
end

function _M._postHandler(_, host, port, time, tag, data)
    ngx.log(ngx.DEBUG, "Creating socket")
    local socket = ngx.socket.tcp()
    local time = math.floor(time)
    ngx.log(ngx.DEBUG, "Connection to host="..host.." port="..port)
    socket:connect(host, port)
    ngx.log(ngx.DEBUG, "Sending message with tag="..tag.." time="..time)
    socket:send(cmsgpack.pack({tag, time, data}))
    ngx.log(ngx.DEBUG, "Message has been sent")
    socket:setkeepalive(0, 30) -- Set connection pool up to 30 connections (per worker)
    ngx.log(ngx.DEBUG, "Connection has been keept in keepalive mode")
end

function _M.post(time, tag, data)
    ngx.log(ngx.DEBUG, "Starting fluentd sending timer")
    local ok, err = ngx.timer.at(0, _M._postHandler, _M.host, _M.port, time, tag, data)
    if not ok then
        ngx.log(ngx.ERR, "Failed to create fluentd reporting timer: ", err)
        return
    end
end

return _M