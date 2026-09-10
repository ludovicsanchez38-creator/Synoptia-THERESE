/**
 * État vide : un titre, un texte, éventuellement un geste.
 *
 * C'est une zone d'information, pas un live region : on n'annonce pas
 * « aucun résultat » deux fois (le titre h3 suffit au parcours).
 */
import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { EtatVide } from './EtatVide';

describe('EtatVide', () => {
  it('centre un h3 et le texte muted, sans rôle d’alerte', () => {
    const { container } = render(
      <EtatVide titre="Aucun rendez-vous">
        Les événements du jour apparaîtront ici.
      </EtatVide>,
    );

    const zone = container.firstElementChild as HTMLElement;
    expect(zone.tagName).toBe('DIV');
    expect(zone.className).toMatch(/px-4/);
    expect(zone.className).toMatch(/py-8/);
    expect(zone.className).toMatch(/text-center/);
    expect(zone.className).toMatch(/text-text-muted/);

    const titre = screen.getByRole('heading', { level: 3, name: 'Aucun rendez-vous' });
    expect(titre.className).toMatch(/text-text/);

    expect(screen.getByText('Les événements du jour apparaîtront ici.')).toBeInTheDocument();
    expect(screen.queryByRole('alert')).not.toBeInTheDocument();
    expect(screen.queryByRole('status')).not.toBeInTheDocument();
  });

  it('rend l’action sous le texte quand on en donne une', () => {
    render(
      <EtatVide titre="Aucun contact" action={<button type="button">Créer un contact</button>}>
        Ajoute un premier contact pour commencer.
      </EtatVide>,
    );

    const bouton = screen.getByRole('button', { name: 'Créer un contact' });
    const texte = screen.getByText('Ajoute un premier contact pour commencer.');
    expect(bouton.compareDocumentPosition(texte) & Node.DOCUMENT_POSITION_PRECEDING).toBeTruthy();
  });
});
