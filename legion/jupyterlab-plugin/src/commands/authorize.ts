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
import { Dialog, showDialog, showErrorMessage } from '@jupyterlab/apputils';
import { CommandRegistry } from '@phosphor/commands';

import { CommandIDs, IAddCloudCommandsOptions } from './base';
import * as dialogs from '../components/dialogs';

/**
 * Add the commands for the legion extension.
 */
export function addCommands(options: IAddCloudCommandsOptions) {
  let { commands } = options.app;

  commands.addCommand(CommandIDs.unAuthorizeOnCluster, {
    label: 'Reset cluster authorization',
    caption: 'Reset currently used cluster context',
    execute: () => {
      try {
        if (options.state.authorizationRequired) {
          showErrorMessage(
            'Can not reset cluster authorization',
            'You are not authorized on any cluster'
          );
        } else {
          dialogs
            .showLogoutDialog(
              options.state.credentials
                ? options.state.credentials.cluster
                : 'Internal cluster'
            )
            .then(({ button }) => {
              if (button.accept) {
                options.state.setCredentials();
              }
            });
        }
      } catch (err) {
        showErrorMessage('Can not reset cluster authorization', err);
      }
    }
  });

  commands.addCommand(CommandIDs.authorizeOnCluster, {
    label: 'Authorize on cluster',
    caption: 'Authorize on Legion cluster',
    execute: () => {
      try {
        if (!options.state.authorizationRequired) {
          showErrorMessage(
            'Can not authorize on a cluster',
            'You are already authorized'
          );
        } else if (
          options.state.authConfiguration.oauth2AuthorizationIsEnabled
        ) {
          oauth2Authentication(options);
        } else {
          authenticateUsingToken(options, commands);
        }
      } catch (err) {
        showErrorMessage('Can not authorize on a cluster', err);
      }
    }
  });
}

function authenticateUsingToken(
  options: IAddCloudCommandsOptions,
  commands: CommandRegistry
) {
  dialogs
    .showLoginDialog(options.state.credentials.cluster)
    .then(({ button, value }) => {
      if (button.accept) {
        let splashScreen = options.splash.show();
        options.api.cloud
          .getCloudAllEntities(value)
          .then(_ => {
            splashScreen.dispose();
            options.state.setCredentials(value);
            showDialog({
              title: 'Legion Cluster mode',
              body:
                'You have been successfully authorized on a cluster ' +
                value.cluster,
              buttons: [Dialog.okButton()]
            });
            commands.execute(CommandIDs.refreshCloud);
          })
          .catch(err => {
            splashScreen.dispose();
            showErrorMessage('Authorization on a cluster failed', err);
          });
      }
    });
}

function oauth2Authentication(options: IAddCloudCommandsOptions) {
  if (options.state.credentials.cluster) {
    let splashScreen = options.splash.show();

    options.api.configuration
      .getOauthUrl()
      .then(function(oauthUrl) {
        splashScreen.dispose();

        window.location.assign(oauthUrl);
      })
      .catch(err => {
        splashScreen.dispose();
      });
  } else {
    dialogs
      .showLoginDialog(options.state.credentials.cluster, false)
      .then(({ button, value }) => {
        if (button.accept) {
          let splashScreen = options.splash.show();

          options.state.setCredentials(value);
          options.api.configuration
            .getOauthUrl()
            .then(oauthUrl => {
              splashScreen.dispose();

              window.location.assign(oauthUrl);
            })
            .catch(err => {
              splashScreen.dispose();
              showErrorMessage('Authorization on a cluster failed', err);
            });
        }
      });
  }
}
