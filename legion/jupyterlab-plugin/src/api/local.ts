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
import * as models from '../models/local';

export namespace URLs {
  export const localBuildsUrl = legionApiRootURL + '/local/builds';
  export const localBuildStatusUrl = legionApiRootURL + '/local/builds/status';
  export const localDeploymentsUrl = legionApiRootURL + '/local/deployments';
  export const localMetricsUrl = legionApiRootURL + '/local/metrics';
  export const localAllDataUrl = legionApiRootURL + '/local';
}

export interface ILocalApi {
  // Builds
  startLocalBuild: () => Promise<void>;
  getLocalBuildStatus: () => Promise<models.ILocalBuildStatus>;
  getLocalBuilds: () => Promise<Array<models.ILocalBuildInformation>>;

  // Deployments
  getLocalDeployments: () => Promise<Array<models.ILocalDeploymentInformation>>;
  createLocalDeployment: (
    request: models.ILocalDeploymentRequest
  ) => Promise<models.ILocalDeploymentInformation>;
  removeLocalDeployment: (
    request: models.ILocalUnDeployRequest
  ) => Promise<void>;

  // Metrics
  getLocalMetrics: () => Promise<models.ILocalMetricsResponse>;

  // Aggregated
  getLocalAllEntities: () => Promise<models.ILocalAllEntitiesResponse>;
}

export class LocalApi implements IApiGroup, ILocalApi {
  // Builds
  async startLocalBuild(): Promise<void> {
    try {
      let response = await httpRequest(URLs.localBuildsUrl, 'POST', {});
      if (response.status !== 200) {
        const data = await response.json();
        throw new ServerConnection.ResponseError(response, data.message);
      }
      return null;
    } catch (err) {
      throw new ServerConnection.NetworkError(err);
    }
  }
  async getLocalBuildStatus(): Promise<models.ILocalBuildStatus> {
    try {
      let response = await httpRequest(URLs.localBuildStatusUrl, 'GET', null);
      if (response.status !== 200) {
        const data = await response.json();
        throw new ServerConnection.ResponseError(response, data.message);
      }
      return response.json();
    } catch (err) {
      throw new ServerConnection.NetworkError(err);
    }
  }
  async getLocalBuilds(): Promise<Array<models.ILocalBuildInformation>> {
    try {
      let response = await httpRequest(URLs.localBuildsUrl, 'GET', null);
      if (response.status !== 200) {
        const data = await response.json();
        throw new ServerConnection.ResponseError(response, data.message);
      }
      return response.json();
    } catch (err) {
      throw new ServerConnection.NetworkError(err);
    }
  }

  // Deployments
  async getLocalDeployments(): Promise<
    Array<models.ILocalDeploymentInformation>
  > {
    try {
      let response = await httpRequest(URLs.localDeploymentsUrl, 'GET', null);
      if (response.status !== 200) {
        const data = await response.json();
        throw new ServerConnection.ResponseError(response, data.message);
      }
      return response.json();
    } catch (err) {
      throw new ServerConnection.NetworkError(err);
    }
  }
  async createLocalDeployment(
    request: models.ILocalDeploymentRequest
  ): Promise<models.ILocalDeploymentInformation> {
    try {
      let response = await httpRequest(
        URLs.localDeploymentsUrl,
        'POST',
        request
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
  async removeLocalDeployment(
    request: models.ILocalUnDeployRequest
  ): Promise<void> {
    try {
      let response = await httpRequest(
        URLs.localDeploymentsUrl,
        'DELETE',
        request
      );
      if (response.status !== 200) {
        const data = await response.json();
        throw new ServerConnection.ResponseError(response, data.message);
      }
      return null;
    } catch (err) {
      throw new ServerConnection.NetworkError(err);
    }
  }

  async getLocalMetrics(): Promise<models.ILocalMetricsResponse> {
    try {
      let response = await httpRequest(URLs.localMetricsUrl, 'GET', null);
      if (response.status !== 200) {
        const data = await response.json();
        throw new ServerConnection.ResponseError(response, data.message);
      }
      return response.json();
    } catch (err) {
      throw new ServerConnection.NetworkError(err);
    }
  }

  // Aggregated
  async getLocalAllEntities(): Promise<models.ILocalAllEntitiesResponse> {
    try {
      let response = await httpRequest(URLs.localAllDataUrl, 'GET', null);
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
