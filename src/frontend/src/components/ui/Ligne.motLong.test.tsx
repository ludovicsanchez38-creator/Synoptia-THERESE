/**
 * B-1402 (persona Zoé, cycle 13) : un prénom de 150 caractères sans espace
 * s'étendait jusqu'à 1 312 px dans la rangée des Contacts (1 024 px), passait
 * sous « RGPD ? » et les icônes, et faisait défiler la page en largeur. Un
 * e-mail long faisait pareil dans le détail. Le libellé et le détail coupent
 * désormais un mot trop long plutôt que de sortir de leur colonne.
 *
 * jsdom ne mesure pas de largeur : le test vérifie la règle de coupure posée
 * sur les deux textes, la mesure a été faite dans Chrome (1 024 px).
 */
import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { Ligne } from './Ligne';

const MOT_LONG = 'A'.repeat(150);
const COUPURE = '[overflow-wrap:anywhere]';

describe('B-1402 : un mot trop long reste dans sa colonne', () => {
  it('rangée cliquable : le libellé et le détail coupent un mot trop long', () => {
    render(<Ligne titre={MOT_LONG} detail={`${MOT_LONG}@exemple.fr`} onClick={() => {}} droite={<button type="button">Supprimer</button>} />);

    expect(screen.getByRole('button', { name: MOT_LONG }).className).toContain(COUPURE);
    expect(screen.getByText(`${MOT_LONG}@exemple.fr`).className).toContain(COUPURE);
  });

  it('rangée non cliquable : même règle', () => {
    render(<Ligne titre={MOT_LONG} />);
    expect(screen.getByText(MOT_LONG).className).toContain(COUPURE);
  });

  it('une rangée « coupe » garde sa coupure à une ligne', () => {
    render(<Ligne titre={MOT_LONG} coupe onClick={() => {}} />);
    const libelle = screen.getByRole('button', { name: MOT_LONG });
    expect(libelle.className).toContain('truncate');
    expect(libelle.className).not.toContain(COUPURE);
  });
});
