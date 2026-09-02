/**
 * B-213 - Maj+Tab depuis la cible `data-dialog-autofocus` sortait du dialogue.
 *
 * Un dialogue qui se déclare `aria-modal="true"` retient le focus : aucune
 * touche ne doit en faire sortir tant qu'il est ouvert.
 *
 * Le piège ne neutralisait Tab que si `document.activeElement` valait
 * EXACTEMENT le premier ou le dernier focusable du dialogue. Or l'assistant
 * d'installation pose son focus initial sur son titre - `h1#onboarding-title`
 * porte `tabindex="-1"` et `data-dialog-autofocus` (OnboardingWizard.tsx) - et
 * `FOCUSABLE_SELECTOR` exclut explicitement `[tabindex="-1"]`. Depuis ce
 * titre, aucune des deux branches ne s'appliquait : Maj+Tab partait en natif
 * vers le tabulable précédent, hors du dialogue.
 *
 * Le même angle mort existe pour toute cible de focus non tabulable : le
 * conteneur lui-même quand le dialogue n'a aucun focusable préféré, ou un
 * titre `tabindex=-1` - motif partagé par les panneaux de la coque.
 */
import { fireEvent, render } from '@testing-library/react';
import { useRef, useState } from 'react';
import { describe, expect, it } from 'vitest';

import { useDialogFocusTrap } from './useDialogFocusTrap';

/**
 * Forme réelle d'App.tsx : un dialogue frère d'un arrière-plan tabulable, et
 * un titre autofocus non tabulable en tête du dialogue.
 */
function Coque() {
  const [ouvert, setOuvert] = useState(false);
  const ref = useRef<HTMLDivElement>(null);
  useDialogFocusTrap(ref, { active: ouvert, isolateBackground: true });
  return (
    <div>
      {/* `data-dialog-allow` : la barre de titre de la fenêtre reste joignable,
          donc jamais isolée - c'est bien vers elle que le focus s'échappait. */}
      <header data-dialog-allow>
        <button data-testid="hors-dialogue" onClick={() => setOuvert(true)}>
          Agrandir la fenêtre
        </button>
      </header>
      {ouvert && (
        <div ref={ref} role="dialog" aria-modal="true" aria-label="Assistant">
          <h1 data-testid="titre" data-dialog-autofocus tabIndex={-1}>
            Bienvenue
          </h1>
          <button data-testid="premier">Précédent</button>
          <button data-testid="dernier">Continuer</button>
        </div>
      )}
    </div>
  );
}

describe('B-213 - le piège couvre aussi la cible autofocus non tabulable', () => {
  it('le focus initial va bien sur le titre, hors de FOCUSABLE_SELECTOR', () => {
    const { getByTestId } = render(<Coque />);
    fireEvent.click(getByTestId('hors-dialogue'));

    expect(document.activeElement).toBe(getByTestId('titre'));
  });

  it('Maj+Tab depuis le titre autofocus reste dans le dialogue', () => {
    const { getByTestId } = render(<Coque />);
    fireEvent.click(getByTestId('hors-dialogue'));

    const evenement = new KeyboardEvent('keydown', {
      key: 'Tab',
      shiftKey: true,
      bubbles: true,
      cancelable: true,
    });
    document.dispatchEvent(evenement);

    expect(evenement.defaultPrevented).toBe(true);
    expect(getByTestId('dernier')).toBe(document.activeElement);
  });

  it('Tab depuis le titre laisse la navigation native descendre dans le dialogue', () => {
    // Contre-épreuve : il y a des focusables APRÈS le titre, donc rien à
    // rattraper. Neutraliser Tab ici enfermerait le focus sur le premier
    // bouton au lieu de laisser le navigateur avancer.
    const { getByTestId } = render(<Coque />);
    fireEvent.click(getByTestId('hors-dialogue'));

    const evenement = new KeyboardEvent('keydown', {
      key: 'Tab',
      bubbles: true,
      cancelable: true,
    });
    document.dispatchEvent(evenement);

    expect(evenement.defaultPrevented).toBe(false);
  });

  it('témoin : les deux bouclages historiques tiennent toujours', () => {
    const { getByTestId } = render(<Coque />);
    fireEvent.click(getByTestId('hors-dialogue'));

    getByTestId('premier').focus();
    fireEvent.keyDown(document, { key: 'Tab', shiftKey: true });
    expect(document.activeElement).toBe(getByTestId('dernier'));

    fireEvent.keyDown(document, { key: 'Tab' });
    expect(document.activeElement).toBe(getByTestId('premier'));
  });
});
