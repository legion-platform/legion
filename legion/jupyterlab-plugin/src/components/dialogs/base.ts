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
import * as style from '../../componentsStyle/dialogs';

import { Dialog, showDialog } from '@jupyterlab/apputils';
import { Widget } from '@phosphor/widgets';

// General dialogs

export interface IChooseVariant {
  value: string;
  text: string;
}

export interface IChooseVariantOrInput {
  selection?: IChooseVariant;
  input: string;
}

class ChooseDialog extends Widget {
  constructor(body: string, variants: Array<IChooseVariant>) {
    super({ node: Private.buildChooseDialogBody(body, variants) });
  }

  getValue(): IChooseVariant {
    let selects = this.node.getElementsByTagName('select');
    const targetSelect = selects[0];

    if (targetSelect.selectedIndex >= 0) {
      return {
        value: targetSelect.options[targetSelect.selectedIndex].value,
        text: targetSelect.options[targetSelect.selectedIndex].text
      };
    } else {
      return {
        value: undefined,
        text: undefined
      };
    }
  }
}

class ChooseOrInputDialog extends Widget {
  constructor(
    body: string,
    secondText: string,
    variants: Array<IChooseVariant>
  ) {
    super({
      node: Private.buildChooseOrInputDialogBody(body, secondText, variants)
    });
  }

  getValue(): IChooseVariantOrInput {
    const selects = this.node.getElementsByTagName('select');
    const targetSelect = selects[0];

    const inputs = this.node.getElementsByTagName('input');
    const targetInput = inputs[0];

    return {
      selection:
        targetSelect.selectedIndex >= 0
          ? {
              value: targetSelect.options[targetSelect.selectedIndex].value,
              text: targetSelect.options[targetSelect.selectedIndex].text
            }
          : null,
      input: targetInput.value
    };
  }
}

export function showChooseDialog(
  title: string,
  body: string,
  variants: Array<IChooseVariant>,
  confirmChoose: string,
  warn: boolean
) {
  return showDialog({
    title: title,
    body: new ChooseDialog(body, variants),
    buttons: [
      Dialog.cancelButton(),
      Dialog.okButton({
        label: confirmChoose,
        displayType: warn ? 'warn' : 'default'
      })
    ]
  });
}

export function showChooseOrInputDialog(
  title: string,
  body: string,
  secondText: string,
  variants: Array<IChooseVariant>,
  confirmChoose: string,
  warn: boolean
) {
  return showDialog({
    title: title,
    body: new ChooseOrInputDialog(body, secondText, variants),
    buttons: [
      Dialog.cancelButton(),
      Dialog.okButton({
        label: confirmChoose,
        displayType: warn ? 'warn' : 'default'
      })
    ]
  });
}

class PromptDialog extends Widget {
  constructor(body: string) {
    super({ node: Private.buildPromptDialogBody(body) });
  }

  getValue(): string {
    let inputs = this.node.getElementsByTagName('input');
    const targetInput = inputs[0] as HTMLInputElement;

    return targetInput.value;
  }
}

export function showPromptDialog(
  title: string,
  body: string,
  confirm: string,
  warn: boolean
) {
  return showDialog({
    title: title,
    body: new PromptDialog(body),
    buttons: [
      Dialog.cancelButton(),
      Dialog.okButton({
        label: confirm,
        displayType: warn ? 'warn' : 'default'
      })
    ]
  });
}

/**
 * PARTIALS
 */

export function createDialogBody(): HTMLElement {
  return document.createElement('div');
}

export function createDialogInput(
  defaultValue?: string,
  placeholder?: string
): HTMLInputElement {
  let input = document.createElement('input');
  input.className = `${style.inputFieldStyle} ${style.dialogLine}`;
  if (defaultValue !== undefined) {
    input.value = defaultValue;
  }
  if (placeholder !== undefined) {
    input.placeholder = placeholder;
  }
  return input;
}

export function createSelect(
  variants: Array<IChooseVariant>,
  selectedOptionValue?: string
): HTMLSelectElement {
  let select = document.createElement('select');
  select.className = `${style.inputFieldStyle}`;
  variants.forEach(item => {
    let option = document.createElement('option');
    option.value = item.value;
    option.text = item.text;
    if (
      option.value === selectedOptionValue &&
      selectedOptionValue !== undefined
    ) {
      option.selected = true;
    }
    select.appendChild(option);
  });
  return select;
}

export function createDialogInputLabel(text): HTMLElement {
  let description = document.createElement('span');
  description.className = style.dialogInputLabel;
  description.textContent = text;
  return description;
}

export function createDescriptionLine(text): HTMLElement {
  let description = document.createElement('span');
  description.className = `jp-Dialog-body ${style.dialogLine}`;
  description.textContent = text;
  return description;
}

namespace Private {
  export function buildChooseDialogBody(
    bodyText: string,
    variants: Array<IChooseVariant>
  ) {
    const body = createDialogBody();
    body.appendChild(createDialogInputLabel(bodyText));
    body.appendChild(createSelect(variants));
    return body;
  }

  export function buildChooseOrInputDialogBody(
    bodyText: string,
    secondText: string,
    variants: Array<IChooseVariant>
  ) {
    const body = createDialogBody();
    body.appendChild(createDialogInputLabel(bodyText));
    body.appendChild(createSelect(variants));
    body.appendChild(createDialogInputLabel(secondText));
    body.appendChild(createDialogInput());
    return body;
  }

  export function buildPromptDialogBody(bodyText: string) {
    const body = createDialogBody();
    body.appendChild(createDialogInputLabel(bodyText));
    body.appendChild(createDialogInput());
    return body;
  }
}
