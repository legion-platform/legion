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
import * as style from '../componentsStyle/GeneralWidgetStyle';

/** Interface for LogView component state */
export interface ILogViewState {
  data: string;
  scrollOnEnd: boolean;
}

/** Interface for LogView component props */
export interface ILogViewProps {
  dataProvider: {
    getData: () => string;
  };
}

/** A React component for the git extension's main display */
export class LogView extends React.Component<ILogViewProps, ILogViewState> {
  private _scrollableAreaRef: React.RefObject<HTMLDivElement>;

  constructor(props: ILogViewProps) {
    super(props);
    this.state = {
      data: props.dataProvider.getData(),
      scrollOnEnd: true
    };
    this._scrollableAreaRef = React.createRef();
  }

  refresh = async () => {
    this.setState({
      data: this.props.dataProvider.getData()
    });
  };

  onActivate() {}

  scrollHandler(event) {
    const percent =
      (event.target.scrollTop /
        (event.target.scrollHeight - event.target.clientHeight)) *
      100;
    if (percent > 99.9 && !this.state.scrollOnEnd) {
      this.setState({
        scrollOnEnd: true
      });
    } else if (percent < 99.9 && this.state.scrollOnEnd) {
      this.setState({
        scrollOnEnd: false
      });
    }
  }

  componentDidUpdate(prevProps: ILogViewProps, prevState: ILogViewState) {
    if (prevState.scrollOnEnd && this.state.data !== prevState.data) {
      if (this._scrollableAreaRef.current) {
        this._scrollableAreaRef.current.scrollTo(
          0,
          this._scrollableAreaRef.current.scrollHeight
        );
      }
    }
  }

  render() {
    if (this.state.data.length === 0) {
      return (
        <div className={`${style.widgetPane} ${style.generalWidgetCentered}`}>
          <p className={style.noDataLine}>NO DATA</p>
        </div>
      );
    }
    return (
      <div
        className={`${style.widgetPane} ${style.cloudTrainingLogWidget}`}
        onScroll={this.scrollHandler.bind(this)}
        ref={this._scrollableAreaRef}
      >
        <div className={style.cloudTrainingLogWidgetText}>
          {this.state.data}
        </div>
      </div>
    );
  }
}
