/**
 * Persona Sophie (c4), quatre constats sur l'éditeur de section :
 * - B-627 : pendant la génération de la trame, le volet central disait
 *   « Sélectionne une section » alors qu'il n'y en avait aucune ;
 * - B-628 : « Explorer » une piste préremplit un champ à 1 247 px de haut dans
 *   une fenêtre de 800 px, sans défiler ni signaler ;
 * - B-629 : le champ « Instruction de retouche » n'a que 139 px de large sur
 *   une ligne partagée avec trois boutons (preuve de largeur : visuelle ; ici
 *   on vérifie la structure : le champ occupe sa propre ligne) ;
 * - B-633 : la rédaction « en streaming » n'affiche rien pendant plusieurs
 *   minutes (modèle local qui raisonne avant d'écrire) et le nœud `status`
 *   est vide pour une synthèse vocale.
 */
import { fireEvent, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { SectionEditor, type SectionEditorProps } from './SectionEditor';
import type { DocumentSection } from '../../services/api/documents';

function makeSection(overrides: Partial<DocumentSection> = {}): DocumentSection {
  return {
    id: 's1',
    document_id: 'd1',
    title: 'Introduction',
    brief: 'Poser le contexte',
    order: 10,
    depth: 0,
    content: '',
    summary: '',
    status: 'vide',
    orphan: false,
    created_at: '2026-07-01T00:00:00Z',
    updated_at: '2026-07-01T00:00:00Z',
    ...overrides,
  };
}

function renderEditor(overrides: Partial<SectionEditorProps> = {}) {
  return render(
    <SectionEditor
      section={makeSection()}
      isStreaming={false}
      error={null}
      onUpdateSection={vi.fn()}
      onDraft={vi.fn()}
      onValidate={vi.fn()}
      {...overrides}
    />
  );
}

describe('B-627 : le volet central pendant la génération de la trame', () => {
  it('dit que la trame est en cours de génération au lieu d’inviter à choisir une section', () => {
    renderEditor({ section: null, trameEnCours: true });
    expect(screen.getByRole('status')).toHaveTextContent(/trame est en cours de génération/i);
    expect(screen.queryByText(/Sélectionne une section/)).toBeNull();
  });

  it('sans génération, garde l’invitation à choisir une section', () => {
    renderEditor({ section: null });
    expect(screen.getByText(/Sélectionne une section/)).toBeInTheDocument();
  });
});

describe('B-628 : « Explorer » une piste amène le champ d’instruction à l’écran', () => {
  const scrollIntoView = vi.fn();
  beforeEach(() => {
    Element.prototype.scrollIntoView = scrollIntoView;
  });
  afterEach(() => {
    scrollIntoView.mockReset();
  });

  it('au préremplissage, le champ défile jusqu’à lui et reçoit le focus', () => {
    renderEditor({
      section: makeSection({ content: 'Un long contenu déjà rédigé.', status: 'brouillon' }),
      instructionPrefill: 'Ajouter un exemple chiffré sur le ROI',
    });
    const champ = screen.getByLabelText('Instruction de retouche');
    expect(champ).toHaveValue('Ajouter un exemple chiffré sur le ROI');
    expect(scrollIntoView).toHaveBeenCalled();
    expect(document.activeElement).toBe(champ);
  });
});

describe('B-629 : le champ « Instruction de retouche » a sa propre ligne', () => {
  it('occupe toute la largeur et ne partage pas sa ligne avec les boutons', () => {
    renderEditor({ section: makeSection({ content: 'Contenu.', status: 'brouillon' }) });
    const champ = screen.getByLabelText('Instruction de retouche');
    expect(champ).toHaveClass('w-full');
    expect(champ.parentElement?.querySelector('button')).toBeNull();
  });
});

describe('B-633 : la rédaction en attente du premier mot est annoncée', () => {
  it('tant qu’aucun caractère n’est arrivé, le statut explique l’attente', () => {
    renderEditor({ section: makeSection({ content: '' }), isStreaming: true });
    const statut = screen.getByRole('status');
    expect(statut.textContent?.trim().length ?? 0).toBeGreaterThan(0);
    expect(statut).toHaveTextContent(/aucun mot reçu pour l’instant|aucun mot reçu pour l'instant/i);
    expect(statut).toHaveTextContent(/modèle local/i);
  });

  it('dès que du texte arrive, le statut dit que la rédaction est en cours', () => {
    renderEditor({ section: makeSection({ content: 'Bonjour', status: 'brouillon' }), isStreaming: true });
    expect(screen.getByRole('status')).toHaveTextContent(/Rédaction en cours/i);
    expect(screen.queryByText(/aucun mot reçu/i)).toBeNull();
  });

  it('hors rédaction, aucun statut vide ne traîne', () => {
    renderEditor({ section: makeSection({ content: 'Bonjour', status: 'brouillon' }) });
    expect(screen.queryByRole('status')).toBeNull();
    fireEvent.click(screen.getByRole('button', { name: /Rédiger/ }));
  });
});
