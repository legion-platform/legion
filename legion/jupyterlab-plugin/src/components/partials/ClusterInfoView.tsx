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
  clusterName: string;
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
        <p className={style.infoTitle}>Cluster information</p>

        <p className={style.infoPairLine}><span className={style.infoPairTitle}>Cluster:</span><a href={this.props.clusterName} target='_blank'>{this.props.clusterName}</a></p>
      </div>
    );
  }
}