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
import { Dialog, showDialog } from '@jupyterlab/apputils';
import { Widget } from '@phosphor/widgets';

import * as base from './base';

interface ILoginDialogValues {
  cluster: string;
  authString: string;
}

class LoginDialog extends Widget {
  /**
   * Construct a new "rename" dialog.
   */
  constructor() {
    super({ node: Private.buildAuthorizeDialogBody() });
  }

  getInputNodeValue(no: number): string {
    let allInputs = this.node.getElementsByTagName('input');
    if (allInputs.length <= no) {
      return undefined;
    } else {
      return allInputs[no].value;
    }
  }

  /**
   * Get the value of the widget.
   */
  getValue(): ILoginDialogValues {
    return {
      cluster: this.getInputNodeValue(0),
      authString: this.getInputNodeValue(1)
    };
  }
}

export function showLoginDialog() {
  return showDialog({
    title: 'Authorization on a Legion cluster',
    body: new LoginDialog(),
    buttons: [Dialog.cancelButton(), Dialog.okButton({ label: 'Login' })]
  });
}

export function showLogoutDialog(clusterName) {
  return showDialog({
    title: 'Logging out on a Legion cluster',
    body: `Do you want to log out on legion cluster ${clusterName}?`,
    buttons: [
      Dialog.cancelButton(),
      Dialog.okButton({ label: 'Log out', displayType: 'warn' })
    ]
  });
}

namespace Private {
  export function buildAuthorizeDialogBody() {
    let body = base.createDialogBody();

    body.appendChild(base.createDialogInputLabel('Cluster (EDI) url'));
    body.appendChild(
      base.createDialogInput(undefined, 'https://edi-company-a.example.com')
    );

    body.appendChild(base.createDialogInputLabel('Oauth2 token'));
    body.appendChild(
      base.createDialogInput(undefined, 'ZW1haWw6dGVzdHMtdXNlckBsZWdpb24uY....')
    );

    return body;
  }
}
