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

import * as style from '../../componentsStyle/ClusterInfoStyle';

/** Interface for ClusterInfoView component state */
export interface IClusterInfoViewNodeState {}

/** Interface for ClusterInfoView component props */
export interface IClusterInfoViewNodeProps {
  ediUrl: string;
  metricUiUrl: string;
  serviceCatalogUrl: string;
  grafanaUrl: string;
}

export class ClusterInfoView extends React.Component<
  IClusterInfoViewNodeProps,
  IClusterInfoViewNodeState
> {
  constructor(props: IClusterInfoViewNodeProps) {
    super(props);
  }

  render() {
    return (
      <div className={style.infoHolder}>
        <ul>
          <li className={style.infoPairLine}>
            <a
              className={style.infoPairTitle}
              href={this.props.ediUrl}
              target="_blank"
            >
              EDI service
            </a>
          </li>

          <li className={style.infoPairLine}>
            <a
              className={style.infoPairTitle}
              href={this.props.metricUiUrl}
              target="_blank"
            >
              Metric UI
            </a>
          </li>

          <li className={style.infoPairLine}>
            <a
              className={style.infoPairTitle}
              href={this.props.serviceCatalogUrl}
              target="_blank"
            >
              Service catalog
            </a>
          </li>
          <li className={style.infoPairLine}>
            <a
              className={style.infoPairTitle}
              href={this.props.grafanaUrl}
              target="_blank"
            >
              Grafana
            </a>
          </li>
        </ul>
      </div>
    );
  }
}
