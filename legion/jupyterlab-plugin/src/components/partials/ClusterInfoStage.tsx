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
import { Configuration } from '../../legion/Configuration';

export interface IClusterInfoStageProps {
  configuration: Configuration;
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
    let externalLinks = [];
    if (this.props.configuration != null) {
      for (let link of this.props.configuration.common.externalUrls) {
        externalLinks.push(
          <li className={infoPairLine}>
            <a className={infoPairTitle} href={link.url} target="_blank">
              {link.name}
            </a>
          </li>
        );
      }
    }

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
            <ul className={infoList}>{externalLinks}</ul>
          </div>
        )}
      </div>
    );
  }
}
