/**
 * US-010 : tableaux markdown rendus (remark-gfm) + memo réparé.
 *
 * Avant : react-markdown sans remark-gfm ne parse PAS la syntaxe de tableau
 * GFM (| a | b |) → les tableaux arrivaient en texte brut. Et le memo de
 * MessageBubble était cassé par la prop onSaveAsCommand recréée à chaque
 * rendu (closure inline dans MessageList).
 */
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, expect, it, vi, beforeEach } from 'vitest';
import { MessageBubble, arePropsEqual } from './MessageBubble';
import type { Message } from '../../stores/chatStore';
import { useStatusStore } from '../../stores/statusStore';

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

describe('Fichiers générés visibles (suggestion Dr_logic, 10/07)', () => {
  const skillFile = {
    skill_id: 'xlsx-pro',
    file_id: 'f1',
    file_name: 'scoring.xlsx',
    file_size: 4917,
    format: 'xlsx',
    local_dir: '/Users/toto/.therese/outputs',
  };

  it('affiche un bloc « Fichier généré » avec nom et taille lisible', () => {
    render(<MessageBubble message={makeMessage({ skillFile })} />);
    expect(screen.getByText(/fichier généré/i)).toBeInTheDocument();
    expect(screen.getByText('scoring.xlsx')).toBeInTheDocument();
    expect(screen.getByText(/4,8 ?Ko/)).toBeInTheDocument();
  });

  it('propose « Afficher dans le dossier » quand le chemin local est connu', () => {
    render(<MessageBubble message={makeMessage({ skillFile })} />);
    expect(
      screen.getByRole('button', { name: /afficher dans le dossier/i })
    ).toBeInTheDocument();
  });

  it('sans chemin local (contexte web), pas de bouton dossier', () => {
    render(
      <MessageBubble
        message={makeMessage({ skillFile: { ...skillFile, local_dir: undefined } })}
      />
    );
    expect(
      screen.queryByRole('button', { name: /afficher dans le dossier/i })
    ).not.toBeInTheDocument();
  });
});

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

  it('échec de téléchargement (fichier introuvable) -> notification erreur', async () => {
    // Revue adversariale : au reload d'une conversation dont le fichier a été
    // purgé, le clic ne doit pas rester silencieux.
    const notifSpy = vi.fn();
    useStatusStore.setState({ addNotification: notifSpy });
    downloadSkillFileMock.mockRejectedValueOnce(new Error('404'));

    render(<MessageBubble message={skillMsg} />);
    fireEvent.click(screen.getByTitle(/Télécharger Presentation-Therese\.pptx/i));

    await waitFor(() => expect(notifSpy).toHaveBeenCalled());
    expect(notifSpy).toHaveBeenCalledWith(
      expect.objectContaining({ type: 'error' })
    );
  });
});

describe('MessageBubble - BUG-130 code du générateur masqué quand un fichier est produit', () => {
  const codeMsg = makeMessage({
    content: [
      'Voici le tableau demandé.',
      '',
      '```python',
      'from openpyxl import Workbook',
      'wb = Workbook()',
      'ws = wb.active',
      'ws.append(["Offre", "Prix"])',
      'wb.save("offres.xlsx")',
      '```',
      '',
      'Bonne journée.',
    ].join('\n'),
    skillFile: {
      skill_id: 'xlsx-pro',
      file_id: 'abc-123',
      file_name: 'Offres.xlsx',
      file_size: 4917,
      format: 'xlsx',
    },
  });

  it('masque le mur de code openpyxl mais garde la prose et le bouton', () => {
    render(<MessageBubble message={codeMsg} />);
    // Le mur de code du générateur ne doit plus s'afficher.
    expect(document.body.textContent).not.toContain('openpyxl');
    expect(document.body.textContent).not.toContain('wb.save');
    // La prose du modèle, elle, reste visible.
    expect(screen.getByText(/Voici le tableau demandé/)).toBeTruthy();
    expect(screen.getByText(/Bonne journée/)).toBeTruthy();
    // Le bouton de téléchargement porte le fichier généré.
    expect(screen.getByText('Offres.xlsx')).toBeTruthy();
    expect(screen.getByText('Télécharger')).toBeTruthy();
  });

  it('code seul (sans prose) -> message de repli au lieu du code brut', () => {
    const codeOnly = makeMessage({
      content: '```python\nfrom openpyxl import Workbook\nwb = Workbook()\nwb.save("x.xlsx")\n```',
      skillFile: {
        skill_id: 'xlsx-pro',
        file_id: 'def-456',
        file_name: 'Donnees.xlsx',
        file_size: 1234,
        format: 'xlsx',
      },
    });
    render(<MessageBubble message={codeOnly} />);
    expect(document.body.textContent).not.toContain('openpyxl');
    expect(screen.getByText('Voici ton fichier.')).toBeTruthy();
    expect(screen.getByText('Donnees.xlsx')).toBeTruthy();
  });

  it('pendant le streaming, le code reste visible (retour de progression)', () => {
    const streaming = makeMessage({
      content: '```python\nfrom openpyxl import Workbook',
      isStreaming: true,
    });
    render(<MessageBubble message={streaming} />);
    // Le fichier n'est pas encore produit : on ne masque rien, l'utilisateur
    // voit la génération avancer.
    expect(document.body.textContent).toContain('openpyxl');
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

describe('BUG-136 - plusieurs fichiers par tour', () => {
  it('rend une carte par fichier généré', () => {
    const message = {
      id: 'm-multi',
      role: 'assistant' as const,
      content: 'Deux fichiers créés.',
      timestamp: new Date(),
      skillFiles: [
        {
          skill_id: 'docx-pro', file_id: 'f1', file_name: 'un.docx',
          file_size: 1000, format: 'docx', local_dir: '/tmp',
        },
        {
          skill_id: 'docx-pro', file_id: 'f2', file_name: 'deux.docx',
          file_size: 2000, format: 'docx', local_dir: '/tmp',
        },
      ],
    };
    render(<MessageBubble message={message as never} />);
    expect(screen.getAllByText('Fichier généré')).toHaveLength(2);
    expect(screen.getByText('un.docx')).toBeInTheDocument();
    expect(screen.getByText('deux.docx')).toBeInTheDocument();
  });

  it('repli legacy : skillFile seul rend une carte', () => {
    const message = {
      id: 'm-legacy',
      role: 'assistant' as const,
      content: 'Un fichier.',
      timestamp: new Date(),
      skillFile: {
        skill_id: 'docx-pro', file_id: 'f9', file_name: 'legacy.docx',
        file_size: 500, format: 'docx',
      },
    };
    render(<MessageBubble message={message as never} />);
    expect(screen.getAllByText('Fichier généré')).toHaveLength(1);
    expect(screen.getByText('legacy.docx')).toBeInTheDocument();
  });
});
