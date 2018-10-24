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
local _M = {}

function _M.check_token()
    local auth_header = ngx.var.http_Authorization

    local _, _, token = string.find(auth_header, "Bearer%s+(.+)")
    if _M.invalid_tokens[token] ~= nil then
        ngx.log(ngx.WARN, "Invalid token")
        ngx.exit(ngx.HTTP_UNAUTHORIZED)
    end
end

function _M.init(invalid_tokens)
    _M.invalid_tokens = {}
    for invalid_token in string.gmatch(invalid_tokens, "%S+") do
        _M.invalid_tokens[invalid_token] = true
    end
end

return _M