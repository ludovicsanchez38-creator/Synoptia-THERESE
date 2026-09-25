/**
 * B-1349 (persona Claire, cycle 13) : carnet vide, quatre boutons « Ouvrir
 * Contacts » identiques à l'écran (deux dans la carte, deux dans le panneau)
 * et aucun moyen d'ajouter un contact.
 *
 * L'état vide portait son propre « Ouvrir Contacts » en plus de celui de
 * l'en-tête (carte) ou du pied (panneau). Il propose désormais « Ajouter un
 * contact », qui ouvre le formulaire de création ; chaque surface garde un
 * seul « Ouvrir Contacts ».
 */
import { fireEvent, render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { ContactsMemoryCanvas, ContactsMemoryCard } from './ContactsMemoryCard';
import { usePanelStore } from '../../stores/panelStore';

const vide = { status: 'ready' as const, data: [], error: null };

beforeEach(() => {
  usePanelStore.getState().closeContactModal();
});

describe('carnet vide (B-1349)', () => {
  it('la carte : un seul « Ouvrir Contacts », et « Ajouter un contact »', () => {
    render(<ContactsMemoryCard resource={vide} onRetry={vi.fn()} onOpenContact={vi.fn()} onOpenClassic={vi.fn()} />);
    expect(screen.getAllByRole('button', { name: 'Ouvrir Contacts' })).toHaveLength(1);
    fireEvent.click(screen.getByRole('button', { name: 'Ajouter un contact' }));
    expect(usePanelStore.getState().showContactModal).toBe(true);
    expect(usePanelStore.getState().editingContact).toBeNull();
  });

  it('le panneau : un seul « Ouvrir Contacts », et « Ajouter un contact »', () => {
    render(<ContactsMemoryCanvas resource={vide} selectedContactId={null} onSelectContact={vi.fn()} onRetry={vi.fn()} onOpenClassic={vi.fn()} />);
    expect(screen.getAllByRole('button', { name: 'Ouvrir Contacts' })).toHaveLength(1);
    expect(screen.getByRole('button', { name: 'Ajouter un contact' })).toBeInTheDocument();
  });
});
