/**
 * THÉRÈSE v2 - Logique de réorganisation de la trame (Atelier documentaire, D3)
 *
 * Extrait de `OutlineTree.tsx` dans son propre module : un fichier de
 * composant React qui exporte aussi une fonction utilitaire déclenche le
 * lint `react-refresh/only-export-components` (Fast Refresh cassé) - le
 * budget du projet est déjà à son plafond (`--max-warnings 27`, cf
 * CLAUDE.md « 27 warnings ESLint préexistants »), donc pas de marge pour un
 * avertissement supplémentaire.
 *
 * Fonction pure - testée indépendamment du geste DnD réel (jsdom ne mesure
 * aucun rect de layout, donc la détection de collision de @dnd-kit n'est
 * pas fiable à piloter précisément en test).
 */
import { arrayMove } from '@dnd-kit/sortable';
import type { DocumentSection, SectionsReorderItem } from '../../services/api/documents';

/**
 * Calcule la nouvelle trame complète (ordre recalculé par pas de 10,
 * profondeur inchangée) après un déplacement `activeId` -> `overId`.
 * Retourne `null` si le déplacement est un no-op (mêmes ids, ou ids
 * introuvables dans `sortedSections`).
 *
 * Revue adversariale lot D (finding D) : le backend exige EXACTEMENT
 * l'ensemble des sections non-orphelines (409 sinon, `documents.py
 * reorder_sections`) - les sections `orphan: true` sont exclues du payload
 * (ordre recalculé sur les seules sections restantes).
 */
export function computeReorderPayload(
  sortedSections: DocumentSection[],
  activeId: string,
  overId: string
): SectionsReorderItem[] | null {
  if (activeId === overId) return null;
  const oldIndex = sortedSections.findIndex((s) => s.id === activeId);
  const newIndex = sortedSections.findIndex((s) => s.id === overId);
  if (oldIndex === -1 || newIndex === -1) return null;

  const reordered = arrayMove(sortedSections, oldIndex, newIndex);
  return reordered
    .filter((section) => !section.orphan)
    .map((section, index) => ({
      id: section.id,
      order: (index + 1) * 10,
      depth: section.depth,
    }));
}
