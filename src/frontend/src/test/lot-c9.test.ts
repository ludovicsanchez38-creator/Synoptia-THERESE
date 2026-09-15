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
    const reset = src.match(/useEffect\(\(\) => \{\n {4}if \(isOpen\) \{([\s\S]*?)\n {4}\}\n {2}\}, \[isOpen\]\);/);
    expect(reset, 'effet de réinitialisation à l’ouverture introuvable').not.toBeNull();
    expect(reset![1]).toMatch(/setServiceIaConserve\(null\)/);
  });

  it('B-805 : un filet hors bundle offre une issue si React ne monte jamais', () => {
    const index = readFileSync(resolve(__dirname, '..', '..', 'index.html'), 'utf8');
    expect(index).toMatch(/<script src="\/demarrage-filet\.js"><\/script>/);
    const filet = readFileSync(resolve(__dirname, '..', '..', 'public', 'demarrage-filet.js'), 'utf8');
    expect(filet).toMatch(/__thereseMonte/);
    expect(filet).toMatch(/location\.reload\(\)/);
    expect(filet).toMatch(/-webkit-app-region:no-drag/);
    // B-821 : posé au montage réel (App), pas avant createRoot.
    expect(lire('App.tsx')).toMatch(/useEffect\(\(\) => \{\n\s+\(window as unknown as \{ __thereseMonte\?: boolean \}\)\.__thereseMonte = true;/);
    expect(lire('main.tsx')).not.toMatch(/__thereseMonte/);
  });

  it('B-839 : aucune infobulle n’invite à cliquer un bouton désactivé (Réglages > Outils)', () => {
    expect(lire('components/settings/ToolsPanel.tsx')).not.toMatch(/cliquer pour démarrer/);
  });
});
