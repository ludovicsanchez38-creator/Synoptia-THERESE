/**
 * Lecteur D de la carte c12 : B-1061 (« Annuler » d'une confirmation de
 * suppression laisse tomber le focus sur la page) et B-1060 (la confirmation
 * de suppression d'un fichier joint n'est ni amenée dans la vue ni focalisée).
 */
import { fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

const listProjectFiles = vi.fn();
vi.mock('../../services/api', async () => {
  const actual = await vi.importActual<typeof import('../../services/api')>('../../services/api');
  return { ...actual, listProjects: vi.fn().mockResolvedValue([]), listContacts: vi.fn().mockResolvedValue([]), listFiles: vi.fn().mockResolvedValue([]), listProjectFiles: (...a: unknown[]) => listProjectFiles(...a) };
});
import { ContactModal } from './ContactModal';
import { ProjectModal } from './ProjectModal';

const scrollIntoView = vi.fn();
const original = Element.prototype.scrollIntoView;
const contact = { id: 'c-1', first_name: 'Jeanne', last_name: 'Martin', company: null, email: 'j@example.com', phone: null, address: null, notes: null, tags: [], scope: 'global', created_at: '2026-09-01T00:00:00Z', updated_at: '2026-09-01T00:00:00Z' };
const projet = { id: 'p-1', name: 'Refonte', description: '', status: 'active', budget: null, contact_id: null, notes: '', tags: [], created_at: '2026-09-01T00:00:00Z', updated_at: '2026-09-01T00:00:00Z' };

describe('cycle 12 : confirmations de suppression des fiches', () => {
  beforeEach(() => {
    scrollIntoView.mockClear();
    Element.prototype.scrollIntoView = scrollIntoView;
    listProjectFiles.mockResolvedValue({ files: [{ id: 'f-1', name: 'devis.pdf', path: '/x/devis.pdf', size: 10, mime_type: 'application/pdf', created_at: '2026-09-01T00:00:00Z' }], truncated: false });
  });
  afterEach(() => { Element.prototype.scrollIntoView = original; });

  it('B-1061 : « Annuler » sur un contact rend le focus à « Supprimer »', async () => {
    render(<ContactModal isOpen onClose={vi.fn()} contact={contact as never} />);
    fireEvent.click(screen.getByRole('button', { name: /Supprimer/ }));
    const question = await screen.findByText('Supprimer ce contact ?');
    const annuler = within(question.closest('div')?.parentElement as HTMLElement).getByRole('button', { name: 'Annuler' });
    await waitFor(() => expect(annuler).toHaveFocus());
    fireEvent.click(annuler);
    await waitFor(() => expect(screen.getByRole('button', { name: /^Supprimer$/ })).toHaveFocus());
  });

  it('B-1061 : « Annuler » sur un projet rend le focus à « Supprimer »', async () => {
    render(<ProjectModal isOpen onClose={vi.fn()} project={projet as never} />);
    fireEvent.click(screen.getByRole('button', { name: /^Supprimer$/ }));
    const question = await screen.findByText('Supprimer ce projet ?');
    const annuler = within(question.closest('div')?.parentElement as HTMLElement).getByRole('button', { name: 'Annuler' });
    await waitFor(() => expect(annuler).toHaveFocus());
    fireEvent.click(annuler);
    await waitFor(() => expect(screen.getByRole('button', { name: /^Supprimer$/ })).toHaveFocus());
  });

  it('B-1060 : la confirmation de suppression d’un fichier joint est amenée dans la vue et focalisée', async () => {
    render(<ProjectModal isOpen onClose={vi.fn()} project={projet as never} />);
    fireEvent.click(await screen.findByRole('button', { name: 'Supprimer le fichier devis.pdf' }));
    const question = await screen.findByText(/Supprimer « devis\.pdf » \?/);
    const bloc = question.closest('div')?.parentElement as HTMLElement;
    await waitFor(() => expect(scrollIntoView.mock.contexts).toContain(bloc));
    expect(within(bloc).getByRole('button', { name: 'Conserver le fichier' })).toHaveFocus();
  });
});
