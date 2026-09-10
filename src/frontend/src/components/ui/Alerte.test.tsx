/**
 * Alerte : le seul bandeau d'erreur de ce lot (ton limité à « erreur »).
 *
 * role="alert" pour que le lecteur d'écran l'annonce sans qu'on pose un
 * live region à la main. L'icône est décorative (aria-hidden) : le titre
 * en gras rouge porte le sens.
 */
import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { Alerte } from './Alerte';

describe('Alerte', () => {
  it('s’annonce comme alerte, teinte d’erreur opaque, titre en gras rouge', () => {
    const { container } = render(
      <Alerte titre="Envoi impossible">Le serveur n’a pas confirmé le message.</Alerte>,
    );

    const alerte = screen.getByRole('alert');
    expect(alerte.className).toMatch(/flex/);
    expect(alerte.className).toMatch(/gap-3/);
    expect(alerte.className).toMatch(/items-start/);
    expect(alerte.className).toMatch(/px-4/);
    expect(alerte.className).toMatch(/py-3/);
    expect(alerte.className).toMatch(/rounded-sm/);
    expect(alerte.className).toContain('bg-[var(--color-error-tint)]');
    expect(alerte.className).toMatch(/border-error\/30/);
    expect(alerte.className).toMatch(/text-text/);

    const titre = container.querySelector('b');
    expect(titre).toHaveTextContent('Envoi impossible');
    expect(titre?.className).toMatch(/text-error/);

    expect(alerte).toHaveTextContent('Le serveur n’a pas confirmé le message.');
  });

  it('cache l’icône aux lecteurs d’écran quand on en donne une', () => {
    render(
      <Alerte titre="Attention" icone={<svg data-testid="icone-alerte" />}>
        Détail
      </Alerte>,
    );

    const icone = screen.getByTestId('icone-alerte');
    expect(icone.parentElement).toHaveAttribute('aria-hidden', 'true');
  });
});
