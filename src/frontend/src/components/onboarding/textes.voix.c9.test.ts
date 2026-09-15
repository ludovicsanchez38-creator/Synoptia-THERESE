/**
 * B-859 (cycle 9) : la fiche de risque « Transcription vocale » de la mise en
 * route affirmait que l'audio part chez Groq, sans dire qu'une transcription
 * locale existe (Réglages > Confidentialité : « La dictée reste possible en
 * 100 % local »). Le catalogue annonce « Whisper et Piper » pour la même
 * fonction : la fiche contredisait le reste de l'application.
 */
import { describe, expect, it } from 'vitest';

import { TEXTES_ONBOARDING } from './textes';

describe('textes de mise en route - B-859, la fiche voix connaît la dictée locale', () => {
  it('mentionne la transcription locale à côté de l’envoi à Groq', () => {
    const risques = Object.values(TEXTES_ONBOARDING).flatMap((section) => (Array.isArray(section) ? section : []));
    const voix = risques.find((r) => typeof r === 'object' && r !== null && 'id' in r && r.id === 'voix') as { description: string } | undefined;
    expect(voix).toBeDefined();
    expect(voix!.description).toMatch(/Groq/);
    expect(voix!.description).toMatch(/local/i);
  });
});
