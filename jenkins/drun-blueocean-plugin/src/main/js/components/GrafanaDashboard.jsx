/**
 *   Copyright 2017 EPAM Systems
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
import React, { Component, PropTypes } from 'react';
import { blueocean } from '@jenkins-cd/blueocean-core-js/dist/js/scopes';
import { Fetch, FetchFunctions } from '@jenkins-cd/blueocean-core-js';
import UrlConfig from '../config';

export default class GrafanaDashboard extends Component {

    constructor(props) {
        super(props);
        this.params = props.params;
        this.pipeline = props.pipeline;
        this.run = props.run;
        this.runId = props.runId;
        this.t = props.t;
        this.iframeHeight = 0;
        this.intervalId = null;
        this.counter = 0;
    }

    componentDidMount() {
        this.refs.iframe2.addEventListener('load', this._iframeLoaded.bind(this));
    }

    _iframeSizeCheck() {
        const currentHeight = this.refs.iframe2.contentWindow.document.body.scrollHeight;
        this.counter++;

        if (currentHeight > this.iframeHeight || this.counter >= 10) {
            clearInterval(this.intervalId);
            this.refs.iframe2.style.height = `${currentHeight}px`;
        }
    }

    _iframeLoaded() {
        this.iframeHeight = this.refs.iframe2.contentWindow.document.body.scrollHeight;
        this.intervalId = setInterval(this._iframeSizeCheck.bind(this), 1000);
    }

    render() {
        const modelUrl =
            `${UrlConfig.getJenkinsRootURL()}/job/${this.pipeline.name}` +
            `/${this.runId}/model/json`;

        Fetch.fetchJSON(encodeURI(modelUrl))
            .then(json => {
                const url = `${blueocean.drun.dashboardUrl}${json.modelName}`;

                this.refs.iframe2.src = url;
            }).catch(FetchFunctions.consoleError);

        /* eslint-disable react/jsx-closing-bracket-location */
        return (
            <div className="drun-dashboard">
                <iframe ref="iframe2" id="grafana-iframe" className="grafana-iframe" />
            </div>
        );
    }
}

GrafanaDashboard.propTypes = {
    params: PropTypes.object,
    pipeline: PropTypes.object,
    run: PropTypes.object,
    runId: PropTypes.number,
    t: PropTypes.func,
};
