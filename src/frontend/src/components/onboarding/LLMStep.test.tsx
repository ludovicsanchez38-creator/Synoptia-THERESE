import { act, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { LLMStep } from './LLMStep';

const apiMocks = vi.hoisted(() => ({
  getApiKeys: vi.fn(),
  getOllamaStatus: vi.fn(),
  setApiKey: vi.fn(),
  setLLMConfig: vi.fn(),
}));

vi.mock('../../services/api', () => apiMocks);

describe('LLMStep', () => {
  beforeEach(() => {
    vi.useFakeTimers();
    vi.clearAllMocks();
    vi.spyOn(console, 'error').mockImplementation(() => undefined);
    apiMocks.getApiKeys.mockReturnValue(new Promise(() => {}));
    apiMocks.getOllamaStatus.mockReturnValue(new Promise(() => {}));
  });

  afterEach(() => {
    vi.restoreAllMocks();
    vi.useRealTimers();
  });

  it('sort du chargement après timeout et laisse configurer le modèle plus tard', async () => {
    const onNext = vi.fn();
    render(<LLMStep onNext={onNext} onBack={vi.fn()} />);

    expect(screen.getByText('Vérification des modèles disponibles…')).toBeInTheDocument();
    await act(async () => vi.advanceTimersByTimeAsync(10_000));

    expect(screen.getByRole('alert')).toHaveTextContent('prend trop de temps');
    fireEvent.click(screen.getByRole('button', { name: 'Configurer plus tard' }));
    expect(onNext).toHaveBeenCalledTimes(1);
  });
});
