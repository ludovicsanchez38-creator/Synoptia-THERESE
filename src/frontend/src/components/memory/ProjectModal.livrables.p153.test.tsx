/** P-153 : la fenêtre d'un projet existant montre ses livrables. */
import { act, render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const api = vi.hoisted(() => ({
  listContacts: vi.fn(), listProjectFiles: vi.fn(), etatSync: vi.fn(),
  updateProject: vi.fn(), createProject: vi.fn(), deleteProject: vi.fn(),
  deleteFile: vi.fn(), uploadProjectFile: vi.fn(),
  definirRacineSync: vi.fn(), retirerRacineSync: vi.fn(),
  preparerPlanSync: vi.fn(), appliquerPlanSync: vi.fn(), journalSync: vi.fn(),
}));
vi.mock('../../services/api', () => api);
const livrables = vi.hoisted(() => ({ listDeliverables: vi.fn(), createDeliverable: vi.fn() }));
vi.mock('../../services/api/crm-extended', async (importOriginal) => ({
  ...(await importOriginal<object>()),
  ...livrables,
}));

import { ProjectModal } from './ProjectModal';

describe('P-153 : la fenêtre du projet et ses livrables', () => {
  beforeEach(() => {
    Object.values(api).forEach((mock) => mock.mockReset());
    api.listContacts.mockResolvedValue([]);
    api.listProjectFiles.mockResolvedValue({ files: [], truncated: false });
    api.etatSync.mockResolvedValue(null);
    livrables.listDeliverables.mockResolvedValue([
      { id: 'd1', project_id: 'p1', title: 'Plans cotés', description: null, status: 'a_faire', due_date: null, completed_at: null, created_at: '', updated_at: '' },
    ]);
  });

  it('en modification, la section Livrables est là', async () => {
    await act(async () => {
      render(<ProjectModal isOpen onClose={vi.fn()} project={{ id: 'p1', name: 'Cuisine Roux', description: null, contact_id: null, status: 'active', budget: null, notes: null, tags: null, created_at: '', updated_at: '' } as never} />);
    });
    expect(await screen.findByText('Plans cotés')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Ajouter le livrable' })).toBeInTheDocument();
  });
});
