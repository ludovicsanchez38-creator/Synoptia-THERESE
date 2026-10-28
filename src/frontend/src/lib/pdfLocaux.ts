import { resolveResource } from '@tauri-apps/api/path';
import { openPath } from '@tauri-apps/plugin-opener';
import { invoke } from '@tauri-apps/api/core';
import { getSessionToken, initializeAuth } from '../services/api/core';

export const GUIDE_VERSION = '0.82';
export const GUIDE_RESSOURCE = 'resources/guide-therese-0.82.pdf';

export async function ouvrirGuide(): Promise<void> {
  await openPath(await resolveResource(GUIDE_RESSOURCE));
}

export async function ouvrirPdfFacture(invoiceId: string): Promise<void> {
  // Reprendre le jeton après une éventuelle relance du moteur.
  await initializeAuth();
  const token = getSessionToken();
  if (!token) throw new Error('Le moteur local n’est pas encore prêt. Réessaie.');
  await invoke('ouvrir_pdf_facture', { invoiceId, token });
}
