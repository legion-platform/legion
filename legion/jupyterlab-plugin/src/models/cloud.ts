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

export interface ICloudTrainingRequest {
    name: string;
    toolchain: string;
    entrypoint: string;
    image: string;
    vcsName: string;
    workDir: string;
    reference: string;

}


export interface ICloudTrainingResponseSpec {
    toolchain: string;
    resources: string;
    entrypoint: string;
    args: Array<string>;
    vcsName: string;
    workDir: string;
    reference: string;
}


export interface ICloudTrainingResponseStatus {
    id: string;
    version: string;
    state: string;
    modelImage: string;
}

export interface ICloudTrainingResponse {
    name: string;
    spec: ICloudTrainingResponseSpec;
    status: ICloudTrainingResponseStatus;
}

export interface ICloudTrainingRemoveRequest {
    name: string;
}


export interface ICloudTrainingLogsRequest {
    name: string;
}

export interface ICloudTrainingLogsResponse {
    data: string;
    futureLogsExpected: boolean;
}

export interface ICloudDeploymentCreateRequest {
    name: string;
    image: string;
    replicas: number;
    livenessProbeInitialDelay: number;
    readinessProbeInitialDelay: number;
}

export interface ICloudDeploymentScaleRequest {
    name: string;
    newScale: number;
}

export interface ICloudDeploymentRemoveRequest {
    name: string;
}

export interface ICloudDeploymentResponseSpec {
    image: string
    resources: string;
    annotations: Array<string>;
    replicas: number;
    livenessProbeInitialDelay: number;
    readinessProbeInitialDelay: number;
}

export interface ICloudDeploymentResponseStatus {
    state: string;
    serviceURL: string;
    availableReplicas: number;
}

export interface ICloudDeploymentResponse {
    name: string;
    spec: ICloudDeploymentResponseSpec;
    status: ICloudDeploymentResponseStatus;
}

export interface IVCSResponseSpec {
    type: string;
    uri: string;
    defaultReference: string;
    credential: string;
    publicKey: string;
}

export interface IVCSResponse {
    name: string;
    spec: IVCSResponseSpec;
}

/**
 * All data for cloud widget
 */
export interface ICloudAllEntitiesResponse {
    trainings: Array<ICloudTrainingResponse>,
    deployments: Array<ICloudDeploymentResponse>,
    vcss: Array<IVCSResponse>
}

export interface ICloudIssueTokenRequest {
    model_id: string;
    model_version: string;
}

export interface ICloudIssueTokenResponse {
    token: string;  //+safeToCommit
}

export interface ILocalFileInformationRequest {
    path: string;

}

export interface ILocalFileInformationResponse {
    path: string
    workDir: string
    extension: string
    gitCommandAvailable: boolean;
    fileInGitRepository: boolean;
    remotes: Array<string>;
    references: Array<string>;
}


export interface IApplyFromFileRequest {
    path: string;
    removal: boolean;
}

export interface IApplyFromFileResponse {
    created: Array<string>;
    changed: Array<string>;
    removed: Array<string>;
    errors: Array<string>;
}