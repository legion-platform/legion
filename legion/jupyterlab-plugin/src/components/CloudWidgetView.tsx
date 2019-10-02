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
import { ButtonView } from './partials/ButtonView';

import * as style from '../componentsStyle/GeneralWidgetStyle';
import { CommandIDs } from '../commands';
import { IApiCloudState } from '../models';
import { ICloudAllEntitiesResponse } from '../models/cloud';
import { ClusterInfoStage } from './partials/ClusterInfoStage';
import { ConfStage } from './partials/ConfStage';
import { LifecycleStage } from './partials/LifecycleStage';
import '../../style/scrollbar.css';

const cloudWidgetScrollbarName = 'CloudWidgetScrollbar';
// 60 seconds
const defaultUpdatePeriod = 60000;

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
  private interval?: number;

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
      <div className={`${style.widgetPane} ${cloudWidgetScrollbarName}`}>
        <TitleBarView
          text={'Legion'}
          onRefresh={() =>
            this.props.app.commands.execute(CommandIDs.refreshCloud)
          }
          isRefreshing={this.state.isLoading}
        />

        <ClusterInfoStage configuration={this.props.dataState.configuration} />

        <LifecycleStage app={this.props.app} dataState={this.props.dataState} />

        <ConfStage app={this.props.app} dataState={this.props.dataState} />
      </div>
    );
  }

  componentDidMount() {
    this.interval = setInterval(() => {
      if (!this.props.dataState.authorizationRequired) {
        this.props.app.commands.execute(CommandIDs.refreshCloud);
      }
    }, defaultUpdatePeriod);
  }

  componentWillUnmount() {
    clearInterval(this.interval);
  }

  render() {
    if (this.state.authorizationRequired) {
      return this.renderAuthView();
    } else {
      return this.renderDataView();
    }
  }
}
