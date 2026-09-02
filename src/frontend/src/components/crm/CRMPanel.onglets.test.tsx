/**
 * B-219 : le bandeau « Pipeline / Activités » était deux `<button>` nus.
 *
 * Ni `role`, ni `aria-selected`, ni `aria-pressed` : l'onglet actif ne se
 * distinguait que par un fond et un trait animé, c'est-à-dire par la couleur
 * seule. La même application sait pourtant faire — la barre des Paramètres est
 * un vrai `tablist`.
 *
 * Le test lit le rendu, pas la classe CSS : un onglet dont l'état ne passerait
 * que par `bg-surface` échoue ici.
 */
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { useCRMStore } from '../../stores/crmStore';
import { useContactsStore } from '../../stores/contactsStore';

vi.mock('../../services/api', async () => {
  const reel = await vi.importActual<typeof import('../../services/api')>('../../services/api');
  return {
    ...reel,
    listProjects: vi.fn().mockResolvedValue([]),
    listActivities: vi.fn().mockResolvedValue([]),
  };
});

import { CRMPanel } from './CRMPanel';

describe("B-219 : les onglets du Pipeline s'annoncent comme des onglets", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useCRMStore.setState({ projects: [], activeTab: 'pipeline' });
    useContactsStore.setState({ contacts: [], selectedContactId: null, truncated: false });
  });

  it('le bandeau est un tablist, chaque onglet un tab', async () => {
    render(<CRMPanel standalone />);

    const bandeau = await screen.findByRole('tablist');
    expect(bandeau).toBeInTheDocument();

    const onglets = screen.getAllByRole('tab');
    expect(onglets.map((o) => o.textContent?.trim())).toEqual(['Pipeline', 'Activités']);
  });

  it("aria-selected suit l'onglet actif, dans les deux sens", async () => {
    render(<CRMPanel standalone />);

    const pipeline = await screen.findByRole('tab', { name: /Pipeline/ });
    const activites = screen.getByRole('tab', { name: /Activités/ });
    expect(pipeline).toHaveAttribute('aria-selected', 'true');
    expect(activites).toHaveAttribute('aria-selected', 'false');

    fireEvent.click(activites);

    await waitFor(() => expect(activites).toHaveAttribute('aria-selected', 'true'));
    expect(pipeline).toHaveAttribute('aria-selected', 'false');
  });

  it('le contenu affiché est le panneau de l’onglet actif', async () => {
    render(<CRMPanel standalone />);

    const onglet = await screen.findByRole('tab', { name: /Pipeline/ });
    const panneau = screen.getByRole('tabpanel');
    // Le lien onglet -> panneau doit être posé dans les DEUX sens, sinon un
    // lecteur d'écran annonce un onglet qui ne commande rien.
    expect(onglet.getAttribute('aria-controls')).toBe(panneau.getAttribute('id'));
    expect(panneau.getAttribute('aria-labelledby')).toBe(onglet.getAttribute('id'));
  });

  it('un onglet inactif reste joignable au clavier', async () => {
    render(<CRMPanel standalone />);

    const pipeline = await screen.findByRole('tab', { name: /Pipeline/ });
    const activites = screen.getByRole('tab', { name: /Activités/ });
    // Un `tabIndex={-1}` posé sans navigation par flèches rendrait l'onglet
    // inactif inatteignable : la correction serait pire que le défaut.
    pipeline.focus();
    fireEvent.keyDown(pipeline, { key: 'ArrowRight' });
    await waitFor(() => expect(document.activeElement).toBe(activites));
  });
});
