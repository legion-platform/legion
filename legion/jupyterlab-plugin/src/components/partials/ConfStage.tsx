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

export interface IConfStageProps {
  app: JupyterLab;
  dataState: IApiCloudState;
}

export interface IConfStageState {
  showStage: boolean;
  cloudData: ICloudAllEntitiesResponse;
  isLoading: boolean;
}

export class ConfStage extends React.Component<
  IConfStageProps,
  IConfStageState
> {
  constructor(props: IConfStageProps) {
    super(props);
    this.state = {
      cloudData: props.dataState,
      isLoading: props.dataState.isLoading,
      showStage: false
    };
  }

  displayStage() {
    this.setState({ showStage: !this.state.showStage });
  }

  render() {
    return (
      <div>
        <div className={sectionAreaStyle}>
          <span className={sectionHeaderLabelStyle}>Configuration</span>
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
              title={'Connection'}
              topButton={null}
              columns={[
                {
                  name: 'ID',
                  flex: {
                    flexGrow: 1,
                    flexBasis: 80
                  }
                },
                {
                  name: 'Type',
                  flex: {
                    flexGrow: 0,
                    flexBasis: 40
                  }
                },
                {
                  name: 'URI',
                  flex: {
                    flexGrow: 3,
                    flexBasis: 100
                  }
                }
              ]}
              isLoading={this.state.isLoading}
              items={this.state.cloudData.connections.map(conn => {
                return {
                  items: [
                    {
                      value: conn.id
                    },
                    {
                      value: conn.spec.type
                    },
                    {
                      value: conn.spec.uri
                    }
                  ],
                  onClick: () =>
                    dialog
                      .showConnectionInformationDialog(conn)
                      .then(({ button }) => {
                        if (button.label === dialog.REMOVE_CONNECTION_LABEL) {
                          this.props.app.commands.execute(
                            CommandIDs.removeConnection,
                            {
                              name: conn.id
                            }
                          );
                        }
                      })
                };
              })}
            />
            <ListingView
              title={'Toolchain'}
              topButton={null}
              columns={[
                {
                  name: 'ID',
                  flex: {
                    flexGrow: 1,
                    flexBasis: 40
                  }
                },
                {
                  name: 'Image',
                  flex: {
                    flexGrow: 2,
                    flexBasis: 40
                  }
                }
              ]}
              isLoading={this.state.isLoading}
              items={this.state.cloudData.toolchainIntegrations.map(ti => {
                return {
                  items: [
                    {
                      value: ti.id
                    },
                    {
                      value: ti.spec.defaultImage
                    }
                  ],
                  onClick: () =>
                    dialog
                      .showToolchainIntegrationDialog(ti)
                      .then(({ button }) => {})
                };
              })}
            />
            <ListingView
              title={'Packager'}
              topButton={null}
              columns={[
                {
                  name: 'ID',
                  flex: {
                    flexGrow: 1,
                    flexBasis: 40
                  }
                },
                {
                  name: 'Image',
                  flex: {
                    flexGrow: 2,
                    flexBasis: 40
                  }
                }
              ]}
              isLoading={this.state.isLoading}
              items={this.state.cloudData.packagingIntegrations.map(pi => {
                return {
                  items: [
                    {
                      value: pi.id
                    },
                    {
                      value: pi.spec.defaultImage
                    }
                  ],
                  onClick: () =>
                    dialog
                      .showPackagingIntegrationDialog(pi)
                      .then(({ button }) => {})
                };
              })}
            />
          </div>
        )}
      </div>
    );
  }
}
