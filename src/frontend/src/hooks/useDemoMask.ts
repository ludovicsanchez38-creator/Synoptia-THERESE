/**
 * THÉRÈSE v2 - useDemoMask Hook
 *
 * Hook React qui combine le store démo + les utilitaires de masquage.
 * Renvoie des identity functions quand le mode démo est désactivé (zero overhead).
 */

import { useCallback, useMemo } from 'react';
import { useDemoStore } from '../stores/demoStore';
import {
  maskContact,
  maskProject,
  maskText,
  buildReplacementMap,
  type MaskableContact,
  type MaskableProject,
} from '../lib/demoMask';

export function useDemoMask() {
  const enabled = useDemoStore((s) => s.enabled);
  const replacementMap = useDemoStore((s) => s.replacementMap);

  /**
   * Peupler la map de remplacement depuis les contacts et projets chargés.
   * À appeler quand les données sont disponibles (CRMPanel, MemoryPanel).
   */
  const populateMap = useCallback(
    (
      contacts: Array<{ first_name?: string | null; last_name?: string | null; company?: string | null; email?: string | null }>,
      projects: Array<{ name?: string | null }>
    ) => {
      if (!enabled) return;
      const map = buildReplacementMap(contacts, projects);
      useDemoStore.setState({ replacementMap: map });
    },
    [enabled]
  );

  /**
   * Masquer un contact. Identity function si mode démo off.
   */
  const maskContactFn = useCallback(
    <T extends MaskableContact>(contact: T): T => {
      if (!enabled) return contact;
      return maskContact(contact);
    },
    [enabled]
  );

  /**
   * Masquer un projet. Identity function si mode démo off.
   */
  const maskProjectFn = useCallback(
    <T extends MaskableProject>(project: T): T => {
      if (!enabled) return project;
      return maskProject(project);
    },
    [enabled]
  );

  /**
   * Masquer du texte libre (messages, titres, previews).
   * Identity function si mode démo off ou map vide.
   */
  const maskTextFn = useCallback(
    (text: string): string => {
      if (!enabled || replacementMap.size === 0) return text;
      return maskText(text, replacementMap);
    },
    [enabled, replacementMap]
  );

  return useMemo(
    () => ({
      enabled,
      maskContact: maskContactFn,
      maskProject: maskProjectFn,
      maskText: maskTextFn,
      populateMap,
      replacementMap,
    }),
    [enabled, maskContactFn, maskProjectFn, maskTextFn, populateMap, replacementMap]
  );
}
