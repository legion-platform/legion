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

import { JupyterLab } from '@jupyterlab/application';
import { showErrorMessage } from '@jupyterlab/apputils';

import { TitleBarView } from './partials/TitleBarView';
import { ListingView } from './partials/ListingView';
import { SmallButtonView, ButtonView } from './partials/ButtonView';

import * as style from '../componentsStyle/GeneralWidgetStyle';
import * as dialog from '../components/dialogs/cloud';
import { CommandIDs } from '../commands';
import { IApiCloudState } from '../models';
import { ICloudAllEntitiesResponse } from '../models/cloud';
import { ClusterInfoView } from './partials/ClusterInfoView';

/** Interface for GitPanel component state */
export interface ICloudWidgetViewNodeState {
  cloudData: ICloudAllEntitiesResponse;
  isLoading: boolean;
  authorizationRequired: boolean;
}

/** Interface for GitPanel component props */
export interface ICloudWidgetViewNodeProps {
  app: JupyterLab;
  dataState: IApiCloudState;
}

/** A React component for the git extension's main display */
export class CloudWidgetView extends React.Component<
  ICloudWidgetViewNodeProps,
  ICloudWidgetViewNodeState
> {
  constructor(props: ICloudWidgetViewNodeProps) {
    super(props);
    this.state = {
      cloudData: props.dataState,
      isLoading: props.dataState.isLoading,
      authorizationRequired: props.dataState.authorizationRequired
    };
  }

  /**
   * Refresh widget, update all content
   */
  refresh = async () => {
    try {
      this.setState({
        cloudData: this.props.dataState,
        isLoading: this.props.dataState.isLoading,
        authorizationRequired: this.props.dataState.authorizationRequired
      });
    } catch (err) {
      showErrorMessage('Can not update cloud widget', err);
    }
  };

  onActivate() {
    if (!this.props.dataState.authorizationRequired) {
      this.props.app.commands.execute(CommandIDs.refreshCloud);
    }
  }

  renderAuthView() {
    return (
      <div className={style.widgetPane}>
        <TitleBarView text={'Legion cloud mode'} onRefresh={null} />
        <div className={style.authSubPane}>
          <div className={style.authIcon}>&nbsp;</div>
          <h2 className={style.authDisclaimerText}>
            Please, authorize on a cluster
          </h2>
          <ButtonView
            text={'Login'}
            style={'jp-mod-accept'}
            onClick={() =>
              this.props.app.commands.execute(CommandIDs.authorizeOnCluster)
            }
          />
        </div>
      </div>
    );
  }

  renderDataView() {
    return (
      <div className={style.widgetPane}>
        <TitleBarView
          text={'Legion cluster mode'}
          onRefresh={() =>
            this.props.app.commands.execute(CommandIDs.refreshCloud)
          }
          isRefreshing={this.state.isLoading}
        />
        <ClusterInfoView
          clusterName={
            this.props.dataState.credentials
              ? this.props.dataState.credentials.cluster
              : 'Internal Cluster'
          }
        />
        <ListingView
          title={'Cloud trainings'}
          topButton={null}
          columns={[
            {
              name: 'Training',
              flex: {
                flexGrow: 1,
                flexBasis: 200
              }
            },
            {
              name: 'Status',
              flex: {
                flexGrow: 0,
                flexBasis: 120
              }
            }
          ]}
          isLoading={this.state.isLoading}
          items={this.state.cloudData.trainings.map(training => {
            return {
              items: [
                {
                  value: training.name
                },
                {
                  value: training.status.state
                }
              ],
              onClick: () =>
                dialog
                  .showCloudTrainInformationDialog(training)
                  .then(({ button }) => {
                    if (button.label === dialog.CREATE_DEPLOYMENT_LABEL) {
                      this.props.app.commands.execute(
                        CommandIDs.newCloudDeployment,
                        {
                          image: training.status.modelImage
                        }
                      );
                    } else if (button.label === dialog.REMOVE_TRAINING_LABEL) {
                      this.props.app.commands.execute(
                        CommandIDs.removeCloudTraining,
                        {
                          name: training.name
                        }
                      );
                    } else if (button.label === dialog.LOGS_LABEL) {
                      this.props.app.commands.execute(
                        CommandIDs.openTrainingLogs,
                        {
                          name: training.name
                        }
                      );
                    }
                  })
            };
          })}
        />
        <ListingView
          title={'Cloud deployments'}
          topButton={
            <SmallButtonView
              text={'New deployment'}
              iconClass={'jp-AddIcon'}
              onClick={() =>
                this.props.app.commands.execute(CommandIDs.newCloudDeployment)
              }
            />
          }
          columns={[
            {
              name: 'Deployment',
              flex: {
                flexGrow: 3,
                flexBasis: 70
              }
            },
            {
              name: 'Replicas',
              flex: {
                flexGrow: 0,
                flexBasis: 70
              }
            },
            {
              name: 'Image',
              flex: {
                flexGrow: 5,
                flexBasis: 70
              }
            }
          ]}
          isLoading={this.state.isLoading}
          items={this.state.cloudData.deployments.map(deployment => {
            return {
              items: [
                {
                  value: deployment.name
                },
                {
                  value: '' + deployment.status.availableReplicas
                },
                {
                  value: deployment.spec.image
                }
              ],
              onClick: () =>
                dialog
                  .showCloudDeploymentInformationDialog(deployment)
                  .then(({ button }) => {
                    if (button.label === dialog.REMOVE_DEPLOYMENT_LABEL) {
                      this.props.app.commands.execute(
                        CommandIDs.removeCloudDeployment,
                        { name: deployment.name }
                      );
                    }
                  })
            };
          })}
        />
      </div>
    );
  }

  render() {
    if (this.state.authorizationRequired) {
      return this.renderAuthView();
    } else {
      return this.renderDataView();
    }
  }
}
