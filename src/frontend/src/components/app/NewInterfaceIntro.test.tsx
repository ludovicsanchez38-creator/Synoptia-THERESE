import { fireEvent, render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { INTERFACE_MODE_STORAGE_KEY } from '../../lib/interfaceMode';
import { installLocalStorageStub } from '../../test/localStorage-stub';
import {
  NewInterfaceIntro,
  NEW_INTERFACE_INTRO_STORAGE_KEY,
} from './NewInterfaceIntro';

describe('NewInterfaceIntro', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    installLocalStorageStub();
  });

  it('présente une seule fois la nouvelle interface avec un dialogue accessible', () => {
    render(
      <>
        <button type="button">Hors dialogue</button>
        <NewInterfaceIntro />
      </>,
    );

    const dialog = screen.getByRole('dialog', { name: 'La nouvelle interface est active' });
    const title = screen.getByRole('heading', { name: 'La nouvelle interface est active' });
    const acknowledge = screen.getByRole('button', { name: 'J’ai compris' });

    expect(dialog).toHaveAttribute('aria-modal', 'true');
    expect(dialog).toHaveAttribute('aria-labelledby', title.id);
    expect(title).toHaveFocus();

    acknowledge.focus();
    fireEvent.keyDown(document, { key: 'Tab' });
    expect(acknowledge).toHaveFocus();
  });

  it.each(['classic', 'conversation-canvas'] as const)(
    "ne s'affiche pas après un choix explicite %s",
    (storedMode) => {
      window.localStorage.setItem(INTERFACE_MODE_STORAGE_KEY, storedMode);
      render(<NewInterfaceIntro />);

      expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
    },
  );

  it('ignore une préférence invalide et présente le nouveau défaut', () => {
    window.localStorage.setItem(INTERFACE_MODE_STORAGE_KEY, 'experimental');
    render(<NewInterfaceIntro />);

    expect(screen.getByRole('dialog', { name: 'La nouvelle interface est active' }))
      .toBeInTheDocument();
  });

  it("ne s'affiche pas si l'introduction a déjà été vue", () => {
    window.localStorage.setItem(NEW_INTERFACE_INTRO_STORAGE_KEY, 'true');
    render(<NewInterfaceIntro />);

    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
  });

  it("mémorise l'acquittement, ferme et ne se réaffiche plus", () => {
    const firstRender = render(<NewInterfaceIntro />);

    fireEvent.click(screen.getByRole('button', { name: 'J’ai compris' }));

    expect(window.localStorage.setItem).toHaveBeenCalledWith(
      NEW_INTERFACE_INTRO_STORAGE_KEY,
      'true',
    );
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();

    firstRender.unmount();
    render(<NewInterfaceIntro />);
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
  });

  it('mémorise aussi la fermeture par Échap', () => {
    render(<NewInterfaceIntro />);

    fireEvent.keyDown(document, { key: 'Escape' });

    expect(window.localStorage.setItem).toHaveBeenCalledWith(
      NEW_INTERFACE_INTRO_STORAGE_KEY,
      'true',
    );
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
  });
});
