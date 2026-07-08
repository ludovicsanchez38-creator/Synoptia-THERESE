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

interface BillingProfileState {
  /** null = profil complet (ou pas encore vérifié) */
  missing: string[] | null;
  refresh: () => Promise<void>;
}

export const useBillingProfileStore = create<BillingProfileState>((set) => ({
  missing: null,

  refresh: async () => {
    try {
      const status = await getBillingProfileStatus();
      set({ missing: status.is_complete ? null : status.missing });
    } catch {
      // Garde-fou best-effort : une erreur réseau ne doit pas bloquer le formulaire
    }
  },
}));
