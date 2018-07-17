/**
 *   Copyright 2018 EPAM Systems
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

export default class MetricsDashboard extends Component {

    constructor(props) {
        super(props);
        this.iframeHeight = 0;
        this.intervalId = null;
        this.counter = 0;
    }

    componentDidMount() {
        this.refs.iframeMetrics.addEventListener('load', this._iframeLoaded.bind(this));
    }

    _iframeSizeCheck() {
        if (this.refs.iframeMetrics) {
            const currHeight = this.refs.iframeMetrics.contentWindow.document.body.scrollHeight;
            this.counter++;

            if (currHeight > this.iframeHeight || this.counter >= 10) {
                clearInterval(this.intervalId);
                this.refs.iframeMetrics.style.height = `${currHeight + 20}px`;
            }
        }
    }

    _iframeLoaded() {
        this.iframeHeight = this.refs.iframeMetrics.contentWindow.document.body.scrollHeight;
        this.intervalId = setInterval(this._iframeSizeCheck.bind(this), 1000);
    }

    render() {
        // Request parameter json and get model id
        const modelUrl =
            `${UrlConfig.getJenkinsRootURL()}/job/${this.props.pipeline.name}` +
            `/${this.props.run.id}/model/json`;

        Fetch.fetchJSON(encodeURI(modelUrl))
            .then(json => {
                const url = `${blueocean.legion.dashboardUrl}${json.modelId}`;

                this.refs.iframeMetrics.src = url;
            }).catch(FetchFunctions.consoleError);

        const style = { width: '100%', border: 0, margin: 0 };

        /* eslint-disable react/jsx-closing-bracket-location */
        return (
            <div>
              <iframe ref="iframeMetrics" style={style} className="metrics-iframe" />
            </div>
        );
    }
}

MetricsDashboard.propTypes = {
    params: PropTypes.object,
    pipeline: PropTypes.object,
    run: PropTypes.object,
    locale: PropTypes.string,
    t: PropTypes.func,
};
