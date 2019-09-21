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
import { showErrorMessage, showDialog, Dialog } from '@jupyterlab/apputils';

import { CommandIDs, IAddCloudCommandsOptions } from './base';
import * as dialogs from '../components/dialogs';
import * as cloudDialogs from '../components/dialogs/cloud';

/**
 * Add the commands for the legion extension.
 */
export function addCommands(options: IAddCloudCommandsOptions) {
  let { commands } = options.app;

  commands.addCommand(CommandIDs.removeConnection, {
    label: 'Remove connection',
    caption: 'Remove cloud connection',
    execute: args => {
      try {
        const name = args['name'] as string;
        if (name) {
          showDialog({
            title: `Removing connection`,
            body: `Do you want to remove connection ${name}?`,
            buttons: [
              Dialog.cancelButton(),
              Dialog.okButton({ label: 'Remove', displayType: 'warn' })
            ]
          }).then(({ button }) => {
            if (button.accept) {
              let splashScreen = options.splash.show();
              options.api.cloud
                .removeConnection(
                  {
                    id: name
                  },
                  options.state.credentials
                )
                .then(() => {
                  splashScreen.dispose();
                  commands.execute(CommandIDs.refreshCloud, {});
                })
                .catch(err => {
                  splashScreen.dispose();
                  showErrorMessage('Can not remove connection', err);
                  commands.execute(CommandIDs.refreshCloud, {});
                });
            }
          });
        } else {
          dialogs
            .showChooseDialog(
              'Choose connection',
              'Please choose one connection from list',
              options.state.connections.map(conn => {
                return {
                  value: conn.id,
                  text: conn.id
                };
              }),
              'Remove connection',
              true
            )
            .then(({ value }) =>
              commands.execute(CommandIDs.removeConnection, {
                name: value.value
              })
            );
        }
      } catch (err) {
        showErrorMessage('Can not remove connection', err);
      }
    }
  });

  commands.addCommand(CommandIDs.removeModelPackaging, {
    label: 'Model Packaging ',
    caption: 'Remove model packaging',
    execute: args => {
      try {
        const name = args['name'] as string;
        if (name) {
          showDialog({
            title: `Removing model packaging`,
            body: `Do you want to remove model packaging ${name}?`,
            buttons: [
              Dialog.cancelButton(),
              Dialog.okButton({ label: 'Remove', displayType: 'warn' })
            ]
          }).then(({ button }) => {
            if (button.accept) {
              let splashScreen = options.splash.show();
              options.api.cloud
                .removeModelPackaging(
                  {
                    id: name
                  },
                  options.state.credentials
                )
                .then(() => {
                  splashScreen.dispose();
                  commands.execute(CommandIDs.refreshCloud, {});
                })
                .catch(err => {
                  splashScreen.dispose();
                  showErrorMessage('Can not remove model packagings', err);
                  commands.execute(CommandIDs.refreshCloud, {});
                });
            }
          });
        } else {
          dialogs
            .showChooseDialog(
              'Choose model packaging',
              'Please choose one model packaging from list',
              options.state.modelPackagings.map(mp => {
                return {
                  value: mp.id,
                  text: mp.id
                };
              }),
              'Remove model packaging',
              true
            )
            .then(({ value }) =>
              commands.execute(CommandIDs.removeModelPackaging, {
                name: value.value
              })
            );
        }
      } catch (err) {
        showErrorMessage('Can not remove model packaging', err);
      }
    }
  });

  commands.addCommand(CommandIDs.removeCloudTraining, {
    label: 'Remove cloud training',
    caption: 'Stop and remove cloud training',
    execute: args => {
      try {
        const name = args['name'] as string;
        if (name) {
          showDialog({
            title: `Removing training`,
            body: `Do you want to remove training ${name}?`,
            buttons: [
              Dialog.cancelButton(),
              Dialog.okButton({ label: 'Remove', displayType: 'warn' })
            ]
          }).then(({ button }) => {
            if (button.accept) {
              let splashScreen = options.splash.show();
              options.api.cloud
                .removeCloudTraining(
                  {
                    id: name
                  },
                  options.state.credentials
                )
                .then(() => {
                  splashScreen.dispose();
                  commands.execute(CommandIDs.refreshCloud, {});
                })
                .catch(err => {
                  splashScreen.dispose();
                  showErrorMessage('Can not remove cloud training', err);
                  commands.execute(CommandIDs.refreshCloud, {});
                });
            }
          });
        } else {
          dialogs
            .showChooseDialog(
              'Choose training to remove',
              'Please choose one training from list',
              options.state.trainings.map(training => {
                return {
                  value: training.id,
                  text: training.id
                };
              }),
              'Remove training',
              true
            )
            .then(({ value }) =>
              commands.execute(CommandIDs.removeCloudTraining, {
                name: value.value
              })
            );
        }
      } catch (err) {
        showErrorMessage('Can not remove cloud training', err);
      }
    }
  });

  commands.addCommand(CommandIDs.newCloudDeployment, {
    label: 'Deploy model in a cloud',
    caption: 'Create cloud deployment',
    execute: args => {
      try {
        const image = args['image'] as string;
        if (image) {
          cloudDialogs
            .showCreateNewDeploymentDetails(image)
            .then(({ value, button }) => {
              if (button.accept) {
                let splashScreen = options.splash.show();
                options.api.cloud
                  .createCloudDeployment(
                    {
                      id: value.name,
                      spec: {
                        image: image,
                        livenessProbeInitialDelay: 5,
                        readinessProbeInitialDelay: 3
                      }
                    },
                    options.state.credentials
                  )
                  .then(_ => {
                    splashScreen.dispose();
                    commands.execute(CommandIDs.refreshCloud, {});
                  })
                  .catch(err => {
                    splashScreen.dispose();
                    showErrorMessage('Can not deploy image on a cloud', err);
                  });
              }
            });
        } else {
          dialogs
            .showInputDialog(
              'Choose image to deploy',
              'type image name',
              'Deploy image',
              false
            )
            .then(({ value }) =>
              commands.execute(CommandIDs.newCloudDeployment, {
                image: value.input
              })
            );
        }
      } catch (err) {
        showErrorMessage('Can not deploy model on a cloud', err);
      }
    }
  });

  commands.addCommand(CommandIDs.removeCloudDeployment, {
    label: 'Remove Legion cloud deployment',
    caption: 'Remove cloud deployment',
    execute: args => {
      try {
        const name = args['name'] as string;
        if (name) {
          showDialog({
            title: `Removing deployment`,
            body: `Do you want to remove deployment ${name}?`,
            buttons: [
              Dialog.cancelButton(),
              Dialog.okButton({ label: 'Remove', displayType: 'warn' })
            ]
          }).then(({ button }) => {
            if (button.accept) {
              let splashScreen = options.splash.show();
              options.api.cloud
                .removeCloudDeployment(
                  {
                    id: name
                  },
                  options.state.credentials
                )
                .then(() => {
                  splashScreen.dispose();
                  commands.execute(CommandIDs.refreshCloud, {});
                })
                .catch(err => {
                  splashScreen.dispose();
                  showErrorMessage('Can not remove cloud deployment', err);
                  commands.execute(CommandIDs.refreshCloud, {});
                });
            }
          });
        } else {
          dialogs
            .showChooseDialog(
              'Choose deployment to remove',
              'Please choose one deployment from list',
              options.state.deployments.map(deployment => {
                return {
                  value: deployment.id,
                  text: deployment.id
                };
              }),
              'Remove deployment',
              true
            )
            .then(({ value, button }) => {
              if (button.accept) {
                commands.execute(CommandIDs.removeCloudDeployment, {
                  name: value.value
                });
              }
            });
        }
      } catch (err) {
        showErrorMessage('Can not remove cloud deployment', err);
      }
    }
  });

  commands.addCommand(CommandIDs.refreshCloud, {
    label: 'Force data refresh for cloud mode',
    caption: 'Force data synchronization for cloud mode',
    execute: () => {
      options.state.signalLoadingStarted();

      options.api.cloud
        .getCloudAllEntities(options.state.credentials)
        .then(response => {
          options.state.updateAllState(response);
        })
        .catch(err => {
          options.state.updateAllState();
          showErrorMessage(
            'Can not forcefully update data for cloud mode',
            err
          );
        });
    }
  });

  commands.addCommand(CommandIDs.openCloudModelPlugin, {
    label: 'Cloud mode interface',
    caption: 'Go to Cloud mode interface',
    execute: () => {
      try {
        options.app.shell.activateById('legion-cloud-sessions-widget');
      } catch (err) {}
    }
  });

  commands.addCommand(CommandIDs.openTrainingLogs, {
    label: 'Open cloud training logs',
    execute: args => {
      try {
        const name = args['name'] as string;
        if (name) {
          const widget = options.trainingLogs.getOrConstruct(name);
          if (!widget.isAttached) {
            options.app.shell.addToMainArea(widget);
          }
          options.app.shell.activateById(widget.id);
        } else {
          dialogs
            .showChooseDialog(
              'Choose deployment to remove',
              'Please choose one deployment from list',
              options.state.trainings.map(trainings => {
                return {
                  value: trainings.id,
                  text: trainings.id
                };
              }),
              'Open logs of training',
              true
            )
            .then(({ value, button }) => {
              if (button.accept) {
                commands.execute(CommandIDs.openTrainingLogs, {
                  name: value.value
                });
              }
            });
        }
      } catch (err) {
        showErrorMessage('Can not remove cloud deployment', err);
      }
    }
  });

  commands.addCommand(CommandIDs.openPackagingLogs, {
    label: 'Open cloud training logs',
    execute: args => {
      try {
        const name = args['name'] as string;
        if (name) {
          const widget = options.packagingLogs.getOrConstruct(name);
          if (!widget.isAttached) {
            options.app.shell.addToMainArea(widget);
          }
          options.app.shell.activateById(widget.id);
        }
      } catch (err) {
        showErrorMessage('Can not remove cloud deployment', err);
      }
    }
  });

  commands.addCommand(CommandIDs.applyCloudResources, {
    label: 'Submit',
    iconClass: 'jp-AddIcon',
    execute: () => {
      const widget = options.tracker.currentWidget;
      if (!widget) {
        return;
      }
      const path = encodeURI(widget.selectedItems().next().path);

      let splashScreen = options.splash.show();
      options.api.cloud
        .applyFromFile({ path, removal: false }, options.state.credentials)
        .then(results => {
          splashScreen.dispose();
          dialogs.showApplyResultsDialog(results);
        })
        .catch(err => {
          splashScreen.dispose();
          showErrorMessage('Can not apply file ' + path, err);
        });
    }
  });

  commands.addCommand(CommandIDs.removeCloudResources, {
    label: 'Remove Legion resources',
    iconClass: 'jp-CloseIcon',
    execute: () => {
      const widget = options.tracker.currentWidget;
      if (!widget) {
        return;
      }
      const path = encodeURI(widget.selectedItems().next().path);

      let splashScreen = options.splash.show();
      options.api.cloud
        .applyFromFile({ path, removal: true }, options.state.credentials)
        .then(results => {
          splashScreen.dispose();
          dialogs.showApplyResultsDialog(results);
        })
        .catch(err => {
          splashScreen.dispose();
          showErrorMessage('Can not remove from file ' + path, err);
        });
    }
  });

  commands.addCommand(CommandIDs.condaUpdateEnv, {
    label: 'Update conda env',
    iconClass: 'jp-CloseIcon',
    execute: () => {
      const widget = options.tracker.currentWidget;
      if (!widget) {
        return;
      }
      const path = encodeURI(widget.selectedItems().next().path);
      console.log(path);
      commands.execute('terminal:create-new', {
        initialCommand: `conda-update mlflow ${path}`
      });
    }
  });
}
