/**
 * B-1080 : en mode démo, la liste Mémoire passe à ContactModal la fiche déjà
 * masquée (persona fictif). « Mettre à jour » écrivait alors le persona sur la
 * vraie fiche, et l'adresse, les notes et les tags restaient en clair.
 * La fiche se consulte en lecture seule, comme ProjectModal (B-939).
 */
import { act, cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import type { Contact } from '../../services/api';
import { maskContact } from '../../lib/demoMask';
import { useContactsStore } from '../../stores/contactsStore';
import { useDemoStore } from '../../stores/demoStore';
import { ContactModal } from './ContactModal';

// Données synthétiques ; aucun appel réseau.
const REEL: Contact = {
  id: 'contact-demo-c12', first_name: 'Victor', last_name: 'Ruiz',
  company: 'Entreprise Ardent', email: 'victor@example.invalid', phone: '0600000000',
  address: '12 rue des Oliviers, 04100 Manosque', notes: 'Rappeler après le chantier',
  tags: ['chantier-ardent'], stage: 'prospect', score: 20, source: null,
  last_interaction: null, created_at: '2026-09-24T10:00:00Z', updated_at: '2026-09-24T10:00:00Z',
};
const MASQUE = maskContact(REEL);

const updateContact = vi.fn();
const createContact = vi.fn();
const deleteContact = vi.fn();

function ouvrir(contact: Contact | null) {
  render(<ContactModal isOpen onClose={vi.fn()} contact={contact} />);
}

describe('B-1080 : ContactModal en mode démonstration', () => {
  beforeEach(() => {
    updateContact.mockReset().mockResolvedValue(undefined);
    createContact.mockReset().mockResolvedValue(undefined);
    deleteContact.mockReset().mockResolvedValue(undefined);
    useContactsStore.setState({ updateContact, createContact, deleteContact });
  });

  afterEach(() => {
    cleanup();
    useDemoStore.setState({ enabled: false, replacementMap: new Map() });
  });

  it('n’écrit jamais le persona fictif sur la vraie fiche', async () => {
    useDemoStore.setState({ enabled: true });
    ouvrir(MASQUE);
    expect(screen.getByText('Mode démo : lecture seule')).toBeInTheDocument();
    const enregistrer = screen.getByRole('button', { name: /mettre à jour|consulter/i });
    expect(enregistrer).toBeDisabled();
    await act(async () => { fireEvent.click(enregistrer); });
    expect(updateContact).not.toHaveBeenCalled();
    expect(screen.getByLabelText('Prénom')).toBeDisabled();
  });

  it('ne supprime pas la fiche depuis l’aperçu masqué', () => {
    useDemoStore.setState({ enabled: true });
    ouvrir(MASQUE);
    expect(screen.getByRole('button', { name: /supprimer/i })).toBeDisabled();
    expect(deleteContact).not.toHaveBeenCalled();
  });

  it('ne montre ni l’adresse, ni les notes, ni les tags réels', () => {
    useDemoStore.setState({ enabled: true });
    ouvrir(MASQUE);
    expect(screen.queryByDisplayValue(REEL.address as string)).toBeNull();
    expect(screen.queryByDisplayValue(REEL.notes as string)).toBeNull();
    expect(screen.queryByDisplayValue('chantier-ardent')).toBeNull();
  });

  it('hors démo, « Mettre à jour » enregistre toujours la fiche', async () => {
    ouvrir(REEL);
    expect(screen.queryByText('Mode démo : lecture seule')).toBeNull();
    await act(async () => { fireEvent.click(screen.getByRole('button', { name: 'Mettre à jour' })); });
    expect(updateContact).toHaveBeenCalledWith(REEL.id, expect.objectContaining({ first_name: 'Victor' }));
  });
});
