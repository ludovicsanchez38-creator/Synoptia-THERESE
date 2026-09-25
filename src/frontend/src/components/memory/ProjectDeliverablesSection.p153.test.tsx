/**
 * P-153 (recette P-146, lot 2, O9 ; acceptée le 25/09) : ajouter un livrable
 * passait par la capacité « Livrables et suivi client » ; la fenêtre du
 * projet ne montrait ni ne créait ses livrables.
 */
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const api = vi.hoisted(() => ({ listDeliverables: vi.fn(), createDeliverable: vi.fn() }));
vi.mock('../../services/api/crm-extended', async (importOriginal) => ({
  ...(await importOriginal<object>()),
  ...api,
}));

import { ProjectDeliverablesSection } from './ProjectDeliverablesSection';

describe('P-153 : les livrables dans la fenêtre du projet', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    api.listDeliverables.mockResolvedValue([
      { id: 'd1', project_id: 'p1', title: 'Plans cotés', description: null, status: 'en_cours', due_date: null, completed_at: null, created_at: '', updated_at: '' },
    ]);
    api.createDeliverable.mockImplementation(async (d: { title: string }) => ({
      id: 'd2', project_id: 'p1', title: d.title, description: null, status: 'a_faire', due_date: null, completed_at: null, created_at: '', updated_at: '',
    }));
  });

  it('liste les livrables du projet', async () => {
    render(<ProjectDeliverablesSection projectId="p1" />);
    expect(await screen.findByText('Plans cotés')).toBeInTheDocument();
    expect(screen.getByText('En cours')).toBeInTheDocument();
    expect(api.listDeliverables).toHaveBeenCalledWith({ project_id: 'p1' });
  });

  it('en ajoute un sans quitter la fenêtre', async () => {
    render(<ProjectDeliverablesSection projectId="p1" />);
    await screen.findByText('Plans cotés');
    fireEvent.change(screen.getByLabelText('Nouveau livrable'), { target: { value: 'Pose de la cuisine' } });
    fireEvent.click(screen.getByRole('button', { name: 'Ajouter le livrable' }));
    await waitFor(() => expect(api.createDeliverable).toHaveBeenCalledWith({ project_id: 'p1', title: 'Pose de la cuisine', status: 'a_faire' }));
    expect(await screen.findByText('Pose de la cuisine')).toBeInTheDocument();
  });

  it('en lecture seule (démo), pas d’ajout', async () => {
    render(<ProjectDeliverablesSection projectId="p1" lectureSeule />);
    await screen.findByText('Plans cotés');
    expect(screen.queryByRole('button', { name: 'Ajouter le livrable' })).toBeNull();
  });
});
