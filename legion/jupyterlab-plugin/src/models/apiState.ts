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
import * as configurationModels from './configuration';

export const PLUGIN_CREDENTIALS_STORE_CLUSTER = `legion.cluster:credentials-cluster`;
export const PLUGIN_CREDENTIALS_STORE_TOKEN = `legion.cluster:credentials-token`;

export interface IApiCloudState {
  trainings: Array<cloud.ICloudTrainingResponse>;
  deployments: Array<cloud.ICloudDeploymentResponse>;
  vcss: Array<cloud.IVCSResponse>;

  isLoading: boolean;
  signalLoadingStarted(): void;
  onDataChanged: ISignal<this, void>;
  updateAllState(data?: cloud.ICloudAllEntitiesResponse): void;

  authorizationRequired: boolean;
  credentials: ICloudCredentials;
  setCredentials(
    credentials?: ICloudCredentials,
    skipPersisting?: boolean
  ): void;

  configuration: configurationModels.IConfigurationMainResponse;
  onConfigurationLoaded(config: configurationModels.IConfigurationMainResponse): void;
}

class APICloudStateImplementation implements IApiCloudState {
  private _trainings: Array<cloud.ICloudTrainingResponse>;
  private _deployments: Array<cloud.ICloudDeploymentResponse>;
  private _vcss: Array<cloud.IVCSResponse>;

  private _isLoading: boolean;
  private _dataChanged = new Signal<this, void>(this);

  private _credentials?: ICloudCredentials;
  private _configuration?: configurationModels.IConfigurationMainResponse;

  constructor() {
    this._isLoading = false;
    this._trainings = [];
    this._deployments = [];
    this._vcss = [];
    this._credentials = null;
    this._configuration = null;
  }

  get trainings(): Array<cloud.ICloudTrainingResponse> {
    return this._trainings;
  }

  get deployments(): Array<cloud.ICloudDeploymentResponse> {
    return this._deployments;
  }

  get vcss(): Array<cloud.IVCSResponse> {
    return this._vcss;
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
      this._vcss = data.vcss;
    }
    this._isLoading = false;
    this._dataChanged.emit(null);
  }

  get credentials(): ICloudCredentials {
    return this._credentials;
  }

  setCredentials(
    credentials?: ICloudCredentials,
    skipPersisting?: boolean
  ): void {
    if (credentials != undefined) {
      console.log('Updating credentials for ', credentials.cluster);
      this._credentials = credentials;
    } else {
      console.log('Resetting credentials');
      this._credentials = null;
    }

    if (skipPersisting !== true) {
      if (this._credentials) {
        localStorage.setItem(
          PLUGIN_CREDENTIALS_STORE_CLUSTER,
          this._credentials.cluster
        );
        localStorage.setItem(
          PLUGIN_CREDENTIALS_STORE_TOKEN,
          this._credentials.authString
        );
      } else {
        localStorage.removeItem(PLUGIN_CREDENTIALS_STORE_CLUSTER);
        localStorage.removeItem(PLUGIN_CREDENTIALS_STORE_TOKEN);
      }
    }
    this._dataChanged.emit(null);
  }

  tryToLoadCredentialsFromSettings(): void {
    const cluster = localStorage.getItem(PLUGIN_CREDENTIALS_STORE_CLUSTER);
    const authString = localStorage.getItem(PLUGIN_CREDENTIALS_STORE_TOKEN);

    if (cluster && authString) {
      this.setCredentials(
        {
          cluster,
          authString
        },
        true
      );
    } else {
      console.error('Can not load credentials from store');
    }
  }

  get configuration(): configurationModels.IConfigurationMainResponse {
    return this._configuration;
  }

  onConfigurationLoaded(config: configurationModels.IConfigurationMainResponse): void {
    this._configuration = config;

    if (!config.tokenProvided){
      this.tryToLoadCredentialsFromSettings();
    }
  }

  get authorizationRequired(): boolean {
    return !this._configuration.tokenProvided && this._credentials == null;
  }
}

export function buildInitialCloudAPIState(): IApiCloudState {
  return new APICloudStateImplementation();
}
