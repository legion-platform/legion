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
import * as authorize from './authorize';
import * as cloud from './cloud';
import { IAddCloudCommandsOptions } from './base';

export { CommandIDs, IAddCloudCommandsOptions } from './base';

/**
 * List of cloud command handlers
 */
const CLOUD_HANDLERS = [authorize, cloud];

/**
 * Add the commands for the legion extension.
 */
export function addCloudCommands(options: IAddCloudCommandsOptions) {
  CLOUD_HANDLERS.forEach(handler => {
    handler.addCommands(options);
  });
}
