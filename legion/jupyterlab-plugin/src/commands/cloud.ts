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
import { ReadonlyJSONObject } from '@phosphor/coreutils';

import { CommandIDs, IAddCloudCommandsOptions } from './base';
import * as dialogs from '../components/dialogs';
import * as models from '../models/cloud';
import * as cloudDialogs from '../components/dialogs/cloud';
import { cloudModeTabStyle } from '../componentsStyle/GeneralWidgetStyle';

export interface ICloudScaleParameters {}

/**
 * Add the commands for the legion extension.
 */
export function addCommands(options: IAddCloudCommandsOptions) {
  let { commands } = options.app;

  commands.addCommand(CommandIDs.newCloudTraining, {
    label: 'Train model in a cloud',
    caption: 'Create new cloud training',
    execute: args => {
      let values = (args as unknown) as cloudDialogs.ICreateNewTrainingDialogValues;

      cloudDialogs
        .showCreateNewTrainingDialog(options.state.vcss, values)
        .then(({ value, button }) => {
          if (button.accept) {
            if (!value.isFinished) {
              showErrorMessage(
                'Can not create cloud training',
                'Not all fields are filled'
              ).then(() =>
                commands.execute(
                  CommandIDs.newCloudTraining,
                  (value as unknown) as ReadonlyJSONObject
                )
              );
            } else {
              let splashScreen = options.splash.show();
              options.api.cloud
                .createCloudTraining(
                  value as models.ICloudTrainingRequest,
                  options.state.credentials
                )
                .then(() => {
                  splashScreen.dispose();
                  commands.execute(CommandIDs.refreshCloud, {});
                })
                .catch(err => {
                  splashScreen.dispose();
                  showErrorMessage('Can not create cloud deployment', err);
                  commands.execute(CommandIDs.refreshCloud, {});
                });
            }
          }
        });
    }
  });

  // newCloudTrainingFromContextMenu
  commands.addCommand(CommandIDs.newCloudTrainingFromContextMenu, {
    label: 'Train model on a cloud',
    iconClass: cloudModeTabStyle,
    execute: () => {
      const widget = options.tracker.currentWidget;
      if (!widget) {
        return;
      }
      const path = encodeURI(widget.selectedItems().next().path);

      let splashScreen = options.splash.show();
      options.api.cloud
        .getLocalFileInformation({ path })
        .then(response => {
          let toolchain = undefined;
          if (response.extension === '.py') {
            toolchain = 'python';
          } else if (response.extension === '.ipynb') {
            toolchain = 'jupyter';
          }

          let value: cloudDialogs.ICreateNewTrainingDialogValues = {
            entrypoint: response.path,
            workDir: response.workDir,
            toolchain,
            reference:
              response.references.length > 0
                ? response.references[0]
                : undefined,
            isFinished: false
          };

          splashScreen.dispose();
          commands.execute(
            CommandIDs.newCloudTraining,
            (value as unknown) as ReadonlyJSONObject
          );
        })
        .catch(err => {
          splashScreen.dispose();
          showErrorMessage('Can not get information about file', err);
        });
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
                    name: name
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
              'Choose training to remove',
              'Please choose one training from list',
              options.state.trainings.map(training => {
                return {
                  value: training.name,
                  text: training.name
                };
              }),
              'Remove deployment',
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
                      name: value.name,
                      image,
                      replicas: value.replicas,
                      livenessProbeInitialDelay: 5,
                      readinessProbeInitialDelay: 3
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
            .showChooseOrInputDialog(
              'Choose image to deploy',
              'Please choose finished training',
              'or type image name manually',
              options.state.trainings
                .filter(training => training.status.modelImage.length > 0)
                .map(training => {
                  return {
                    value: training.status.modelImage,
                    text: training.name
                  };
                }),
              'Deploy image',
              false
            )
            .then(({ value }) =>
              commands.execute(CommandIDs.newCloudDeployment, {
                image:
                  value.input.length > 0 ? value.input : value.selection.value
              })
            );
        }
      } catch (err) {
        showErrorMessage('Can not deploy model on a cloud', err);
      }
    }
  });

  commands.addCommand(CommandIDs.scaleCloudDeployment, {
    label: 'Scale model in a cloud',
    caption: 'Change count of desired replicas in a cloud',
    execute: args => {
      try {
        const name = args['name'] as string;
        const currentAvailableReplicas = args[
          'currentAvailableReplicas'
        ] as number;
        const currentDesiredReplicas = args['currentDesiredReplicas'] as number;
        const newScale = args['newScale'] as number;
        if (newScale !== undefined) {
          let splashScreen = options.splash.show();
          options.api.cloud
            .scaleCloudDeployment(
              {
                name,
                newScale
              },
              options.state.credentials
            )
            .then(_ => {
              splashScreen.dispose();
              commands.execute(CommandIDs.refreshCloud, {});
            })
            .catch(err => {
              splashScreen.dispose();
              showErrorMessage('Can not scale model in a cloud', err);
            });
        } else if (name !== undefined) {
          dialogs
            .showPromptDialog(
              'Provide new desired count',
              `Please provide new scale for model ${name} (currently ${currentAvailableReplicas}/${currentDesiredReplicas} replicas available)`,
              'Scale',
              false
            )
            .then(({ value, button }) => {
              if (button.accept) {
                commands.execute(CommandIDs.scaleCloudDeployment, {
                  name,
                  newScale: parseInt(value, 10)
                });
              }
            });
        } else {
          dialogs
            .showChooseDialog(
              'Choose deployment to scale',
              'Please choose one deployment from list',
              options.state.deployments.map(deployment => {
                return {
                  value: deployment.name,
                  text: deployment.name
                };
              }),
              'Scale deployment',
              false
            )
            .then(({ value, button }) => {
              if (button.accept) {
                const targetDeployment = options.state.deployments.find(
                  deployment => deployment.name === value.value
                );
                if (targetDeployment != undefined) {
                  commands.execute(CommandIDs.scaleCloudDeployment, {
                    name: value.value,
                    currentAvailableReplicas:
                      targetDeployment.status.availableReplicas,
                    currentDesiredReplicas: targetDeployment.spec.replicas
                  });
                }
              }
            });
        }
      } catch (err) {
        showErrorMessage('Can not scale cloud model', err);
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
                    name: name
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
                  value: deployment.name,
                  text: deployment.name
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

  commands.addCommand(CommandIDs.issueNewCloudAccessToken, {
    label: 'Issue token for models deployed on a cloud',
    caption: 'Create new JWT token',
    execute: args => {
      try {
        const modelID = args['modelID'] as string;
        const modelVersion = args['modelVersion'] as string;
        if (modelID) {
          let splashScreen = options.splash.show();
          options.api.cloud
            .issueCloudAccess(
              {
                model_id: modelID,
                model_version: modelVersion
              },
              options.state.credentials
            )
            .then(response => {
              splashScreen.dispose();
              showDialog({
                title: `Generated token`,
                body: response.token,
                buttons: [Dialog.okButton({ label: 'OK' })]
              });
            })
            .catch(err => {
              splashScreen.dispose();
              showErrorMessage('Can not remove issue cloud access token', err);
            });
        } else {
          cloudDialogs.showIssueModelAccessToken().then(({ value, button }) => {
            if (button.accept) {
              commands.execute(CommandIDs.issueNewCloudAccessToken, {
                modelID: value.modelId,
                modelVersion: value.modelVersion
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
                  value: trainings.name,
                  text: trainings.name
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

  commands.addCommand(CommandIDs.applyCloudResources, {
    label: 'Apply Legion resources',
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
}
