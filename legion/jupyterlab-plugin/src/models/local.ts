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

/**
 * Response that contains information about found models (docker images)
 */
export interface ILocalBuildInformation {
    imageName: string;
    modelName: string;
    modelVersion: string;
}

/**
 * Response that contains information about current build status
 */
export interface ILocalBuildStatus {
    started: boolean;
    finished: boolean;
    logs: string;
}


/**
 * Response that contains information about deployment
 */
export interface ILocalDeploymentInformation {
    name: string;
    image: string;
    port: number;
}

/**
 * Request to create new local deployment (to start docker container)
 */
export interface ILocalDeploymentRequest {
    name: string;
    image: string;
    port?: number;
}

/**
 * Request to remove local deployment (to stop docker container)
 */
export interface ILocalUnDeployRequest {
    name: string;
}

/**
 * Local metrics data
 */
export interface ILocalMetricsResponse {
    columns: Array<string>,
    index: Array<string>,
    data: Array<Array<any>>
}

/**
 * All data for local widget
 */
export interface ILocalAllEntitiesResponse {
    builds: Array<ILocalBuildInformation>,
    deployments: Array<ILocalDeploymentInformation>,
    buildStatus: ILocalBuildStatus
}