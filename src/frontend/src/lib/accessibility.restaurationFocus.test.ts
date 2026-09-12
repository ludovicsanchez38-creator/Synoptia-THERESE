import { afterEach, describe, expect, it } from 'vitest';
import { createFocusTrap } from './accessibility';

describe('B-758 - restitution du focus par createFocusTrap', () => {
  afterEach(() => {
    document.body.replaceChildren();
  });

  it('le cleanup restaure le déclencheur encore connecté au document', () => {
    const trigger = document.createElement('button');
    trigger.textContent = 'Ouvrir';
    const dialog = document.createElement('div');
    const close = document.createElement('button');
    close.textContent = 'Fermer';
    dialog.append(close);
    document.body.append(trigger, dialog);

    trigger.focus();
    const cleanup = createFocusTrap(dialog);
    expect(close).toHaveFocus();

    cleanup();

    expect(trigger).toHaveFocus();
  });
});
