/**
 * B-242 — « … soient envoyés à Mistralpour traitement. »
 *
 * Le piège n'est pas dans le texte, il est dans la mise en page du source :
 * `{providerLabel}` termine une ligne et « pour traitement » commence la
 * suivante. Babel comme esbuild suppriment l'indentation de tête des lignes de
 * continuation d'un JSXText, si bien que le littéral compilé vaut
 * « pour traitement… » sans espace initiale et que les deux mots se collent.
 * Le défaut ne dépend pas du fournisseur : il vient de la coupure de ligne.
 *
 * Aucun test ne lisait cette phrase — les trois tests de SecurityStep passaient
 * au vert avec le défaut à l'écran.
 */
import { render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { SecurityStep } from './SecurityStep';

function texteDuConsentement(): string {
  const consentement = screen.getByRole('checkbox').closest('label');
  expect(consentement).not.toBeNull();
  return consentement?.textContent ?? '';
}

describe('SecurityStep — le consentement sépare le nom du fournisseur du mot suivant', () => {
  beforeEach(() => vi.clearAllMocks());

  it('écrit « envoyés à Mistral pour traitement »', () => {
    render(<SecurityStep provider="mistral" onNext={vi.fn()} onBack={vi.fn()} />);

    const texte = texteDuConsentement();
    expect(texte).not.toMatch(/Mistralpour/);
    expect(texte).toMatch(/envoyés à Mistral pour traitement/);
  });

  it('vaut pour n’importe quel fournisseur cloud', () => {
    render(<SecurityStep provider="anthropic" onNext={vi.fn()} onBack={vi.fn()} />);

    const texte = texteDuConsentement();
    expect(texte).not.toMatch(/Anthropicpour/);
    expect(texte).toMatch(/envoyés à Anthropic pour traitement/);
  });
});
