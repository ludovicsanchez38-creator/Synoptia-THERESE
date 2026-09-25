/**
 * P-133 (persona Nathalie, cycle 13) : impossible de poser une relance datée
 * sur un prospect sans boîte mail. Le moteur accepte `next_follow_up` en
 * création et en modification, le brief de l'Accueil le lit ; aucun
 * formulaire ne l'écrivait.
 */
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import type { Contact } from '../../services/api';
import { useContactsStore } from '../../stores/contactsStore';
import { ContactModal } from './ContactModal';

const KARIM = {
  id: 'c-karim', first_name: 'Karim', last_name: 'Benali', company: null, email: null, phone: '06 00 00 00 00',
  address: null, notes: null, tags: [], stage: 'discovery', score: 60, source: null, last_interaction: null,
  created_at: '2026-09-20T09:00:00', updated_at: '2026-09-20T09:00:00', next_follow_up: '2026-10-01T09:00:00',
} as Contact;

const createContact = vi.fn();
const updateContact = vi.fn();

describe('P-133 : une relance datée depuis la fiche', () => {
  beforeEach(() => {
    createContact.mockReset().mockResolvedValue(undefined);
    updateContact.mockReset().mockResolvedValue(undefined);
    useContactsStore.setState({ createContact, updateContact });
  });
  afterEach(() => cleanup());

  it('à la création, la date de relance part avec la fiche', async () => {
    render(<ContactModal isOpen onClose={vi.fn()} />);
    fireEvent.change(screen.getByLabelText('Prénom'), { target: { value: 'Karim' } });
    fireEvent.change(screen.getByLabelText('Prochaine relance'), { target: { value: '2026-10-01' } });
    fireEvent.click(screen.getByRole('button', { name: /créer|enregistrer|ajouter/i }));
    await waitFor(() => expect(createContact).toHaveBeenCalledTimes(1));
    expect(createContact.mock.calls[0][0]).toMatchObject({ next_follow_up: '2026-10-01' });
  });

  it('en modification, la date lue s’affiche et peut s’effacer', async () => {
    render(<ContactModal isOpen onClose={vi.fn()} contact={KARIM} />);
    const champ = screen.getByLabelText('Prochaine relance') as HTMLInputElement;
    expect(champ.value).toBe('2026-10-01');
    fireEvent.change(champ, { target: { value: '' } });
    fireEvent.click(screen.getByRole('button', { name: /mettre à jour/i }));
    await waitFor(() => expect(updateContact).toHaveBeenCalledTimes(1));
    expect(updateContact.mock.calls[0][1]).toMatchObject({ next_follow_up: null });
  });
});
