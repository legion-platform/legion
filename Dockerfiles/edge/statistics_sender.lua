--
--   Copyright 2019 EPAM Systems
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

function _M.send_request_statistics(model_id, model_version, model_endpoint, latency)
    _M.metric_requests:inc(1, {model_id, model_version, model_endpoint})
    _M.metric_latency:observe(latency, {model_id, model_version, model_endpoint})
end

function _M.metrics()
    return _M.prometheus:collect()
end

function _M.init()
    _M.prometheus = require("prometheus").init("prometheus_metrics")
    _M.metric_requests = _M.prometheus:counter(
            "legion_model_request_counter", "Number of model HTTP requests",
            {"model_id", "model_version", "model_endpoint"}
    )
    _M.metric_latency = _M.prometheus:histogram(
            "legion_model_request_time", "HTTP model request latency",
            {"model_id", "model_version", "model_endpoint"}
    )
end

return _M