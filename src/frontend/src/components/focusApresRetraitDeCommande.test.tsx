/**
 * B-288 - une commande qui se retire sous le focus doit le rendre à un voisin.
 *
 * Trois surfaces perdaient le focus sur le corps du document : le bouton de
 * repli du volet Pistes disparaît avec le volet, les deux boutons Oui/Non de
 * l'étape guide sont démontés dès le choix, et Rédiger/Retoucher se
 * désactivent à l'instant où la rédaction démarre. Dans les trois cas la
 * tabulation suivante repartait du haut de la page (RULES-DESIGN §9.2,
 * « navigation clavier complète » et « ordre de tabulation prévisible »,
 * WCAG 2.1 A critère 2.4.3).
 *
 * Note de mesure sur le troisième cas : jsdom ne retire PAS le focus d'un
 * élément qui devient `disabled`, là où les navigateurs le rendent au corps du
 * document. Le correctif traite les deux formes, et ce test observe celle que
 * jsdom sait produire.
 */
import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import { PistesPanel } from './documents/PistesPanel';
import { SectionEditor } from './documents/SectionEditor';
import { GuideStep } from './email/wizard/GuideStep';
import type { DocumentSection } from '../services/api/documents';

vi.mock('../services/api', () => ({
  generateEmailSetupGuide: vi.fn().mockResolvedValue({ message: 'Étapes du guide' }),
}));

function sectionDeTest(): DocumentSection {
  return {
    id: 's1',
    document_id: 'd1',
    title: 'Introduction',
    brief: 'Poser le décor',
    order: 0,
    depth: 0,
    content: 'Un premier jet.',
    summary: '',
    status: 'brouillon',
    orphan: false,
    created_at: '2026-09-01T09:00:00Z',
    updated_at: '2026-09-01T09:00:00Z',
  };
}

describe('B-288 - le focus ne retombe pas sur le corps du document', () => {
  it('PistesPanel : replier le volet donne le focus au bouton de dépliage', () => {
    render(<PistesPanel pistes={[]} onExplore={vi.fn()} onIgnore={vi.fn()} />);

    const replier = screen.getByRole('button', { name: 'Replier le volet Pistes' });
    replier.focus();
    fireEvent.click(replier);

    expect(document.activeElement).toBe(
      screen.getByRole('button', { name: 'Déplier le volet Pistes' }),
    );
  });

  it("GuideStep : choisir une réponse donne le focus au bloc de guide qui la remplace", () => {
    render(<GuideStep provider="gmail" onHasProjectChange={vi.fn()} onBack={vi.fn()} />);

    const oui = screen
      .getByText(/Oui, j'ai déjà des identifiants/)
      .closest('button') as HTMLButtonElement;
    oui.focus();
    fireEvent.click(oui);

    expect(document.activeElement).toBe(screen.getByTestId('guide-message'));
    expect(document.activeElement).not.toBe(document.body);
  });

  it('SectionEditor : le démarrage de la rédaction rend le focus à la zone de contenu', () => {
    const props = {
      section: sectionDeTest(),
      error: null,
      onUpdateSection: vi.fn(),
      onDraft: vi.fn(),
      onValidate: vi.fn(),
    };
    const { rerender } = render(<SectionEditor {...props} isStreaming={false} />);

    const rediger = screen.getByRole('button', { name: /Rédiger/ });
    rediger.focus();
    expect(document.activeElement).toBe(rediger);

    rerender(<SectionEditor {...props} isStreaming={true} />);

    expect(document.activeElement).toBe(screen.getByTestId('section-content'));
  });
});
