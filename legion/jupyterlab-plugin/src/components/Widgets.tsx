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

// import * as React from 'react';
// import * as ReactDOM from 'react-dom';

import { Message } from '@phosphor/messaging';
import { Widget } from '@phosphor/widgets';

export interface IWidgetOptions {
  defaultRenderHolder: string;
  renderer?: IRenderer;
}

/**
 * A renderer for use with a running sessions widget.
 */
export interface IRenderer {
  createNode(): HTMLElement;
}

/**
 * The default implementation of `IRenderer`.
 */
export class Renderer implements IRenderer {
  nodeName: string;

  constructor(nodeName: string) {
    this.nodeName = nodeName;
  }

  createNode(): HTMLElement {
    let node = document.createElement('div');
    node.id = this.nodeName;
    return node;
  }
}

/**
 * The default `Renderer` instance.
 */

/**
 * A class that exposes the plugin sessions.
 */
export class BaseLegionWidget extends Widget {
  component: any;
  /**
   * Construct a new running widget.
   */
  constructor(options: IWidgetOptions) {
    super({
      node: (
        options.renderer || new Renderer(options.defaultRenderHolder)
      ).createNode()
    });
  }

  /**
   * Override widget's default show() to
   * refresh content every time widget is shown.
   */
  show(): void {
    super.show();
    this.component.refresh();
    this.component.onActivate();
  }

  refresh(): void {
    this.component.refresh();
  }

  /**
   * The renderer used by the running widget.
   */
  get renderer(): IRenderer {
    return this._renderer;
  }

  /**
   * Dispose of the resources used by the widget.
   */
  dispose(): void {
    this._renderer = null;
    super.dispose();
  }

  /**
   * Handle the DOM events for the widget.
   *
   * @param event - The DOM event sent to the widget.
   *
   * #### Notes
   * This method implements the DOM `EventListener` interface and is
   * called in response to events on the widget's DOM nodes. It should
   * not be called directly by user code.
   */
  handleEvent(event: Event): void {
    switch (event.type) {
      case 'change':
        this._evtChange(event as MouseEvent);
        break;
      case 'click':
        this._evtClick(event as MouseEvent);
        break;
      case 'dblclick':
        this._evtDblClick(event as MouseEvent);
        break;
      default:
        break;
    }
  }

  /**
   * A message handler invoked on an `'after-attach'` message.
   */
  protected onAfterAttach(msg: Message): void {
    this.node.addEventListener('change', this);
    this.node.addEventListener('click', this);
    this.node.addEventListener('dblclick', this);
  }

  /**
   * A message handler invoked on a `'before-detach'` message.
   */
  protected onBeforeDetach(msg: Message): void {
    this.node.addEventListener('change', this);
    this.node.removeEventListener('click', this);
    this.node.removeEventListener('dblclick', this);
  }

  /**
   * Handle the `'click'` event for the widget.
   *
   * #### Notes
   * This listener is attached to the document node.
   */
  private _evtChange(event: MouseEvent): void {}
  /**
   * Handle the `'click'` event for the widget.
   *
   * #### Notes
   * This listener is attached to the document node.
   */
  private _evtClick(event: MouseEvent): void {}

  /**
   * Handle the `'dblclick'` event for the widget.
   */
  private _evtDblClick(event: MouseEvent): void {}

  private _renderer: IRenderer = null;
}

export interface IWidgetRegistry<TargetWidget> {
  getOrConstruct(name: string): TargetWidget;
}

export type WidgetRegistryBuilder<TargetWidget> = (
  name: string
) => TargetWidget;

export class WidgetRegistry<TargetWidget>
  implements IWidgetRegistry<TargetWidget> {
  private _storage: Map<string, TargetWidget>;
  private _builder: WidgetRegistryBuilder<TargetWidget>;

  constructor(builder: WidgetRegistryBuilder<TargetWidget>) {
    this._storage = new Map<string, TargetWidget>();
    this._builder = builder;
  }

  getOrConstruct(name: string): TargetWidget {
    if (!this._storage.has(name)) {
      this._storage.set(name, this._builder(name));
    }

    return this._storage.get(name);
  }
}
