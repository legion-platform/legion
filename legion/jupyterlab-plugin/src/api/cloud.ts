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
  legionApiRootURL,
  ICloudCredentials
} from './base';
import * as models from '../models/cloud';

export namespace URLs {
  export const cloudTrainingsUrl = legionApiRootURL + '/cloud/trainings';
  export const cloudTrainingLogsUrl =
    legionApiRootURL + '/cloud/trainings/:trainingName:/logs';
  export const cloudDeploymentsUrl = legionApiRootURL + '/cloud/deployments';
  export const cloudDeploymentsScaleUrl =
    legionApiRootURL + '/cloud/deployments/scale';
  export const cloudAllDataUrl = legionApiRootURL + '/cloud';
  export const cloudIssueModelTokenUrl =
    legionApiRootURL + '/cloud/security/token';
  export const cloudApplyFileUrl = legionApiRootURL + '/cloud/apply';
}

export interface ICloudApi {
  // Trainings
  getCloudTrainings: (
    credentials: ICloudCredentials
  ) => Promise<Array<models.ICloudTrainingResponse>>;
  removeCloudTraining: (
    request: models.ICloudTrainingRemoveRequest,
    credentials: ICloudCredentials
  ) => Promise<void>;
  getTrainingLogs: (
    request: models.ICloudTrainingLogsRequest,
    credentials: ICloudCredentials
  ) => Promise<models.ICloudTrainingLogsResponse>;

  // Deployments
  getCloudDeployments: (
    credentials: ICloudCredentials
  ) => Promise<Array<models.ICloudDeploymentResponse>>;
  createCloudDeployment: (
    request: models.ICloudDeploymentCreateRequest,
    credentials: ICloudCredentials
  ) => Promise<models.ICloudDeploymentResponse>;
  scaleCloudDeployment: (
    request: models.ICloudDeploymentScaleRequest,
    credentials: ICloudCredentials
  ) => Promise<void>;
  removeCloudDeployment: (
    request: models.ICloudDeploymentRemoveRequest,
    credentials: ICloudCredentials
  ) => Promise<void>;

  // Aggregated
  getCloudAllEntities: (
    credentials: ICloudCredentials
  ) => Promise<models.ICloudAllEntitiesResponse>;

  // Issue model JWT token
  issueCloudAccess: (
    request: models.ICloudIssueTokenRequest,
    credentials: ICloudCredentials
  ) => Promise<models.ICloudIssueTokenResponse>;

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
  ): Promise<Array<models.ICloudTrainingResponse>> {
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
    request: models.ICloudTrainingRemoveRequest,
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
  async getTrainingLogs(
    request: models.ICloudTrainingLogsRequest,
    credentials: ICloudCredentials
  ): Promise<models.ICloudTrainingLogsResponse> {
    try {
      const url = URLs.cloudTrainingLogsUrl.replace(
        ':trainingName:',
        request.name
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
  ): Promise<Array<models.ICloudDeploymentResponse>> {
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
    request: models.ICloudDeploymentCreateRequest,
    credentials: ICloudCredentials
  ): Promise<models.ICloudDeploymentResponse> {
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
  async scaleCloudDeployment(
    request: models.ICloudDeploymentScaleRequest,
    credentials: ICloudCredentials
  ): Promise<void> {
    try {
      let response = await httpRequest(
        URLs.cloudDeploymentsScaleUrl,
        'PUT',
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
    request: models.ICloudDeploymentRemoveRequest,
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
  async issueCloudAccess(
    request: models.ICloudIssueTokenRequest,
    credentials: ICloudCredentials
  ): Promise<models.ICloudIssueTokenResponse> {
    try {
      let response = await httpRequest(
        URLs.cloudIssueModelTokenUrl,
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
