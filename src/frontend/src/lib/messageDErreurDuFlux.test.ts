/**
 * B-1395 (persona Zoé, cycle 13) : recharger la page pendant une réponse
 * laissait une bulle « network error » de Thérèse, en anglais, brute.
 * L'erreur d'un flux interrompu se dit en français, avec le geste à faire.
 */
import { describe, expect, it } from 'vitest';
import { ApiError } from '../services/api/core';
import { messageDErreurDuFlux } from './messageDErreurDuFlux';

describe('messageDErreurDuFlux (B-1395)', () => {
  it('une coupure en plein flux ne montre jamais le texte brut du navigateur', () => {
    for (const brut of ['network error', 'Failed to fetch', 'Load failed', 'NetworkError when attempting to fetch resource.']) {
      const texte = messageDErreurDuFlux(new TypeError(brut));
      expect(texte, brut).not.toContain(brut);
      expect(texte, brut).toMatch(/^Réponse interrompue/);
      expect(texte, brut).toMatch(/renvoie-la/);
    }
  });

  it('un moteur injoignable se dit sans « Erreur serveur (0) »', () => {
    const texte = messageDErreurDuFlux(new ApiError(0, 'NetworkError', 'Impossible de contacter le serveur'));
    expect(texte).not.toContain('(0)');
    expect(texte).toMatch(/^Réponse interrompue/);
  });

  it('une erreur du moteur garde son statut et son message', () => {
    expect(messageDErreurDuFlux(new ApiError(503, 'Service Unavailable', 'Le fournisseur ne répond pas.')))
      .toBe('Erreur serveur (503): Le fournisseur ne répond pas.');
  });
});
