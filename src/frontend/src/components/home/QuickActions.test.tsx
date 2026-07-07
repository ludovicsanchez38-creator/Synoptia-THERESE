/**
 * Tests QuickActions (Accueil) - lanceur d'actions rapides depuis le
 * registre unique (`actionRegistry`). Vérifie surtout la carte D4
 * « Rédiger un document » : rendu + déclenchement de `documents.new`
 * (navigation vers la vue Documents + demande d'ouverture de la modale).
 */
import { fireEvent, render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it } from 'vitest';
import { QuickActions } from './QuickActions';
import { useNavigationStore } from '../../stores/navigationStore';
import { useDocumentStore } from '../../stores/documentStore';

beforeEach(() => {
  useNavigationStore.setState({ activeView: 'home', history: [] });
  useDocumentStore.setState({ createModalRequested: false });
});

describe('QuickActions', () => {
  it('rend les cartes attendues, dont « Rédiger un document » (D4)', () => {
    render(<QuickActions />);
    expect(screen.getByRole('button', { name: 'Nouvelle conversation' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Rédiger un document' })).toBeInTheDocument();
  });

  it('« Rédiger un document » navigue vers la vue Documents et pose la demande d\'ouverture de la modale', () => {
    render(<QuickActions />);
    fireEvent.click(screen.getByRole('button', { name: 'Rédiger un document' }));

    expect(useNavigationStore.getState().activeView).toBe('documents');
    expect(useDocumentStore.getState().createModalRequested).toBe(true);
  });
});
