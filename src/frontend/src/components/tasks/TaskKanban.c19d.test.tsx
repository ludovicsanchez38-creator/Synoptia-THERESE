import { act, fireEvent, render, screen } from '@testing-library/react';
import { beforeEach, expect, it, vi } from 'vitest';
import { TaskKanban } from './TaskKanban';
import { useTaskStore } from '../../stores/taskStore';
import { useKeyboardShortcuts } from '../../hooks/useKeyboardShortcuts';
import type { Task } from '../../services/api';

function Vue({ fermer }: { fermer: () => void }) {
  useKeyboardShortcuts({ onEscape: fermer });
  return <TaskKanban />;
}
beforeEach(() => useTaskStore.setState({ tasks: [{ id: 't1', title: 'Préparer le chantier', status: 'todo', priority: 'medium', tags: [] } as unknown as Task], searchQuery: '', isTaskFormOpen: false }));
it('B-1075 : le titre est un bouton indépendant du glisser', () => {
  render(<TaskKanban />);
  const ouvrir = screen.getByRole('button', { name: 'Préparer le chantier' });
  expect(ouvrir.tagName).toBe('BUTTON');
  expect(fireEvent.keyDown(ouvrir, { key: 'Enter', code: 'Enter' })).toBe(true);
  fireEvent.click(ouvrir);
  expect(useTaskStore.getState().isTaskFormOpen).toBe(true);
});
it('B-1112 : Échap annule le glisser sans fermer la vue', async () => {
  const fermer = vi.fn();
  render(<Vue fermer={fermer} />);
  // Le même test atteint l'ancien activateur sur la base.
  const poignee = screen.queryByRole('button', { name: /Déplacer Préparer/ }) ?? screen.getByRole('button', { name: 'Préparer le chantier' });
  act(() => poignee.focus());
  fireEvent.keyDown(poignee, { key: ' ', code: 'Space' });
  await act(async () => { await new Promise((r) => setTimeout(r, 10)); });
  fireEvent.keyDown(document, { key: 'Escape', code: 'Escape' });
  await act(async () => { await new Promise((r) => setTimeout(r, 300)); });
  expect(fermer).not.toHaveBeenCalled();
  expect(screen.getAllByText('Préparer le chantier')).toHaveLength(1);
});

it.each(['Appeler Luc', 'Préparer la visite', 'Lire le devis', 'Commander les tuiles', 'Réserver la salle', 'Relancer Léa', 'Vérifier les plans', 'Revoir le budget', 'Ranger le dossier', 'Confirmer la livraison'])('Rejeu B-1075/B-1112 : %s', async (title) => {
  useTaskStore.setState({ tasks: [{ id: 'rejeu', title, status: 'todo', priority: 'medium', tags: [] } as unknown as Task] });
  const fermer = vi.fn();
  render(<Vue fermer={fermer} />);
  const ouvrir = screen.getByRole('button', { name: title });
  expect(fireEvent.keyDown(ouvrir, { key: 'Enter', code: 'Enter' })).toBe(true);
  fireEvent.click(ouvrir);
  expect(useTaskStore.getState().currentTaskId).toBe('rejeu');
  const poignee = screen.getByRole('button', { name: `Déplacer ${title}` });
  act(() => poignee.focus());
  fireEvent.keyDown(poignee, { key: ' ', code: 'Space' });
  await act(async () => { await new Promise((r) => setTimeout(r, 10)); });
  fireEvent.keyDown(document, { key: 'Escape', code: 'Escape' });
  await act(async () => { await new Promise((r) => setTimeout(r, 300)); });
  expect(fermer).not.toHaveBeenCalled();
  expect(screen.getAllByText(title)).toHaveLength(1);
});
