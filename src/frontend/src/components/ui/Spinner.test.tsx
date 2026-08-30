/**
 * Une seule façon de dire « ça charge ».
 *
 * Relevé le 27/08/2026 : 133 indicateurs de chargement dans 67 fichiers,
 * écrits de 38 façons différentes. Ce n'est pas qu'une affaire de style —
 * les tailles varient sans raison d'un écran à l'autre, et aucun n'annonce
 * quoi que ce soit à un lecteur d'écran : l'attente est invisible pour qui
 * n'a pas l'image.
 *
 * Trois tailles NOMMÉES par leur usage plutôt que par leurs pixels, pour
 * qu'on choisisse en pensant à l'endroit, pas au nombre.
 */
import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { Spinner } from './Spinner';

describe('Spinner', () => {
  it('annonce ce qu’on attend, quand on le lui demande', () => {
    render(<Spinner annonce="Envoi du message" />);

    expect(screen.getByRole('status')).toHaveAccessibleName('Envoi du message');
  });

  /**
   * Le premier jet annonçait « Chargement » par défaut. La migration des 133
   * indicateurs a montré que beaucoup vivent DANS une zone déjà annoncée : le
   * défaut créait alors une seconde annonce pour le même événement, et un test
   * existant est tombé en trouvant deux `role="status"`. Annoncer deux fois
   * est pire que ne pas annoncer.
   */
  it('reste muet par défaut, pour ne pas doubler une annonce voisine', () => {
    render(
      <div role="status" aria-label="Transcription en cours">
        <Spinner />
      </div>,
    );

    expect(screen.getAllByRole('status')).toHaveLength(1);
  });

  it('a trois tailles nommées par leur usage, toutes distinctes', () => {
    const { container: enLigne } = render(<Spinner taille="ligne" />);
    const { container: dansBouton } = render(<Spinner taille="bouton" />);
    const { container: pleineZone } = render(<Spinner taille="zone" />);

    const classe = (c: HTMLElement) => c.querySelector('svg')?.getAttribute('class') ?? '';
    const tailles = [classe(enLigne), classe(dansBouton), classe(pleineZone)];

    expect(new Set(tailles).size).toBe(3);
    for (const t of tailles) expect(t).toContain('animate-spin');
  });

  it('hérite de la couleur du texte, et laisse la surcharger', () => {
    const { container } = render(<Spinner className="text-accent-cyan-ink" />);

    expect(container.querySelector('svg')?.getAttribute('class')).toContain('text-accent-cyan-ink');
  });
});
