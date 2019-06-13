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

import { BaseLegionWidget, IWidgetOptions } from './Widgets';

import { IApiLocalState } from '../models/apiState';
import { LogView } from './LogView';

const WIDGET_ID = 'legion:local-build:logs';
const WIDGET_TITLE = 'Local build logs';


export class LocalBuildLogsWidget extends BaseLegionWidget {
    private _state: IApiLocalState;

    /**
     * Construct a new running widget.
     */
    constructor(state: IApiLocalState, options: IWidgetOptions) {
        super(options);

        this._state = state;

        // Initialize meta information
        this.id = WIDGET_ID;
        this.title.label = WIDGET_TITLE;
        this.title.closable = true;

        // Initialize DOM
        const element = <LogView dataProvider={this} />;
        this.component = ReactDOM.render(element, this.node);
        this.component.refresh();
    }

    getData(): string {
        return this._state.buildStatus.logs;
    }

    refresh(): void {
        this.component.refresh();
    }

}