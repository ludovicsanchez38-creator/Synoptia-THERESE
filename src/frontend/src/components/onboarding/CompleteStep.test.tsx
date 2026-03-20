import { render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { CompleteStep } from './CompleteStep';

vi.mock('../../services/api', () => ({
  getProfile: vi.fn().mockResolvedValue(null),
  getLLMConfig: vi.fn().mockResolvedValue(null),
  getWorkingDirectory: vi.fn().mockResolvedValue({ path: null, exists: false }),
  completeOnboarding: vi.fn().mockResolvedValue(undefined),
}));

describe('CompleteStep', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('affiche Ctrl+, sur Windows', async () => {
    Object.defineProperty(window.navigator, 'platform', {
      value: 'Win32',
      configurable: true,
    });

    render(<CompleteStep onComplete={vi.fn()} onBack={vi.fn()} />);

    expect(
      await screen.findByText(/Paramètres \(raccourci Ctrl\+,\)\./i)
    ).toBeInTheDocument();
  });

  it('affiche Cmd+, sur macOS', async () => {
    Object.defineProperty(window.navigator, 'platform', {
      value: 'MacIntel',
      configurable: true,
    });

    render(<CompleteStep onComplete={vi.fn()} onBack={vi.fn()} />);

    expect(
      await screen.findByText(/Paramètres \(raccourci Cmd\+,\)\./i)
    ).toBeInTheDocument();
  });
});
