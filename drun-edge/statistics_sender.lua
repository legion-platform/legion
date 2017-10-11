local _M = {}
local Statsd = require("resty_statsd")

function _M.push_data(_, time, name)
    local conn, err = Statsd({
        host = "graphite",
        port = 8125,
        namespace = "legion.model"
    })
    if conn ~= Nil then
        conn:counter(name..".request.count", 1, 1)
        conn:histogram(name..".request.time", time)
    else
        ngx.log(ngx.ERR, err)
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