/** B-1443 : dans le choix du contact d'un projet, une fiche sans prénom ni
 *  nom s'affichait « Sans nom (Sans Nom SA) ». Elle s'appelle par son
 *  entreprise. */
import { act, render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import type { Contact } from '../../services/api';
import { ProjectModal } from './ProjectModal';

const api = vi.hoisted(() => ({
  listContacts: vi.fn(), listProjectFiles: vi.fn(), etatSync: vi.fn(),
  updateProject: vi.fn(), createProject: vi.fn(), deleteProject: vi.fn(),
  deleteFile: vi.fn(), uploadProjectFile: vi.fn(),
  definirRacineSync: vi.fn(), retirerRacineSync: vi.fn(),
  preparerPlanSync: vi.fn(), appliquerPlanSync: vi.fn(), journalSync: vi.fn(),
}));
vi.mock('../../services/api', () => api);

const SOCIETE: Contact = {
  id: 'ct-sa', first_name: null, last_name: null, company: 'Sans Nom SA', email: null, phone: null,
  address: null, notes: null, tags: null, stage: 'contact', score: 0, source: null, last_interaction: null,
  created_at: '2026-09-22T10:00:00Z', updated_at: '2026-09-22T10:00:00Z',
};

describe('B-1443 : le contact d’un projet s’appelle par son entreprise', () => {
  beforeEach(() => {
    Object.values(api).forEach((mock) => mock.mockReset());
    api.listContacts.mockResolvedValue([SOCIETE]);
  });

  it('l’option du contact est « Sans Nom SA »', async () => {
    await act(async () => {
      render(<ProjectModal isOpen onClose={vi.fn()} project={null} />);
    });
    const options = Array.from(document.querySelectorAll('option')).map((o) => o.textContent);
    expect(options).toContain('Sans Nom SA');
    expect(options.join('|')).not.toContain('Sans nom (');
    expect(screen.getByRole('dialog')).toBeInTheDocument();
  });
});
