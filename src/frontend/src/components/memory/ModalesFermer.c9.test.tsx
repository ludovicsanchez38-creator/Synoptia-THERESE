/**
 * B-813 (cycle 9) : les modales « Nouveau contact » et « Nouveau projet »
 * avaient un bouton de fermeture sans nom, et c'est lui qui recevait le focus
 * à l'ouverture. « Nouveau document » nomme le sien « Fermer » et ouvre sur le titre.
 */
import { render, screen, waitFor } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

vi.mock('../../services/api', async () => {
  const actual = await vi.importActual<typeof import('../../services/api')>('../../services/api');
  return { ...actual, listProjects: vi.fn().mockResolvedValue([]), listContacts: vi.fn().mockResolvedValue([]), listFiles: vi.fn().mockResolvedValue([]) };
});
import { ContactModal } from './ContactModal';
import { ProjectModal } from './ProjectModal';

describe('Modales Mémoire - B-813, bouton Fermer nommé et focus initial sur le premier champ', () => {
  it('Nouveau contact', async () => {
    render(<ContactModal isOpen onClose={vi.fn()} />);
    expect(screen.getByRole('button', { name: 'Fermer' })).toBeInTheDocument();
    await waitFor(() => expect(document.activeElement?.id).toBe('contactmodal-prenom'));
  });

  it('Nouveau projet', async () => {
    render(<ProjectModal isOpen onClose={vi.fn()} />);
    expect(screen.getByRole('button', { name: 'Fermer' })).toBeInTheDocument();
    await waitFor(() => expect(document.activeElement?.id).toBe('projectmodal-nom-du-projet'));
  });
});
