/**
 * E — le contrôle de sortie porte un nom qu'on LIT, pas seulement qu'on entend.
 *
 * Campagne dix personas, persona 08 (responsable administratif) :
 *
 *   « Sur le côté, des petits dessins sans nom. Je n'ose pas. Je cherche
 *     Annuler : il n'y est pas. J'ai peur de casser quelque chose. »
 *
 * Le contrôle existait, en icône seule. Son `aria-label` servait aux lecteurs
 * d'écran ; l'utilisateur qui regarde l'écran, lui, ne voyait qu'un dessin.
 * Une étiquette accessible n'est pas une étiquette visible : c'est la même
 * confusion que « le test passe donc la fonction est utilisable ».
 *
 * Ce test EXÉCUTE le rendu et cherche le mot à l'écran, au lieu de vérifier
 * la présence d'un attribut dans le source.
 */
import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import { BoutonFermerLePanneau } from './BoutonFermerLePanneau';

describe('La sortie se voit', () => {
  it('le bouton affiche un texte, pas seulement une icône', () => {
    render(<BoutonFermerLePanneau onClose={vi.fn()} />);

    const bouton = screen.getByRole('button', { name: /fermer ce panneau/i });
    expect(bouton.textContent?.trim()).toBeTruthy();
    expect(bouton.textContent).toMatch(/fermer/i);
  });

  it('le texte reste dans le flux, il ne se cache pas aux lecteurs voyants', () => {
    render(<BoutonFermerLePanneau onClose={vi.fn()} />);

    const texte = screen.getByText(/^Fermer$/);
    expect(texte.className).not.toMatch(/\bsr-only\b/);
  });

  it('un clic ferme', () => {
    const onClose = vi.fn();
    render(<BoutonFermerLePanneau onClose={onClose} />);

    fireEvent.click(screen.getByRole('button', { name: /fermer ce panneau/i }));
    expect(onClose).toHaveBeenCalledOnce();
  });
});
