/**
 * Cycle 6, lecteurs #294 et D202 : les quatre fournisseurs compatibles
 * OpenAI ajoutés en 0.43.4 (glm, kimi, qwen, minimax) manquaient aux tables
 * de libellés de SecurityStep et ChatInput ; la phrase de consentement
 * affichait l'identifiant brut (« vers glm »).
 */
import { describe, expect, it } from 'vitest';

import { LIBELLES_FOURNISSEURS, libelleDuFournisseur } from './libellesFournisseurs';

describe('libellés des fournisseurs d’IA', () => {
  it.each(['glm', 'kimi', 'qwen', 'minimax'] as const)('%s a un libellé lisible, différent de son identifiant', (id) => {
    expect(LIBELLES_FOURNISSEURS[id]).toBeTruthy();
    expect(libelleDuFournisseur(id)).not.toBe(id);
  });
});
