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
local cjson = require("cjson")

local _M = {}

function _M.get_config(name, default)
    local value = os.getenv(name)
    if value ~= Nil then
        return value
    else
        return default
    end
end


function _M.init_worker()
    uuid.seed()
end

function _M.generate_request_id()
    return uuid()
end

function _M.get_model_id_and_version_from_feedback_url()
    local m, err = ngx.re.match(ngx.var.uri, "/api/model/(.+)/(.+)/feedback")

    if err then
        ngx.exit(ngx.HTTP_BAD_REQUEST)
    end

    return m[1], m[2]
end

function _M.parse_feedback_data()
    local model_id, model_version = _M.get_model_id_and_version_from_feedback_url()
    local reqargs = require "resty.reqargs"
    local get, post, files = reqargs()
    local cjson = require "cjson"

    local data = {}
    local params = {}

    if post ~= nil and type(post) == "table" then
        for key, value in pairs(post) do
            params[key] = value
        end
    end

    if get ~= nil and type(get) == "table" then
        for key, value in pairs(get) do
            params[key] = value
        end
    end

    data["feedback_payload"] = params

    data["request_id"] = ngx.req.get_headers()["Request-ID"]

    data["model_id"] = model_id
    data["model_version"] = model_version

    return data
end

function _M.response_feedback(data)
    local response = {
        status = true,
        data = data
    }

    local json_encoded_response = cjson.encode(response)

    ngx.header["Content-Type"] = "application/json;charset=utf-8"
    ngx.say(json_encoded_response);
end

function _M.catch_model_api_response_chunk(model_id, model_version, content, eof)
    local http_request_headers = ngx.req.get_headers()
    local requestID = http_request_headers["Request-ID"]

    if eof and string.len(content) == 0 then
        return nil
    end

    local chunk_id = ngx.var.model_api_chunk_count

    local data = {
        request_id = requestID,
        response_chunk_id = chunk_id,
        response_content = content,
        model_id = model_id,
        model_version = model_version
    }

    ngx.var.model_api_chunk_count = chunk_id + 1

    return data
end

function _M.catch_model_api_call(model_id, model_version)
    local request_http_headers = ngx.req.get_headers()
    local request_id = request_http_headers["Request-ID"]
    local http_method = ngx.req.get_method()
    request_http_headers["authorization"] = nil

    local data = {
        request_id = request_id,
        request_http_method = http_method,
        request_http_headers = request_http_headers,
        request_host = ngx.var.HOST,
        request_uri = ngx.var.uri,
        response_duration = ngx.var.upstream_response_time,
        response_http_headers = ngx.resp.get_headers(),
        response_body_chunk_count = ngx.var.model_api_chunk_count,
        response_status = ngx.status,
        model_id = model_id,
        model_version = model_version
    }

    local content_type = ngx.var.content_type or ""
    if http_method == 'GET' then
        data['request_get_args'] = ngx.req.get_uri_args()
    elseif string.sub(content_type, 1, 33) == "application/x-www-form-urlencoded"
            and http_method == 'POST' then
        data["request_post_args"] = ngx.req.get_post_args()
    end

    return data
end

return _M
