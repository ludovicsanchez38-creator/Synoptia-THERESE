/**
 * B-1030 (ronde B3 du cycle 11, D-B3-2) : dans « Nouveau contact »,
 * « Modifier le contact » et « Nouveau projet », le message de validation et
 * la confirmation de suppression étaient rendus sous la zone visible du
 * contenu défilant. « Créer » paraissait sans effet, et le focus tombait sur
 * la page après « Supprimer ». Mesuré en navigateur par la ronde ; ici on
 * vérifie le geste : l'élément est amené dans la vue, la confirmation prend
 * le focus.
 */
import { fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

vi.mock('../../services/api', async () => {
  const actual = await vi.importActual<typeof import('../../services/api')>('../../services/api');
  return { ...actual, listProjects: vi.fn().mockResolvedValue([]), listContacts: vi.fn().mockResolvedValue([]), listFiles: vi.fn().mockResolvedValue([]) };
});
import { ContactModal } from './ContactModal';
import { ProjectModal } from './ProjectModal';

const scrollIntoView = vi.fn();
const original = Element.prototype.scrollIntoView;

const contact = {
  id: 'c-1', first_name: 'Jeanne', last_name: 'Martin', company: null, email: 'jeanne@example.com',
  phone: null, address: null, notes: null, tags: [], scope: 'global', created_at: '2026-09-01T00:00:00Z',
  updated_at: '2026-09-01T00:00:00Z',
};
const projet = {
  id: 'p-1', name: 'Refonte', description: '', status: 'active', budget: null, contact_id: null,
  notes: '', tags: [], created_at: '2026-09-01T00:00:00Z', updated_at: '2026-09-01T00:00:00Z',
};

function amenesDansLaVue(): Element[] {
  return scrollIntoView.mock.contexts as Element[];
}

describe('B-1030 : ce qui apparaît au bas d’une modale défilante est amené dans la vue', () => {
  beforeEach(() => {
    scrollIntoView.mockClear();
    Element.prototype.scrollIntoView = scrollIntoView;
  });
  afterEach(() => { Element.prototype.scrollIntoView = original; });

  it('Nouveau contact : « Créer » sans nom amène le message dans la vue', async () => {
    render(<ContactModal isOpen onClose={vi.fn()} />);
    fireEvent.click(screen.getByRole('button', { name: 'Créer' }));
    const message = await screen.findByText('Le prénom ou le nom est requis');
    await waitFor(() => expect(amenesDansLaVue().some((el) => el.contains(message))).toBe(true));
  });

  it('Modifier le contact : « Supprimer » amène la confirmation dans la vue et lui donne le focus', async () => {
    render(<ContactModal isOpen onClose={vi.fn()} contact={contact as never} />);
    fireEvent.click(screen.getByRole('button', { name: /Supprimer/ }));
    const question = await screen.findByText('Supprimer ce contact ?');
    await waitFor(() => expect(amenesDansLaVue().some((el) => el.contains(question))).toBe(true));
    const bloc = question.closest('div')?.parentElement as HTMLElement;
    expect(within(bloc).getByRole('button', { name: 'Annuler' })).toHaveFocus();
  });

  it('Nouveau projet : « Créer » sans nom amène le message dans la vue', async () => {
    render(<ProjectModal isOpen onClose={vi.fn()} />);
    fireEvent.click(screen.getByRole('button', { name: 'Créer' }));
    const message = await screen.findByText('Le nom du projet est requis');
    await waitFor(() => expect(amenesDansLaVue().some((el) => el.contains(message))).toBe(true));
  });

  it('Modifier le projet : « Supprimer » amène la confirmation dans la vue et lui donne le focus', async () => {
    render(<ProjectModal isOpen onClose={vi.fn()} project={projet as never} />);
    fireEvent.click(screen.getByRole('button', { name: /^Supprimer$/ }));
    const question = await screen.findByText('Supprimer ce projet ?');
    await waitFor(() => expect(amenesDansLaVue().some((el) => el.contains(question))).toBe(true));
    const bloc = question.closest('div')?.parentElement as HTMLElement;
    expect(within(bloc).getByRole('button', { name: 'Annuler' })).toHaveFocus();
  });
});
