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
import UrlConfig from '../config';

export default class TrainingReport extends Component {
    componentDidMount() {
        this.refs.iframeReport.addEventListener('load', this._iframeLoaded.bind(this));
    }

    _iframeLoaded() {
        this.refs.iframeReport.style.height
            = `${this.refs.iframeReport.contentWindow.document.body.scrollHeight}px`;
        this.refs.iframeReport.contentWindow.document.head.insertAdjacentHTML(
            'beforeend',
            '<style type="text/css">#notebook-container {box-shadow: none;}</style>');
    }

    render() {
        /* eslint-disable react/jsx-closing-bracket-location */
        const display = (this.props.run.state === 'FINISHED') ? 'block' : 'none';
        const style = { width: '100%', border: 0, margin: 0, display: `${display}` };

        const url =
            `${UrlConfig.getJenkinsRootURL()}/job/${this.props.pipeline.name}` +
            `/${this.props.run.id}/artifact/${blueocean.legion.reportHtmlPath}`;

        const result = (
            <div>
                <iframe ref="iframeReport" style={style} className="report-iframe"
                  src={url} />
            </div>
        );

        return result;
    }
}

TrainingReport.propTypes = {
    params: PropTypes.object,
    pipeline: PropTypes.object,
    run: PropTypes.object,
    locale: PropTypes.string,
    t: PropTypes.func,
};
