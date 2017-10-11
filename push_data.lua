            local function push_data(time)
                local Statsd = require("resty_statsd")
                local conn, err = Statsd({
                    host = "graphite",
                    port = 8125,
                    namespace = "legion.model"
                })
                if conn ~= Nil then
                    conn:counter("{{$name}}.request.count", 1, 1)
                    conn:histogram("{{$name}}.request.time", time)
                else
                    ngx.log(ngx.ERR, err)
                end
            end

            local latency = floor((ngx.now() - ngx.req.start_time()) * 1000)

            local ok, err = ngx.timer.at(0, push_data, latency)
            if not ok then
                ngx.log(ngx.ERR, "Failed to create Statsd reporting timer: ", err)
                return
            end
