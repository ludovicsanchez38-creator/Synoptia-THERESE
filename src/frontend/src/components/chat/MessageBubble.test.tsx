/**
 * US-010 : tableaux markdown rendus (remark-gfm) + memo réparé.
 *
 * Avant : react-markdown sans remark-gfm ne parse PAS la syntaxe de tableau
 * GFM (| a | b |) → les tableaux arrivaient en texte brut. Et le memo de
 * MessageBubble était cassé par la prop onSaveAsCommand recréée à chaque
 * rendu (closure inline dans MessageList).
 */
import { render, screen, fireEvent } from '@testing-library/react';
import { describe, expect, it, vi, beforeEach } from 'vitest';
import { MessageBubble, arePropsEqual } from './MessageBubble';
import type { Message } from '../../stores/chatStore';

const { downloadSkillFileMock } = vi.hoisted(() => ({ downloadSkillFileMock: vi.fn() }));

vi.mock('../../services/api', async () => {
  const actual = await vi.importActual<typeof import('../../services/api')>('../../services/api');
  return { ...actual, downloadSkillFile: downloadSkillFileMock };
});

function makeMessage(over: Partial<Message> = {}): Message {
  return {
    id: 'm1',
    role: 'assistant',
    content: 'Bonjour',
    timestamp: new Date(),
    ...over,
  } as Message;
}

describe('MessageBubble - tableaux GFM (US-010)', () => {
  it('rend un tableau markdown GFM en vrai <table>', () => {
    const md = [
      '| Offre | Prix |',
      '| --- | --- |',
      '| FORGER | 490 |',
      '| PROPULSER | 2490 |',
    ].join('\n');
    render(<MessageBubble message={makeMessage({ content: md })} />);

    const table = screen.getByRole('table');
    expect(table).toBeTruthy();
    expect(screen.getByText('FORGER')).toBeTruthy();
    expect(screen.getAllByRole('columnheader').length).toBe(2);
  });

  it('rend le texte barré GFM (~~)', () => {
    render(<MessageBubble message={makeMessage({ content: 'prix ~~2990~~ 2490' })} />);
    const del = document.querySelector('del');
    expect(del?.textContent).toBe('2990');
  });
});

describe('MessageBubble - BUG-131 fichier de skill (bouton de téléchargement réel)', () => {
  beforeEach(() => {
    downloadSkillFileMock.mockClear();
    downloadSkillFileMock.mockResolvedValue(undefined);
  });

  const skillMsg = makeMessage({
    content: 'Voici votre présentation.',
    skillFile: {
      skill_id: 'pptx-pro',
      file_id: '8d9226e6-690f-43bd-9623-a18e88a8e297',
      file_name: 'Presentation-Therese.pptx',
      file_size: 12345,
      format: 'pptx',
    },
  });

  it('affiche un bouton de téléchargement avec le nom du fichier, sans lien relatif mort', () => {
    render(<MessageBubble message={skillMsg} />);
    expect(screen.getByText('Presentation-Therese.pptx')).toBeTruthy();
    expect(screen.getByText('Télécharger')).toBeTruthy();
    // L'ancien lien markdown vers l'URL relative /api/skills/download/... ne doit plus exister.
    expect(document.querySelector('a[href*="/api/skills/download/"]')).toBeNull();
  });

  it('clic -> downloadSkillFile(file_id, file_name)', () => {
    render(<MessageBubble message={skillMsg} />);
    fireEvent.click(screen.getByTitle(/Télécharger Presentation-Therese\.pptx/i));
    expect(downloadSkillFileMock).toHaveBeenCalledWith(
      '8d9226e6-690f-43bd-9623-a18e88a8e297',
      'Presentation-Therese.pptx'
    );
  });
});

describe('MessageBubble - comparateur memo (US-010)', () => {
  const msg = makeMessage();

  it('égal quand seul onSaveAsCommand change d identité (closure recréée)', () => {
    expect(
      arePropsEqual(
        { message: msg, onSaveAsCommand: () => {} },
        { message: msg, onSaveAsCommand: () => {} }
      )
    ).toBe(true);
  });

  it('inégal quand le message change (nouveau contenu streamé)', () => {
    expect(
      arePropsEqual(
        { message: msg },
        { message: { ...msg, content: 'Bonjour le monde' } }
      )
    ).toBe(false);
  });

  it('inégal quand onSaveAsCommand apparaît ou disparaît', () => {
    expect(arePropsEqual({ message: msg }, { message: msg, onSaveAsCommand: () => {} })).toBe(
      false
    );
  });
});
