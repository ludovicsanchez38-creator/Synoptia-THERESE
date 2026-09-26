/**
 * Revue P-148, constat 8 (et B-1543) : « Voir les N tâches dans Tâches »
 * pouvait montrer moins de tâches qu'annoncé. Le filtre par étiquette vivait
 * dans un état local de la vue : une vue Tâches déjà montée, filtrée sur une
 * étiquette, le gardait après le geste. Et le geste effaçait sans le dire
 * les filtres de statut et de priorité enregistrés.
 *
 * Le geste passe par une action du store qui remet aussi l'étiquette à zéro,
 * et la vue dit quels filtres ont été retirés.
 */
import { StrictMode } from 'react';
import { act, cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { useTaskStore } from '../../stores/taskStore';

const api = vi.hoisted(() => ({ listTasks: vi.fn(), listProjects: vi.fn(), getProject: vi.fn(), listContacts: vi.fn() }));
vi.mock('../../services/api', async () => {
  const actual = await vi.importActual<Record<string, unknown>>('../../services/api');
  return { ...actual, ...api };
});

import { TasksPanel } from './TasksPanel';

function tache(id: string, titre: string, tags: string[]) {
  return {
    id, title: titre, description: null, status: 'todo', priority: 'medium', due_date: null,
    project_id: 'p-cuisine', contact_id: null, tags,
    created_at: '2026-09-25T10:00:00', updated_at: '2026-09-25T10:00:00', completed_at: null,
  };
}
const DEVIS = tache('t-devis', 'Envoyer le devis', ['devis']);
const PLANS = tache('t-plans', 'Commander les plans', ['atelier']);

describe('Revue P-148, constat 8 et B-1543 : le geste « Voir les tâches » d’un projet', () => {
  beforeEach(() => {
    Object.values(api).forEach((mock) => mock.mockReset());
    api.listTasks.mockResolvedValue([DEVIS, PLANS]);
    api.listProjects.mockResolvedValue([{ id: 'p-cuisine', name: 'Cuisine Roux' }]);
    api.listContacts.mockResolvedValue([]);
    useTaskStore.setState({
      tasks: [], currentTaskId: null, isTaskFormOpen: false, viewMode: 'list', searchQuery: '',
      filterStatus: null, filterPriority: null, filterProjectId: null,
    } as never);
  });
  afterEach(() => cleanup());

  it('sur une vue déjà montée, filtrée par étiquette, le geste remet l’étiquette à zéro et le dit', async () => {
    render(<TasksPanel standalone />);
    await screen.findByText('Envoyer le devis');
    fireEvent.click(screen.getByRole('button', { name: 'Filtrer les tâches' }));
    fireEvent.change(screen.getByRole('combobox', { name: 'Filtrer par étiquette' }), { target: { value: 'devis' } });
    await waitFor(() => expect(screen.queryByText('Commander les plans')).toBeNull());
    // Un statut enregistré d'une visite précédente, posé pendant que la vue est là.
    act(() => { useTaskStore.getState().setFilterStatus('done'); });

    act(() => { useTaskStore.getState().ouvrirSurLeProjet('p-cuisine'); });

    await waitFor(() => expect(api.listTasks).toHaveBeenLastCalledWith({ project_id: 'p-cuisine' }));
    await screen.findByText('Commander les plans');
    expect(screen.getByText('Envoyer le devis')).toBeInTheDocument();
    expect(screen.getByRole('combobox', { name: 'Filtrer par étiquette' })).toHaveValue('');
    const annonce = screen.getByText(/Filtres précédents retirés/).closest('[role="status"]');
    expect(annonce).toHaveTextContent('Filtres précédents retirés : statut « Terminé », étiquette « devis ».');
  });

  it('le geste nomme chaque filtre retiré, y compris la priorité', () => {
    useTaskStore.setState({ filterStatus: 'in_progress', filterPriority: 'high', filterProjectId: 'p-autre' } as never);
    useTaskStore.getState().setFilterTag('devis');

    useTaskStore.getState().ouvrirSurLeProjet('p-cuisine');

    const etat = useTaskStore.getState();
    expect({
      filterProjectId: etat.filterProjectId, filterStatus: etat.filterStatus,
      filterPriority: etat.filterPriority, filterTag: etat.filterTag,
    }).toEqual({ filterProjectId: 'p-cuisine', filterStatus: null, filterPriority: null, filterTag: null });
    expect(etat.filtresRetires).toEqual({ statut: 'in_progress', priorite: 'high', etiquette: 'devis' });
  });

  it('sans filtre à retirer, rien n’est annoncé', async () => {
    render(<TasksPanel standalone />);
    await screen.findByText('Envoyer le devis');
    act(() => { useTaskStore.getState().ouvrirSurLeProjet('p-cuisine'); });
    await waitFor(() => expect(api.listTasks).toHaveBeenLastCalledWith({ project_id: 'p-cuisine' }));
    expect(useTaskStore.getState().filtresRetires).toBeNull();
    expect(screen.queryByText(/Filtres précédents retirés/)).toBeNull();
  });

  it('le geste qui précède le montage de la vue est annoncé, même sous StrictMode', async () => {
    useTaskStore.setState({ filterStatus: 'done' } as never);
    act(() => { useTaskStore.getState().ouvrirSurLeProjet('p-cuisine'); });
    render(<StrictMode><TasksPanel standalone /></StrictMode>);
    expect(await screen.findByText('Filtres précédents retirés : statut « Terminé ».')).toBeInTheDocument();
  });

  it('quitter la vue oublie l’étiquette, comme l’ancien état local', async () => {
    const { unmount } = render(<TasksPanel standalone />);
    await screen.findByText('Envoyer le devis');
    fireEvent.click(screen.getByRole('button', { name: 'Filtrer les tâches' }));
    fireEvent.change(screen.getByRole('combobox', { name: 'Filtrer par étiquette' }), { target: { value: 'devis' } });
    expect(useTaskStore.getState().filterTag).toBe('devis');
    unmount();
    expect(useTaskStore.getState().filterTag).toBeNull();
  });

  it('l’annonce s’efface dès que l’utilisatrice change un filtre', async () => {
    useTaskStore.setState({ filterStatus: 'done' } as never);
    render(<TasksPanel standalone />);
    act(() => { useTaskStore.getState().ouvrirSurLeProjet('p-cuisine'); });
    expect(await screen.findByText(/Filtres précédents retirés/)).toBeInTheDocument();
    fireEvent.change(screen.getByRole('combobox', { name: 'Filtrer par priorité' }), { target: { value: 'low' } });
    await waitFor(() => expect(screen.queryByText(/Filtres précédents retirés/)).toBeNull());
  });
});
