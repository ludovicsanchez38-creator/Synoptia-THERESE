/**
 * B-1480 (vérification au navigateur de B-1437, 26/09) : hors e-mail, agenda
 * et document (B-1454), la carte s'intitulait « Confirmer l'action
 * create_contact » et listait les clés brutes (first_name, last_name).
 */
import { render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { useToolConfirmationStore } from '../../stores/toolConfirmationStore';
import { ToolConfirmationCard } from './ToolConfirmationCard';

vi.mock('../../services/api/chat', () => ({ confirmTool: vi.fn() }));

describe('B-1480 : les actions natives se confirment en français', () => {
  beforeEach(() => useToolConfirmationStore.setState({ pending: [] }));

  it('un contact : titre et champs nommés comme à l’écran', () => {
    useToolConfirmationStore.getState().add({
      confirmation_id: 'c-1',
      tool_name: 'create_contact',
      arguments: { first_name: 'Julien', last_name: 'Garnier', email: 'julien.garnier@example.test' },
    });
    render(<ToolConfirmationCard />);
    expect(screen.getByText('Confirmer la création du contact')).toBeInTheDocument();
    expect(screen.getByText(/^Prénom/)).toBeInTheDocument();
    expect(screen.getByText(/^E-mail/)).toBeInTheDocument();
    expect(screen.queryByText(/create_contact|first_name|last_name/)).toBeNull();
  });

  it('un projet et une recherche web ont leur titre', () => {
    useToolConfirmationStore.getState().add({ confirmation_id: 'p-1', tool_name: 'create_project', arguments: { name: 'Cuisine Roux' } });
    useToolConfirmationStore.getState().add({ confirmation_id: 'w-1', tool_name: 'web_search', arguments: { query: 'prix du chêne' } });
    render(<ToolConfirmationCard />);
    expect(screen.getByText('Confirmer la création du projet')).toBeInTheDocument();
    expect(screen.getByText('Confirmer la recherche sur le web')).toBeInTheDocument();
    expect(screen.queryByText(/create_project|web_search/)).toBeNull();
  });

  it('un outil de connecteur : titre lisible, nom complet gardé en détail', () => {
    useToolConfirmationStore.getState().add({
      confirmation_id: 'm-1', tool_name: '43731338__sequentialthinking', arguments: { thought: 'Étape 1' },
    });
    render(<ToolConfirmationCard />);
    expect(screen.getByText('Confirmer l’outil « sequentialthinking » d’un connecteur')).toBeInTheDocument();
    expect(screen.getByText('43731338__sequentialthinking')).toBeInTheDocument();
  });
});
