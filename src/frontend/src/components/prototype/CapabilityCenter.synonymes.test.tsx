/**
 * P-114 (persona Claire, cycle 13) : « clients » → « Aucune capacité
 * trouvée » ; « clientes », « carnet », « fiches » non plus. P-129 (persona
 * Nathalie) : « importer », « import », « Excel », « CSV », « fichier » ne
 * menaient pas aux écrans qui importent. La recherche du tiroir connaît ces
 * mots et ne tient plus compte des accents (« echeance » trouve Relances).
 */
import { act, fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import { CapabilityCenter } from './CapabilityCenter';

function chercher(terme: string) {
  render(<CapabilityCenter onClose={vi.fn()} onChoose={vi.fn()} />);
  act(() => {
    fireEvent.change(screen.getByPlaceholderText(/Chercher une capacité/), { target: { value: terme } });
  });
  return screen.queryAllByRole('button').map((b) => (b.textContent ?? '').trim());
}

describe('P-114 et P-129 : la recherche du tiroir connaît les mots des gens', () => {
  it.each(['clients', 'clientes', 'carnet', 'fiches', 'client'])('« %s » mène à Contacts', (terme) => {
    expect(chercher(terme).some((t) => t.startsWith('Contacts'))).toBe(true);
  });

  it.each(['importer', 'import', 'Excel', 'CSV', 'vcf'])('« %s » mène à Contacts et au Pipeline', (terme) => {
    const cartes = chercher(terme);
    expect(cartes.some((t) => t.startsWith('Contacts'))).toBe(true);
    expect(cartes.some((t) => t.startsWith('Pipeline'))).toBe(true);
  });

  it('« fichier » mène à Fichiers', () => {
    expect(chercher('fichier').some((t) => t.startsWith('Fichiers'))).toBe(true);
  });

  it('les accents ne comptent pas : « echeance » trouve Relances et alertes', () => {
    expect(chercher('echeance').some((t) => t.startsWith('Relances et alertes'))).toBe(true);
  });
});
