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
import { IStateDB } from "@jupyterlab/coreutils";

import { ICloudCredentials } from '../api/base';
import * as local from './local';
import * as cloud from './cloud';

export const PLUGIN_CREDENTIALS_STORE_CLUSTER = `legion.cluster:credentials-cluster`;
export const PLUGIN_CREDENTIALS_STORE_TOKEN = `legion.cluster:credentials-token`;

export interface IApiLocalState {
    builds: Array<local.ILocalBuildInformation>;
    deployments: Array<local.ILocalDeploymentInformation>;
    buildStatus: local.ILocalBuildStatus;

    isLoading: boolean;
    signalLoadingStarted(): void;
    onDataChanged: ISignal<this, void>;

    updateAllState(data?: local.ILocalAllEntitiesResponse): void;
    updateBuildState(data: local.ILocalBuildStatus): void;
    updateBuildStateStarted(): void;
}

export interface IApiCloudState {
    trainings: Array<cloud.ICloudTrainingResponse>,
    deployments: Array<cloud.ICloudDeploymentResponse>,
    vcss: Array<cloud.IVCSResponse>

    isLoading: boolean;
    signalLoadingStarted(): void;
    onDataChanged: ISignal<this, void>;
    updateAllState(data?: cloud.ICloudAllEntitiesResponse): void;

    credentials: ICloudCredentials;
    setCredentials(credentials?: ICloudCredentials, skipPersisting?: boolean): void;
    tryToLoadCredentialsFromSettings(): void;
}

class APILocalStateImplementation implements IApiLocalState {
    private _builds: Array<local.ILocalBuildInformation>;
    private _deployments: Array<local.ILocalDeploymentInformation>;
    private _buildStatus: local.ILocalBuildStatus;

    private _isLoading: boolean;
    private _dataChanged = new Signal<this, void>(this);

    constructor() {
        this._isLoading = false;
        this._builds = [];
        this._deployments = [];
        this._buildStatus = {
            started: false,
            finished: false,
            logs: ''
        };
    }

    get builds(): Array<local.ILocalBuildInformation> {
        return this._builds;
    }
    get deployments(): Array<local.ILocalDeploymentInformation> {
        return this._deployments;
    }
    get buildStatus(): local.ILocalBuildStatus {
        return this._buildStatus;
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

    updateAllState(data?: local.ILocalAllEntitiesResponse): void {
        if (data) {
            this._builds = data.builds;
            this._deployments = data.deployments;
            this._buildStatus = data.buildStatus;
        }
        this._isLoading = false;
        this._dataChanged.emit(null);
    }

    updateBuildState(data: local.ILocalBuildStatus): void {
        this._buildStatus = data;
        this._dataChanged.emit(null);
    }

    updateBuildStateStarted(): void {
        this._buildStatus = {
            started: true,
            finished: false,
            logs: ''
        };
        this._dataChanged.emit(null);

    }
}

class APICloudStateImplementation implements IApiCloudState {
    private _trainings: Array<cloud.ICloudTrainingResponse>;
    private _deployments: Array<cloud.ICloudDeploymentResponse>;
    private _vcss: Array<cloud.IVCSResponse>

    private _isLoading: boolean;
    private _dataChanged = new Signal<this, void>(this);

    private _credentials?: ICloudCredentials;
    private _appState: IStateDB;

    constructor(appState: IStateDB) {
        this._isLoading = false;
        this._trainings = [];
        this._deployments = [];
        this._vcss = [];
        this._credentials = null;
        this._appState = appState;
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

    setCredentials(credentials?: ICloudCredentials, skipPersisting?: boolean): void {
        if (credentials != undefined) {
            console.log('Updating credentials for ', credentials.cluster);
            this._credentials = credentials;
        } else {
            console.log('Resetting credentials');
            this._credentials = null;
        }

        if (skipPersisting !== true) {
            if (this._credentials) {
                Promise.all([
                    this._appState.save(PLUGIN_CREDENTIALS_STORE_CLUSTER, this._credentials.cluster),
                    this._appState.save(PLUGIN_CREDENTIALS_STORE_TOKEN, this._credentials.authString),
                ]).then(() => {
                    console.log('Cluster and token have been persisted in settings');
                }).catch(err => {
                    console.error('Can not persist cluster and token in settings', err);
                });
            } else {
                Promise.all([
                    this._appState.remove(PLUGIN_CREDENTIALS_STORE_CLUSTER),
                    this._appState.remove(PLUGIN_CREDENTIALS_STORE_TOKEN)
                ]).then(() => {
                    console.log('Cluster and token have been removed from storage');
                }).catch(err => {
                    console.error('Can not remove cluster and token from storage', err);
                });
            }
        }
        this._dataChanged.emit(null);
    }

    tryToLoadCredentialsFromSettings(): void {
        Promise.all([
            this._appState.fetch(PLUGIN_CREDENTIALS_STORE_CLUSTER),
            this._appState.fetch(PLUGIN_CREDENTIALS_STORE_TOKEN),
        ]).then((answers) => {
            if (!answers[0]) {
                console.warn('Empty data loaded from credentials store');
            } else {
                let credentials = {
                    cluster: answers[0] as string,
                    authString: answers[1] as string
                };
                this.setCredentials(credentials, true);
            }
        }).catch(err => {
            console.error('Can not load credentials from store', err);
        });
    }
}

export function buildInitialLocalAPIState(): IApiLocalState {
    return new APILocalStateImplementation();
}

export function buildInitialCloudAPIState(appState: IStateDB): IApiCloudState {
    return new APICloudStateImplementation(appState);
}