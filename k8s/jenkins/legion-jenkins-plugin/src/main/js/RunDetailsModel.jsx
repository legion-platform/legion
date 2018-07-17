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
import TrainingReport from './components/TrainingReport';
import MetricsDashboard from './components/MetricsDashboard';

const t = require('@jenkins-cd/blueocean-core-js').i18nTranslator('legion-jenkins-plugin');

export class RunDetailsModel extends Component {

    /* eslint-disable no-useless-constructor */
    constructor(props) {
        super(props);
    }

    render() {
        /* eslint-disable react/jsx-closing-bracket-location */
        const result = (
            <div className="model-container">
              <MetricsDashboard
                params={this.props.params}
                pipeline={this.props.pipeline}
                run={this.props.result}
                locale={this.props.locale}
                t={t}
              />
              <TrainingReport
                params={this.props.params}
                pipeline={this.props.pipeline}
                run={this.props.result}
                locale={this.props.locale}
                t={t}
              />
            </div>
        );
        return result;
    }
}

RunDetailsModel.propTypes = {
    params: PropTypes.object,
    pipeline: PropTypes.object,
    result: PropTypes.object,
    locale: PropTypes.string,
};


export default {
    name: 'model',
    title: 'Model', // t('model.tab'),
    component: RunDetailsModel,
};
