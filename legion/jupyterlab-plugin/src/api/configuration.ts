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

import { httpRequest, IApiGroup, legionApiRootURL } from './base';
import * as models from '../models/configuration';
import { legionHttpExceptionHandler } from './errorHandler';

export namespace URLs {
  export const configurationUrl = legionApiRootURL + '/common/configuration';
  export const oauthInfoUrl = legionApiRootURL + '/oauth2/info';
  export const exampleContentUrl = legionApiRootURL + '/examples/:name/content';
}

export interface IConfigurationApi {
  getCloudConfiguration: () => Promise<models.IConfigurationMainResponse>;
  getExampleContent: (name: string) => Promise<string>;
  getOauthUrl: () => Promise<string>;
}

export class ConfigurationApi implements IApiGroup, IConfigurationApi {
  @legionHttpExceptionHandler()
  async getCloudConfiguration(): Promise<models.IConfigurationMainResponse> {
    let response = await httpRequest(URLs.configurationUrl, 'GET', null, null);
    if (response.status !== 200) {
      const data = await response.json();
      throw new ServerConnection.ResponseError(response, data.message);
    }
    return await response.json();
  }

  @legionHttpExceptionHandler()
  async getExampleContent(name: string): Promise<string> {
    let response = await httpRequest(
      URLs.exampleContentUrl.replace(':name', name),
      'GET',
      null,
      null
    );
    if (response.status !== 200) {
      const data = await response.json();
      throw new ServerConnection.ResponseError(response, data.message);
    }
    return response.text();
  }

  @legionHttpExceptionHandler()
  async getOauthUrl(): Promise<string> {
    let response = await httpRequest(URLs.oauthInfoUrl, 'GET', null, null);
    if (response.status !== 200) {
      const data = await response.json();
      throw new ServerConnection.ResponseError(response, data.message);
    }
    return response.text();
  }
}
