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
import * as React from 'react';
import { Dialog, showDialog } from '@jupyterlab/apputils';

import * as style from '../../componentsStyle/dialogs';
import * as model from '../../models/local';

export const REMOVE_DEPLOYMENT_LABEL = 'Remove deployment';
export const CREATE_DEPLOYMENT_LABEL = 'Deploy model';

export function showLocalBuildInformationDialog(build: model.ILocalBuildInformation) {
  return showDialog({
    title: `Local build information`,
    body: (
      <div>
        <h3 className={style.fieldLabelStyle}>Image</h3>
        <p className={style.fieldTextStyle}>{build.imageName}</p>
        <h3 className={style.fieldLabelStyle}>Model Name</h3>
        <p className={style.fieldTextStyle}>{build.modelName}</p>
        <h3 className={style.fieldLabelStyle}>Model Version</h3>
        <p className={style.fieldTextStyle}>{build.modelVersion}</p>
      </div>
    ),
    buttons: [
      Dialog.createButton({ label: CREATE_DEPLOYMENT_LABEL }),
      Dialog.okButton({ label: 'Close window' })
    ]
  })
}

export function showLocalDeploymentInformationDialog(deploymentInformation: model.ILocalDeploymentInformation) {
  return showDialog({
    title: `Local deployment information`,
    body: (
      <div>
        <h3 className={style.fieldLabelStyle}>Deployment name</h3>
        <p className={style.fieldTextStyle}>{deploymentInformation.name}</p>
        <h3 className={style.fieldLabelStyle}>Mode</h3>
        <p className={style.fieldTextStyle}>LOCAL</p>
        <h3 className={style.fieldLabelStyle}>Image</h3>
        <p className={style.fieldTextStyle}>{deploymentInformation.image}</p>
        <h3 className={style.fieldLabelStyle}>Port</h3>
        <p className={style.fieldTextStyle}>{deploymentInformation.port}</p>
      </div>
    ),
    buttons: [
      Dialog.createButton({ label: REMOVE_DEPLOYMENT_LABEL, displayType: 'warn' }),
      Dialog.okButton({ label: 'Close window' })
    ]
  })
}