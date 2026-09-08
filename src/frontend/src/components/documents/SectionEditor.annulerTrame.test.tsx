/** P-056 : pendant la génération de la trame, un levier d'arrêt est visible ; une fois l'arrêt demandé, il le dit et se désactive. */
import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { SectionEditor, type SectionEditorProps } from './SectionEditor';

function renderEditor(overrides: Partial<SectionEditorProps> = {}) {
  return render(
    <SectionEditor section={null} isStreaming={false} error={null} onUpdateSection={vi.fn()} onDraft={vi.fn()} onValidate={vi.fn()} {...overrides} />,
  );
}

describe('SectionEditor : annuler la génération de trame (P-056)', () => {
  it('propose « Annuler la génération » pendant la trame et appelle le rappel', () => {
    const onAnnulerTrame = vi.fn();
    renderEditor({ trameEnCours: true, onAnnulerTrame });
    fireEvent.click(screen.getByRole('button', { name: 'Annuler la génération' }));
    expect(onAnnulerTrame).toHaveBeenCalled();
  });

  it('arrêt demandé : le bouton le dit et se désactive', () => {
    renderEditor({ trameEnCours: true, onAnnulerTrame: vi.fn(), arretDemande: true });
    const bouton = screen.getByRole('button', { name: /Arrêt demandé/ });
    expect(bouton).toBeDisabled();
  });

  it('hors génération : aucun bouton', () => {
    renderEditor({ trameEnCours: false, onAnnulerTrame: vi.fn() });
    expect(screen.queryByRole('button', { name: /Annuler la génération|Arrêt demandé/ })).toBeNull();
  });
});
