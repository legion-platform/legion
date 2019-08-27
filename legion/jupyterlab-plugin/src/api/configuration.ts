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

export namespace URLs {
  export const configurationUrl = legionApiRootURL + '/common/configuration';
}

export interface IConfigurationApi {
  getCloudTrainings: () => Promise<models.IConfigurationMainResponse>;
}

export class ConfigurationApi implements IApiGroup, IConfigurationApi {
  // Trainings
  async getCloudTrainings(): Promise<models.IConfigurationMainResponse> {
    try {
      let response = await httpRequest(
        URLs.configurationUrl,
        'GET',
        null,
        null
      );
      if (response.status !== 200) {
        const data = await response.json();
        throw new ServerConnection.ResponseError(response, data.message);
      }
      return response.json();
    } catch (err) {
      throw new ServerConnection.NetworkError(err);
    }
  }
}
