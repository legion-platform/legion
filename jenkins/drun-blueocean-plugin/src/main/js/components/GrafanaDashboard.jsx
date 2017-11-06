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
    }

    componentDidMount() {
        this.refs.iframe.addEventListener('load', this._iframeLoaded.bind(this));
        this.refs.iframe.contentWindow.document.addEventListener(
            'resize', this._documentResized.bind(this));
    }

    _iframeLoaded() {
        this.refs.iframe.style.height
            = `${this.refs.iframe.contentWindow.document.body.scrollHeight}px`;
    }

    _documentResized() {
        this.refs.iframe.style.height
            = `${this.refs.iframe.contentWindow.document.body.scrollHeight}px`;
    }

    render() {
        const modelUrl =
            `${UrlConfig.getJenkinsRootURL()}/job/${this.pipeline.name}` +
            `/${this.runId}/model/json`;

        Fetch.fetchJSON(encodeURI(modelUrl))
            .then(json => {
                const url = `${blueocean.drun.dashboardUrl}${json.modelName}`;

                this.refs.iframe.src = url;
            }).catch(FetchFunctions.consoleError);

        /* eslint-disable react/jsx-closing-bracket-location */
        return (
            <div className="drun-dashboard">
                <iframe ref="iframe" id="grafana-iframe"
                  className="grafana-iframe" />
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
