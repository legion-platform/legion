import { Widget } from '@phosphor/widgets';

export class OpenTemplateWidget extends Widget {
  constructor(templates: Array<string>) {
    const body = document.createElement('div');
    const label = document.createElement('label');
    label.textContent = 'Template:';

    const input = document.createElement('select');
    for (const t of templates) {
      const val = document.createElement('option');
      val.label = t;
      val.text = t;
      val.value = t;
      input.appendChild(val);
    }

    body.appendChild(label);
    body.appendChild(input);
    super({ node: body });
  }

  public getValue(): string {
    return this.inputNode.value;
  }

  get inputNode(): HTMLSelectElement {
    return this.node.getElementsByTagName('select')[0] as HTMLSelectElement;
  }
}
