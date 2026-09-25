/**
 * THÉRÈSE v2 - useDemoMask Hook
 *
 * Hook React qui combine le store démo + les utilitaires de masquage.
 * Renvoie des identity functions quand le mode démo est désactivé (zero overhead).
 */

import { useCallback, useEffect, useMemo, useState } from 'react';
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
      // B-1419 : un panneau enrichit la table, il ne l'écrase plus (MemoryPanel
      // la remplissait sans les projets, qui redevenaient lisibles).
      const map = buildReplacementMap(contacts, projects);
      useDemoStore.setState((etat) => ({ replacementMap: new Map([...etat.replacementMap, ...map]) }));
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

/**
 * B-1419 : en démonstration, l'Accueil, « Cette semaine » et la palette
 * montraient les vrais noms tant qu'aucun panneau n'avait rempli la table
 * (`maskText` est l'identité sans table). Monté par la coque : dès que la
 * démonstration est active, la table se remplit des contacts et projets.
 */
export function useRemplirLeMasqueDeDemo(
  lireLesContacts: () => Promise<void>,
  contacts: Array<{ first_name?: string | null; last_name?: string | null; company?: string | null; email?: string | null }>,
  contactsLus: boolean,
  lireLesProjets: () => Promise<Array<{ name?: string | null }>>,
): void {
  const enabled = useDemoStore((s) => s.enabled);
  const [projets, setProjets] = useState<Array<{ name?: string | null }>>([]);
  useEffect(() => {
    if (enabled && !contactsLus) void lireLesContacts().catch(() => undefined);
  }, [enabled, contactsLus, lireLesContacts]);
  useEffect(() => {
    if (!enabled) return;
    let vivant = true;
    Promise.resolve(lireLesProjets())
      .then((liste) => { if (vivant) setProjets(liste ?? []); })
      .catch(() => undefined);
    return () => { vivant = false; };
  }, [enabled, lireLesProjets]);
  useEffect(() => {
    if (!enabled) return;
    const map = buildReplacementMap(contacts, projets);
    useDemoStore.setState((etat) => ({ replacementMap: new Map([...etat.replacementMap, ...map]) }));
  }, [enabled, contacts, projets]);
}
