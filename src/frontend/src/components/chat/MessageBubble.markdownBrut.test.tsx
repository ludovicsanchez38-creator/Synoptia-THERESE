/**
 * B-224, moitié affichage — le lien inventé arrive BRUT à l'écran.
 *
 * Pendant qu'un outil sensible attend la validation de l'utilisateur, le
 * modèle a fabriqué « **[Télécharger Tâches en cours - Léa Moreau.docx]
 * (sandbox:/Tâches en cours - Léa Moreau.docx)** ». La destination inventée
 * contient des espaces : hors chevrons, ce n'est pas une destination
 * CommonMark valide, donc remark n'analyse AUCUN lien et émet le texte
 * littéral. L'utilisateur lit des crochets, des parenthèses et « sandbox: »
 * en gras au milieu d'une phrase.
 *
 * La garde d'affichage prévue pour ce cas ne s'applique pas : le repli
 * « texte seul » de MessageBubble ne se déclenche que si ReactMarkdown a
 * VIDÉ le href, ce qui suppose qu'un lien a été reconnu.
 *
 * Ce que ce test exige est le comportement à l'écran, pas une chaîne du
 * source : le libellé reste lisible ET la syntaxe disparaît. Un correctif
 * qui blanchirait le message échouerait sur la première assertion.
 */
import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import { MessageBubble } from './MessageBubble';
import type { Message } from '../../stores/chatStore';

const { downloadSkillFileMock, fetchImageObjectUrlMock } = vi.hoisted(() => ({
  downloadSkillFileMock: vi.fn(),
  fetchImageObjectUrlMock: vi.fn(),
}));

vi.mock('../../services/api', async () => {
  const actual = await vi.importActual<typeof import('../../services/api')>(
    '../../services/api',
  );
  return {
    ...actual,
    downloadSkillFile: downloadSkillFileMock,
    fetchImageObjectUrl: fetchImageObjectUrlMock,
  };
});

function message(content: string): Message {
  return {
    id: 'b224',
    role: 'assistant',
    content,
    timestamp: new Date(),
  } as Message;
}

const LIEN_INVENTE =
  'Voici ton document. **[Télécharger Tâches en cours - Léa Moreau.docx]' +
  '(sandbox:/Tâches en cours - Léa Moreau.docx)**';

describe('B-224 — une destination non analysable ne s’affiche pas telle quelle', () => {
  it('le libellé reste lisible, la syntaxe markdown disparaît', () => {
    const { container } = render(<MessageBubble message={message(LIEN_INVENTE)} />);

    // Le message garde son sens : on ne blanchit pas la bulle.
    expect(
      screen.getByText(/Télécharger Tâches en cours - Léa Moreau\.docx/),
    ).toBeInTheDocument();

    const vu = container.textContent ?? '';
    expect(vu).not.toContain('sandbox:');
    expect(vu).not.toContain('](');
    expect(vu).not.toContain('[Télécharger');

    // Une destination que le navigateur ne sait pas suivre ne doit pas non
    // plus devenir un lien cliquable : ce serait le trou D2 à l'envers.
    expect(container.querySelector('a')).toBeNull();
  });
});

describe('B-224 — la normalisation ne casse pas les liens légitimes', () => {
  it('un lien http classique reste cliquable', () => {
    const { container } = render(
      <MessageBubble
        message={message('Voir [la doc](https://exemple.fr/guide) pour la suite.')}
      />,
    );
    const lien = container.querySelector('a');
    expect(lien).not.toBeNull();
    expect(lien?.getAttribute('href')).toBe('https://exemple.fr/guide');
    expect(lien?.textContent).toBe('la doc');
  });

  it('un lien avec titre entre guillemets garde sa destination', () => {
    const { container } = render(
      <MessageBubble
        message={message('Voir [la doc](https://exemple.fr/guide "Le guide").')}
      />,
    );
    const lien = container.querySelector('a');
    expect(lien?.getAttribute('href')).toBe('https://exemple.fr/guide');
    expect(container.textContent ?? '').not.toContain('"Le guide"');
  });
});
