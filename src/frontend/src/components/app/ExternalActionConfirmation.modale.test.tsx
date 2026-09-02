/**
 * B-251 : la carte de confirmation annonçait `aria-modal` sans rien tenir.
 *
 * `useDialogFocusTrap.ts:1-19` se déclare « source unique de vérité du
 * comportement modal clavier » — focus initial dans le dialogue, Tab et
 * Shift+Tab bouclés, Échap, retour du focus au déclencheur — et dit
 * s'appliquer « aux modales artisanales ». La carte posait `role="dialog"` et
 * `aria-modal="true"` sans jamais appeler le hook : `trapStackTaille()`
 * restait à zéro, le focus ne quittait pas le déclencheur, Échap ne fermait
 * rien. Un utilisateur au clavier se retrouvait annoncé « dans une boîte de
 * dialogue » tout en tabulant dans la page qui la porte.
 *
 * Point de départ : le test de reproduction RP19
 * (`.cartography-work/reproductions/c2-RP19.json`), qui VÉRIFIAIT le défaut ;
 * ce test-ci exige le comportement promis. `trapStackTaille()` porte la
 * preuve : en jsdom, un clic ne déplace pas le focus, si bien que le
 * déclencheur reste `activeElement` avec ou sans piège — c'est le contenu de
 * la pile, puis le focus effectivement posé DANS la carte, qui distinguent.
 *
 * Le contrat fail-open de `useExternalActionConfirmation` (sans provider,
 * l'action part immédiatement) n'est pas touché ici : ce test ne parle que du
 * clavier et du focus.
 */
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';

import { PrototypeExternalActionConfirmationProvider } from './ExternalActionConfirmation';
import { useExternalActionConfirmation } from './useExternalActionConfirmation';
import { trapStackTaille } from '../../hooks/useDialogFocusTrap';

const apercu = {
  title: 'Confirmer',
  description: 'Un effet hors de la machine.',
  confirmLabel: 'Confirmer',
  details: [{ label: 'Destination', value: 'a@b.fr' }],
};

function Declencheur({ action }: { action: () => void }) {
  const request = useExternalActionConfirmation();
  return (
    <button type="button" onClick={() => request(apercu, action)}>
      Préparer
    </button>
  );
}

function monterEtOuvrir(action = vi.fn()) {
  render(
    <PrototypeExternalActionConfirmationProvider>
      <Declencheur action={action} />
    </PrototypeExternalActionConfirmationProvider>,
  );
  const declencheur = screen.getByRole('button', { name: 'Préparer' });
  declencheur.focus();
  fireEvent.click(declencheur);
  return { declencheur, action };
}

describe('B-251 : la carte de confirmation tient sa promesse modale', () => {
  afterEach(() => {
    // Le démontage doit RENDRE le piège. `cleanup()` est appelé ici
    // explicitement : les `afterEach` s'exécutent en ordre inverse de leur
    // déclaration, donc celui de testing-library passerait APRÈS et la pile
    // serait encore pleine — le garde-fou mesurerait alors le montage, pas le
    // démontage. `cleanup` est idempotent, l'appel automatique suit sans mal.
    cleanup();
    expect(trapStackTaille()).toBe(0);
  });

  it('ouvre un vrai piège clavier et y amène le focus', () => {
    monterEtOuvrir();

    const carte = screen.getByTestId('external-action-confirmation');
    expect(carte).toHaveAttribute('aria-modal', 'true');

    // La promesse `aria-modal` est tenue par le piège, pas par l'attribut.
    expect(trapStackTaille()).toBe(1);
    expect(carte.contains(document.activeElement)).toBe(true);
  });

  it('Échap ferme la carte et rend le focus au déclencheur', async () => {
    const { declencheur, action } = monterEtOuvrir();
    expect(screen.getByTestId('external-action-confirmation')).toBeInTheDocument();

    fireEvent.keyDown(document, { key: 'Escape' });

    await waitFor(() =>
      expect(screen.queryByTestId('external-action-confirmation')).toBeNull(),
    );
    // Échap ABANDONNE : l'effet externe ne doit jamais partir de là.
    expect(action).not.toHaveBeenCalled();
    expect(document.activeElement).toBe(declencheur);
  });

  it("Échap reste sans effet pendant que l'action est en vol", async () => {
    // Le bouton « Annuler » est `disabled` tant que l'action tourne : Échap ne
    // doit pas offrir une sortie que l'écran refuse, ni escamoter la carte
    // au-dessus d'un effet externe déjà parti.
    let libere: () => void = () => {};
    const action = vi.fn(() => new Promise<void>((resolve) => { libere = resolve; }));
    monterEtOuvrir(action);

    fireEvent.click(screen.getByRole('button', { name: 'Confirmer' }));
    await waitFor(() => expect(action).toHaveBeenCalledTimes(1));

    fireEvent.keyDown(document, { key: 'Escape' });
    expect(screen.getByTestId('external-action-confirmation')).toBeInTheDocument();

    libere();
    await waitFor(() =>
      expect(screen.queryByTestId('external-action-confirmation')).toBeNull(),
    );
  });
});
