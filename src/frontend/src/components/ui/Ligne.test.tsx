/**
 * Ligne : une rangée de liste (grille 2 rem / 1fr / auto).
 *
 * Quand elle est cliquable, la rangée n'EST PAS un bouton : le titre l'est,
 * étiré par un pseudo-élément sur toute la surface, et les actions de droite
 * passent au-dessus (z-10). Un seul interactif, Entrée et Espace natifs,
 * aucun bouton emboîté. Sans onClick : aucun rôle, aucun tabIndex — une
 * rangée d'information n'est pas un arrêt de tabulation.
 *
 * Le détail est en text-sm : la ligne se clique, le plancher typographique
 * interdit text-xs sur un interactif.
 */
import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import { Ligne } from './Ligne';

describe('Ligne', () => {
  it('pose la grille DA, la puce de domaine, le titre 600 et le détail en sm', () => {
    const { container } = render(
      <Ligne
        domaine="agenda"
        puce="A"
        titre="Point client"
        detail="Mardi 10 h"
        droite={<span>14:00</span>}
      />,
    );

    const rangee = container.firstElementChild as HTMLElement;
    expect(rangee.className).toMatch(/grid-cols-\[2rem_1fr_auto\]/);
    expect(rangee.className).toMatch(/gap-3/);
    expect(rangee.className).toMatch(/items-center/);
    expect(rangee.className).toMatch(/px-4/);
    expect(rangee.className).toMatch(/py-3/);
    expect(rangee.className).toMatch(/border-t/);
    expect(rangee.className).toMatch(/border-border/);
    expect(rangee.className).toMatch(/hover:bg-surface-2/);

    const puce = screen.getByText('A');
    expect(puce.className).toMatch(/h-8/);
    expect(puce.className).toMatch(/w-8/);
    expect(puce.className).toMatch(/rounded-sm/);
    expect(puce.className).toMatch(/bg-domaine-agenda-tint/);
    expect(puce.className).toMatch(/text-domaine-agenda/);

    const titre = screen.getByText('Point client');
    expect(titre.className).toMatch(/font-semibold/);
    expect(titre.tagName).not.toBe('BUTTON');

    const detail = screen.getByText('Mardi 10 h');
    expect(detail.className).toMatch(/text-sm/);
    expect(detail.className).toMatch(/text-text-muted/);
    expect(detail.className).not.toMatch(/text-xs/);

    expect(screen.getByText('14:00')).toBeInTheDocument();
  });

  it('sans onClick : aucun rôle, aucun tabIndex', () => {
    const { container } = render(<Ligne titre="Lecture seule" detail="rien à faire" />);
    const rangee = container.firstElementChild as HTMLElement;

    expect(rangee.getAttribute('role')).toBeNull();
    expect(rangee.getAttribute('tabindex')).toBeNull();
    expect(screen.queryByRole('button')).not.toBeInTheDocument();
    expect(screen.getByText('Lecture seule').getAttribute('tabindex')).toBeNull();
  });

  it('avec onClick : le titre est le bouton étiré, la droite reste au-dessus', () => {
    const onClick = vi.fn();
    const { container } = render(
      <Ligne
        titre="Ouvrir le dossier"
        detail="Cliquer ouvre"
        onClick={onClick}
        droite={<button type="button">Relancer</button>}
      />,
    );

    const rangee = container.firstElementChild as HTMLElement;
    expect(rangee.className).toMatch(/\brelative\b/);

    const titre = screen.getByRole('button', { name: 'Ouvrir le dossier' });
    expect(titre).toHaveAttribute('type', 'button');
    expect(titre.className).toMatch(/before:absolute/);
    expect(titre.className).toMatch(/before:inset-0/);
    expect(titre.className).toMatch(/before:content-\[''\]/);

    const relancer = screen.getByRole('button', { name: 'Relancer' });
    expect(relancer.parentElement?.className).toMatch(/relative/);
    expect(relancer.parentElement?.className).toMatch(/z-10/);

    fireEvent.click(titre);
    expect(onClick).toHaveBeenCalledTimes(1);

    /* Entrée et Espace viennent du bouton natif : le titre EST un button,
       donc le navigateur les déclenche. On vérifie le contrat, pas un
       keyDown synthétique qui en jsdom n'active pas un button. */
    expect(titre.tagName).toBe('BUTTON');
  });

  it('en dense, réduit le padding vertical', () => {
    const { container } = render(<Ligne titre="Compacte" dense />);
    expect((container.firstElementChild as HTMLElement).className).toMatch(/py-2/);
    expect((container.firstElementChild as HTMLElement).className).not.toMatch(/py-3/);
  });
});

/**
 * Revue Grok du diff du lot 1 (P1) : la zone de droite était hissée en
 * `z-10` dès que la rangée était cliquable, même quand elle ne contient
 * qu'une heure ou un chevron : elle mangeait le clic du bouton étiré. Le
 * conteneur laisse passer le pointeur, seuls ses enfants (interactifs ou
 * non) le reçoivent. jsdom ne simule pas `pointer-events` : la garde porte
 * sur les classes, la preuve visuelle sur la recette.
 */
describe('Ligne : la zone de droite ne mange pas le clic', () => {
  it('laisse passer le pointeur vers le bouton étiré', () => {
    const { container } = render(
      <Ligne titre="Relancer Claire" detail="échue" droite={<span>12:04</span>} onClick={() => {}} />,
    );
    const droite = container.querySelector('.z-10') as HTMLElement;
    expect(droite).not.toBeNull();
    expect(droite.className).toMatch(/\bpointer-events-none\b/);
    // Seuls les vrais interactifs reçoivent le pointeur : un span (heure,
    // chevron) reste transparent au bouton étiré (second passage Grok).
    expect(droite.className).not.toMatch(/\[&>\*\]:pointer-events-auto/);
    for (const cible of ['button', 'a', 'input', 'select', 'textarea', '[role=button]']) {
      expect(droite.className, cible).toContain(`[&_${cible}]:pointer-events-auto`);
    }
  });
});

/**
 * DA lot 7 (`docs/plans/2026-09-11-da-lot7-decision-design.md`, § 1 et
 * garde 6.9) : la liste des décisions coupe ses rangées à une ligne, ce que
 * `Ligne` ne savait pas faire — le détail est rendu dans un `p` sans classe
 * transmissible. `coupe` ajoute `block w-full truncate` au libellé et
 * `truncate` au détail, et surtout **jamais** `relative` sur le bouton : son
 * `before:absolute before:inset-0` se cale sur la rangée, le positionner
 * rabattrait le pseudo-élément sur le texte et tuerait le clic étiré (P1 de
 * la revue du lot 1). jsdom ne mesure pas la coupe : la garde porte sur les
 * classes, la preuve visuelle sur la recette.
 */
describe('Ligne : la prop coupe', () => {
  const LONG = 'Faut-il accepter la mission du Garage Benali à 840 € en trois semaines ?';

  it('coupe le libellé cliquable et le détail, sans positionner le bouton', () => {
    render(<Ligne titre={LONG} detail="Accepter, à deux conditions." onClick={() => {}} coupe />);

    const titre = screen.getByRole('button', { name: LONG });
    expect(titre.className).toMatch(/\bblock\b/);
    expect(titre.className).toMatch(/\bw-full\b/);
    expect(titre.className).toMatch(/\btruncate\b/);
    expect(titre.className).not.toMatch(/\brelative\b/);
    expect(titre.className).toMatch(/before:absolute/);
    expect(titre.className).toMatch(/before:inset-0/);

    expect(screen.getByText('Accepter, à deux conditions.').className).toMatch(/\btruncate\b/);
  });

  it('coupe aussi un libellé non cliquable', () => {
    render(<Ligne titre={LONG} detail="Sans geste." coupe />);
    const titre = screen.getByText(LONG);
    expect(titre.tagName).toBe('SPAN');
    expect(titre.className).toMatch(/\bblock\b/);
    expect(titre.className).toMatch(/\bw-full\b/);
    expect(titre.className).toMatch(/\btruncate\b/);
  });

  it('sans coupe, aucune de ces classes n’apparaît', () => {
    render(<Ligne titre={LONG} detail="Accepter, à deux conditions." onClick={() => {}} />);
    const titre = screen.getByRole('button', { name: LONG });
    expect(titre.className).not.toMatch(/\btruncate\b/);
    expect(titre.className).not.toMatch(/\bw-full\b/);
    expect(screen.getByText('Accepter, à deux conditions.').className).not.toMatch(/\btruncate\b/);
  });
});
