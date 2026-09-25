/**
 * B-1391 (persona Zoé, cycle 13, haute) : deux onglets sur la même fiche, le
 * second enregistrement effaçait le premier. Le formulaire envoie la version
 * qu'il a lue (`updated_at`), que le moteur compare avant d'écrire ; un refus
 * s'affiche et la saisie reste dans le formulaire.
 */
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import type { Contact } from '../../services/api';
import { useContactsStore } from '../../stores/contactsStore';
import { ContactModal } from './ContactModal';

const FICHE: Contact = {
  id: 'c-zoe', first_name: 'Zoé', last_name: 'Doubleclic', company: 'Contradiction SARL',
  email: null, phone: null, address: null, notes: null, tags: [], stage: 'contact', score: 60,
  source: null, last_interaction: null, created_at: '2026-09-25T09:00:00', updated_at: '2026-09-25T09:24:45.331408',
} as Contact;

const updateContact = vi.fn();

describe('B-1391 : le formulaire envoie la version qu’il a lue', () => {
  beforeEach(() => {
    updateContact.mockReset().mockResolvedValue(undefined);
    useContactsStore.setState({ updateContact });
  });
  afterEach(() => cleanup());

  it('« Mettre à jour » porte version_lue', async () => {
    render(<ContactModal isOpen onClose={vi.fn()} contact={FICHE} />);
    fireEvent.change(screen.getByLabelText(/Notes/), { target: { value: 'Note saisie dans l’onglet A' } });
    fireEvent.click(screen.getByRole('button', { name: /mettre à jour/i }));
    await waitFor(() => expect(updateContact).toHaveBeenCalledTimes(1));
    expect(updateContact.mock.calls[0][1]).toMatchObject({ version_lue: '2026-09-25T09:24:45.331408' });
  });

  it('un refus « modifiée ailleurs » s’affiche et garde la saisie', async () => {
    updateContact.mockRejectedValueOnce(new Error('Cette fiche a été modifiée ailleurs depuis que tu l’as ouverte.'));
    const onClose = vi.fn();
    render(<ContactModal isOpen onClose={onClose} contact={FICHE} />);
    fireEvent.change(screen.getByLabelText(/Notes/), { target: { value: 'Ma note' } });
    fireEvent.click(screen.getByRole('button', { name: /mettre à jour/i }));
    expect(await screen.findByText(/modifiée ailleurs/)).toBeInTheDocument();
    expect(onClose).not.toHaveBeenCalled();
    expect((screen.getByLabelText(/Notes/) as HTMLTextAreaElement).value).toBe('Ma note');
  });
});
