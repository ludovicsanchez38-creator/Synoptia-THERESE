/** B-1726 : la bibliothèque ouverte est un vrai dialogue modal. */
import { act, cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

vi.mock('../memory/ContactModal', () => ({ ContactModal: () => null }));
vi.mock('../memory/ProjectModal', () => ({ ProjectModal: () => null }));
vi.mock('../settings/SettingsModal', () => ({ SettingsModal: () => null }));
vi.mock('../board/BoardPanel', () => ({ BoardPanel: () => null }));
vi.mock('../atelier/AtelierPanel', () => ({ AtelierPanel: () => null }));
vi.mock('../prompts/PromptLibrary', () => ({
  PromptLibrary: ({ onClose }: { onClose: () => void }) => (
    <><input aria-label="Rechercher un prompt" /><button onClick={onClose}>Fermer la bibliothèque</button></>
  ),
}));

import { usePanelStore } from '../../stores/panelStore';
import { PanelContainer } from './PanelContainer';

describe('B-1726 : bibliothèque modale', () => {
  beforeEach(() => {
    usePanelStore.setState({ showPromptLibrary: false, showSaveCommand: false, saveCommandData: null });
  });
  afterEach(() => {
    cleanup();
    act(() => usePanelStore.setState({ showPromptLibrary: false }));
  });

  it('isole le fond, piège le clavier et restitue le focus à la fermeture', async () => {
    render(<><button type="button">Déclencheur</button><PanelContainer onUserCommandsRefresh={() => {}} /></>);
    const declencheur = screen.getByRole('button', { name: 'Déclencheur' });
    declencheur.focus();
    act(() => usePanelStore.getState().openPromptLibrary());

    const dialogue = await screen.findByRole('dialog', { name: 'Bibliothèque de prompts' });
    expect(dialogue).toHaveAttribute('aria-modal', 'true');
    expect(declencheur.closest('[inert]')).not.toBeNull();
    expect(dialogue).toContainElement(document.activeElement as HTMLElement);

    fireEvent.keyDown(document, { key: 'Escape' });
    await waitFor(() => expect(screen.queryByRole('dialog', { name: 'Bibliothèque de prompts' })).toBeNull());
    expect(declencheur).toHaveFocus();
    expect(declencheur.closest('[inert]')).toBeNull();
  });
});
