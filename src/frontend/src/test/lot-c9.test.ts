/**
 * Lot c9 (15/09/2026) : gardes de source pour les correctifs d'une ligne du
 * cycle 9 qu'aucun test de composant ne peut atteindre à coût raisonnable.
 */
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { describe, expect, it } from 'vitest';

const lire = (f: string) => readFileSync(resolve(__dirname, '..', f), 'utf8');

describe('lot c9 - gardes de source', () => {
  it('B-772 : la réouverture de l’assistant remet à zéro l’avertissement de service d’IA conservé', () => {
    const src = lire('components/onboarding/OnboardingWizard.tsx');
    const reset = src.match(/useEffect\(\(\) => \{\n    if \(isOpen\) \{([\s\S]*?)\n    \}\n  \}, \[isOpen\]\);/);
    expect(reset, 'effet de réinitialisation à l’ouverture introuvable').not.toBeNull();
    expect(reset![1]).toMatch(/setServiceIaConserve\(null\)/);
  });
});
