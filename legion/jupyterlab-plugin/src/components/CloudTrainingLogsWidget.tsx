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
import * as ReactDOM from 'react-dom';

import { JupyterLab } from '@jupyterlab/application';

import { BaseLegionWidget, IWidgetOptions } from './Widgets';

import * as style from '../componentsStyle/GeneralWidgetStyle';
import { ICloudApi } from '../api/cloud';
import { ICloudLogsResponse } from '../models/cloud';
import { IApiCloudState } from '../models';
import { LogView } from './LogView';

const WIDGET_ID = 'legion:cloud-training:logs:';
const WIDGET_TITLE = 'Logs of :trainingName:';
const WIDGET_UPDATE_TIME = 5000;

export class CloudTrainingLogsWidget extends BaseLegionWidget {
  private _data: ICloudLogsResponse;
  private _api: ICloudApi;
  private _timerId?: number;
  private _state: IApiCloudState;
  private _trainingName: string;
  private _updating: boolean;

  /**
   * Construct a new running widget.
   */
  constructor(
    app: JupyterLab,
    api: ICloudApi,
    trainingName: string,
    state: IApiCloudState,
    options: IWidgetOptions
  ) {
    super(options);

    this._api = api;
    this._state = state;
    this._trainingName = trainingName;
    this._finishUpdating();
    this._data = {
      data: '',
      futureLogsExpected: true
    };

    // Initialize meta information
    this.id = WIDGET_ID + trainingName;
    this.title.label = WIDGET_TITLE.replace(':trainingName:', trainingName);
    this.title.closable = true;

    // Initialize DOM
    const element = <LogView dataProvider={this} />;
    this.component = ReactDOM.render(element, this.node);
    this.component.refresh();
  }

  _clearTimeInterval(): void {
    if (this._timerId !== undefined) {
      console.log('Removing metrics update timer');
      clearInterval(this._timerId);
      this._timerId = undefined;
      this._finishUpdating();
    }
  }

  /**
   * Dispose of the resources used by the widget.
   */
  dispose(): void {
    this._data.futureLogsExpected = true;
    this._clearTimeInterval();
    super.dispose();
  }

  close(): void {
    this._data.futureLogsExpected = true;
    this._clearTimeInterval();
    super.close();
  }

  show(): void {
    super.show();
    // Start update timer
    if (this._timerId === undefined) {
      console.log('Starting cloud log update loop');
      this._timerId = setInterval(_ => this.refreshData(), WIDGET_UPDATE_TIME);
    }
    // Force on show
    this.refreshData();
  }

  getData(): string {
    return this._data.data;
  }

  refreshData() {
    if (!this.isVisible) {
      return;
    }

    if (!this._data.futureLogsExpected) {
      return;
    }

    if (this._updating) {
      return;
    }

    this._startUpdating();
    this._api
      .getTrainingLogs(
        {
          id: this._trainingName
        },
        this._state.credentials
      )
      .then(logs => {
        this._data = logs;
        this.component.refresh();
        this._finishUpdating();
      })
      .catch(err => {
        this._finishUpdating();
        console.error('Can not update training logs', err);
      });
  }

  private _startUpdating() {
    console.log('Update started');
    this._updating = true;
    this.title.iconClass = style.cloudLogWidgetIcon;
  }

  private _finishUpdating() {
    console.log('Update finished');
    this._updating = false;
    this.title.iconClass = 'jp-TextEditorIcon';
  }
}
