/**
 * Carte et CarteTete : la primitive de surface de la DA « Application affinée ».
 *
 * Les cartes des écrans sont encore écrites à la main (lot suivant). Cette
 * primitive fige la forme (surface, bordure, ombre sm, tête avec icône ronde)
 * pour qu'on ne réinvente pas une ombre ou un h3 à chaque écran.
 */
import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { Carte, CarteTete } from './Carte';

describe('Carte', () => {
  it('est un article par défaut, surface bordée à ombre sm', () => {
    render(
      <Carte>
        <p>Contenu</p>
      </Carte>,
    );

    const carte = screen.getByRole('article');
    expect(carte).toHaveTextContent('Contenu');
    expect(carte.className).toMatch(/bg-surface/);
    expect(carte.className).toMatch(/\bborder\b/);
    expect(carte.className).toMatch(/border-border/);
    expect(carte.className).toMatch(/rounded-md/);
    expect(carte.className).toMatch(/shadow-sm/);
    expect(carte.className).not.toMatch(/shadow-card/);
  });

  it('peut se poser en section quand on le demande', () => {
    render(
      <Carte as="section" aria-label="Dossier client">
        dossier
      </Carte>,
    );

    expect(screen.getByRole('region', { name: 'Dossier client' })).toBeInTheDocument();
    expect(screen.queryByRole('article')).not.toBeInTheDocument();
  });

  it('laisse passer une className sans perdre la forme', () => {
    render(<Carte className="mt-4">x</Carte>);
    const carte = screen.getByRole('article');
    expect(carte.className).toMatch(/mt-4/);
    expect(carte.className).toMatch(/bg-surface/);
  });
});

describe('CarteTete', () => {
  it('rend le titre en h2, la méta en 12 px muted, les actions à droite', () => {
    render(
      <Carte>
        <CarteTete
          icone={<span>A</span>}
          titre="Agenda de la semaine"
          meta="3 rendez-vous"
          actions={<button type="button">Ouvrir</button>}
        />
      </Carte>,
    );

    const titre = screen.getByRole('heading', { level: 2, name: 'Agenda de la semaine' });
    expect(titre.tagName).toBe('H2');

    const meta = screen.getByText('3 rendez-vous');
    expect(meta.className).toMatch(/text-xs/);
    expect(meta.className).toMatch(/font-medium/);
    expect(meta.className).toMatch(/text-text-muted/);

    expect(screen.getByRole('button', { name: 'Ouvrir' })).toBeInTheDocument();
  });

  it('peint l’icône en pastille ronde accent, 2 rem', () => {
    const { container } = render(
      <CarteTete icone={<span data-testid="glyphe">A</span>} titre="Titre" />,
    );

    const glyphe = screen.getByTestId('glyphe');
    const pastille = glyphe.parentElement;
    expect(pastille).not.toBeNull();
    expect(pastille?.className).toMatch(/rounded-full/);
    expect(pastille?.className).toMatch(/bg-accent-tint/);
    expect(pastille?.className).toMatch(/text-accent/);
    expect(pastille?.className).toMatch(/\bh-8\b/);
    expect(pastille?.className).toMatch(/\bw-8\b/);
    expect(container.querySelector('h2')).toHaveTextContent('Titre');
  });

  // Lot 9 : la carte du service d'IA vit SOUS le h2 de sa section. Un h2
  // imbrique dans un h2 casse le plan du document pour qui navigue par titres.
  it('niveau="h3" : le titre descend d’un cran et garde son idTitre', () => {
    const { container } = render(
      <Carte as="section" aria-labelledby="carte-service">
        <CarteTete niveau="h3" idTitre="carte-service" titre="OpenAI" />
      </Carte>,
    );

    const titre = screen.getByRole('heading', { level: 3, name: 'OpenAI' });
    expect(titre.tagName).toBe('H3');
    expect(titre).toHaveAttribute('id', 'carte-service');
    expect(container.querySelector('h2')).toBeNull();
  });
});
