/**
 * B-016 — la mise en route n'annonce que ce que la finalité couvre.
 *
 * `consent.ts` écrit la règle noir sur blanc : envoyer le contenu d'un
 * document au fournisseur est une finalité DISTINCTE d'une conversation.
 * L'écran de sécurité promettait pourtant « mes messages, pièces jointes
 * sélectionnées et contexte utile » et enregistrait ces catégories sous la
 * finalité `llm`, qui ne couvre pas les documents.
 *
 * Deux conséquences, visibles dans le journal réel : l'utilisateur croit avoir
 * consenti pour ses pièces jointes alors que l'enregistrement les exclut, et
 * le composeur lui redemandera son accord sous `documents` à la première
 * pièce jointe.
 */
import { fireEvent, render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { SecurityStep } from './SecurityStep';

/** Ce qu'un accord « llm » n'a pas le droit d'annoncer. */
const HORS_FINALITE = /pièces? jointes?|document|fichier/i;

function consentementEnregistre(): string {
  const appels = vi.mocked(localStorage.setItem).mock.calls.filter(
    ([cle]) => cle === 'therese-cloud-consent',
  );
  expect(appels.length).toBe(1);
  return String(appels[0][1]);
}

describe('SecurityStep — le consentement de mise en route reste dans sa finalité', () => {
  beforeEach(() => vi.clearAllMocks());

  it('n’annonce à l’écran aucune donnée que la finalité « llm » ne couvre pas', () => {
    render(<SecurityStep provider="mistral" onNext={vi.fn()} onBack={vi.fn()} />);

    const consentement = screen.getByRole('checkbox').closest('label');
    expect(consentement).not.toBeNull();
    expect(consentement?.textContent ?? '').not.toMatch(HORS_FINALITE);
  });

  it('n’enregistre sous « llm » aucune catégorie qui relève de « documents »', () => {
    render(<SecurityStep provider="mistral" onNext={vi.fn()} onBack={vi.fn()} />);

    fireEvent.click(screen.getByRole('checkbox'));
    fireEvent.click(screen.getByTestId('onboarding-next-btn'));

    const enregistre = consentementEnregistre();
    expect(enregistre).toContain('"llm:mistral"');
    const grant = JSON.parse(enregistre).grants['llm:mistral'];
    expect(grant.purpose).toBe('llm');
    for (const categorie of grant.dataCategories as string[]) {
      expect(categorie).not.toMatch(HORS_FINALITE);
    }
  });
});
