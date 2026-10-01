/** Le confinement visuel ne doit pas retirer le nom complet ni l'ouverture.
 * La géométrie est mesurée en Chromium dans le témoin Pipeline natif v2.
 */
import { fireEvent, render, screen, within } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';

import { _clearEscapeHandlers } from '../../lib/escapeStack';
import type { ContactResponse } from '../../services/api';
import { PipelineView } from './PipelineView';

afterEach(() => _clearEscapeHandlers());

const ENTREPRISE = 'Entreprise synthétique de contrôle';
const SANS_ESPACES = 'OrganisationSynthétiqueAvecUnNomSansEspaces'.repeat(4);

function contact(champs: Partial<ContactResponse>): ContactResponse {
  return {
    id: 'long-contact', first_name: null, last_name: null,
    company: null, email: 'adresse-synthetique-tres-longue@example.invalid',
    phone: null, address: null, notes: null, tags: null,
    stage: 'contact', score: 60, source: 'THERESE', last_interaction: null,
    created_at: '2026-10-01T09:00:00Z', updated_at: '2026-10-01T09:00:00Z',
    ...champs,
  };
}

describe('Pipeline : contenu des cartes longues conservé', () => {
  it.each([
    { nom: 'Interlocuteur synthétique avec un nom complet long', champs: {
      first_name: 'Interlocuteur synthétique avec un nom complet long', company: ENTREPRISE,
    } },
    { nom: SANS_ESPACES, champs: { company: SANS_ESPACES } },
  ])('conserve le nom accessible et ouvre la bonne fiche : $nom', ({ nom, champs }) => {
    const cible = contact(champs);
    const autre = contact({ id: 'autre-contact', first_name: 'Autre interlocuteur', stage: 'discovery' });
    const ouvrir = vi.fn();
    const deplacer = vi.fn();
    render(<PipelineView contacts={[cible, autre]} onContactClick={ouvrir} onStageChange={deplacer} />);

    const carte = screen.getByRole('button', { name: nom });
    expect(carte).toHaveAccessibleName(nom);
    expect(within(carte).getByText(nom)).toHaveTextContent(nom);
    expect(within(carte).getByText(cible.email!)).toHaveTextContent(cible.email!);
    if (cible.first_name) expect(within(carte).getByText(ENTREPRISE)).toHaveTextContent(ENTREPRISE);

    fireEvent.click(within(carte).getByRole('button', { name: 'Ouvrir la fiche' }));
    expect(ouvrir).toHaveBeenCalledOnce();
    expect(ouvrir).toHaveBeenCalledWith(cible);
    expect(deplacer).not.toHaveBeenCalled();
  });
});
