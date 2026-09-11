/**
 * DA « Application affinée », lot 6 : le formulaire de tâche
 * (`docs/plans/2026-09-11-da-lot6-projets-design.md`, § 5 et § 9).
 */
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { useTaskStore } from '../../stores/taskStore';

const api = vi.hoisted(() => ({ createTask: vi.fn() }));
vi.mock('../../services/api', async (importOriginal) => ({
  ...(await importOriginal<object>()),
  listProjects: vi.fn().mockResolvedValue([]),
  listContacts: vi.fn().mockResolvedValue([]),
  createTask: (...a: unknown[]) => api.createTask(...a),
}));

import { TaskForm } from './TaskForm';

/** Le message exact de la maquette (`projets.html:53`, apostrophe droite). */
const MESSAGE_TITRE = "Ajoute un titre : c'est la seule chose obligatoire.";

function messageDuChamp(): HTMLElement | null {
  return document.getElementById('taskform-titre-error');
}

beforeEach(() => {
  vi.clearAllMocks();
  api.createTask.mockResolvedValue({ id: 't-neuf' });
  useTaskStore.setState({ tasks: [], currentTaskId: null, isTaskFormOpen: true, searchQuery: '' });
});

describe('Lot 6 DA : les champs du formulaire', () => {
  it('les identifiants et le contrat du titre sont conservés', () => {
    render(<TaskForm />);

    const titre = screen.getByLabelText(/Titre/) as HTMLInputElement;
    expect(titre.id).toBe('taskform-titre');
    expect(titre).toBeRequired();
    expect(titre).toHaveAttribute('aria-required', 'true');
    expect(titre).not.toHaveAttribute('aria-invalid', 'true');

    // L'astérisque vient de FormField required, et il est décoratif : le nom
    // du champ reste « Titre », il n'est pas écrit dans la chaîne du label.
    const label = document.querySelector('label[for="taskform-titre"]') as HTMLElement;
    expect(label).not.toBeNull();
    expect(label.textContent).toBe('Titre*');
    expect(label.querySelector('[aria-hidden="true"]')?.textContent).toBe('*');
    expect(label.firstChild?.textContent).toBe('Titre');

    for (const id of ['taskform-description', 'taskform-statut', 'taskform-priorite', 'taskform-date-limite', 'taskform-tags']) {
      expect(document.getElementById(id), id).not.toBeNull();
    }
  });

  it('Statut et Priorité restent côte à côte dans une grille de deux colonnes', () => {
    render(<TaskForm />);

    const statut = document.getElementById('taskform-statut') as HTMLElement;
    const priorite = document.getElementById('taskform-priorite') as HTMLElement;
    const grille = statut.closest('[class*="grid-cols-2"]');
    expect(grille).not.toBeNull();
    expect(grille?.contains(priorite)).toBe(true);
  });

  it('le retour porte un nom', () => {
    render(<TaskForm />);
    expect(screen.getByRole('button', { name: 'Retour' })).toBeInTheDocument();
  });
});

describe('Lot 6 DA : le titre manquant est une erreur de champ, pas un bandeau', () => {
  it('pose le message de la maquette sous le champ, sans monter Alerte', () => {
    render(<TaskForm />);
    fireEvent.click(screen.getByRole('button', { name: /Enregistrer/ }));

    const message = messageDuChamp();
    expect(message).not.toBeNull();
    expect(message?.textContent).toBe(MESSAGE_TITRE);

    const titre = screen.getByLabelText(/Titre/);
    expect(titre).toHaveAttribute('aria-invalid', 'true');
    expect(titre.getAttribute('aria-describedby') ?? '').toContain('taskform-titre-error');

    // Alerte pose role="alert" sur un div et son titre dans un <b class="text-error">.
    expect(document.querySelector('div[role="alert"]')).toBeNull();
    expect(document.querySelector('b.text-error')).toBeNull();
    expect(api.createTask).not.toHaveBeenCalled();
  });

  it('efface le bandeau de sauvegarde : un titre vidé ne laisse pas les deux messages', async () => {
    api.createTask.mockRejectedValueOnce(new Error('Échec de la sauvegarde'));
    render(<TaskForm />);

    const titre = screen.getByLabelText(/Titre/);
    fireEvent.change(titre, { target: { value: 'Relancer Ruiz' } });
    fireEvent.click(screen.getByRole('button', { name: /Enregistrer/ }));
    await waitFor(() => expect(document.querySelector('div[role="alert"]')).not.toBeNull());

    fireEvent.change(titre, { target: { value: '   ' } });
    fireEvent.click(screen.getByRole('button', { name: /Enregistrer/ }));

    expect(document.querySelector('div[role="alert"]')).toBeNull();
    expect(messageDuChamp()?.textContent).toBe(MESSAGE_TITRE);
  });
});

describe('Lot 6 DA : l’enregistrement', () => {
  it('le bouton est désactivé tant que la sauvegarde est en vol', async () => {
    api.createTask.mockImplementation(() => new Promise(() => {}));
    render(<TaskForm />);

    fireEvent.change(screen.getByLabelText(/Titre/), { target: { value: 'Relancer Ruiz' } });
    fireEvent.click(screen.getByRole('button', { name: /Enregistrer/ }));

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /Enregistrement/ })).toBeDisabled();
    });
  });
});
