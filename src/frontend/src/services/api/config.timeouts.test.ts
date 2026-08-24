/**
 * Le délai d'attente des appels de configuration (0.43.4).
 *
 * `API_TIMEOUT_MS` vaut 30 secondes et s'applique à TOUT appel passant par
 * `request()`. Douze fichiers de `services/api/` posent un opt-out explicite là
 * où l'attente est légitime — indexation, transcription, flux SSE. `config.ts`
 * n'en posait aucun, alors qu'il porte le parcours de premier usage.
 *
 * Sur la machine d'un testeur (AMD E1-7010, 1,5 GHz), le chargement du modèle
 * d'embeddings a pris 68 secondes et Ollama plusieurs minutes pour un premier
 * jeton. Trois de ses sept rapports — faux timeout du profil, « Ollama grisé »,
 * backend « indisponible » — partagent cette cause unique.
 *
 * La réponse n'est pas de tout passer en attente illimitée : un appel qui ne
 * revient jamais laisse l'utilisateur devant un écran figé, sans rien à faire.
 * Chaque famille reçoit donc un délai justifié par ce qu'elle attend vraiment.
 */
import { describe, expect, it } from 'vitest';

import { DELAIS_CONFIG } from './config';

describe('Chaque appel de configuration a un délai justifié', () => {
  it('laisse à Ollama le temps de charger un modèle', () => {
    // Un serveur Ollama qui démarre charge le modèle en mémoire avant de
    // répondre. Trente secondes ne suffisent pas sur une machine modeste, et
    // l'utilisateur voyait « indisponible » alors qu'il fallait attendre.
    expect(DELAIS_CONFIG.interrogationOllama).toBeGreaterThanOrEqual(90_000);
  });

  it('borne quand même l’attente d’Ollama', () => {
    // Sans borne, un Ollama planté fige l'écran sans recours. Mieux vaut dire
    // « il ne répond pas » et proposer de revérifier.
    expect(DELAIS_CONFIG.interrogationOllama).toBeLessThanOrEqual(180_000);
  });

  it('laisse le temps de lire un fichier de profil importé', () => {
    // L'import lit un fichier, l'analyse et peut déclencher une indexation.
    expect(DELAIS_CONFIG.importProfil).toBeNull();
  });

  it('garde un délai court pour les lectures simples', () => {
    // Ces appels ne font qu'une lecture en base : s'ils traînent, c'est une
    // panne, et il vaut mieux le dire vite.
    expect(DELAIS_CONFIG.lectureSimple).toBeLessThanOrEqual(30_000);
  });
});
