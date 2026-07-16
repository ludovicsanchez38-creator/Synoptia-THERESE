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

  it("affiche la nouvelle interface active par défaut et permet de choisir l'ancienne", () => {
    const onReload = vi.fn();
    render(<InterfaceBetaToggle onReload={onReload} />);

    const toggle = screen.getByRole('switch', {
      name: 'Essayer la nouvelle interface',
    });
    expect(toggle).toHaveAttribute('aria-checked', 'true');

    fireEvent.click(toggle);

    expect(window.localStorage.setItem).toHaveBeenCalledWith(
      INTERFACE_MODE_STORAGE_KEY,
      'classic',
    );
    expect(toggle).toHaveAttribute('aria-checked', 'false');

    fireEvent.click(screen.getByRole('button', { name: 'Recharger maintenant' }));
    expect(onReload).toHaveBeenCalledOnce();
  });

  it('réactive la nouvelle interface depuis un choix classique mémorisé', () => {
    window.localStorage.setItem(INTERFACE_MODE_STORAGE_KEY, 'classic');
    render(<InterfaceBetaToggle />);

    const toggle = screen.getByRole('switch', {
      name: 'Essayer la nouvelle interface',
    });
    expect(toggle).toHaveAttribute('aria-checked', 'false');

    fireEvent.click(toggle);

    expect(window.localStorage.setItem).toHaveBeenLastCalledWith(
      INTERFACE_MODE_STORAGE_KEY,
      'conversation-canvas',
    );
    expect(toggle).toHaveAttribute('aria-checked', 'true');
    expect(screen.getByRole('button', { name: 'Recharger maintenant' })).toBeInTheDocument();
  });
});
