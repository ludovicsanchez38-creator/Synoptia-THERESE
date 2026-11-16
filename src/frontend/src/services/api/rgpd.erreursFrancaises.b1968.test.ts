import { afterEach, describe, expect, it, vi } from 'vitest';
import * as api from './rgpd';

afterEach(() => vi.unstubAllGlobals());

describe.each([
  ['export', () => api.exportContactRGPD('contact-fictif'), 'L’export des données personnelles a échoué'],
  ['anonymisation', () => api.anonymizeContact('contact-fictif', 'Demande de test'), 'L’anonymisation du contact a échoué'],
  ['consentement', () => api.renewContactConsent('contact-fictif'), 'Le renouvellement du consentement a échoué'],
  ['modification', () => api.updateContactRGPD('contact-fictif', { rgpd_consentement: true }), 'La mise à jour des informations de confidentialité a échoué'],
  ['statistiques', () => api.getRGPDStats(), 'Le chargement des statistiques de confidentialité a échoué'],
  ['base légale', () => api.inferContactRGPD('contact-fictif'), 'La détermination de la base légale a échoué'],
  ['lecture des réglages', () => api.getPurgeSettings(), 'La lecture des réglages de suppression automatique a échoué'],
  ['écriture des réglages', () => api.updatePurgeSettings(true, 12), 'L’enregistrement des réglages de suppression automatique a échoué'],
  ['protection du contact', () => api.togglePurgeExclude('contact-fictif'), 'La modification de la protection du contact contre la suppression automatique a échoué'],
] as const)('B-1968 : erreur RGPD, %s', (_etape, appeler, message) => {
  it.each(['{}', 'Service Unavailable'])('le repli est français avec le statut HTTP, corps %s', async (body) => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(body, { status: 503, statusText: 'Service Unavailable' })));
    await expect(appeler()).rejects.toThrow(`${message} (erreur 503).`);
  });

  it('conserve le détail donné par le moteur', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(JSON.stringify({ detail: 'Contact introuvable.' }), { status: 404 })));
    await expect(appeler()).rejects.toThrow('Contact introuvable.');
  });
});
