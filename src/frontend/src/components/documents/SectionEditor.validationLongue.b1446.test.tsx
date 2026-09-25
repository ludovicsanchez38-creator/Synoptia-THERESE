/**
 * B-1446 (recette P-146, lot 3, KO-3) : avec le modèle local, « Valider » une
 * section affichait « Délai de 30000 ms dépassé » : la validation résume la
 * section par le modèle et dure près d'une minute. Le client abandonnait,
 * la section restait « Brouillon » à l'écran pendant que le moteur, lui,
 * aboutissait. La validation n'a plus de délai client, et le bouton dit
 * qu'elle est en cours.
 */
import { act, fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import type { DocumentSection } from '../../services/api/documents';
import { SectionEditor } from './SectionEditor';

const { request } = vi.hoisted(() => ({ request: vi.fn() }));
vi.mock('../../services/api/core', async (importOriginal) => ({
  ...(await importOriginal<typeof import('../../services/api/core')>()),
  request,
}));

import { validateSection } from '../../services/api/documents';

const SECTION = {
  id: 's-1', document_id: 'd-1', title: 'Organisation de l’agenda', brief: null, content: 'Texte rédigé.',
  status: 'brouillon', position: 0, parent_id: null, orphan: false, summary: null,
  created_at: '2026-09-25T10:00:00Z', updated_at: '2026-09-25T10:00:00Z',
} as unknown as DocumentSection;

describe('B-1446 : une validation longue', () => {
  it('n’a pas de délai client', async () => {
    request.mockResolvedValue({ ...SECTION, status: 'validee' });
    await validateSection('s-1');
    expect(request).toHaveBeenCalledWith('/api/documents/sections/s-1/validate', expect.objectContaining({ timeoutMs: null }));
  });

  it('le bouton dit que la validation est en cours', async () => {
    let finir: () => void = () => {};
    const onValidate = vi.fn(() => new Promise<void>((resoudre) => { finir = resoudre; }));
    render(
      <SectionEditor section={SECTION} isStreaming={false} error={null} onUpdateSection={vi.fn()} onDraft={vi.fn()} onValidate={onValidate} />,
    );
    await act(async () => { fireEvent.click(screen.getByRole('button', { name: 'Valider' })); });
    const bouton = screen.getByRole('button', { name: /Validation…/ });
    expect(bouton).toBeDisabled();
    await act(async () => { finir(); });
    expect(screen.getByRole('button', { name: 'Valider' })).toBeInTheDocument();
  });
});
