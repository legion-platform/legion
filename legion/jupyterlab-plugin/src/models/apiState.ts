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
import { ISignal, Signal } from '@phosphor/signaling';

import { ICloudCredentials } from '../api/base';
import * as cloud from './cloud';
import { ModelTraining } from '../legion/ModelTraining';
import { ModelDeployment } from '../legion/ModelDeployment';
import { Connection } from '../legion/Connection';
import { ModelPackaging } from '../legion/ModelPackaging';
import { ToolchainIntegration } from '../legion/ToolchainIntegration';
import { PackagingIntegration } from '../legion/PackagingIntegration';

import * as configurationModels from './configuration';
import { IConfigurationMainResponse } from './configuration';
import { Configuration } from '../legion/Configuration';

export const PLUGIN_CREDENTIALS_STORE_CLUSTER = `legion.cluster:credentials-cluster`;
export const PLUGIN_CREDENTIALS_STORE_TOKEN = `legion.cluster:credentials-token`;
export const LEGION_OAUTH_TOKEN_COOKIE_NAME = `_legion_oauth_token`;

export interface IApiCloudState {
  trainings: Array<ModelTraining>;
  deployments: Array<ModelDeployment>;
  connections: Array<Connection>;
  modelPackagings: Array<ModelPackaging>;
  toolchainIntegrations: Array<ToolchainIntegration>;
  packagingIntegrations: Array<PackagingIntegration>;
  configuration: Configuration;
  isLoading: boolean;

  signalLoadingStarted(): void;

  onDataChanged: ISignal<this, void>;

  updateAllState(data?: cloud.ICloudAllEntitiesResponse): void;

  authorizationRequired: boolean;

  updateAuthConfiguration(data?: IConfigurationMainResponse): void;

  credentials: ICloudCredentials;

  setCredentials(credentials?: ICloudCredentials): void;

  authConfiguration: configurationModels.IConfigurationMainResponse;

  onConfigurationLoaded(
    config: configurationModels.IConfigurationMainResponse
  ): void;
}

class APICloudStateImplementation implements IApiCloudState {
  private _trainings: Array<ModelTraining>;
  private _deployments: Array<ModelDeployment>;
  private _connections: Array<Connection>;
  private _modelpackagings: Array<ModelPackaging>;
  private _toolchainIntegrations: Array<ToolchainIntegration>;
  private _packagingIntegrations: Array<PackagingIntegration>;
  private _configuration: Configuration;

  private _isLoading: boolean;
  private _dataChanged = new Signal<this, void>(this);

  private _oauthConfiguration?: configurationModels.IConfigurationMainResponse;

  constructor() {
    this._isLoading = false;
    this._trainings = [];
    this._deployments = [];
    this._connections = [];
    this._modelpackagings = [];
    this._toolchainIntegrations = [];
    this._packagingIntegrations = [];
    this._configuration = null;
    this._oauthConfiguration = null;
  }

  get trainings(): Array<ModelTraining> {
    return this._trainings;
  }

  get deployments(): Array<ModelDeployment> {
    return this._deployments;
  }

  get connections(): Array<Connection> {
    return this._connections;
  }

  get modelPackagings(): Array<ModelPackaging> {
    return this._modelpackagings;
  }

  get toolchainIntegrations(): Array<ToolchainIntegration> {
    return this._toolchainIntegrations;
  }

  get packagingIntegrations(): Array<PackagingIntegration> {
    return this._packagingIntegrations;
  }

  get configuration(): Configuration {
    return this._configuration;
  }

  get isLoading(): boolean {
    return this._isLoading;
  }

  get onDataChanged(): ISignal<this, void> {
    return this._dataChanged;
  }

  signalLoadingStarted(): void {
    this._isLoading = true;
    this._dataChanged.emit(null);
  }

  updateAllState(data?: cloud.ICloudAllEntitiesResponse): void {
    if (data) {
      this._trainings = data.trainings;
      this._deployments = data.deployments;
      this._connections = data.connections;
      this._modelpackagings = data.modelPackagings;
      this._toolchainIntegrations = data.toolchainIntegrations;
      this._packagingIntegrations = data.packagingIntegrations;
      this._configuration = data.configuration;
    }
    this._isLoading = false;
    this._dataChanged.emit(null);
  }

  updateAuthConfiguration(data?: IConfigurationMainResponse): void {
    if (data) {
      this._oauthConfiguration = data;
    }
    this._isLoading = false;
    this._dataChanged.emit(null);
  }

  get credentials(): ICloudCredentials {
    let defaultEDIURL = this.authConfiguration
      ? this.authConfiguration.defaultEDIEndpoint
      : '';

    return {
      cluster:
        localStorage.getItem(PLUGIN_CREDENTIALS_STORE_CLUSTER) || defaultEDIURL,
      authString: localStorage.getItem(PLUGIN_CREDENTIALS_STORE_TOKEN)
    };
  }

  setCredentials(credentials?: ICloudCredentials): void {
    if (credentials) {
      if (credentials.cluster) {
        localStorage.setItem(
          PLUGIN_CREDENTIALS_STORE_CLUSTER,
          credentials.cluster
        );
      }

      if (credentials.authString) {
        localStorage.setItem(
          PLUGIN_CREDENTIALS_STORE_TOKEN,
          credentials.authString
        );
      }
    } else {
      console.log('Resetting credentials');

      localStorage.removeItem(PLUGIN_CREDENTIALS_STORE_CLUSTER);
      localStorage.removeItem(PLUGIN_CREDENTIALS_STORE_TOKEN);
    }

    this._dataChanged.emit(null);
  }

  get authConfiguration(): configurationModels.IConfigurationMainResponse {
    return this._oauthConfiguration;
  }

  onConfigurationLoaded(
    config: configurationModels.IConfigurationMainResponse
  ): void {
    this._oauthConfiguration = config;

    if (config.oauth2AuthorizationIsEnabled && config.idToken) {
      this.setCredentials({
        authString: config.idToken,
        cluster: ''
      });
    }
  }

  get authorizationRequired(): boolean {
    return (
      (this._oauthConfiguration == null ||
        !this._oauthConfiguration.tokenProvided) &&
      (!this.credentials.authString || !this.credentials.cluster)
    );
  }
}

export function buildInitialCloudAPIState(): IApiCloudState {
  return new APICloudStateImplementation();
}
