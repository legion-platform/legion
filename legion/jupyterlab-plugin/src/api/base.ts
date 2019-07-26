/**
 *   Copyright 2019 EPAM Systems
 *
 *   Licensed under the Apache License, Version 2.0 (the "License");
 *   you may not use this file except in compliance with the License.
 *   You may obtain a copy of the License at
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 *
 *   Unless required by applicable law or agreed to in writing, software
 *   distributed under the License is distributed on an "AS IS" BASIS,
 *   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 *   See the License for the specific language governing permissions and
 *   limitations under the License.
 */
import { ServerConnection } from '@jupyterlab/services';
import { URLExt } from '@jupyterlab/coreutils';

export interface ICloudCredentials {
  cluster: string;
  authString: string;
}

/**
 * Create request promise
 * @param url string target URL (relevant)
 * @param method request method
 * @param request request payload (as JSON body)
 * @param credentials
 */
export function httpRequest(
  url: string,
  method: string,
  request: Object | null,
  credentials?: ICloudCredentials | null
): Promise<Response> {
  let fullRequest = {
    method: method,
    body: request != null ? JSON.stringify(request) : null
  };

  let setting = ServerConnection.makeSettings({
    init: {
      headers:
        credentials != null
          ? {
              'X-Legion-Cloud-Endpoint': credentials.cluster,
              'X-Legion-Cloud-Token': credentials.authString
            }
          : {}
    }
  });
  let fullUrl = URLExt.join(setting.baseUrl, url);
  return ServerConnection.makeRequest(fullUrl, fullRequest, setting);
}

/**
 * Root API for all Legion endpoints
 */
export const legionApiRootURL = '/legion/api';

export interface IApiGroup {}
