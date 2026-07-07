/**
 * Tests OutlineTree - régression BUG-041 (drag depuis le corps de la ligne),
 * sélection de section, calcul de réorganisation au drop, erreur 409 et
 * création manuelle de section.
 *
 * Gotcha (pattern TaskKanban.test.tsx) : le test de CLIC (sélection) est
 * placé AVANT les tests de drag dans ce fichier - après un drag, dnd-kit
 * arme une suppression du prochain click qui avalerait un clic de test
 * ultérieur s'il n'est pas explicitement consommé.
 *
 * Le calcul de la trame après un drop (`computeReorderPayload`) est testé
 * comme une fonction pure plutôt que via un geste pointeur/clavier complet
 * simulé de bout en bout : jsdom ne mesure aucun rect de layout réel, donc
 * la détection de collision de @dnd-kit (closestCenter) n'est pas fiable à
 * piloter précisément en test (même limite déjà acceptée par
 * ProjectsKanban.test.tsx / TaskKanban.test.tsx, qui ne vérifient que le
 * DÉMARRAGE du drag, pas un drop avec une cible précise).
 */
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { OutlineTree, type OutlineTreeProps } from './OutlineTree';
import { computeReorderPayload } from './reorderPayload';
import type { DocumentSection } from '../../services/api/documents';

function makeSection(overrides: Partial<DocumentSection> & Pick<DocumentSection, 'id' | 'title'>): DocumentSection {
  return {
    document_id: 'd1',
    brief: '',
    order: 10,
    depth: 0,
    content: '',
    summary: '',
    status: 'vide',
    orphan: false,
    created_at: '2026-07-01T00:00:00Z',
    updated_at: '2026-07-01T00:00:00Z',
    ...overrides,
  };
}

const sections: DocumentSection[] = [
  makeSection({ id: 's-alpha', title: 'Introduction', order: 10 }),
  makeSection({ id: 's-beta', title: 'Contexte', order: 20 }),
];

function renderTree(overrides: Partial<OutlineTreeProps> = {}) {
  const onSelect = vi.fn();
  const onReorder = vi.fn();
  const onCreateSection = vi.fn();
  const onGenerateOutline = vi.fn();
  render(
    <OutlineTree
      sections={sections}
      activeSectionId={null}
      isLoading={false}
      error={null}
      onSelect={onSelect}
      onReorder={onReorder}
      onCreateSection={onCreateSection}
      onGenerateOutline={onGenerateOutline}
      {...overrides}
    />
  );
  return { onSelect, onReorder, onCreateSection, onGenerateOutline };
}

/** Le wrapper sortable de la ligne (élément portant role + tabIndex posés par useSortable). */
function getSortableWrapper(title: string): HTMLElement {
  const label = screen.getByText(title);
  const wrapper = label.closest('[aria-roledescription="sortable"]');
  if (!(wrapper instanceof HTMLElement)) {
    throw new Error(`Wrapper sortable introuvable pour ${title}`);
  }
  return wrapper;
}

describe('OutlineTree', () => {
  // NB : ce test passe AVANT les tests de drag - cf. gotcha en tête de fichier.
  it('un clic simple sur une ligne sélectionne la section (pas de drag parasite)', () => {
    const { onSelect } = renderTree();

    fireEvent.click(screen.getByText('Introduction'));

    expect(onSelect).toHaveBeenCalledTimes(1);
    expect(onSelect).toHaveBeenCalledWith('s-alpha');
  });

  describe('drag & drop (pattern BUG-041, ProjectsKanban.tsx)', () => {
    it('démarre un drag au pointeur depuis le corps de la ligne (pas seulement la poignée)', async () => {
      renderTree();

      // Geste utilisateur : attraper la ligne par son titre, puis bouger
      // au-delà de l'activationConstraint (distance 8px).
      const title = screen.getByText('Introduction');
      fireEvent.pointerDown(title, { button: 0, isPrimary: true, pointerId: 1, clientX: 5, clientY: 5 });
      fireEvent.pointerMove(document, { pointerId: 1, clientX: 5, clientY: 40 });

      // Drag actif = le DragOverlay rend une seconde ligne de la même section.
      expect(screen.getAllByText('Introduction')).toHaveLength(2);

      fireEvent.pointerUp(document, { pointerId: 1 });
      fireEvent.click(document);

      // @dnd-kit/core PointerSensor.handleStart() pose un listener `click`
      // capture-phase sur `document` (stopPropagation, anti-clic-parasite
      // post-drag d'un VRAI navigateur) retiré seulement par un
      // `setTimeout(..., 50)` interne (core.esm.js, PointerSensor.detach) -
      // PAS un `{once:true}` qu'un simple `fireEvent.click` suffirait à
      // consommer. Sans attendre ce délai réel, le listener reste actif et
      // avale le PROCHAIN clic de n'importe quel test suivant (peu importe
      // sa cible) - d'où cette pause, seule garantie fiable.
      await new Promise((resolve) => setTimeout(resolve, 60));
    });

    it('démarre un drag au clavier depuis la ligne focusée (Entrée)', async () => {
      renderTree();

      const wrapper = getSortableWrapper('Contexte');
      wrapper.focus();
      fireEvent.keyDown(wrapper, { code: 'Enter' });

      expect(screen.getAllByText('Contexte')).toHaveLength(2);

      // Le KeyboardSensor attache son listener keydown au document dans un
      // setTimeout(0) : il faut laisser passer un tick avant d'annuler.
      await new Promise((resolve) => setTimeout(resolve, 0));
      fireEvent.keyDown(wrapper, { code: 'Escape' });
      await waitFor(() => expect(screen.getAllByText('Contexte')).toHaveLength(1));
    });
  });

  describe('computeReorderPayload (logique appliquée au drop)', () => {
    it('recalcule order par pas de 10 sur TOUTE la trame, en préservant depth', () => {
      const three = [
        makeSection({ id: 's1', title: 'A', order: 10, depth: 0 }),
        makeSection({ id: 's2', title: 'B', order: 20, depth: 1 }),
        makeSection({ id: 's3', title: 'C', order: 30, depth: 0 }),
      ];

      const items = computeReorderPayload(three, 's3', 's1');

      expect(items).toEqual([
        { id: 's3', order: 10, depth: 0 },
        { id: 's1', order: 20, depth: 0 },
        { id: 's2', order: 30, depth: 1 },
      ]);
    });

    it('retourne null si active === over (pas de déplacement réel)', () => {
      expect(computeReorderPayload(sections, 's-alpha', 's-alpha')).toBeNull();
    });

    it('retourne null si un id est introuvable dans la trame', () => {
      expect(computeReorderPayload(sections, 's-inconnu', 's-alpha')).toBeNull();
    });

    // Revue adversariale lot D (finding D) : le backend exige EXACTEMENT
    // l'ensemble des sections non-orphelines (409 sinon) - une section
    // orpheline présente dans sortedSections ne doit JAMAIS finir dans items.
    it('exclut les sections orphelines du payload (contrat backend anti-409)', () => {
      const withOrphan = [
        makeSection({ id: 's1', title: 'A', order: 10, depth: 0 }),
        makeSection({ id: 's2', title: 'B', order: 20, depth: 0, orphan: true }),
        makeSection({ id: 's3', title: 'C', order: 30, depth: 0 }),
      ];

      const items = computeReorderPayload(withOrphan, 's3', 's1');

      expect(items?.some((i) => i.id === 's2')).toBe(false);
      expect(items).toEqual([
        { id: 's3', order: 10, depth: 0 },
        { id: 's1', order: 20, depth: 0 },
      ]);
    });
  });

  it('affiche les sections triées par order (pas par ordre d\'arrivée dans le tableau)', () => {
    const { container } = render(
      <OutlineTree
        sections={[
          makeSection({ id: 's-b', title: 'Deuxième', order: 20 }),
          makeSection({ id: 's-a', title: 'Première', order: 10 }),
        ]}
        activeSectionId={null}
        isLoading={false}
        error={null}
        onSelect={vi.fn()}
        onReorder={vi.fn()}
        onCreateSection={vi.fn()}
        onGenerateOutline={vi.fn()}
      />
    );

    const text = container.textContent || '';
    expect(text.indexOf('Première')).toBeLessThan(text.indexOf('Deuxième'));
  });

  it('affiche l\'erreur du store (ex. 409 de réorganisation incomplète)', () => {
    renderTree({ error: 'La réorganisation ne couvre pas exactement les sections existantes du document.' });
    expect(screen.getByText(/ne couvre pas exactement/i)).toBeInTheDocument();
  });

  it('« Ajouter une section » crée une section avec titre, consigne et profondeur choisie', () => {
    const { onCreateSection } = renderTree();

    fireEvent.click(screen.getByRole('button', { name: /Ajouter une section/i }));
    fireEvent.change(screen.getByLabelText('Titre de la nouvelle section'), {
      target: { value: 'Nouvelle section' },
    });
    fireEvent.change(screen.getByLabelText('Consigne de la nouvelle section'), {
      target: { value: 'Expliquer le contexte' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Niveau 2' }));
    fireEvent.click(screen.getByRole('button', { name: /^Créer$/i }));

    expect(onCreateSection).toHaveBeenCalledWith({
      title: 'Nouvelle section',
      brief: 'Expliquer le contexte',
      order: 30,
      depth: 1,
    });
  });

  it('« Ajouter une section » est sans effet si le titre est vide', () => {
    const { onCreateSection } = renderTree();

    fireEvent.click(screen.getByRole('button', { name: /Ajouter une section/i }));
    fireEvent.click(screen.getByRole('button', { name: /^Créer$/i }));

    expect(onCreateSection).not.toHaveBeenCalled();
  });

  it('trame vide : propose de générer la trame', () => {
    const { onGenerateOutline } = renderTree({ sections: [] });

    expect(screen.getByText(/Aucune section pour l'instant/i)).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: /Générer la trame/i }));

    expect(onGenerateOutline).toHaveBeenCalledTimes(1);
  });
});
