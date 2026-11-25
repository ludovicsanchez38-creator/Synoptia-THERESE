import { invoke } from '@tauri-apps/api/core';
import { getSessionToken, initializeAuth } from '../services/api/core';

export async function ouvrirPdfFacture(invoiceId: string): Promise<void> {
  // Reprendre le jeton après une éventuelle relance du moteur.
  await initializeAuth();
  const token = getSessionToken();
  if (!token) throw new Error('Le moteur local n’est pas encore prêt. Réessaie.');
  await invoke('ouvrir_pdf_facture', { invoiceId, token });
}
