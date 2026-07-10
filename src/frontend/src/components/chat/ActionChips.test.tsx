/**
 * Tranche 1c - puces d'actions déterministes sur conversation vide.
 * Un clic insère la syntaxe {action: ...} dans l'input (l'utilisateur voit
 * ce qui part et peut compléter le sujet avant d'envoyer).
 */
import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { ActionChips } from './ActionChips';

describe('ActionChips', () => {
  it('propose les 4 actions de départ', () => {
    render(<ActionChips onInsert={() => {}} />);
    expect(screen.getByRole('button', { name: /ouvrir l'email/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /ouvrir le crm/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /document word/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /tableur excel/i })).toBeInTheDocument();
  });

  it("un clic insère la syntaxe d'action correspondante", () => {
    const onInsert = vi.fn();
    render(<ActionChips onInsert={onInsert} />);
    fireEvent.click(screen.getByRole('button', { name: /ouvrir le crm/i }));
    expect(onInsert).toHaveBeenCalledWith('{action: ouvrir crm}');
    fireEvent.click(screen.getByRole('button', { name: /document word/i }));
    expect(onInsert).toHaveBeenCalledWith('{action: produire docx "sujet du document"}');
  });
});
