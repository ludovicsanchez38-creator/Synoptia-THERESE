import { act, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { LLMStep } from './LLMStep';

const doubles = vi.hoisted(() => ({ catalogue: vi.fn() }));
vi.mock('../../services/api', () => ({
  getApiKeysWithCorrupted: vi.fn().mockResolvedValue({ keys: {}, sources: {} }),
  getOllamaStatus: vi.fn().mockResolvedValue({ available: false, models: [] }),
  getSystemResources: vi.fn().mockResolvedValue(null),
}));
vi.mock('../../lib/catalogueModeles', async (original) => ({
  ...await original<typeof import('../../lib/catalogueModeles')>(),
  chargerCatalogue: doubles.catalogue,
}));

describe('R6 : attente du catalogue dans le vrai composant', () => {
  it('annonce immédiatement l’attente puis garde un indicateur jusqu’à la réponse du catalogue', async () => {
    let terminer!: (modeles: unknown[]) => void;
    doubles.catalogue.mockReturnValue(new Promise((resolve) => { terminer = resolve; }));
    render(<LLMStep onNext={vi.fn()} onBack={vi.fn()} />);
    expect(screen.getByRole('status')).toHaveTextContent('Vérification des modèles disponibles');
    await act(async () => { await Promise.resolve(); });
    expect(screen.getByRole('status')).toHaveTextContent('Actualisation de la liste des modèles');
    await act(async () => { terminer([{ id: 'modele-test', name: 'Modèle de test' }]); });
    expect(screen.queryByText(/Actualisation de la liste/)).not.toBeInTheDocument();
    expect(screen.getByRole('option', { name: 'Modèle de test' })).toBeInTheDocument();
  });
});
