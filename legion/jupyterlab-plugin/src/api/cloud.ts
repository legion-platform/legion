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

import {
  httpRequest,
  IApiGroup,
  ICloudCredentials,
  legionApiRootURL
} from './base';
import * as models from '../models/cloud';
import { ModelTraining } from '../legion/ModelTraining';
import { ModelDeployment } from '../legion/ModelDeployment';

export namespace URLs {
  export const cloudTrainingsUrl = legionApiRootURL + '/cloud/trainings';
  export const cloudConnectionsUrl = legionApiRootURL + '/cloud/connections';
  export const cloudModelPackagingUrl =
    legionApiRootURL + '/cloud/modelpackagings';
  export const cloudTrainingLogsUrl =
    legionApiRootURL + '/cloud/trainings/:trainingName:/logs';
  export const cloudPackagingLogsUrl =
    legionApiRootURL + '/cloud/packagings/:packagingName:/logs';
  export const cloudDeploymentsUrl = legionApiRootURL + '/cloud/deployments';
  export const cloudAllDataUrl = legionApiRootURL + '/cloud';
  export const cloudApplyFileUrl = legionApiRootURL + '/cloud/apply';
}

export interface ICloudApi {
  // Trainings
  getCloudTrainings: (
    credentials: ICloudCredentials
  ) => Promise<Array<ModelTraining>>;
  removeCloudTraining: (
    request: models.IRemoveRequest,
    credentials: ICloudCredentials
  ) => Promise<void>;
  removeConnection: (
    request: models.IRemoveRequest,
    credentials: ICloudCredentials
  ) => Promise<void>;
  removeModelPackaging: (
    request: models.IRemoveRequest,
    credentials: ICloudCredentials
  ) => Promise<void>;
  getTrainingLogs: (
    request: models.ICloudTrainingLogsRequest,
    credentials: ICloudCredentials
  ) => Promise<models.ICloudLogsResponse>;
  getPackagingLogs: (
    request: models.ICloudTrainingLogsRequest,
    credentials: ICloudCredentials
  ) => Promise<models.ICloudLogsResponse>;

  // Deployments
  getCloudDeployments: (
    credentials: ICloudCredentials
  ) => Promise<Array<ModelDeployment>>;
  createCloudDeployment: (
    request: ModelDeployment,
    credentials: ICloudCredentials
  ) => Promise<ModelDeployment>;
  removeCloudDeployment: (
    request: models.IRemoveRequest,
    credentials: ICloudCredentials
  ) => Promise<void>;

  // Aggregated
  getCloudAllEntities: (
    credentials: ICloudCredentials
  ) => Promise<models.ICloudAllEntitiesResponse>;

  // General
  applyFromFile: (
    request: models.IApplyFromFileRequest,
    credentials: ICloudCredentials
  ) => Promise<models.IApplyFromFileResponse>;
}

export class CloudApi implements IApiGroup, ICloudApi {
  // Trainings
  async getCloudTrainings(
    credentials: ICloudCredentials
  ): Promise<Array<ModelTraining>> {
    try {
      let response = await httpRequest(
        URLs.cloudTrainingsUrl,
        'GET',
        null,
        credentials
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

  async removeCloudTraining(
    request: models.IRemoveRequest,
    credentials: ICloudCredentials
  ): Promise<void> {
    try {
      let response = await httpRequest(
        URLs.cloudTrainingsUrl,
        'DELETE',
        request,
        credentials
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

  async removeConnection(
    request: models.IRemoveRequest,
    credentials: ICloudCredentials
  ): Promise<void> {
    try {
      let response = await httpRequest(
        URLs.cloudConnectionsUrl,
        'DELETE',
        request,
        credentials
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

  async removeModelPackaging(
    request: models.IRemoveRequest,
    credentials: ICloudCredentials
  ): Promise<void> {
    try {
      let response = await httpRequest(
        URLs.cloudModelPackagingUrl,
        'DELETE',
        request,
        credentials
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

  async getTrainingLogs(
    request: models.ICloudTrainingLogsRequest,
    credentials: ICloudCredentials
  ): Promise<models.ICloudLogsResponse> {
    try {
      const url = URLs.cloudTrainingLogsUrl.replace(
        ':trainingName:',
        request.id
      );
      let response = await httpRequest(url, 'GET', undefined, credentials);
      if (response.status !== 200) {
        const data = await response.json();
        throw new ServerConnection.ResponseError(response, data.message);
      }
      return response.json();
    } catch (err) {
      throw new ServerConnection.NetworkError(err);
    }
  }

  async getPackagingLogs(
    request: models.ICloudTrainingLogsRequest,
    credentials: ICloudCredentials
  ): Promise<models.ICloudLogsResponse> {
    try {
      const url = URLs.cloudPackagingLogsUrl.replace(
        ':packagingName:',
        request.id
      );
      let response = await httpRequest(url, 'GET', undefined, credentials);
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
  async getCloudDeployments(
    credentials: ICloudCredentials
  ): Promise<Array<ModelDeployment>> {
    try {
      let response = await httpRequest(
        URLs.cloudDeploymentsUrl,
        'GET',
        null,
        credentials
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

  async createCloudDeployment(
    request: ModelDeployment,
    credentials: ICloudCredentials
  ): Promise<ModelDeployment> {
    try {
      let response = await httpRequest(
        URLs.cloudDeploymentsUrl,
        'POST',
        request,
        credentials
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

  async removeCloudDeployment(
    request: models.IRemoveRequest,
    credentials: ICloudCredentials
  ): Promise<void> {
    try {
      let response = await httpRequest(
        URLs.cloudDeploymentsUrl,
        'DELETE',
        request,
        credentials
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

  // Aggregated
  async getCloudAllEntities(
    credentials: ICloudCredentials
  ): Promise<models.ICloudAllEntitiesResponse> {
    try {
      let response = await httpRequest(
        URLs.cloudAllDataUrl,
        'GET',
        null,
        credentials
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

  // General
  async applyFromFile(
    request: models.IApplyFromFileRequest,
    credentials: ICloudCredentials
  ): Promise<models.IApplyFromFileResponse> {
    try {
      let response = await httpRequest(
        URLs.cloudApplyFileUrl,
        'POST',
        request,
        credentials
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
