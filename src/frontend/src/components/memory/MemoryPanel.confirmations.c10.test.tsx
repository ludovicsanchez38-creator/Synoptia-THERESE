/** B-941 : les confirmations Contacts/RGPD sont de vrais dialogues clavier. */
import { act, fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import type { Contact } from '../../services/api';
import { useContactsStore } from '../../stores/contactsStore';
import { useStatusStore } from '../../stores/statusStore';
import { _clearEscapeHandlers, runTopEscapeHandler } from '../../lib/escapeStack';

const api = vi.hoisted(() => ({
  listContacts: vi.fn(), deleteContactWithCascade: vi.fn(), anonymizeContact: vi.fn(),
  exportContactRGPD: vi.fn(), renewContactConsent: vi.fn(),
}));
vi.mock('../../services/api/memory', async () => ({
  ...await vi.importActual<typeof import('../../services/api/memory')>('../../services/api/memory'),
  listContacts: api.listContacts,
}));
vi.mock('../../services/api', async () => ({
  ...await vi.importActual<typeof import('../../services/api')>('../../services/api'),
  ...api,
  getRGPDStats: vi.fn().mockResolvedValue(null),
}));
// Préserver les vrais hooks, notamment useDialogFocusTrap. Seul le masquage
// des noms est neutralisé, comme dans les fixtures Contacts existantes.
vi.mock('../../hooks', async () => ({
  ...await vi.importActual<typeof import('../../hooks')>('../../hooks'),
  useDemoMask: () => ({ enabled: false, maskContact: (c: Contact) => c, populateMap: vi.fn() }),
}));

import { MemoryPanel } from './MemoryPanel';

const contact: Contact = {
  id: 'contact-c10', first_name: 'Sophie', last_name: 'Garcia', company: null,
  email: 'sophie@example.fr', phone: null, address: null, notes: null, tags: [],
  stage: 'contact', score: 0, source: null, last_interaction: null, scope: 'global',
  created_at: '2026-09-01T00:00:00Z', updated_at: '2026-09-01T00:00:00Z',
};

const parcours = [
  { action: 'suppression', titre: 'Supprimer le contact ?', menu: null, confirmer: 'Supprimer' },
  { action: 'export', titre: 'Export RGPD', menu: 'Exporter (Art. 20)', confirmer: 'Exporter' },
  { action: 'anonymisation', titre: 'Anonymisation RGPD', menu: 'Anonymiser (Art. 17)', confirmer: 'Anonymiser' },
  { action: 'renouvellement', titre: 'Renouveler le consentement', menu: 'Renouveler consentement', confirmer: 'Renouveler' },
] as const;

async function ouvrirLaConfirmation(cas: typeof parcours[number]) {
  render(<MemoryPanel standalone />);
  const declencheur = await screen.findByRole('button', {
    name: cas.menu ? 'Actions RGPD' : 'Supprimer Sophie Garcia',
  });
  declencheur.focus();
  fireEvent.click(declencheur);
  if (cas.menu) {
    const commande = await screen.findByRole('button', { name: cas.menu });
    commande.focus();
    fireEvent.click(commande);
  }
  await screen.findByRole('heading', { name: cas.titre });
  return { declencheur, annuler: screen.getByRole('button', { name: 'Annuler' }) };
}

function aucuneMutation() {
  expect(api.deleteContactWithCascade).not.toHaveBeenCalled();
  expect(api.anonymizeContact).not.toHaveBeenCalled();
  expect(api.renewContactConsent).not.toHaveBeenCalled();
  expect(api.exportContactRGPD).not.toHaveBeenCalled();
}

describe('B-941 : confirmations Contacts et RGPD', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    _clearEscapeHandlers();
    api.listContacts.mockResolvedValue([contact]);
    api.deleteContactWithCascade.mockResolvedValue({ deleted: true });
    api.anonymizeContact.mockResolvedValue(undefined);
    api.exportContactRGPD.mockResolvedValue({});
    api.renewContactConsent.mockResolvedValue({ new_expiration: '2029-09-22' });
    useContactsStore.setState({
      contacts: [], searchResults: null, loading: false, loaded: false,
      error: null, selectedContactId: null, truncated: false,
    });
    useStatusStore.setState({ notifications: [] });
  });

  it.each(parcours)('$action : expose un dialogue nommé et modal', async (cas) => {
    await ouvrirLaConfirmation(cas);
    aucuneMutation();
    expect(screen.getByRole('dialog', { name: cas.titre })).toHaveAttribute('aria-modal', 'true');
  });

  it.each(parcours)('$action : pose le focus sur une commande ou un champ de confirmation', async (cas) => {
    const { annuler } = await ouvrirLaConfirmation(cas);
    aucuneMutation();
    const cibleInitiale = cas.action === 'anonymisation'
      ? screen.getByRole('textbox', { name: /Raison de l'anonymisation/ })
      : annuler;
    expect(cibleInitiale).toHaveFocus();
  });

  it.each(parcours)('$action : boucle aux deux bords de la confirmation', async (cas) => {
    const { annuler } = await ouvrirLaConfirmation(cas);
    const premier = cas.action === 'anonymisation'
      ? screen.getByRole('textbox', { name: /Raison de l'anonymisation/ })
      : annuler;
    if (cas.action === 'anonymisation') {
      fireEvent.change(premier, { target: { value: 'Demande du contact' } });
    }
    // Le panneau expose aussi un export VCF : viser le groupe d'actions de
    // la confirmation, identifiable par Annuler même avant la correction ARIA.
    const confirmer = within(annuler.parentElement!).getByRole('button', { name: cas.confirmer });
    premier.focus();
    fireEvent.keyDown(premier, { key: 'Tab', shiftKey: true });
    expect(confirmer).toHaveFocus();
    fireEvent.keyDown(confirmer, { key: 'Tab' });
    expect(premier).toHaveFocus();
    aucuneMutation();
  });

  it.each(parcours)('$action : restaure le focus après annulation', async (cas) => {
    const { declencheur, annuler } = await ouvrirLaConfirmation(cas);
    annuler.focus();
    fireEvent.click(annuler);
    await waitFor(() => expect(screen.queryByRole('heading', { name: cas.titre })).not.toBeInTheDocument());
    // Les commandes RGPD du menu disparaissent après le clic : le point de
    // reprise doit être le bouton Actions RGPD toujours monté dans la liste.
    expect(declencheur).toHaveFocus();
    aucuneMutation();
  });

  it.each(parcours)('$action : isole le fond et le réactive à la fermeture', async (cas) => {
    const { declencheur, annuler } = await ouvrirLaConfirmation(cas);
    const dialogue = screen.getByRole('dialog', { name: cas.titre });
    expect(declencheur.closest('[inert]')).not.toBeNull();
    expect(declencheur.closest('[aria-hidden="true"]')).not.toBeNull();
    expect(dialogue.closest('[inert]')).toBeNull();
    fireEvent.click(annuler);
    await waitFor(() => expect(dialogue).not.toBeInTheDocument());
    expect(declencheur.closest('[inert]')).toBeNull();
    expect(declencheur.closest('[aria-hidden="true"]')).toBeNull();
    expect(declencheur).toHaveFocus();
    aucuneMutation();
  });

  it.each(parcours)('$action : Échap ferme uniquement la confirmation et rend le focus', async (cas) => {
    const { declencheur } = await ouvrirLaConfirmation(cas);
    const dialogue = screen.getByRole('dialog', { name: cas.titre });
    act(() => { expect(runTopEscapeHandler()).toBe(true); });
    await waitFor(() => expect(dialogue).not.toBeInTheDocument());
    expect(screen.getByTestId('memory-panel')).toBeInTheDocument();
    expect(declencheur).toHaveFocus();
    expect(runTopEscapeHandler()).toBe(false);
    aucuneMutation();
  });

  it.each(parcours)('$action : garde la confirmation et le clavier confinés pendant l’appel', async (cas) => {
    const mutation = cas.action === 'suppression' ? api.deleteContactWithCascade
      : cas.action === 'export' ? api.exportContactRGPD
        : cas.action === 'anonymisation' ? api.anonymizeContact : api.renewContactConsent;
    mutation.mockReturnValue(new Promise(() => {}));
    const { annuler } = await ouvrirLaConfirmation(cas);
    const dialogue = screen.getByRole('dialog', { name: cas.titre });
    if (cas.action === 'anonymisation') {
      fireEvent.change(within(dialogue).getByRole('textbox'), { target: { value: 'Demande du contact' } });
    }
    fireEvent.click(within(dialogue).getByRole('button', { name: cas.confirmer }));
    expect(dialogue).toHaveAttribute('aria-busy', 'true');
    expect(dialogue).toHaveFocus();
    expect(annuler).toBeDisabled();
    const tab = new KeyboardEvent('keydown', { key: 'Tab', bubbles: true, cancelable: true });
    fireEvent(dialogue, tab);
    expect(tab.defaultPrevented).toBe(true);
    expect(dialogue).toHaveFocus();
    act(() => { expect(runTopEscapeHandler()).toBe(true); });
    fireEvent.click(dialogue.parentElement!);
    expect(dialogue).toBeInTheDocument();
    expect(mutation).toHaveBeenCalledTimes(1);
  });

  it('supprime uniquement après confirmation explicite', async () => {
    await ouvrirLaConfirmation(parcours[0]);
    aucuneMutation();
    fireEvent.click(screen.getByRole('button', { name: 'Supprimer' }));
    await waitFor(() => expect(api.deleteContactWithCascade).toHaveBeenCalledExactlyOnceWith('contact-c10', true));
  });

  it('reprend sur la recherche après suppression du dernier contact', async () => {
    await ouvrirLaConfirmation(parcours[0]);
    const dialogue = screen.getByRole('dialog', { name: 'Supprimer le contact ?' });
    fireEvent.click(within(dialogue).getByRole('button', { name: 'Supprimer' }));
    await waitFor(() => expect(dialogue).not.toBeInTheDocument());
    expect(screen.getByRole('searchbox', { name: 'Retrouver un contact' })).toHaveFocus();
  });

  it('ne reprend pas le focus si les Contacts ont fermé pendant la suppression', async () => {
    let terminer!: () => void;
    api.deleteContactWithCascade.mockReturnValue(new Promise<void>((resolve) => { terminer = resolve; }));
    const vue = render(<><button type="button">Autre vue</button><MemoryPanel isOpen /></>);
    const declencheur = await screen.findByRole('button', { name: 'Supprimer Sophie Garcia' });
    declencheur.focus();
    fireEvent.click(declencheur);
    const dialogue = await screen.findByRole('dialog', { name: 'Supprimer le contact ?' });
    fireEvent.click(within(dialogue).getByRole('button', { name: 'Supprimer' }));
    vue.rerender(<><button type="button">Autre vue</button><MemoryPanel isOpen={false} /></>);
    const autreVue = screen.getByRole('button', { name: 'Autre vue' });
    autreVue.focus();
    await act(async () => { terminer(); });
    expect(autreVue).toHaveFocus();
  });

  it('exige une raison et une confirmation explicite avant anonymisation', async () => {
    await ouvrirLaConfirmation(parcours[2]);
    aucuneMutation();
    const confirmer = screen.getByRole('button', { name: 'Anonymiser' });
    expect(confirmer).toBeDisabled();
    fireEvent.change(screen.getByRole('textbox', { name: /Raison de l'anonymisation/ }), {
      target: { value: 'Demande du contact' },
    });
    aucuneMutation();
    fireEvent.click(confirmer);
    await waitFor(() => expect(api.anonymizeContact).toHaveBeenCalledExactlyOnceWith('contact-c10', 'Demande du contact'));
  });

  it.each([parcours[2], parcours[3]])('$action : retrouve le bouton RGPD après le rechargement réussi', async (cas) => {
    const { annuler } = await ouvrirLaConfirmation(cas);
    const dialogue = screen.getByRole('dialog', { name: cas.titre });
    let finirChargement!: (contacts: Contact[]) => void;
    api.listContacts.mockReturnValueOnce(new Promise<Contact[]>((resolve) => { finirChargement = resolve; }));
    if (cas.action === 'anonymisation') {
      fireEvent.change(within(dialogue).getByRole('textbox'), { target: { value: 'Demande du contact' } });
    }
    fireEvent.click(within(annuler.parentElement!).getByRole('button', { name: cas.confirmer }));
    await waitFor(() => expect(api.listContacts).toHaveBeenCalledTimes(2));
    await act(async () => { finirChargement([contact]); });
    await waitFor(() => expect(dialogue).not.toBeInTheDocument());
    expect(screen.getByRole('button', { name: 'Actions RGPD' })).toHaveFocus();
  });
});
