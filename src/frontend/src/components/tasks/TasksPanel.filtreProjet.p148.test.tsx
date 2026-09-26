/**
 * P-148, recette : « Voir les tâches » d'un projet ouvre la vue Tâches filtrée
 * sur ce projet, mais le filtre vivait replié derrière « Filtrer » : la liste
 * était filtrée sans que rien à l'écran ne le dise. Un filtre de projet posé
 * (à l'ouverture ou pendant que la vue est affichée) déplie les filtres, et
 * se retire d'un geste.
 */
import { act, cleanup, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { maskProject } from '../../lib/demoMask';
import { useDemoStore } from '../../stores/demoStore';
import { useTaskStore } from '../../stores/taskStore';

const api = vi.hoisted(() => ({
  listTasks: vi.fn(), listProjects: vi.fn(), listContacts: vi.fn(), getProject: vi.fn(),
}));
vi.mock('../../services/api', async () => {
  const actual = await vi.importActual<Record<string, unknown>>('../../services/api');
  return { ...actual, ...api };
});

import { TasksPanel } from './TasksPanel';

function poser(filterProjectId: string | null) {
  useTaskStore.setState({
    tasks: [], currentTaskId: null, isTaskFormOpen: false, viewMode: 'list',
    filterStatus: null, filterPriority: null, filterProjectId,
  } as never);
}

describe('P-148 : un filtre de projet se voit', () => {
  beforeEach(() => {
    Object.values(api).forEach((mock) => mock.mockReset());
    api.listTasks.mockResolvedValue([]);
    api.listProjects.mockResolvedValue([{ id: 'p-cuisine', name: 'Cuisine Roux' }]);
    api.listContacts.mockResolvedValue([]);
    poser(null);
  });
  afterEach(() => cleanup());

  it('ouverte filtrée sur un projet, la vue montre le filtre', async () => {
    poser('p-cuisine');
    render(<TasksPanel isOpen onClose={() => {}} standalone />);
    const filtre = await screen.findByRole('combobox', { name: 'Filtrer par projet' });
    await waitFor(() => expect(filtre).toHaveValue('p-cuisine'));
    expect(screen.getByRole('button', { name: 'Réinitialiser' })).toBeInTheDocument();
  });

  it('sans filtre, les filtres restent repliés', async () => {
    render(<TasksPanel isOpen onClose={() => {}} standalone />);
    await act(async () => { await Promise.resolve(); });
    expect(screen.queryByRole('combobox', { name: 'Filtrer par projet' })).toBeNull();
  });

  it('revue P-148, constat 1 : en démonstration, le filtre déplié porte le pseudonyme, jamais le vrai nom', async () => {
    useDemoStore.setState({ enabled: true, replacementMap: new Map() });
    try {
      poser('p-cuisine');
      render(<TasksPanel isOpen onClose={() => {}} standalone />);
      const filtre = await screen.findByRole('combobox', { name: 'Filtrer par projet' });
      await waitFor(() => expect(filtre).toHaveValue('p-cuisine'));
      expect(screen.queryByText('Cuisine Roux')).toBeNull();
      const pseudonyme = maskProject({ id: 'p-cuisine', name: 'Cuisine Roux' }).name;
      expect((filtre as HTMLSelectElement).selectedOptions[0]).toHaveTextContent(pseudonyme);
    } finally {
      useDemoStore.setState({ enabled: false, replacementMap: new Map() });
    }
  });

  /**
   * Revue P-148, constat 9 : la liste des projets s'arrête aux 50 derniers
   * modifiés. Un projet filtré absent de la liste faisait retomber le
   * sélecteur natif sur « Tous les projets » alors que la liste était filtrée.
   */
  it('revue P-148, constat 9 : un projet filtré hors des 50 premiers est lu et nommé dans le sélecteur', async () => {
    api.getProject.mockResolvedValue({ id: 'p-ancien', name: 'Grange Villeneuve' });
    poser('p-ancien');
    render(<TasksPanel isOpen onClose={() => {}} standalone />);
    const filtre = await screen.findByRole('combobox', { name: 'Filtrer par projet' });
    await waitFor(() => expect(filtre).toHaveValue('p-ancien'));
    // Le nom arrive avec la lecture à part ; jusque-là, « Projet filtré ».
    await waitFor(() => expect((filtre as HTMLSelectElement).selectedOptions[0]).toHaveTextContent('Grange Villeneuve'));
    expect(api.getProject).toHaveBeenCalledWith('p-ancien');
    // Le projet de la liste reste proposé.
    expect(screen.getByRole('option', { name: 'Cuisine Roux' })).toBeInTheDocument();
  });

  it('revue P-148, constat 9 : sans liste de projets lisible, le filtre posé reste visible', async () => {
    api.listProjects.mockResolvedValue([]);
    api.getProject.mockRejectedValue(new Error('réseau'));
    poser('p-ancien');
    render(<TasksPanel isOpen onClose={() => {}} standalone />);
    const filtre = await screen.findByRole('combobox', { name: 'Filtrer par projet' });
    await waitFor(() => expect(filtre).toHaveValue('p-ancien'));
    expect((filtre as HTMLSelectElement).selectedOptions[0]).toHaveTextContent('Projet filtré');
    expect(screen.getByRole('button', { name: 'Réinitialiser' })).toBeInTheDocument();
  });

  it('revue P-148, constat 9 : en démonstration, le projet lu hors de la liste porte son pseudonyme', async () => {
    useDemoStore.setState({ enabled: true, replacementMap: new Map() });
    try {
      api.getProject.mockResolvedValue({ id: 'p-ancien', name: 'Grange Villeneuve' });
      poser('p-ancien');
      render(<TasksPanel isOpen onClose={() => {}} standalone />);
      const filtre = await screen.findByRole('combobox', { name: 'Filtrer par projet' });
      const pseudonyme = maskProject({ id: 'p-ancien', name: 'Grange Villeneuve' }).name;
      await waitFor(() => expect((filtre as HTMLSelectElement).selectedOptions[0]).toHaveTextContent(pseudonyme));
      expect(screen.queryByText(/Grange|Villeneuve/)).toBeNull();
    } finally {
      useDemoStore.setState({ enabled: false, replacementMap: new Map() });
    }
  });

  it('un projet filtré présent dans la liste n’est pas relu', async () => {
    poser('p-cuisine');
    render(<TasksPanel isOpen onClose={() => {}} standalone />);
    const filtre = await screen.findByRole('combobox', { name: 'Filtrer par projet' });
    await waitFor(() => expect(filtre).toHaveValue('p-cuisine'));
    expect(api.getProject).not.toHaveBeenCalled();
  });

  it('un filtre de projet posé pendant que la vue est affichée déplie les filtres', async () => {
    render(<TasksPanel isOpen onClose={() => {}} standalone />);
    await act(async () => { await Promise.resolve(); });
    act(() => { useTaskStore.setState({ filterProjectId: 'p-cuisine' }); });
    expect(await screen.findByRole('combobox', { name: 'Filtrer par projet' })).toBeInTheDocument();
  });
});
