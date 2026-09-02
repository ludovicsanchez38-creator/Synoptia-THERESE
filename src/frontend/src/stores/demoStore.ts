/**
 * THÉRÈSE v2 - Demo Mode Store
 *
 * Store Zustand pour le mode démo.
 * Masque les données réelles par des personas fictifs pour les vidéos de présentation.
 * Aucune donnée n'est modifiée en base - masquage purement cosmétique.
 */

import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { buildReplacementMap } from '../lib/demoMask';
import { useContactsStore } from './contactsStore';

interface DemoState {
  /** Mode démo activé */
  enabled: boolean;
  /** Map des remplacements texte (réel → fictif) - non persistée, reconstruite au besoin */
  replacementMap: Map<string, string>;
  /** Toggle on/off */
  toggle: () => void;
  /** Set enabled directement */
  setEnabled: (enabled: boolean) => void;
  /** Construire la map de remplacement depuis les contacts et projets */
  buildMap: (contacts: Array<{ first_name?: string | null; last_name?: string | null; company?: string | null; email?: string | null }>, projects: Array<{ name?: string | null }>) => void;
  /** Vider la map */
  clearMap: () => void;
}

/** Les contacts deja charges suffisent : les titres du brief citent leurs
 *  noms et leurs societes. Les projets viennent en plus quand une surface
 *  appelle buildMap avec sa propre liste. */
function mapDepuisLesContacts(): Map<string, string> {
  return buildReplacementMap(useContactsStore.getState().contacts, []);
}

export const useDemoStore = create<DemoState>()(
  persist(
    (set) => ({
      enabled: false,
      replacementMap: new Map(),

      // La map n'est pas persistee et n'etait remplie que par CRMPanel et
      // MemoryPanel. Tant qu'on n'avait ouvert ni l'un ni l'autre, activer le
      // mode demo ne masquait RIEN, nulle part — constate dans l'application
      // lancee le 01/09/2026, avec les vrais noms de clients a l'ecran. Le
      // basculement remplit donc lui-meme la map depuis les contacts deja
      // charges, et la vide en s'eteignant.
      toggle: () => {
        set((state) => {
          const enabled = !state.enabled;
          return enabled
            ? { enabled, replacementMap: mapDepuisLesContacts() }
            : { enabled, replacementMap: new Map() };
        });
      },

      setEnabled: (enabled) => {
        set(
          enabled
            ? { enabled, replacementMap: mapDepuisLesContacts() }
            : { enabled, replacementMap: new Map() },
        );
      },

      buildMap: (contacts, projects) => {
        const map = buildReplacementMap(contacts, projects);
        set({ replacementMap: map });
      },

      clearMap: () => {
        set({ replacementMap: new Map() });
      },
    }),
    {
      name: 'therese-demo-mode',
      partialize: (state) => ({
        // On ne persiste que le flag enabled, pas la map
        enabled: state.enabled,
      }),
    }
  )
);

/**
 * B-145 : le drapeau revient du stockage, la table de remplacement non.
 *
 * Après un rechargement, `enabled` valait de nouveau `true` et la table
 * repartait VIDE : le badge annonçait le mode démo pendant que `maskText`
 * redevenait l'identité et laissait les vrais noms dans le texte libre. Seuls
 * `toggle` et `setEnabled` armaient la table ; la rehydratation, jamais.
 *
 * On ne reconstruit que si la table est vide : `buildMap` (Contacts, CRM,
 * Tâches) y ajoute AUSSI les projets, et ce rattrapage ne doit pas reprendre
 * la main sur une table plus riche.
 */
function armerLaTableSiVide() {
  const etat = useDemoStore.getState();
  if (!etat.enabled || etat.replacementMap.size > 0) return;
  const map = mapDepuisLesContacts();
  if (map.size > 0) useDemoStore.setState({ replacementMap: map });
}

// L'hydratation initiale est déjà faite quand ce module finit de charger.
armerLaTableSiVide();

// Les rehydratations ultérieures (un `persist.rehydrate()` explicite).
useDemoStore.persist.onFinishHydration(armerLaTableSiVide);

// Le cas réel du rechargement : la rehydratation précède le chargement des
// contacts, donc la table serait construite vide. Elle s'arme quand le carnet
// arrive.
useContactsStore.subscribe((etat, precedent) => {
  if (etat.contacts !== precedent.contacts) armerLaTableSiVide();
});
