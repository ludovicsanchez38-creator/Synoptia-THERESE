/**
 * US-013 : scan axe-core automatisé sur les composants clés.
 *
 * jsdom ne calcule pas les styles en cascade, donc les règles de CONTRASTE
 * sont vérifiées séparément (calcul direct sur les tokens du design system).
 * axe couvre ici : ARIA (roles, labels), structure des dialogues, boutons.
 */
import { render } from '@testing-library/react';
import { axe } from 'vitest-axe';
import { describe, expect, it } from 'vitest';
import { DialogShell } from '../components/ui/DialogShell';
import { SetupChecklist } from '../components/home/SetupChecklist';

// ---------------------------------------------------------------------------
// Contraste WCAG : calcul direct (jsdom n'applique pas les feuilles de style)
// ---------------------------------------------------------------------------

function luminance(hex: string): number {
  const v = hex.replace('#', '');
  const [r, g, b] = [0, 2, 4].map((i) => {
    const c = parseInt(v.slice(i, i + 2), 16) / 255;
    return c <= 0.04045 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4);
  });
  return 0.2126 * r + 0.7152 * g + 0.0722 * b;
}

function contrast(fg: string, bg: string): number {
  const [l1, l2] = [luminance(fg), luminance(bg)].sort((a, b) => b - a);
  return (l1 + 0.05) / (l2 + 0.05);
}

// Tokens du design system (globals.css) - à maintenir en phase
const LIGHT_BG = '#F3F6FC';
const LIGHT_SURFACE = '#FFFFFF';
const DARK_BG = '#0B1226';
const DARK_SURFACE = '#131B35';

const LIGHT_SEMANTIC = {
  success: '#047857',
  warning: '#A16207',
  error: '#B91C1C',
  info: '#1D4ED8',
};
const DARK_SEMANTIC = {
  success: '#10B981',
  warning: '#F59E0B',
  error: '#EF4444',
  info: '#60A5FA',
};

describe('US-013 : contraste AA des tokens sémantiques', () => {
  it.each(Object.entries(LIGHT_SEMANTIC))(
    'thème clair : %s lisible sur fond et surface (>= 4.5:1)',
    (_name, color) => {
      expect(contrast(color, LIGHT_BG)).toBeGreaterThanOrEqual(4.5);
      expect(contrast(color, LIGHT_SURFACE)).toBeGreaterThanOrEqual(4.5);
    }
  );

  it.each(Object.entries(DARK_SEMANTIC))(
    'thème sombre : %s lisible sur fond et surface (>= 4.5:1)',
    (_name, color) => {
      expect(contrast(color, DARK_BG)).toBeGreaterThanOrEqual(4.5);
      expect(contrast(color, DARK_SURFACE)).toBeGreaterThanOrEqual(4.5);
    }
  );

  it('texte principal lisible dans les deux thèmes', () => {
    expect(contrast('#101C36', LIGHT_BG)).toBeGreaterThanOrEqual(7);
    expect(contrast('#E6EDF7', DARK_BG)).toBeGreaterThanOrEqual(7);
  });
});

// ---------------------------------------------------------------------------
// Scan axe sur les composants
// ---------------------------------------------------------------------------

describe('US-013 : axe sans violation', () => {
  it('DialogShell : dialogue conforme (role, aria-modal, label)', async () => {
    const { container } = render(
      <DialogShell open onClose={() => {}} ariaLabel="Dialogue de test">
        <div>
          <h2>Titre</h2>
          <button>Valider</button>
          <button>Annuler</button>
        </div>
      </DialogShell>
    );
    const results = await axe(container);
    expect(results.violations).toEqual([]);
  });

  it('SetupChecklist : boutons nommés, structure saine', async () => {
    const { container } = render(
      <SetupChecklist
        status={{
          has_calendar: false,
          has_email: false,
          billing_complete: false,
          has_llm_key: false,
        }}
      />
    );
    const results = await axe(container);
    expect(results.violations).toEqual([]);
  });
});
