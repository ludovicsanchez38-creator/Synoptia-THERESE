/**
 * B-197 - l'isolation du fond était un INSTANTANÉ pris au montage.
 *
 * `isolateOutsideDialog` ne s'exécutait qu'une fois, ses dépendances
 * `[active, isolateBackground, ref]` ne changeant jamais. Or App.tsx rend le
 * canevas de conversation ET l'assistant d'installation en `lazy`, enfants du
 * même `div[data-testid="app-main"]`, montés dans le même commit : le chunk
 * qui arrive en second REMPLACE un élément déjà isolé (le fallback du
 * Suspense) par un élément neuf, que plus rien n'isole. Résultat mesuré par la
 * persona : le rail (« Accueil », « Conversations »…) restait focalisable
 * derrière un dialogue qui se déclare pourtant `aria-modal="true"`.
 *
 * Le harnais reproduit cette forme d'arbre. Les deux branches du Suspense sont
 * des nœuds DISTINCTS (fallback puis contenu réel), donc React remplace
 * réellement l'élément : c'est bien une mutation de `childList` que le
 * correctif doit rattraper, pas une simple mise à jour d'attributs.
 */
import { render, screen, waitFor } from '@testing-library/react';
import { Suspense, lazy, useRef, useState } from 'react';
import { describe, expect, it } from 'vitest';

import { useDialogFocusTrap } from './useDialogFocusTrap';

function Fond() {
  return (
    <div data-testid="fond-reel">
      <nav data-dialog-allow aria-label="Navigation principale">
        <button>Accueil</button>
      </nav>
      <main>
        <button data-testid="bouton-du-fond">Conversations</button>
      </main>
    </div>
  );
}

const differe = { resoudre: null as null | (() => void) };
const FondDiffere = lazy(
  () =>
    new Promise<{ default: typeof Fond }>((resolve) => {
      differe.resoudre = () => resolve({ default: Fond });
    }),
);

function Coque() {
  const [ouvert, setOuvert] = useState(false);
  const ref = useRef<HTMLDivElement>(null);
  useDialogFocusTrap(ref, { active: ouvert, isolateBackground: true });

  return (
    <div data-testid="app-main">
      <Suspense fallback={<div data-testid="fond-fallback" />}>
        <FondDiffere />
      </Suspense>
      <button data-testid="ouvrir" onClick={() => setOuvert(true)}>
        Ouvrir l’assistant
      </button>
      {ouvert && (
        <div ref={ref} role="dialog" aria-modal="true" aria-label="Assistant">
          <button data-testid="dans-le-dialogue">Continuer</button>
        </div>
      )}
    </div>
  );
}

describe('B-197 - l’isolation suit le fond qui arrive après le dialogue', () => {
  it('la racine qui remplace un fallback isolé est isolée à son tour', async () => {
    const { unmount } = render(<Coque />);
    screen.getByTestId('ouvrir').click();

    // Le dialogue est ouvert pendant que le fond n'est encore que son fallback.
    await waitFor(() => {
      expect(screen.getByTestId('fond-fallback').hasAttribute('inert')).toBe(true);
    });

    // Le chunk du fond arrive ensuite : React échange les deux nœuds.
    differe.resoudre?.();
    const racine = await screen.findByTestId('fond-reel');

    await waitFor(() => {
      expect(racine.hasAttribute('inert')).toBe(true);
      expect(racine.getAttribute('aria-hidden')).toBe('true');
    });
    // Le rail derrière le dialogue n'est plus atteignable…
    expect(screen.getByTestId('bouton-du-fond').closest('[inert]')).toBe(racine);
    // …et le dialogue, lui, n'est jamais isolé.
    expect(screen.getByTestId('dans-le-dialogue').closest('[inert]')).toBeNull();

    // La fermeture rend le fond à l'application : une isolation reprise doit
    // aussi savoir se retirer, sinon l'écran resterait mort après le wizard.
    unmount();
    expect(racine.hasAttribute('inert')).toBe(false);
    expect(racine.getAttribute('aria-hidden')).toBeNull();
  });

  it('témoin : un fond déjà monté à l’ouverture reste isolé, sans double comptage', async () => {
    // Le module différé est déjà résolu par le test précédent : le fond est
    // donc présent AVANT l'ouverture, l'ordre inverse du cas ci-dessus.
    const { unmount } = render(<Coque />);
    const racine = await screen.findByTestId('fond-reel');
    expect(racine.hasAttribute('inert')).toBe(false);

    screen.getByTestId('ouvrir').click();
    await waitFor(() => expect(racine.hasAttribute('inert')).toBe(true));

    unmount();
    expect(racine.hasAttribute('inert')).toBe(false);
  });
});
