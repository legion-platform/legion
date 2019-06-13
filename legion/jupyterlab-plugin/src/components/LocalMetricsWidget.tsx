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
import { ILocalApi } from '../api/local';
import { ILocalMetricsResponse } from '../models/local';

const WIDGET_ID = 'legion:local-metrics';
const WIDGET_TITLE = 'Legion local metrics';
const WIDGET_UPDATE_TIME = 1000;

/** Interface for GitPanel component state */
export interface ILocalMetricsWidgetViewState {
    data: ILocalMetricsResponse;
}

/** Interface for GitPanel component props */
export interface ILocalMetricsWidgetViewProps {
    app: JupyterLab;
    dataProvider: {
        getData: () => ILocalMetricsResponse;
    };
}

/** A React component for the git extension's main display */
export class LocalMetricsWidgetView extends React.Component<
    ILocalMetricsWidgetViewProps,
    ILocalMetricsWidgetViewState
    > {

    constructor(props: ILocalMetricsWidgetViewProps) {
        super(props);
        this.state = {
            data: props.dataProvider.getData()
        };
    }

    refresh = async () => {
        this.setState({
            data: this.props.dataProvider.getData()
        });
    };

    onActivate(){}

    render() {
        if (this.state.data.data.length == 0){
            return (
                <div className={`${style.widgetPane} ${style.localMetricsWidget}`}>
                    <p className={style.localMetricsWidgetNoDataLine}>NO DATA</p>
                </div>
            )
        }
        return (
            <div className={`${style.widgetPane} ${style.localMetricsWidget}`}>
                <table className={style.localMetricsTable} cellPadding={0} cellSpacing={0}>
                    <thead>
                        <tr>
                            {this.state.data.columns.map((name, idx) => (
                                <th key={idx} className={style.localMetricsTableHeadTrTh}>
                                    {name}
                                </th>
                            ) )}
                        </tr>
                    </thead>
                    <tbody>
                        {this.state.data.data.map((row, idx) => (
                            <tr key={idx}>
                                {row.map((item, col) => (
                                    <td key={col} className={style.localMetricsTableBodyTrTd}>
                                        {item}
                                    </td>
                                ))}
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        );
    }
}


export class LocalMetricsWidget extends BaseLegionWidget {
    private _data: ILocalMetricsResponse;
    private _api: ILocalApi;
    private _timerId?: number;

    /**
     * Construct a new running widget.
     */
    constructor(app: JupyterLab, api: ILocalApi, options: IWidgetOptions) {
        super(options);

        this._api = api;
        this._data = {
            columns: [],
            index: [],
            data: []
        }

        // Initialize meta information
        this.id = WIDGET_ID;
        this.title.label = WIDGET_TITLE;
        this.title.closable = true;

        // Initialize DOM
        const element = <LocalMetricsWidgetView app={app} dataProvider={this} />;
        this.component = ReactDOM.render(element, this.node);
        this.component.refresh();
    }

    _clearTimeInterval(): void {
        if (this._timerId !== undefined) {
            console.log('Removing metrics update timer');
            clearInterval(this._timerId);
            this._timerId = undefined;
        }
    }

    /**
     * Dispose of the resources used by the widget.
     */
    dispose(): void {
        this._clearTimeInterval();
        super.dispose();
    }

    close(): void {
        this._clearTimeInterval();
        super.close();
    }

    show(): void {
        super.show();
        // Start update timer
        if (this._timerId === undefined) {
            console.log('Starting local metrics update loop');
            this._timerId = setInterval(_ => this.refreshData(), WIDGET_UPDATE_TIME);
        }
    }

    getData(): ILocalMetricsResponse {
        return this._data;
    }

    refreshData() {
        if (!this.isVisible)
            return;

        this._api.getLocalMetrics().then(metrics => {
            this._data = metrics;
            this.component.refresh();
            console.log('Updated', metrics);
        }).catch(err => {
            console.error('Can not update metrics', err);
        })
    }
}