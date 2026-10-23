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

it('B-1056 : la commande reçoit le focus, le piège et nomme sa fermeture', async () => {
  usePanelStore.setState({ showSaveCommand: true, saveCommandData: { userPrompt: 'Résume ce document.', assistantContent: 'Résumé factice' } });
  render(<PanelContainer onUserCommandsRefresh={vi.fn()} />);
  const dialogue = await screen.findByRole('dialog', { name: 'Enregistrer comme commande' });
  expect(dialogue).toContainElement(document.activeElement as HTMLElement);
  expect(screen.getByRole('button', { name: 'Fermer la commande' })).toBeInTheDocument();
});

it.each(['Résumer ce courrier', 'Relire le devis', 'Préparer un rendez-vous', 'Expliquer la facture', 'Classer cette note', 'Lister les travaux', 'Traduire le paragraphe', 'Comparer les offres', 'Rédiger une relance', 'Préparer la visite'])('Rejeu B-1056 : %s', async (userPrompt) => {
  usePanelStore.setState({ showPromptLibrary: false, showSaveCommand: true, saveCommandData: { userPrompt, assistantContent: 'Réponse factice capturée' } });
  render(<PanelContainer onUserCommandsRefresh={vi.fn()} />);
  const dialogue = await screen.findByRole('dialog', { name: 'Enregistrer comme commande' });
  expect(dialogue).toContainElement(document.activeElement as HTMLElement);
  expect(screen.getByRole('button', { name: 'Fermer la commande' })).toHaveAttribute('type', 'button');
  fireEvent.keyDown(document, { key: 'Escape' });
  await waitFor(() => expect(screen.queryByRole('dialog', { name: 'Enregistrer comme commande' })).toBeNull());
});
