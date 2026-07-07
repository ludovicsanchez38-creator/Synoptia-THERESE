/**
 * Tests SectionEditor - streaming (contenu qui grandit chunk par chunk),
 * édition titre/consigne au blur, validation, erreur + Reprendre.
 *
 * Le composant est purement réactif aux props qu'il reçoit : le stream lui-
 * même (concaténation chunk par chunk, rechargement canonique au chunk
 * `done`, conservation du partiel au chunk `error`) est la responsabilité
 * de `documentStore.draftSection`, déjà couverte par `documentStore.test.ts`.
 * Ici, on simule l'arrivée des chunks en re-rendant avec un `section.content`
 * grandissant (ce que `DocumentWorkspace` ferait réellement, abonné au store).
 */
import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
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
  const onUpdateSection = vi.fn();
  const onDraft = vi.fn();
  const onValidate = vi.fn();
  const utils = render(
    <SectionEditor
      section={makeSection()}
      isStreaming={false}
      error={null}
      onUpdateSection={onUpdateSection}
      onDraft={onDraft}
      onValidate={onValidate}
      {...overrides}
    />
  );
  return { onUpdateSection, onDraft, onValidate, ...utils };
}

describe('SectionEditor', () => {
  it('affiche un état vide guidé quand aucune section n\'est active', () => {
    render(
      <SectionEditor section={null} isStreaming={false} error={null} onUpdateSection={vi.fn()} onDraft={vi.fn()} onValidate={vi.fn()} />
    );
    expect(screen.getByTestId('section-editor-empty')).toBeInTheDocument();
  });

  it('le stream fait grandir le contenu au fil de 3 chunks simulés', () => {
    const { rerender } = renderEditor({
      section: makeSection({ content: 'Bon', status: 'brouillon' }),
      isStreaming: true,
    });
    expect(screen.getByTestId('section-content')).toHaveTextContent('Bon');

    rerender(
      <SectionEditor
        section={makeSection({ content: 'Bonjour', status: 'brouillon' })}
        isStreaming
        error={null}
        onUpdateSection={vi.fn()}
        onDraft={vi.fn()}
        onValidate={vi.fn()}
      />
    );
    expect(screen.getByTestId('section-content')).toHaveTextContent('Bonjour');

    rerender(
      <SectionEditor
        section={makeSection({ content: 'Bonjour monde', status: 'brouillon' })}
        isStreaming
        error={null}
        onUpdateSection={vi.fn()}
        onDraft={vi.fn()}
        onValidate={vi.fn()}
      />
    );
    expect(screen.getByTestId('section-content')).toHaveTextContent('Bonjour monde');
  });

  it('pendant le stream, Rédiger/Retoucher/Valider sont désactivés', () => {
    renderEditor({ section: makeSection({ content: 'En cours de rédaction', status: 'brouillon' }), isStreaming: true });

    expect(screen.getByRole('button', { name: /^Rédiger$/i })).toBeDisabled();
    expect(screen.getByRole('button', { name: /^Retoucher$/i })).toBeDisabled();
    expect(screen.getByRole('button', { name: /^Valider$/i })).toBeDisabled();
  });

  it('blur du titre appelle updateSection avec le nouveau titre', () => {
    const { onUpdateSection } = renderEditor();
    const titleInput = screen.getByLabelText('Titre de la section');

    fireEvent.change(titleInput, { target: { value: 'Nouveau titre' } });
    fireEvent.blur(titleInput);

    expect(onUpdateSection).toHaveBeenCalledWith('s1', { title: 'Nouveau titre' });
  });

  it('blur du titre SANS changement ne déclenche aucun PATCH inutile', () => {
    const { onUpdateSection } = renderEditor();
    fireEvent.blur(screen.getByLabelText('Titre de la section'));
    expect(onUpdateSection).not.toHaveBeenCalled();
  });

  it('blur de la consigne appelle updateSection avec la nouvelle consigne', () => {
    const { onUpdateSection } = renderEditor();
    const briefInput = screen.getByLabelText('Consigne de la section');

    fireEvent.change(briefInput, { target: { value: 'Nouvelle consigne' } });
    fireEvent.blur(briefInput);

    expect(onUpdateSection).toHaveBeenCalledWith('s1', { brief: 'Nouvelle consigne' });
  });

  it('« Valider » appelle validateSection ; le tag passe à Validée une fois la section rechargée', () => {
    const { onValidate, rerender } = renderEditor({
      section: makeSection({ content: 'Du contenu rédigé.', status: 'brouillon' }),
    });

    fireEvent.click(screen.getByRole('button', { name: /^Valider$/i }));
    expect(onValidate).toHaveBeenCalledWith('s1');

    rerender(
      <SectionEditor
        section={makeSection({ content: 'Du contenu rédigé.', status: 'validee', summary: 'Résumé de la section.' })}
        isStreaming={false}
        error={null}
        onUpdateSection={vi.fn()}
        onDraft={vi.fn()}
        onValidate={vi.fn()}
      />
    );

    expect(screen.getByText('Validée')).toBeInTheDocument();
    expect(screen.getByTestId('section-summary')).toHaveTextContent('Résumé de la section.');
    expect(screen.queryByRole('button', { name: /^Rédiger$/i })).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /^Valider$/i })).not.toBeInTheDocument();
  });

  it('« Valider » est désactivé quand le contenu de la section est vide', () => {
    renderEditor({ section: makeSection({ content: '   ', status: 'vide' }) });
    expect(screen.getByRole('button', { name: /^Valider$/i })).toBeDisabled();
  });

  it('« Rédiger » appelle draftSection sans instruction', () => {
    const { onDraft } = renderEditor({ section: makeSection({ content: '', status: 'vide' }) });
    fireEvent.click(screen.getByRole('button', { name: /^Rédiger$/i }));
    expect(onDraft).toHaveBeenCalledWith('s1');
  });

  it('« Retoucher » appelle draftSection avec l\'instruction saisie', () => {
    const { onDraft } = renderEditor({ section: makeSection({ content: 'Contenu existant.', status: 'brouillon' }) });

    fireEvent.change(screen.getByLabelText('Instruction de retouche'), { target: { value: 'Plus concis' } });
    fireEvent.click(screen.getByRole('button', { name: /^Retoucher$/i }));

    expect(onDraft).toHaveBeenCalledWith('s1', 'Plus concis');
  });

  it('« Retoucher » est désactivé tant qu\'aucune instruction n\'est saisie', () => {
    renderEditor({ section: makeSection({ content: 'Contenu existant.', status: 'brouillon' }) });
    expect(screen.getByRole('button', { name: /^Retoucher$/i })).toBeDisabled();
  });

  it('erreur : affiche le message causal du store et « Reprendre » relance la rédaction', () => {
    const { onDraft } = renderEditor({
      section: makeSection({ content: 'Début de rédaction', status: 'brouillon' }),
      error: 'Erreur du fournisseur IA pendant la rédaction : timeout',
    });

    expect(screen.getByText(/Erreur du fournisseur IA/i)).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: /Reprendre/i }));

    expect(onDraft).toHaveBeenCalledWith('s1');
  });

  it('section validée : « Rédiger » et « Valider » disparaissent, seul « Retoucher » reste', () => {
    renderEditor({ section: makeSection({ content: 'Contenu final.', status: 'validee', summary: 'Résumé.' }) });

    expect(screen.queryByRole('button', { name: /^Rédiger$/i })).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /^Valider$/i })).not.toBeInTheDocument();
    expect(screen.getByRole('button', { name: /^Retoucher$/i })).toBeInTheDocument();
  });

  it('changer de section réinitialise les buffers titre/consigne (pas de fuite entre sections)', () => {
    const { rerender } = renderEditor({ section: makeSection({ id: 's1', title: 'Section A', brief: 'Brief A' }) });
    expect(screen.getByLabelText('Titre de la section')).toHaveValue('Section A');

    rerender(
      <SectionEditor
        section={makeSection({ id: 's2', title: 'Section B', brief: 'Brief B' })}
        isStreaming={false}
        error={null}
        onUpdateSection={vi.fn()}
        onDraft={vi.fn()}
        onValidate={vi.fn()}
      />
    );

    expect(screen.getByLabelText('Titre de la section')).toHaveValue('Section B');
    expect(screen.getByLabelText('Consigne de la section')).toHaveValue('Brief B');
  });
});
