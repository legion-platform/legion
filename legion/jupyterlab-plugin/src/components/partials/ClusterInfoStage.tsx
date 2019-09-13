import {
  caretdownImageStyle,
  caretrightImageStyle,
  changeStageButtonStyle,
  sectionAreaStyle,
  sectionHeaderLabelStyle
} from '../../componentsStyle/StageStyle';

import * as React from 'react';
import {
  infoHolder,
  infoList,
  infoPairLine,
  infoPairTitle
} from '../../componentsStyle/ClusterInfoStyle';

export interface IClusterInfoStageProps {
  ediUrl: string;
  metricUiUrl: string;
  serviceCatalogUrl: string;
  grafanaUrl: string;
}

export interface IClusterInfoStageState {
  showStage: boolean;
}

export class ClusterInfoStage extends React.Component<
  IClusterInfoStageProps,
  IClusterInfoStageState
> {
  constructor(props: IClusterInfoStageProps) {
    super(props);

    this.state = {
      showStage: false
    };
  }

  displayStage() {
    this.setState({ showStage: !this.state.showStage });
  }

  render() {
    return (
      <div>
        <div className={sectionAreaStyle}>
          <span className={sectionHeaderLabelStyle}>Components</span>
          <button
            className={
              this.state.showStage
                ? `${changeStageButtonStyle} ${caretdownImageStyle}`
                : `${changeStageButtonStyle} ${caretrightImageStyle}`
            }
            onClick={() => this.displayStage()}
          />
        </div>
        {this.state.showStage && (
          <div className={infoHolder}>
            <ul className={infoList}>
              <li className={infoPairLine}>
                <a
                  className={infoPairTitle}
                  href={this.props.ediUrl}
                  target="_blank"
                >
                  API's Gateway
                </a>
              </li>

              <li className={infoPairLine}>
                <a
                  className={infoPairTitle}
                  href={this.props.metricUiUrl}
                  target="_blank"
                >
                  ML Metrics
                </a>
              </li>

              <li className={infoPairLine}>
                <a
                  className={infoPairTitle}
                  href={this.props.serviceCatalogUrl}
                  target="_blank"
                >
                  Service Catalog
                </a>
              </li>
              <li className={infoPairLine}>
                <a
                  className={infoPairTitle}
                  href={this.props.grafanaUrl}
                  target="_blank"
                >
                  Cluster Monitoring
                </a>
              </li>
            </ul>
          </div>
        )}
      </div>
    );
  }
}
