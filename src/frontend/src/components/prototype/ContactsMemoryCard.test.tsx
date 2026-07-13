import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import type { Contact } from '../../services/api/memory';
import { ContactsMemoryCanvas, ContactsMemoryCard } from './ContactsMemoryCard';

const contact = (id: string, firstName: string, updatedAt: string): Contact => ({
  id,
  first_name: firstName,
  last_name: 'Martin',
  company: 'Synoptïa',
  email: `${firstName.toLowerCase()}@example.test`,
  phone: null,
  notes: `Notes de ${firstName}`,
  tags: ['client'],
  stage: 'client',
  score: 0,
  source: 'local',
  last_interaction: null,
  created_at: updatedAt,
  updated_at: updatedAt,
});

describe('ContactsMemoryCard', () => {
  it('affiche les contacts du store et ouvre la fiche sélectionnée', () => {
    const onOpenContact = vi.fn();
    render(
      <ContactsMemoryCard
        resource={{
          status: 'ready', error: null,
          data: [contact('c1', 'Camille', '2026-07-12'), contact('c2', 'Alex', '2026-07-01')],
        }}
        onRetry={vi.fn()}
        onOpenContact={onOpenContact}
        onOpenClassic={vi.fn()}
      />,
    );

    fireEvent.click(screen.getByText('Camille Martin'));
    expect(onOpenContact).toHaveBeenCalledWith('c1');
    expect(screen.getByText('2 contacts dans la mémoire locale')).toBeInTheDocument();
  });
});

describe('ContactsMemoryCanvas', () => {
  it('recherche localement et ne montre que les données enregistrées', () => {
    render(
      <ContactsMemoryCanvas
        resource={{
          status: 'ready', error: null,
          data: [contact('c1', 'Camille', '2026-07-12'), contact('c2', 'Alex', '2026-07-01')],
        }}
        selectedContactId="c1"
        onSelectContact={vi.fn()}
        onRetry={vi.fn()}
        onOpenClassic={vi.fn()}
      />,
    );

    expect(screen.getByText('Notes de Camille')).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText('Rechercher un contact'), { target: { value: 'Alex' } });
    expect(screen.queryByText('Camille Martin')).not.toBeInTheDocument();
    expect(screen.getAllByText('Alex Martin')).toHaveLength(2);
  });
});
