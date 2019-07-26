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
import * as style from '../../componentsStyle/ButtonStyle';

/** Interface for ButtonView component state */
export interface IButtonViewNodeState {}

/** Interface for ButtonView component props */
export interface IButtonViewNodeProps {
  text: string;
  onClick: () => void;
  disabled?: boolean;
  cursor?: string;
}

export interface IButtonViewWithIconNodeProps extends IButtonViewNodeProps {
  iconClass: string;
}

export interface IButtonViewWithStyleNodeProps extends IButtonViewNodeProps {
  style: string;
}

export class ButtonView extends React.Component<
  IButtonViewWithStyleNodeProps,
  IButtonViewNodeState
> {
  constructor(props: IButtonViewWithStyleNodeProps) {
    super(props);
  }

  getStyle() {
    let finalStyle =
      'jp-Dialog-button ' +
      this.props.style +
      ' jp-mod-styled ' +
      style.normalButtonStyle;
    if (this.props.disabled) {
      finalStyle += ' ' + style.buttonDisabled;
    }
    return finalStyle;
  }

  render() {
    return (
      <button
        className={this.getStyle()}
        onClick={e => (this.props.disabled ? null : this.props.onClick())}
      >
        <div className={'jp-Dialog-buttonIcon'} />
        <div className={'jp-Dialog-buttonLabel'}>{this.props.text}</div>
      </button>
    );
  }
}

export class SmallButtonView extends React.Component<
  IButtonViewWithIconNodeProps,
  IButtonViewNodeState
> {
  constructor(props: IButtonViewWithIconNodeProps) {
    super(props);
  }

  getStyle() {
    let finalStyle = style.smallButtonStyle;
    if (this.props.disabled) {
      finalStyle += ' ' + style.buttonDisabled;
    }
    return finalStyle;
  }

  render() {
    return (
      <button
        className={this.getStyle()}
        onClick={e => (this.props.disabled ? null : this.props.onClick())}
        style={{
          cursor:
            this.props.cursor !== undefined ? this.props.cursor : 'pointer'
        }}
        title={this.props.text}
      >
        <span
          className={
            '' +
            this.props.iconClass +
            ' jp-Icon jp-Icon-16 ' +
            style.smallButtonStyleImage
          }
        />
      </button>
    );
  }
}
