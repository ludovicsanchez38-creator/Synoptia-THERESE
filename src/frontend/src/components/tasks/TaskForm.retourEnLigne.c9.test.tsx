/**
 * B-872 (cycle 9) : « Retour » sur le formulaire de tâche demandait
 * « Abandonner les modifications ? » par `confirm()` natif, non garanti sous
 * Tauri et hors charte (règle D62/D106 : confirmation en ligne).
 */
import { fireEvent, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

vi.mock('../../services/api', async (importOriginal) => ({
  ...(await importOriginal<object>()),
  listProjects: vi.fn().mockResolvedValue([]),
  listContacts: vi.fn().mockResolvedValue([]),
}));

import { useTaskStore } from '../../stores/taskStore';
import { TaskForm } from './TaskForm';

describe('TaskForm - B-872, abandonner se confirme en ligne', () => {
  beforeEach(() => {
    useTaskStore.setState({ tasks: [], currentTaskId: null, isTaskFormOpen: true, searchQuery: '' });
    vi.stubGlobal('confirm', vi.fn(() => { throw new Error('confirm() natif interdit'); }));
  });
  afterEach(() => vi.unstubAllGlobals());

  it('« Retour » pose la question dans le formulaire ; « Abandonner » ferme, « Continuer » garde la saisie', () => {
    render(<TaskForm />);
    fireEvent.change(screen.getByLabelText(/Titre/), { target: { value: 'Relancer Ruiz' } });
    fireEvent.click(screen.getByRole('button', { name: 'Retour' }));
    expect(useTaskStore.getState().isTaskFormOpen).toBe(true);
    expect(screen.getByText(/Abandonner les modifications/)).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'Continuer la saisie' }));
    expect(screen.queryByText(/Abandonner les modifications/)).toBeNull();
    expect((screen.getByLabelText(/Titre/) as HTMLInputElement).value).toBe('Relancer Ruiz');

    fireEvent.click(screen.getByRole('button', { name: 'Retour' }));
    fireEvent.click(screen.getByRole('button', { name: 'Abandonner' }));
    expect(useTaskStore.getState().isTaskFormOpen).toBe(false);
  });
});
