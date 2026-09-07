/** B-621 (Karim, c4) : « Titre * » n'était obligatoire que pour l'œil. */
import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

vi.mock('../../services/api', async (importOriginal) => ({
  ...(await importOriginal<object>()),
  listProjects: vi.fn().mockResolvedValue([]),
  listContacts: vi.fn().mockResolvedValue([]),
}));

import { TaskForm } from './TaskForm';

describe('TaskForm : le titre est requis pour la machine aussi', () => {
  it('le champ titre porte required et aria-required', () => {
    render(<TaskForm />);
    const titre = screen.getByLabelText(/Titre/);
    expect(titre).toBeRequired();
    expect(titre).toHaveAttribute('aria-required', 'true');
  });
});
