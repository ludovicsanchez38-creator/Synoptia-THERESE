import { act, cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import type { Project } from '../../services/api';
import { _clearEscapeHandlers } from '../../lib/escapeStack';
import { ProjectsKanban } from './ProjectsKanban';
import { ProjectsPanel } from './ProjectsPanel';

const api = vi.hoisted(() => ({
  listProjects: vi.fn(),
  deleteProject: vi.fn(),
  lireLEnsembleDuProjet: vi.fn(),
}));
vi.mock('../../services/api', async (original) => ({ ...await original<object>(), ...api }));
vi.mock('./ProjectModal', () => ({ ProjectModal: () => null }));

const PROJET: Project = {
  id: 'p107-patio', name: 'Réaménagement du patio', status: 'active',
  description: null, contact_id: null, budget: null, notes: null, tags: null,
  created_at: '2026-10-26T10:00:00Z', updated_at: '2026-10-26T10:00:00Z',
};
const SUIVANT: Project = { ...PROJET, id: 'p107-verriere', name: 'Réfection de la verrière' };

beforeEach(() => {
  vi.clearAllMocks();
  _clearEscapeHandlers();
  api.listProjects.mockResolvedValue([PROJET]);
  api.deleteProject.mockResolvedValue(undefined);
  api.lireLEnsembleDuProjet.mockRejectedValue(new Error('Lecture simulée indisponible'));
});
afterEach(() => { cleanup(); _clearEscapeHandlers(); });

function monter() {
  const props = {
    projects: [PROJET, SUIVANT], onSelect: vi.fn(), onDelete: vi.fn(),
    onStatusChange: vi.fn().mockResolvedValue(undefined),
  };
  const rendu = render(<ProjectsKanban {...props} />);
  return { ...props, ...rendu };
}

function commandes(projet = PROJET) {
  return [
    screen.getByRole('button', { name: `Déplacer ${projet.name}` }),
    screen.getByRole('button', { name: projet.name }),
    screen.getByRole('button', { name: `Supprimer ${projet.name}` }),
  ];
}

function focaliser(element: HTMLElement) {
  act(() => element.focus());
}

function arrets(racine: ParentNode) {
  return Array.from(racine.querySelectorAll<HTMLElement>(
    'button, a[href], input, select, textarea, [tabindex]',
  )).filter((element) => element.tabIndex >= 0 && !element.hasAttribute('disabled'));
}

// JSDOM n'exécute pas les gestes natifs Tab et Entrée. Après avoir vérifié
// que keydown n'est pas empêché, on rejoue leur effet dans cette vue sans
// éléments cachés : ordre DOM des arrêts, ou clic natif sur le bouton.
function tabuler(shiftKey = false) {
  const courant = document.activeElement as HTMLElement;
  expect(fireEvent.keyDown(courant, { key: 'Tab', code: 'Tab', shiftKey })).toBe(true);
  const elements = arrets(document);
  const suivant = elements[elements.indexOf(courant) + (shiftKey ? -1 : 1)];
  expect(suivant).toBeDefined();
  focaliser(suivant);
}

function entree(bouton: HTMLElement) {
  expect(fireEvent.keyDown(bouton, { key: 'Enter', code: 'Enter' })).toBe(true);
  fireEvent.click(bouton);
}

describe('P-107 : un seul arrêt de tabulation par carte de projet', () => {
  it('garde les trois boutons, avec le nom comme seul arrêt initial', () => {
    monter();
    for (const projet of [PROJET, SUIVANT]) {
      const [poignee, nom, corbeille] = commandes(projet);
      const carte = nom.closest('.group')!;
      expect(within(carte as HTMLElement).getAllByRole('button')).toEqual([poignee, nom, corbeille]);
      expect(arrets(carte)).toEqual([nom]);
      expect(poignee.tabIndex).toBe(-1);
      expect(corbeille.tabIndex).toBe(-1);
    }
  });

  it('nomme chaque groupe et le décrit par une aide masquée visuellement', () => {
    monter();
    for (const projet of [PROJET, SUIVANT]) {
      const carte = screen.getByRole('group', { name: projet.name });
      const aideId = carte.getAttribute('aria-describedby');
      expect(aideId).toBeTruthy();
      const aide = document.getElementById(aideId!);
      expect(aide).toHaveClass('sr-only');
      expect(carte).toHaveAccessibleDescription('Flèches gauche et droite : choisir entre déplacer, ouvrir ou supprimer le projet.');
    }
  });

  it('B-217 : décrit la navigation et le glisser en français au focus de chaque poignée', () => {
    monter();
    for (const projet of [PROJET, SUIVANT]) {
      const [poignee, nom] = commandes(projet);
      focaliser(nom);
      fireEvent.keyDown(nom, { key: 'ArrowLeft', code: 'ArrowLeft' });
      expect(poignee).toHaveFocus();
      expect(poignee).toHaveAccessibleDescription(
        /Flèches gauche et droite : choisir entre déplacer, ouvrir ou supprimer le projet\. Pour saisir un élément, appuie sur la barre d[’']espace\..*flèches du clavier.*barre d[’']espace pour le déposer.*Échap pour annuler\./,
      );
      expect(poignee).not.toHaveAccessibleDescription(/press the space bar/i);
    }
  });

  it('parcourt poignée, nom et corbeille dans les deux sens, sans boucle', () => {
    const { onSelect, onDelete, onStatusChange } = monter();
    const [poignee, nom, corbeille] = commandes();
    focaliser(nom);
    for (const [touche, attendu] of [
      ['ArrowLeft', poignee], ['ArrowLeft', poignee],
      ['ArrowRight', nom], ['ArrowRight', corbeille], ['ArrowRight', corbeille],
      ['ArrowLeft', nom], ['ArrowLeft', poignee],
    ] as const) {
      expect(fireEvent.keyDown(document.activeElement!, { key: touche, code: touche })).toBe(false);
      expect(attendu).toHaveFocus();
      expect(arrets(nom.closest('.group')!)).toEqual([attendu]);
    }
    expect(onSelect).not.toHaveBeenCalled();
    expect(onDelete).not.toHaveBeenCalled();
    expect(onStatusChange).not.toHaveBeenCalled();
  });

  it('Tab sort vers la carte suivante et Maj+Tab retrouve la commande mémorisée', () => {
    const rendu = monter();
    const [, nom, corbeille] = commandes();
    const [, nomSuivant] = commandes(SUIVANT);
    focaliser(nom);
    fireEvent.keyDown(nom, { key: 'ArrowRight', code: 'ArrowRight' });
    expect(corbeille).toHaveFocus();
    tabuler();
    expect(nomSuivant).toHaveFocus();
    rendu.rerender(<ProjectsKanban projects={[{ ...PROJET }, { ...SUIVANT }]} onSelect={rendu.onSelect}
      onDelete={rendu.onDelete} onStatusChange={rendu.onStatusChange} />);
    tabuler(true);
    expect(corbeille).toHaveFocus();
    expect(arrets(document)).toEqual([corbeille, nomSuivant]);
  });

  it('mémorise aussi le focus donné au pointeur, sans changer les clics', () => {
    const { onDelete, onSelect } = monter();
    const [, nom, corbeille] = commandes();
    // Le navigateur focalise le bouton au pointerdown ; JSDOM le simule ici.
    focaliser(corbeille);
    fireEvent.click(corbeille);
    expect(arrets(nom.closest('.group')!)).toEqual([corbeille]);
    expect(onDelete).toHaveBeenCalledExactlyOnceWith(PROJET);
    focaliser(nom);
    fireEvent.click(nom);
    expect(arrets(nom.closest('.group')!)).toEqual([nom]);
    expect(onSelect).toHaveBeenCalledExactlyOnceWith(PROJET);
  });

  it('Entrée sur le nom atteint depuis la poignée ouvre le projet', () => {
    const { onSelect, onDelete } = monter();
    const [poignee, nom] = commandes();
    focaliser(nom);
    fireEvent.keyDown(nom, { key: 'ArrowLeft', code: 'ArrowLeft' });
    expect(poignee).toHaveFocus();
    fireEvent.keyDown(poignee, { key: 'ArrowRight', code: 'ArrowRight' });
    expect(nom).toHaveFocus();
    entree(nom);
    expect(onSelect).toHaveBeenCalledExactlyOnceWith(PROJET);
    expect(onDelete).not.toHaveBeenCalled();
    expect(screen.getAllByText(PROJET.name)).toHaveLength(1);
  });

  it('Entrée sur la corbeille affiche la même confirmation que le clic', async () => {
    render(<ProjectsPanel />);
    const nom = await screen.findByRole('button', { name: PROJET.name });
    const corbeille = screen.getByRole('button', { name: `Supprimer ${PROJET.name}` });
    focaliser(nom);
    fireEvent.keyDown(nom, { key: 'ArrowRight', code: 'ArrowRight' });
    expect(corbeille).toHaveFocus();
    entree(corbeille);
    const dialogue = screen.getByRole('dialog', { name: 'Supprimer ce projet ?' });
    await waitFor(() => expect(within(dialogue).getByRole('status')).toBeEmptyDOMElement());
    expect(dialogue).toHaveTextContent(`« ${PROJET.name} » sera supprimé. Cette action est irréversible.`);
    const texte = dialogue.textContent;
    expect(api.deleteProject).not.toHaveBeenCalled();
    fireEvent.click(within(dialogue).getByRole('button', { name: 'Annuler' }));
    await waitFor(() => expect(corbeille).toHaveFocus());
    expect(arrets(nom.closest('.group')!)).toEqual([corbeille]);
    fireEvent.click(corbeille);
    const auClic = screen.getByRole('dialog', { name: 'Supprimer ce projet ?' });
    await waitFor(() => expect(within(auClic).getByRole('status')).toBeEmptyDOMElement());
    expect(auClic.textContent).toBe(texte);
    expect(api.deleteProject).not.toHaveBeenCalled();
    fireEvent.click(within(auClic).getByRole('button', { name: 'Supprimer' }));
    await waitFor(() => expect(api.deleteProject).toHaveBeenCalledExactlyOnceWith(PROJET.id));
  });

  it.each([['Enter', 'Enter'], [' ', 'Space']])(
    'le glisser depuis la poignée avec %s conserve les flèches pour dnd-kit', async (key, code) => {
      const { onSelect, onDelete, onStatusChange } = monter();
      const [poignee, nom] = commandes();
      focaliser(nom);
      fireEvent.keyDown(nom, { key: 'ArrowLeft', code: 'ArrowLeft' });
      expect(poignee).toHaveFocus();
      fireEvent.keyDown(poignee, { key, code });
      expect(poignee).toHaveAttribute('aria-pressed', 'true');
      expect(screen.getAllByText(PROJET.name)).toHaveLength(2);
      // Le KeyboardSensor branche son écouteur document au prochain tick.
      await act(async () => { await new Promise((resolve) => setTimeout(resolve, 0)); });
      // Avec DragOverlay, c'est le double visuel qui se déplace, pas la source.
      const overlay = screen.getAllByText(PROJET.name)[1].closest('.group')!.parentElement!;
      const avant = overlay.style.transform;
      fireEvent.keyDown(poignee, { key: 'ArrowRight', code: 'ArrowRight' });
      expect(poignee).toHaveFocus();
      expect(overlay.style.transform).not.toBe(avant);
      fireEvent.keyDown(poignee, { key: 'ArrowLeft', code: 'ArrowLeft' });
      expect(poignee).toHaveFocus();
      expect(overlay.style.transform).toBe(avant);
      // Le double visuel du DragOverlay n'ajoute aucun arrêt de tabulation.
      expect(arrets(document)).toEqual([poignee, commandes(SUIVANT)[1]]);
      fireEvent.keyDown(poignee, { key: 'Escape', code: 'Escape' });
      await waitFor(() => expect(screen.getAllByText(PROJET.name)).toHaveLength(1));
      fireEvent.keyDown(poignee, { key: 'ArrowRight', code: 'ArrowRight' });
      expect(nom).toHaveFocus();
      expect(onSelect).not.toHaveBeenCalled();
      expect(onDelete).not.toHaveBeenCalled();
      expect(onStatusChange).not.toHaveBeenCalled();
    },
  );
});
