/**
 * B-280 et B-285 - ce qu'un lecteur d'écran entend d'une notification.
 *
 * B-280 : deux mécanismes annonçaient la même notification. Le conteneur des
 * toasts était lui-même une région live (role="status" + aria-live="polite")
 * ET `announceToScreenReader` posait une seconde région sr-only portant le
 * même texte. La règle est écrite dans le dépôt depuis le 27/08 :
 * « Annoncer deux fois est pire que ne pas annoncer » (Spinner.test.tsx).
 * Des deux, seule l'annonce explicite sait passer en `assertive` sur une
 * erreur : c'est donc la région du conteneur qui devait tomber.
 *
 * B-285 : le bouton de fermeture n'avait ni texte, ni title, ni aria-label -
 * son unique enfant est le <svg> de lucide, qui ne porte aucun nom. Nom
 * accessible vide, annoncé « bouton » et rien de plus (RULES-DESIGN §8 et
 * §9.3, WCAG 2.1 AA critère 4.1.2).
 */
import { act, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { Notifications } from './Notifications';
import { useStatusStore } from '../../stores/statusStore';

/** Les régions live du document qui portent effectivement ce texte. */
function regionsPortant(texte: string): Element[] {
  return Array.from(document.querySelectorAll('[role="status"],[role="alert"],[aria-live]')).filter(
    (r) => (r.textContent || '').includes(texte),
  );
}

describe('B-280 - une notification est annoncée une seule fois', () => {
  beforeEach(() => {
    vi.useFakeTimers();
    useStatusStore.setState({ notifications: [] });
    // L'annonceur sr-only vit 1000 ms : il survivrait d'un test à l'autre.
    document.body.querySelectorAll('.sr-only').forEach((n) => n.remove());
  });
  afterEach(() => {
    vi.useRealTimers();
  });

  it('une seule région live porte le texte de la notification', () => {
    render(<Notifications />);

    act(() => {
      useStatusStore.setState({
        notifications: [
          {
            id: 'n1',
            type: 'info',
            title: 'Facture enregistrée',
            message: 'Devis 2026-004',
            timestamp: new Date(),
          },
        ],
      });
    });
    act(() => {
      vi.advanceTimersByTime(150);
    });

    expect(
      regionsPortant('Facture enregistrée').map(
        (r) => `${r.tagName}[role=${r.getAttribute('role')} live=${r.getAttribute('aria-live')}]`,
      ),
    ).toHaveLength(1);
  });

  it("une erreur est annoncée en assertive, la seule chose que la région du conteneur ne savait pas faire", () => {
    render(<Notifications />);

    act(() => {
      useStatusStore.setState({
        notifications: [
          { id: 'n2', type: 'error', title: 'Échec envoi', timestamp: new Date() },
        ],
      });
    });
    act(() => {
      vi.advanceTimersByTime(150);
    });

    const regions = regionsPortant('Échec envoi');
    expect(regions).toHaveLength(1);
    expect(regions[0].getAttribute('aria-live')).toBe('assertive');
  });
});

describe('B-285 - le bouton de fermeture d’une notification porte un nom', () => {
  beforeEach(() => {
    useStatusStore.setState({ notifications: [] });
    document.body.querySelectorAll('.sr-only').forEach((n) => n.remove());
  });

  it('chaque notification affichée expose un bouton « Fermer » nommé', () => {
    useStatusStore.setState({
      notifications: [
        { id: 'a', type: 'info', title: 'Première', timestamp: new Date() },
        { id: 'b', type: 'warning', title: 'Seconde', timestamp: new Date() },
      ],
    });
    render(<Notifications />);

    expect(screen.getAllByRole('button', { name: /fermer/i })).toHaveLength(2);
  });
});
