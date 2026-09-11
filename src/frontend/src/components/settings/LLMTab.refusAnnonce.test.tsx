/**
 * B-201 - le refus d'une clé API est annoncé, comme sa réussite.
 *
 * Paramètres > IA : coller une clé au mauvais format affiche « La clé API
 * doit commencer par "sk-ant-" ». Le texte est bon, actionnable, très visible
 * à l'œil - et rendu dans un `<p>` sans rôle ni région vivante. Huit lignes
 * plus bas, dans le même composant, le message de SUCCÈS porte `role="status"`.
 * L'échec muet, la réussite annoncée : l'asymétrie exacte que le chantier
 * 0.49 avait voulu fermer, restée ouverte parce que la garde de l'époque
 * n'inspectait que les bandeaux à fond teinté.
 *
 * La garde source (`lib/erreursAnnoncees.test.ts`) empêche la dérive de
 * revenir ; ce test-ci mesure la seule chose qu'un balayage de texte ne peut
 * pas voir : ce que l'arbre d'accessibilité rend vraiment.
 *
 * Lot 9 : la condition de ce refus est devenue `{cleInvalide && error && (`.
 * La garde source ne la voyait plus -- sa `CONDITION` n'acceptait pas de garde
 * devant `error` -- et affirmait donc une couverture qu'elle n'avait plus.
 * Elle a été élargie au garde optionnel (revue du diff, point 2) : les deux
 * gardes tiennent de nouveau ensemble, la source et le rendu.
 */
import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import { LLMTab } from './LLMTab';

function rendre(error: string | null, saved = false) {
  // Lot 9 : `cleInvalide` distingue un REFUS DE CLÉ de toute autre erreur ; lui
  // seul rend l'alerte ici (la coque se tait alors). L'état reproduit est le
  // même qu'avant : un préfixe refusé par `handleSaveApiKey`.
  render(
    <LLMTab
      selectedProvider="anthropic"
      selectedModel="claude-opus-5"
      apiKeys={{}}
      apiKeyInput="clé-au-mauvais-format"
      setApiKeyInput={vi.fn()}
      showApiKey={false}
      setShowApiKey={vi.fn()}
      ollamaStatus={null}
      ollamaModels={[]}
      systemResources={null}
      saving={false}
      saved={saved}
      error={error}
      cleInvalide={error !== null}
      setError={vi.fn()}
      onSelectProvider={vi.fn()}
      onSelectModel={vi.fn()}
      onSaveApiKey={vi.fn()}
    />,
  );
}

const REFUS = 'La clé API doit commencer par "sk-ant-"';

describe('B-201 - un refus de clé API n’entre pas muet dans la page', () => {
  it('le message de refus est porté par une région d’alerte', () => {
    rendre(REFUS);

    expect(screen.getByRole('alert')).toHaveTextContent(REFUS);
  });

  it('témoin : sans erreur, aucune alerte ne traîne', () => {
    rendre(null, true);

    expect(screen.queryByRole('alert')).toBeNull();
    // Le succès, lui, était déjà annoncé : la symétrie est le sujet.
    expect(screen.getByRole('status')).toHaveTextContent('Clé API enregistrée');
  });
});
