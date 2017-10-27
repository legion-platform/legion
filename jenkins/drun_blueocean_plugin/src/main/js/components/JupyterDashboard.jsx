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
import { UrlConfig } from '@jenkins-cd/blueocean-core-js';

export default class JupyterDashboard extends Component {

    constructor(props) {
        super(props);
        this.params = props.params;
        this.pipeline = props.pipeline;
        this.run = props.run;
        this.runId = props.runId;
        this.t = props.t;
    }

    render() {
        const url =
            `${UrlConfig.getJenkinsRootURL()}/job/${this.pipeline.name}` +
            `/${this.runId}/${blueocean.drun.jupyterHtmlPath}`;

        /* eslint-disable react/jsx-closing-bracket-location */

        // Just render a simple <div> with a class name derived from the
        // status of the run. We then use CSS (via LESS) to style the component.
        // See src/main/less/extensions.less
        return (
            <div className="drun-dashboard">
                <iframe id="jupyter-iframe" className="jupyter-iframe" src={url}>&nbsp;</iframe>
            </div>
        );
    }
}

JupyterDashboard.propTypes = {
    params: PropTypes.object,
    pipeline: PropTypes.object,
    run: PropTypes.object,
    runId: PropTypes.number,
    t: PropTypes.func,
};
