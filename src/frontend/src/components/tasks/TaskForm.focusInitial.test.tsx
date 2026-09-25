/**
 * B-1370 (persona Zoé, cycle 13) : « Nouvelle tâche » ouvrait le formulaire
 * en laissant le focus sur le bouton, et « Enregistrer » passait avant le
 * premier champ : trois tabulations pour atteindre « Titre ». Le formulaire
 * s'ouvre désormais sur son premier champ.
 */
import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

vi.mock('../../services/api', async (importOriginal) => ({
  ...(await importOriginal<object>()),
  listProjects: vi.fn().mockResolvedValue([]),
  listContacts: vi.fn().mockResolvedValue([]),
}));

import { TaskForm } from './TaskForm';

describe('B-1370 : le formulaire de tâche s’ouvre sur le titre', () => {
  it('le champ Titre a le focus à l’ouverture', () => {
    const bouton = document.createElement('button');
    document.body.appendChild(bouton);
    bouton.focus();

    render(<TaskForm />);

    expect(document.activeElement).toBe(screen.getByLabelText(/Titre/));
    bouton.remove();
  });
});
