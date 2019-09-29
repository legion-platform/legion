import {
  caretdownImageStyle,
  caretrightImageStyle,
  changeStageButtonStyle,
  sectionAreaStyle,
  sectionHeaderLabelStyle
} from '../../componentsStyle/StageStyle';

import * as React from 'react';
import { ListingView } from './ListingView';
import * as dialog from '../dialogs/cloud';
import { CommandIDs } from '../../commands';
import { ICloudAllEntitiesResponse } from '../../models/cloud';
import { JupyterLab } from '@jupyterlab/application';
import { IApiCloudState } from '../../models';
import { SmallButtonView } from './ButtonView';

export interface ILifecycleStageProps {
  app: JupyterLab;
  dataState: IApiCloudState;
}

export interface ILifecycleStageState {
  showStage: boolean;
  cloudData: ICloudAllEntitiesResponse;
  isLoading: boolean;
}

export class LifecycleStage extends React.Component<
  ILifecycleStageProps,
  ILifecycleStageState
> {
  constructor(props: ILifecycleStageProps) {
    super(props);
    this.state = {
      cloudData: props.dataState,
      isLoading: props.dataState.isLoading,
      showStage: true
    };
  }

  displayStage() {
    this.setState({ showStage: !this.state.showStage });
  }

  render() {
    return (
      <div>
        <div className={sectionAreaStyle}>
          <span className={sectionHeaderLabelStyle}>AI Lifecycle</span>
          <button
            className={
              this.state.showStage
                ? `${changeStageButtonStyle} ${caretdownImageStyle}`
                : `${changeStageButtonStyle} ${caretrightImageStyle}`
            }
            onClick={() => this.displayStage()}
          />
        </div>
        {this.state.showStage && (
          <div>
            <ListingView
              title={'Training'}
              topButton={null}
              columns={[
                {
                  name: 'ID',
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
                      value: training.id
                    },
                    {
                      value:
                        training.status == null ? '' : training.status.state
                    }
                  ],
                  onClick: () =>
                    dialog
                      .showCloudTrainInformationDialog(
                        training,
                        this.props.dataState.configuration.training.metricUrl
                      )
                      .then(({ button }) => {
                        if (button.label === dialog.REMOVE_TRAINING_LABEL) {
                          this.props.app.commands.execute(
                            CommandIDs.removeCloudTraining,
                            {
                              name: training.id
                            }
                          );
                        } else if (button.label === dialog.LOGS_LABEL) {
                          this.props.app.commands.execute(
                            CommandIDs.openTrainingLogs,
                            {
                              name: training.id
                            }
                          );
                        }
                      })
                };
              })}
            />
            <ListingView
              title={'Packaging'}
              topButton={null}
              columns={[
                {
                  name: 'ID',
                  flex: {
                    flexGrow: 2,
                    flexBasis: 40
                  }
                },
                {
                  name: 'Integration name',
                  flex: {
                    flexGrow: 1,
                    flexBasis: 40
                  }
                },
                {
                  name: 'Status',
                  flex: {
                    flexGrow: 2,
                    flexBasis: 40
                  }
                }
              ]}
              isLoading={this.state.isLoading}
              items={this.state.cloudData.modelPackagings.map(mp => {
                return {
                  items: [
                    {
                      value: mp.id
                    },
                    {
                      value: mp.spec.integrationName
                    },
                    {
                      value: mp.status.state
                    }
                  ],
                  onClick: () =>
                    dialog.showModelPackagingDialog(mp).then(({ button }) => {
                      if (button.label === dialog.REMOVE_MODEL_PACKING_LABEL) {
                        this.props.app.commands.execute(
                          CommandIDs.removeModelPackaging,
                          {
                            name: mp.id
                          }
                        );
                      } else if (button.label === dialog.LOGS_LABEL) {
                        this.props.app.commands.execute(
                          CommandIDs.openPackagingLogs,
                          {
                            name: mp.id
                          }
                        );
                      }
                    })
                };
              })}
            />
            <ListingView
              title={'Deployment'}
              topButton={
                <SmallButtonView
                  text={'New deployment'}
                  iconClass={'jp-AddIcon'}
                  onClick={() =>
                    this.props.app.commands.execute(
                      CommandIDs.newCloudDeployment
                    )
                  }
                />
              }
              columns={[
                {
                  name: 'ID',
                  flex: {
                    flexGrow: 3,
                    flexBasis: 60
                  }
                },
                {
                  name: 'Replicas',
                  flex: {
                    flexGrow: 3,
                    flexBasis: 20
                  }
                },
                {
                  name: 'Status',
                  flex: {
                    flexGrow: 3,
                    flexBasis: 60
                  }
                }
              ]}
              isLoading={this.state.isLoading}
              items={this.state.cloudData.deployments.map(deployment => {
                let replicas = 0;
                if (deployment.status.availableReplicas) {
                  replicas = deployment.status.availableReplicas;
                }

                return {
                  items: [
                    {
                      value: deployment.id
                    },
                    {
                      value: replicas.toString()
                    },
                    {
                      value: deployment.status.state
                    }
                  ],
                  onClick: () =>
                    dialog
                      .showCloudDeploymentInformationDialog(deployment)
                      .then(({ button }) => {
                        if (button.label === dialog.REMOVE_DEPLOYMENT_LABEL) {
                          this.props.app.commands.execute(
                            CommandIDs.removeCloudDeployment,
                            { name: deployment.id }
                          );
                        }
                      })
                };
              })}
            />
          </div>
        )}
      </div>
    );
  }
}
