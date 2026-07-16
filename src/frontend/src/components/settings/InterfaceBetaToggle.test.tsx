import { fireEvent, render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { INTERFACE_MODE_STORAGE_KEY } from '../../lib/interfaceMode';
import { installLocalStorageStub } from '../../test/localStorage-stub';
import { InterfaceBetaToggle } from './InterfaceBetaToggle';

describe('InterfaceBetaToggle', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    installLocalStorageStub();
  });

  it('active la bêta, mémorise le mode et propose de recharger', () => {
    const onReload = vi.fn();
    render(<InterfaceBetaToggle onReload={onReload} />);

    const toggle = screen.getByRole('switch', {
      name: 'Essayer la nouvelle interface (bêta)',
    });
    expect(toggle).toHaveAttribute('aria-checked', 'false');

    fireEvent.click(toggle);

    expect(window.localStorage.setItem).toHaveBeenCalledWith(
      INTERFACE_MODE_STORAGE_KEY,
      'conversation-canvas',
    );
    expect(toggle).toHaveAttribute('aria-checked', 'true');

    fireEvent.click(screen.getByRole('button', { name: 'Recharger maintenant' }));
    expect(onReload).toHaveBeenCalledOnce();
  });

  it('désactive une bêta mémorisée et restaure durablement le mode classique', () => {
    window.localStorage.setItem(INTERFACE_MODE_STORAGE_KEY, 'conversation-canvas');
    render(<InterfaceBetaToggle />);

    const toggle = screen.getByRole('switch', {
      name: 'Essayer la nouvelle interface (bêta)',
    });
    expect(toggle).toHaveAttribute('aria-checked', 'true');

    fireEvent.click(toggle);

    expect(window.localStorage.setItem).toHaveBeenLastCalledWith(
      INTERFACE_MODE_STORAGE_KEY,
      'classic',
    );
    expect(toggle).toHaveAttribute('aria-checked', 'false');
    expect(screen.getByRole('button', { name: 'Recharger maintenant' })).toBeInTheDocument();
  });
});
