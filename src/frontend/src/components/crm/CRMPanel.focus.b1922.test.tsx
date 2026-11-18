/**
 * B-1922 : « Nouveau contact CRM » et « Nouvelle activité CRM » sont
 * aria-modal sans déplacer le focus ni le retenir. Échap reste dans la pile.
 */
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, expect, it, vi } from 'vitest';
import { useCRMStore } from '../../stores/crmStore';
import { useContactsStore } from '../../stores/contactsStore';
import { _clearEscapeHandlers, runTopEscapeHandler } from '../../lib/escapeStack';

const CONTACT = {
  id: 'c-marie', first_name: 'Marie', last_name: 'Curie', company: null, email: null,
  phone: null, address: null, notes: null, tags: null, source: null, stage: 'contact',
  score: 50, last_interaction: null, created_at: '2026-09-01T10:00:00',
  updated_at: '2026-09-01T10:00:00',
};

vi.mock('../../services/api', async () => {
  const reel = await vi.importActual<typeof import('../../services/api')>('../../services/api');
  return { ...reel, listProjects: vi.fn().mockResolvedValue([]), listActivities: vi.fn().mockResolvedValue([]) };
});
vi.mock('../../services/api/prestations', async () => {
  const reel = await vi.importActual<typeof import('../../services/api/prestations')>('../../services/api/prestations');
  return { ...reel, listerLesPrestations: vi.fn().mockResolvedValue([]) };
});

import { CRMPanel } from './CRMPanel';

beforeEach(() => {
  _clearEscapeHandlers();
  useCRMStore.setState({ projects: [], activeTab: 'pipeline' });
  useContactsStore.setState({
    contacts: [],
    selectedContactId: null,
    truncated: false,
    loaded: true,
    fetchContacts: vi.fn().mockResolvedValue(undefined),
  });
});
afterEach(() => _clearEscapeHandlers());

async function leFocusResteDans(dialogue: HTMLElement) {
  await waitFor(() => expect(dialogue).toContainElement(document.activeElement as HTMLElement));
  const annuler = screen.getByRole('button', { name: 'Annuler' });
  annuler.focus();
  fireEvent.keyDown(document, { key: 'Tab' });
  expect(dialogue).toContainElement(document.activeElement as HTMLElement);
  expect(document.activeElement).not.toBe(annuler);
}

it('B-1922 : Nouveau contact prend le focus et le garde', async () => {
  render(<CRMPanel standalone />);
  const ouvrir = await screen.findByRole('button', { name: /Nouveau contact/i });
  ouvrir.focus();
  fireEvent.click(ouvrir);
  const dialogue = await screen.findByRole('dialog', { name: 'Nouveau contact CRM' });
  await leFocusResteDans(dialogue);
  expect(ouvrir.closest('[inert]')).not.toBeNull();
  expect(runTopEscapeHandler()).toBe(true);
  await waitFor(() => expect(screen.queryByRole('dialog', { name: 'Nouveau contact CRM' })).toBeNull());
});

it('B-1922 : Nouvelle activité prend le focus et le garde', async () => {
  useCRMStore.setState({ activeTab: 'activities' });
  useContactsStore.setState({ contacts: [CONTACT as never], selectedContactId: 'c-marie' });
  render(<CRMPanel standalone />);
  const ouvrir = await screen.findByRole('button', { name: /Ajouter une activité/i });
  ouvrir.focus();
  fireEvent.click(ouvrir);
  const dialogue = await screen.findByRole('dialog', { name: 'Nouvelle activité CRM' });
  await leFocusResteDans(dialogue);
  expect(ouvrir.closest('[inert]')).not.toBeNull();
  expect(runTopEscapeHandler()).toBe(true);
  await waitFor(() => expect(screen.queryByRole('dialog', { name: 'Nouvelle activité CRM' })).toBeNull());
});
