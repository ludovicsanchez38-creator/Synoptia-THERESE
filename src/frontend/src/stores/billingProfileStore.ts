/**
 * THÉRÈSE v2 - Billing Profile Status Store
 *
 * Statut de complétude du profil émetteur (P0-PROD-2), partagé entre le
 * formulaire de facture et les Réglages. Un `useState` local dans
 * InvoiceForm ne se rafraîchissait qu'au montage : compléter le profil
 * dans Réglages pendant que le formulaire de facture reste ouvert en
 * arrière-plan (deux modales superposées, aucune n'est démontée) laissait
 * l'avertissement affiché avec l'ancien statut. Centraliser l'état permet
 * à SettingsModal d'invalider explicitement après une sauvegarde réussie.
 */

import { create } from 'zustand';
import { getBillingProfileStatus } from '../services/api';

/**
 * B-001 : trois cas, là où `missing: null` en disait deux à la fois.
 *
 * `null` servait d'état initial, de verdict « profil complet » ET de résultat
 * d'un `refresh` en échec (le `catch` était vide). Un profil que l'application
 * n'a jamais pu lire s'affichait donc exactement comme un profil vérifié et
 * conforme. Le statut de LECTURE est désormais porté à part du verdict :
 *
 * - `jamais_lu` : on n'a encore rien demandé, on ne promet rien à l'écran ;
 * - `lu` : `missing` vaut, complet (`null`) ou incomplet (la liste) ;
 * - `illisible` : la lecture a échoué et rien n'est connu — on l'annonce.
 */
export type StatutLectureProfil = 'jamais_lu' | 'lu' | 'illisible';

interface BillingProfileState {
  /** Champs manquants, ou `null` quand le profil est complet. Ne vaut que si
   *  `statutLecture === 'lu'` : sans lecture réussie, il ne dit rien. */
  missing: string[] | null;
  statutLecture: StatutLectureProfil;
  refresh: () => Promise<void>;
}

export const useBillingProfileStore = create<BillingProfileState>((set, get) => {
  /**
   * B-002 : jeton de requête, comme `usePrototypeInvoiceData` en pose déjà un.
   *
   * `refresh` a deux appelants vivants — le formulaire de facture au montage,
   * les Réglages après une sauvegarde de profil. Sans jeton, c'est la réponse
   * ARRIVÉE en dernier qui gagne, même si elle appartient à la requête la plus
   * ancienne : « SIRET manquant » revenait à l'écran juste après que
   * l'utilisateur l'avait renseigné.
   */
  let dernierJeton = 0;

  return {
    missing: null,
    statutLecture: 'jamais_lu',

    refresh: async () => {
      const jeton = ++dernierJeton;
      try {
        const status = await getBillingProfileStatus();
        if (jeton !== dernierJeton) return;
        set({ missing: status.is_complete ? null : status.missing, statutLecture: 'lu' });
      } catch {
        if (jeton !== dernierJeton) return;
        // Une panne réseau ne bloque pas le formulaire, et n'efface pas non
        // plus un verdict déjà obtenu : elle ne s'annonce que si l'on n'a
        // jamais rien pu lire.
        if (get().statutLecture !== 'lu') set({ statutLecture: 'illisible' });
      }
    },
  };
});
