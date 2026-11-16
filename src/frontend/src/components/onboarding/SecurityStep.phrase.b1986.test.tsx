/**
 * B-1986 : la phrase d'acceptation reprend l'ensemble annoncé, y compris
 * ce que l'assistant lit, et pas seulement les messages.
 */
import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { SecurityStep } from './SecurityStep';

describe('B-1986 : l’acceptation couvre les données annoncées', () => {
  it('accepte l’envoi de ces données, pas seulement des messages', () => {
    render(<SecurityStep provider="openai" onNext={vi.fn()} onBack={vi.fn()} />);
    const texte = screen.getByRole('checkbox').closest('label')?.textContent ?? '';
    expect(texte).toMatch(/J'accepte que ces données soient envoyées à OpenAI pour traitement/);
  });
});
