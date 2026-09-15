/**
 * B-856 (cycle 9) : un champ « select » obligatoire sans valeur par défaut
 * n'avait pas de ligne « -- Choisir -- » (réservée aux champs facultatifs).
 * La liste affichait sa première option alors que la valeur restait vide :
 * « Générer » restait grisé sans qu'aucun choix ne paraisse manquer.
 */
import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import { DynamicSkillForm } from './DynamicSkillForm';

const schema = {
  format: { type: 'select' as const, label: 'Format de sortie', required: true, options: ['PDF', 'DOCX'] },
};

describe('DynamicSkillForm - B-856, un select obligatoire dit qu’un choix reste à faire', () => {
  it('montre « -- Choisir -- » sélectionné, bloque Générer, puis le débloque au choix', () => {
    const onSubmit = vi.fn();
    render(<DynamicSkillForm skillName="Exporter" schema={schema} onSubmit={onSubmit} onBack={vi.fn()} />);

    const liste = screen.getByLabelText(/Format de sortie/) as HTMLSelectElement;
    expect(liste.value).toBe('');
    expect(screen.getByRole('option', { name: /Choisir/ })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Générer' })).toBeDisabled();

    fireEvent.change(liste, { target: { value: 'DOCX' } });
    expect(screen.getByRole('button', { name: 'Générer' })).toBeEnabled();
    fireEvent.click(screen.getByRole('button', { name: 'Générer' }));
    expect(onSubmit).toHaveBeenCalledWith({ format: 'DOCX' });
  });
});
