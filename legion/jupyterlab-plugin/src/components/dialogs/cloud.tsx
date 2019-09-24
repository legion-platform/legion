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
import { Widget } from '@phosphor/widgets';

import * as style from '../../componentsStyle/dialogs';
import * as model from '../../models/cloud';
import * as base from './base';
import { ModelTraining } from '../../legion/ModelTraining';
import { ModelDeployment } from '../../legion/ModelDeployment';
import { Connection } from '../../legion/Connection';
import { ModelPackaging } from '../../legion/ModelPackaging';
import { ToolchainIntegration } from '../../legion/ToolchainIntegration';
import { PackagingIntegration } from '../../legion/PackagingIntegration';

export const REMOVE_DEPLOYMENT_LABEL = 'Remove';
export const REMOVE_TRAINING_LABEL = 'Remove';
export const REMOVE_CONNECTION_LABEL = 'Remove';
export const REMOVE_MODEL_PACKING_LABEL = 'Remove';
export const LOGS_LABEL = 'Logs';

export function showConnectionInformationDialog(conn: Connection) {
  let description = conn.spec.description ? (
    <div>
      <h3 className={style.fieldLabelStyle}>Description</h3>
      <p className={style.fieldTextStyle}>{conn.spec.description}</p>
    </div>
  ) : (
    <div />
  );

  let webUILink = conn.spec.webUILink ? (
    <div>
      <h3 className={style.fieldLabelStyle}>WEB UI Link</h3>
      <a href={conn.spec.webUILink} target="_blank">
        {conn.spec.webUILink}
      </a>
    </div>
  ) : (
    <div />
  );

  return showDialog({
    title: `Cloud training information`,
    body: (
      <div>
        <h3 className={style.fieldLabelStyle}>ID</h3>
        <p className={style.fieldTextStyle}>{conn.id}</p>
        <h3 className={style.fieldLabelStyle}>Type</h3>
        <p className={style.fieldTextStyle}>{conn.spec.type}</p>
        <h3 className={style.fieldLabelStyle}>URI</h3>
        <p className={style.fieldTextStyle}>{conn.spec.uri}</p>
        {webUILink}
        {description}
      </div>
    ),
    buttons: [
      Dialog.warnButton({ label: REMOVE_CONNECTION_LABEL }),
      Dialog.cancelButton({ label: 'Close window' })
    ]
  });
}

export function showModelPackagingDialog(mp: ModelPackaging) {
  let result = [];
  if (mp.status.results != null) {
    for (let res of mp.status.results) {
      result.push(
        <li>
          <p className={style.fieldTextStyle}>
            {res.name}: {res.value}
          </p>
        </li>
      );
    }
  }

  let targets = [];
  if (mp.spec.targets != null) {
    for (let target of mp.spec.targets) {
      targets.push(
        <li>
          <p className={style.fieldTextStyle}>
            {target.name}: {target.connectionName}
          </p>
        </li>
      );
    }
  }

  return showDialog({
    title: `Model Packaging information`,
    body: (
      <div>
        <h3 className={style.fieldLabelStyle}>ID</h3>
        <p className={style.fieldTextStyle}>{mp.id}</p>
        <h3 className={style.fieldLabelStyle}>Artifact name</h3>
        <p className={style.fieldTextStyle}>{mp.spec.artifactName}</p>
        <h3 className={style.fieldLabelStyle}>Type</h3>
        <p className={style.fieldTextStyle}>{mp.spec.integrationName}</p>
        <h3 className={style.fieldLabelStyle}>Targets</h3>
        <ul className={style.fieldTextStyle}>{targets}</ul>
        <h3 className={style.fieldLabelStyle}>State</h3>
        <p className={style.fieldTextStyle}>{mp.status.state}</p>

        {result.length > 0 && (
          <div>
            <h3 className={style.fieldLabelStyle}>Results</h3>
            <ul className={style.fieldTextStyle}>{result}</ul>
          </div>
        )}
        {mp.status.message != null && mp.status.message !== '' && (
          <div>
            <h3 className={style.fieldLabelStyle}>Message state</h3>
            <p className={style.fieldTextStyle}>{mp.status.message}</p>
          </div>
        )}
      </div>
    ),
    buttons: [
      Dialog.okButton({ label: LOGS_LABEL }),
      Dialog.warnButton({ label: REMOVE_MODEL_PACKING_LABEL }),
      Dialog.cancelButton({ label: 'Close window' })
    ]
  });
}

export function showPackagingIntegrationDialog(pi: PackagingIntegration) {
  return showDialog({
    title: `Packaging Integration information`,
    body: (
      <div>
        <h3 className={style.fieldLabelStyle}>ID</h3>
        <p className={style.fieldTextStyle}>{pi.id}</p>
        <h3 className={style.fieldLabelStyle}>Image</h3>
        <p className={style.fieldTextStyle}>{pi.spec.defaultImage}</p>
      </div>
    ),
    buttons: [Dialog.cancelButton({ label: 'Close window' })]
  });
}

export function showToolchainIntegrationDialog(ti: ToolchainIntegration) {
  return showDialog({
    title: `Toolchain Integration information`,
    body: (
      <div>
        <h3 className={style.fieldLabelStyle}>ID</h3>
        <p className={style.fieldTextStyle}>{ti.id}</p>
        <h3 className={style.fieldLabelStyle}>Image</h3>
        <p className={style.fieldTextStyle}>{ti.spec.defaultImage}</p>
        <h3 className={style.fieldLabelStyle}>ID</h3>
        <p className={style.fieldTextStyle}>{ti.id}</p>
      </div>
    ),
    buttons: [Dialog.cancelButton({ label: 'Close window' })]
  });
}

export function showCloudTrainInformationDialog(
  training: ModelTraining,
  metricUiUrl: string
) {
  let result = [];
  if (training.status.artifacts != null) {
    for (let elem of training.status.artifacts) {
      let url = `${metricUiUrl}#/experiments/0/runs/${elem.runId}`;
      result.push(
        <li>
          <p className={style.fieldTextStyle}>
            Artifact Name: {elem.artifactName}
          </p>
          <p className={style.fieldTextStyle}>Commit ID: {elem.commitID}</p>
          <p className={style.fieldTextStyle}>
            Run ID:{' '}
            <a href={url} target="_blank">
              {elem.runId}
            </a>
          </p>
        </li>
      );
    }
  }
  return showDialog({
    title: `Cloud training information`,
    body: (
      <div>
        <h3 className={style.fieldLabelStyle}>Name</h3>
        <p className={style.fieldTextStyle}>{training.id}</p>
        <h3 className={style.fieldLabelStyle}>State</h3>
        <p className={style.fieldTextStyle}>{training.status.state}</p>

        <React.Fragment>
          <h3 className={style.fieldLabelStyle}>Toolchain</h3>
          <p className={style.fieldTextStyle}>{training.spec.toolchain}</p>
        </React.Fragment>

        <h3 className={style.fieldLabelStyle}>Model (name / version)</h3>
        <p className={style.fieldTextStyle}>
          {training.spec.model.name} / {training.spec.model.version}
        </p>

        <h3 className={style.fieldLabelStyle}>VCS</h3>
        <p className={style.fieldTextStyle}>
          {training.spec.vcsName}:{training.spec.reference}
        </p>
        <h3 className={style.fieldLabelStyle}>File (working directory)</h3>
        <p className={style.fieldTextStyle}>
          {training.spec.entrypoint}{' '}
          {training.spec.workDir != null ? `(${training.spec.workDir})` : ''}
        </p>
        {result.length > 0 && (
          <div>
            <h3 className={style.fieldLabelStyle}>Results</h3>
            <ul className={style.fieldTextStyle}>{result}</ul>
          </div>
        )}

        {training.status.message != null && training.status.message !== '' && (
          <div>
            <h3 className={style.fieldLabelStyle}>Message state</h3>
            <p className={style.fieldTextStyle}>{training.status.message}</p>
          </div>
        )}
      </div>
    ),
    buttons: [
      Dialog.okButton({ label: LOGS_LABEL }),
      Dialog.warnButton({ label: REMOVE_TRAINING_LABEL }),
      Dialog.cancelButton({ label: 'Close window' })
    ]
  });
}

export function showCloudDeploymentInformationDialog(
  deploymentInformation: ModelDeployment
) {
  return showDialog({
    title: `Cloud deployment information`,
    body: (
      <div>
        <h3 className={style.fieldLabelStyle}>Deployment name</h3>
        <p className={style.fieldTextStyle}>{deploymentInformation.id}</p>
        <h3 className={style.fieldLabelStyle}>Deployment role</h3>
        <p className={style.fieldTextStyle}>
          {deploymentInformation.spec.roleName}
        </p>
        <h3 className={style.fieldLabelStyle}>Mode</h3>
        <p className={style.fieldTextStyle}>CLUSTER</p>
        <h3 className={style.fieldLabelStyle}>Image</h3>
        <p className={style.fieldTextStyle}>
          {deploymentInformation.spec.image}
        </p>
        <h3 className={style.fieldLabelStyle}>Replicas (actual)</h3>
        <p className={style.fieldTextStyle}>
          {deploymentInformation.status.availableReplicas}
        </p>
        <h3 className={style.fieldLabelStyle}>Probes (initial / readiness)</h3>
        <p className={style.fieldTextStyle}>
          {deploymentInformation.spec.livenessProbeInitialDelay} sec. /{' '}
          {deploymentInformation.spec.readinessProbeInitialDelay} sec.
        </p>
      </div>
    ),
    buttons: [
      Dialog.createButton({
        label: REMOVE_DEPLOYMENT_LABEL,
        displayType: 'warn'
      }),
      Dialog.okButton({ label: 'Close window' })
    ]
  });
}

export function showApplyResultsDialog(result: model.IApplyFromFileResponse) {
  return showDialog({
    title: result.errors.length === 0 ? 'Successful' : 'Errors',
    body: (
      <div>
        {result.created.length > 0 ? (
          <React.Fragment>
            <h3 className={style.fieldLabelStyle}>Resources created</h3>
            <p className={style.fieldTextStyle}>
              {result.created.length} ({result.created.join(', ')})
            </p>
          </React.Fragment>
        ) : null}

        {result.changed.length > 0 ? (
          <React.Fragment>
            <h3 className={style.fieldLabelStyle}>Resources changed</h3>
            <p className={style.fieldTextStyle}>
              {result.changed.length} ({result.changed.join(', ')})
            </p>
          </React.Fragment>
        ) : null}

        {result.removed.length > 0 ? (
          <React.Fragment>
            <h3 className={style.fieldLabelStyle}>Resources removed</h3>
            <p className={style.fieldTextStyle}>
              {result.removed.length} ({result.removed.join(', ')})
            </p>
          </React.Fragment>
        ) : null}

        {result.errors.length > 0 ? (
          <React.Fragment>
            <h3 className={style.fieldLabelStyle}>Errors:</h3>
            <ul className={style.ulStyle}>
              {result.errors.map((error, idx) => (
                <li key={idx} className={style.ulItemStyle}>
                  {error}
                </li>
              ))}
            </ul>
          </React.Fragment>
        ) : null}
      </div>
    ),
    buttons: [
      Dialog.okButton({
        label: 'OK',
        displayType: result.errors.length === 0 ? 'default' : 'warn'
      })
    ]
  });
}

export interface ICreateNewDeploymentDialogValues {
  name: string;
}

class CreateNewDeploymentDetailsDialog extends Widget {
  constructor(deploymentImage: string) {
    super({
      node: Private.buildCreateNewDeploymentDetailsDialog(deploymentImage)
    });
  }

  getValue(): ICreateNewDeploymentDialogValues {
    let inputs = this.node.getElementsByTagName('input');
    const nameInput = inputs[0] as HTMLInputElement;

    return {
      name: nameInput.value
    };
  }
}

export function showCreateNewDeploymentDetails(deploymentImage: string) {
  return showDialog({
    title: 'Creation of new deployment',
    body: new CreateNewDeploymentDetailsDialog(deploymentImage),
    buttons: [Dialog.cancelButton(), Dialog.okButton({ label: 'Deploy' })]
  });
}

namespace Private {
  export function buildCreateNewDeploymentDetailsDialog(
    deploymentImage: string
  ) {
    let body = base.createDialogBody();
    body.appendChild(
      base.createDescriptionLine(
        `You are going to deploy image ${deploymentImage} on a cluster.`
      )
    );
    body.appendChild(base.createDialogInputLabel('Deployment name'));
    body.appendChild(base.createDialogInput(undefined, 'name of deployment'));
    return body;
  }
}
