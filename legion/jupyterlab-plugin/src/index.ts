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
import {
  ILayoutRestorer,
  JupyterLab,
  JupyterLabPlugin
} from '@jupyterlab/application';
import { ISplashScreen } from '@jupyterlab/apputils';
import { IMainMenu } from '@jupyterlab/mainmenu';
import { IFileBrowserFactory } from '@jupyterlab/filebrowser';

import { Menu, Widget } from '@phosphor/widgets';
import { CommandRegistry } from '@phosphor/commands';
import { Token } from '@phosphor/coreutils';

import '../style/variables.css';

import { cloudModeTabStyle } from './componentsStyle/GeneralWidgetStyle';

import { WidgetRegistry } from './components/Widgets';

import {
  createCloudSidebarWidget,
  LegionSideWidget
} from './components/SideWidgets';
import { CloudTrainingLogsWidget } from './components/CloudTrainingLogsWidget';
import { addCloudCommands, CommandIDs } from './commands';

import { LegionApi } from './api';
import { IApiCloudState, buildInitialCloudAPIState } from './models/apiState';
import { ILegionPluginMode } from './models/core';

export const PLUGIN_ID = 'jupyter.extensions.legion';
export const PLUGIN_ID_CLOUD = PLUGIN_ID + ':cloud';
export const EXTENSION_ID = 'jupyter.extensions.jupyter_legion';

const FILE_MANAGER_LEGION_RESOURCE =
  '.jp-DirListing-item[title*="legion.yaml"]';
const APPLY_LEGION_RESOURCES = 100;
const REMOVE_LEGION_RESOURCES = 101;

// tslint:disable-next-line: variable-name
export const ILegionExtension = new Token<ILegionExtension>(EXTENSION_ID);

/** Interface for extension class */
export interface ILegionExtension {}

const pluginRequirements = [
  IMainMenu,
  ILayoutRestorer,
  ISplashScreen,
  IFileBrowserFactory
];

/**
 * Plugins declarations
 */
const cloudPlugin: JupyterLabPlugin<ILegionExtension> = {
  id: PLUGIN_ID_CLOUD,
  requires: pluginRequirements,
  provides: ILegionExtension,
  activate: activateCloudPlugin,
  autoStart: true
};

/**
 * Export the plugins as default.
 */
const plugins: JupyterLabPlugin<any>[] = [cloudPlugin];
export default plugins;

class BaseLegionExtension {
  /**
   * Instance of Legion Widget for appropriate mode
   */
  sideWidget: LegionSideWidget;

  /**
   * API to back-end
   */
  api: LegionApi;

  /**
   * API state
   */
  apiCloudState?: IApiCloudState;
}

/**
 * Declare extension for cloud mode
 */
export class LegionCloudExtension extends BaseLegionExtension
  implements ILegionExtension {
  private _trainingLogs: WidgetRegistry<Widget>;
  private _app: JupyterLab;

  /**
   * Construct extension
   * @param app JupyterLab target JupyterLab
   * @param restorer ILayoutRestorer layout restorer
   */
  constructor(app: JupyterLab, restorer: ILayoutRestorer) {
    super();

    this._app = app;
    this.api = new LegionApi();
    this._trainingLogs = new WidgetRegistry<Widget>(name =>
      this.constructTrainingLogWidget(name)
    );

    this.apiCloudState = buildInitialCloudAPIState();
    this.sideWidget = createCloudSidebarWidget(app, {
      manager: app.serviceManager,
      state: this.apiCloudState,
      defaultRenderHolder: 'legion-cloud-sidebar-widget'
    });
    this.sideWidget.id = 'legion-cloud-sessions-widget';
    this.sideWidget.title.iconClass = `jp-SideBar-tabIcon ${cloudModeTabStyle}`;
    this.sideWidget.title.caption = 'Legion cloud mode';

    this.apiCloudState.onDataChanged.connect(_ => this.sideWidget.refresh());

    restorer.add(this.sideWidget, 'legion-cloud-sessions');
    app.shell.addToLeftArea(this.sideWidget, { rank: 210 });

    app.restored.then(() => {
      this.apiCloudState.tryToLoadCredentialsFromSettings();
    });
  }

  get trainingLogs(): WidgetRegistry<Widget> {
    return this._trainingLogs;
  }

  private constructTrainingLogWidget(name: string): Widget {
    return new CloudTrainingLogsWidget(
      this._app,
      this.api.cloud,
      name,
      this.apiCloudState,
      {
        defaultRenderHolder: 'legion-cloud-' + name
      }
    );
  }
}

function buildTopMenu(
  commands: CommandRegistry,
  mode: ILegionPluginMode
): Menu {
  let menu = new Menu({ commands });
  menu.title.label =
    mode === ILegionPluginMode.CLOUD ? 'Legion cloud' : 'UNKNOWN LEGION MODE';

  const commandsToAdd =
    mode === ILegionPluginMode.CLOUD
      ? [
          CommandIDs.refreshCloud,
          CommandIDs.authorizeOnCluster,
          CommandIDs.unAuthorizeOnCluster,
          CommandIDs.issueNewCloudAccessToken
        ]
      : [];

  commandsToAdd.forEach(command => {
    menu.addItem({ command });
  });

  return menu;
}

/**
 * Activate Legion plugin (build & return LegionExtension, register commands)
 */
function activateCloudPlugin(
  app: JupyterLab,
  mainMenu: IMainMenu,
  restorer: ILayoutRestorer,
  splash: ISplashScreen,
  factory: IFileBrowserFactory
): ILegionExtension {
  // Build extension
  let legionExtension = new LegionCloudExtension(app, restorer);

  // Build options for commands
  const addCommandsOptions = {
    app,
    services: app.serviceManager,
    state: legionExtension.apiCloudState,
    api: legionExtension.api,
    splash,
    tracker: factory.tracker,
    trainingLogs: legionExtension.trainingLogs
  };

  // Register commands in JupyterLab
  addCloudCommands(addCommandsOptions);

  app.contextMenu.addItem({
    command: CommandIDs.applyCloudResources,
    selector: FILE_MANAGER_LEGION_RESOURCE,
    rank: APPLY_LEGION_RESOURCES
  });

  app.contextMenu.addItem({
    command: CommandIDs.removeCloudResources,
    selector: FILE_MANAGER_LEGION_RESOURCE,
    rank: REMOVE_LEGION_RESOURCES
  });

  // Create top menu for appropriate mode
  mainMenu.addMenu(buildTopMenu(app.commands, ILegionPluginMode.CLOUD), {
    rank: 60
  });
  return legionExtension;
}
