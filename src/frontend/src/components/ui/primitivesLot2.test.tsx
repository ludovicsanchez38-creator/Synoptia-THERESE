/**
 * DA « Application affinée », lot 2 (écran Accueil) : extensions des
 * primitives du lot 1, dictées par le design v6 (§ 2.1) et la revue Grok.
 */
import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { Alerte } from './Alerte';
import { CarteTete } from './Carte';
import { EtatVide } from './EtatVide';
import { CLASSES_SEGMENTS, Segments, classeSegment } from './Segments';
import { Squelette } from './Squelette';

describe('CarteTete (lot 2)', () => {
  it('pose idTitre sur le h2 pour qu’une section puisse s’en nommer', () => {
    render(<CarteTete titre="Ton attention" idTitre="today-dashboard-title" />);
    expect(screen.getByRole('heading', { level: 2, name: 'Ton attention' })).toHaveAttribute('id', 'today-dashboard-title');
  });

  it('replie les actions sous le titre au lieu de le comprimer', () => {
    const { container } = render(<CarteTete titre="T" actions={<button type="button">A</button>} />);
    const tete = container.firstElementChild as HTMLElement;
    expect(tete.className).toMatch(/\bflex-wrap\b/);
    expect(tete.className).toMatch(/\bitems-center\b/);
    const actions = screen.getByRole('button', { name: 'A' }).parentElement as HTMLElement;
    expect(actions.className).toMatch(/\bflex-wrap\b/);
    expect(actions.className).toMatch(/max-\[840px\]:basis-full/);
    expect(actions.className).toMatch(/max-\[840px\]:ml-0/);
  });
});

describe('Alerte (lot 2)', () => {
  it('transmet les attributs natifs et rend l’action hors du paragraphe', () => {
    render(
      <Alerte data-testid="alerte-panne" titre="Panne" action={<button type="button">Réessayer</button>}>
        Je n’ai pas pu lire Agenda.
      </Alerte>,
    );
    const alerte = screen.getByTestId('alerte-panne');
    expect(alerte).toHaveAttribute('role', 'alert');
    const bouton = screen.getByRole('button', { name: 'Réessayer' });
    expect(alerte).toContainElement(bouton);
    expect(bouton.closest('p')).toBeNull();
    expect(screen.getByText('Je n’ai pas pu lire Agenda.').tagName).toBe('P');
  });
});

describe('EtatVide (lot 2)', () => {
  it('transmet les attributs natifs', () => {
    render(<EtatVide data-testid="today-dashboard-empty" titre="Ta journée est dégagée." />);
    expect(screen.getByTestId('today-dashboard-empty')).toContainElement(screen.getByRole('heading', { level: 3 }));
  });
});

describe('Segments (lot 2)', () => {
  it('expose ses classes et les consomme lui-même', () => {
    const { container } = render(
      <Segments label="Vue" options={[{ id: 'a', label: 'A' }, { id: 'b', label: 'B' }]} valeur="a" onChange={() => {}} />,
    );
    const groupe = container.firstElementChild as HTMLElement;
    for (const c of CLASSES_SEGMENTS.split(' ')) expect(groupe.className).toContain(c);
    const [a, b] = screen.getAllByRole('button');
    for (const c of classeSegment(true).split(' ')) expect(a.className).toContain(c);
    for (const c of classeSegment(false).split(' ')) expect(b.className).toContain(c);
    expect(classeSegment(false)).toMatch(/hover:text-text\b/);
    expect(classeSegment(true)).toMatch(/\bshadow-sm\b/);
  });
});

describe('Squelette (lot 2)', () => {
  it('accepte une classe de barre pour une puce carrée', () => {
    const { container } = render(<Squelette largeur="w-8" classeBarre="h-8 rounded-sm" />);
    const barre = container.querySelector('[aria-hidden="true"] > div:not(style)') as HTMLElement;
    expect(barre.className).toMatch(/\bh-8\b/);
    expect(barre.className).toMatch(/\brounded-sm\b/);
    expect(barre.className).not.toMatch(/\bh-3\b/);
    expect(barre.className).not.toMatch(/\brounded-full\b/);
  });
});
