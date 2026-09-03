/**
 * B-290 et B-294 - les bulles de la session d'agent, peintes hors du thème.
 *
 * B-294 : les deux surfaces étaient écrites en rgba() littéral dans un attribut
 * `style` inline - blanc à 3 % pour l'agent, cyan à 10 % pour l'utilisateur. Le
 * thème clair est le défaut depuis le 30/08 : un blanc à 3 % posé sur #F3F6FC
 * rend exactement la couleur de la page (mesuré 1,000:1). Le garde-fou du
 * dépôt (couleursDeDomaine.test.ts) n'inspectait que les `className` et ne
 * pouvait pas le voir.
 *
 * B-290 : sur la même ligne, `borderLeft: "2px solid"` puis
 * `borderLeftColor: undefined`. React n'émet aucune valeur pour `undefined` :
 * la bordure retombait sur `currentColor`, c'est-à-dire la couleur de texte
 * fixée juste après dans le même objet - un liseré de 2 px dans l'encre la plus
 * forte de la palette, là où RULES-DESIGN §1.1 réserve le jeton `text` au texte
 * et §12 plafonne les bordures à 1 px.
 */
import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

vi.mock('../../services/api/agents', () => ({
  streamAgentSpawn: async function* () {
    yield { type: 'chunk', content: "Voici ce que j'ai trouvé." };
  },
}));

import { AgentSession } from './AgentSession';

/** Mène la session jusqu'à une bulle utilisateur et une bulle d'agent. */
async function sessionAvecUnEchange() {
  render(<AgentSession profileId="researcher" onBack={vi.fn()} />);

  fireEvent.change(screen.getByLabelText(/Message à l/), {
    target: { value: 'Analyse ce site' },
  });
  fireEvent.click(screen.getByTitle('Envoyer'));
  fireEvent.click(screen.getByRole('button', { name: /Confirmer l.appel/ }));

  const agent = await screen.findByText("Voici ce que j'ai trouvé.");
  const utilisateur = screen.getByText('Analyse ce site');
  return {
    bulleAgent: agent.closest('div') as HTMLElement,
    bulleUtilisateur: utilisateur.closest('div') as HTMLElement,
  };
}

describe('B-294 - les bulles prennent leurs surfaces dans les jetons du thème', () => {
  it("aucune des deux bulles ne peint sa surface en couleur littérale inline", async () => {
    const { bulleAgent, bulleUtilisateur } = await sessionAvecUnEchange();

    for (const bulle of [bulleAgent, bulleUtilisateur]) {
      expect(bulle.getAttribute('style') ?? '').not.toMatch(/rgba?\(/);
      expect(bulle.style.backgroundColor).toBe('');
    }
  });

  it('chaque bulle porte une classe de surface du thème', async () => {
    const { bulleAgent, bulleUtilisateur } = await sessionAvecUnEchange();

    expect(bulleAgent.className).toMatch(/\bbg-surface-2\b/);
    expect(bulleUtilisateur.className).toMatch(/\bbg-agent-cyan\/10\b/);
  });
});

describe('B-290 - la bulle d’agent a une bordure gauche colorée et fine', () => {
  it('la couleur du liseré est déclarée, et ce n’est pas celle du texte', async () => {
    const { bulleAgent } = await sessionAvecUnEchange();

    // Une classe de couleur de bordure, prise dans les jetons d'agent.
    expect(bulleAgent.className).toMatch(/\bborder-l-agent-[a-z]+\b/);
    // Et surtout : plus de `borderLeft` sans couleur dans le style inline.
    expect(bulleAgent.getAttribute('style') ?? '').not.toMatch(/border-left/);
  });

  it('le liseré ne dépasse pas 1 px (RULES-DESIGN §12)', async () => {
    const { bulleAgent } = await sessionAvecUnEchange();

    expect(bulleAgent.className).toMatch(/\bborder-l\b/);
    expect(bulleAgent.className).not.toMatch(/\bborder-l-[248]\b/);
  });
});
