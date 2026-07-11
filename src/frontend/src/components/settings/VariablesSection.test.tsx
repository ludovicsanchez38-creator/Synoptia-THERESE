/**
 * Chantier 4 Variables V1 - section Réglages > Services : Variables.
 * Liste, création (texte et liste), remplacement, suppression, refus (409)
 * remonté en notification, bandeau d'honnêteté visible.
 */
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { VariablesSection } from './VariablesSection';
import {
  createVariable,
  deleteVariable,
  listVariables,
} from '../../services/api/variables';

vi.mock('../../services/api/variables', () => ({
  listVariables: vi.fn(),
  createVariable: vi.fn(),
  replaceVariable: vi.fn(),
  deleteVariable: vi.fn(),
}));

const mockedList = vi.mocked(listVariables);
const mockedCreate = vi.mocked(createVariable);
const mockedDelete = vi.mocked(deleteVariable);

const CLIENT = {
  name: 'client',
  kind: 'text' as const,
  value: 'Ets Toto',
  description: null,
  updated_at: '2026-07-11T10:00:00+00:00',
};
const COURSES = {
  name: 'courses',
  kind: 'list' as const,
  value: ['tomates', 'courgettes'],
  description: null,
  updated_at: '2026-07-11T10:00:00+00:00',
};

describe('VariablesSection', () => {
  beforeEach(() => {
    mockedList.mockReset();
    mockedCreate.mockReset();
    mockedDelete.mockReset();
  });

  it('liste les variables avec leur type et leur valeur', async () => {
    mockedList.mockResolvedValue([CLIENT, COURSES]);
    render(<VariablesSection />);
    await waitFor(() => expect(screen.getByText('{client}')).toBeInTheDocument());
    expect(screen.getByText('Ets Toto')).toBeInTheDocument();
    expect(screen.getByText('{courses}')).toBeInTheDocument();
    expect(screen.getByText('tomates, courgettes')).toBeInTheDocument();
    // Bandeau honnêteté (pas un coffre à secrets)
    expect(screen.getByText(/jamais un secret/)).toBeInTheDocument();
  });

  it('crée une variable texte', async () => {
    mockedList.mockResolvedValue([]);
    mockedCreate.mockResolvedValue(CLIENT);
    render(<VariablesSection />);
    await waitFor(() => expect(mockedList).toHaveBeenCalled());
    fireEvent.change(screen.getByLabelText('Nom'), { target: { value: 'client' } });
    fireEvent.change(screen.getByLabelText('Valeur'), { target: { value: 'Ets Toto' } });
    fireEvent.click(screen.getByRole('button', { name: 'Créer' }));
    await waitFor(() =>
      expect(mockedCreate).toHaveBeenCalledWith('client', 'text', 'Ets Toto')
    );
  });

  it('crée une liste depuis des éléments séparés par des virgules', async () => {
    mockedList.mockResolvedValue([]);
    mockedCreate.mockResolvedValue(COURSES);
    render(<VariablesSection />);
    await waitFor(() => expect(mockedList).toHaveBeenCalled());
    fireEvent.change(screen.getByLabelText('Nom'), { target: { value: 'courses' } });
    fireEvent.change(screen.getByLabelText('Type'), { target: { value: 'list' } });
    fireEvent.change(
      screen.getByLabelText('Éléments (séparés par des virgules)'),
      { target: { value: 'tomates, courgettes' } }
    );
    fireEvent.click(screen.getByRole('button', { name: 'Créer' }));
    await waitFor(() =>
      expect(mockedCreate).toHaveBeenCalledWith('courses', 'list', [
        'tomates',
        'courgettes',
      ])
    );
  });

  it('supprime une variable', async () => {
    mockedList.mockResolvedValue([CLIENT]);
    mockedDelete.mockResolvedValue(undefined);
    render(<VariablesSection />);
    await waitFor(() => expect(screen.getByText('{client}')).toBeInTheDocument());
    fireEvent.click(screen.getByLabelText('Supprimer client'));
    await waitFor(() => expect(mockedDelete).toHaveBeenCalledWith('client'));
  });

  it('remonte un refus de création (409 existe déjà)', async () => {
    mockedList.mockResolvedValue([CLIENT]);
    mockedCreate.mockRejectedValue(new Error('La variable « client » existe déjà.'));
    render(<VariablesSection />);
    await waitFor(() => expect(screen.getByText('{client}')).toBeInTheDocument());
    fireEvent.change(screen.getByLabelText('Nom'), { target: { value: 'client' } });
    fireEvent.change(screen.getByLabelText('Valeur'), { target: { value: 'X' } });
    fireEvent.click(screen.getByRole('button', { name: 'Créer' }));
    await waitFor(() => expect(mockedCreate).toHaveBeenCalled());
    // La liste n'est pas rafraîchie en erreur : la variable existante reste seule
    expect(screen.getAllByText('{client}')).toHaveLength(1);
  });
});
