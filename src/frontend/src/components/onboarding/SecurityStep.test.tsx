import { fireEvent, render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { SecurityStep } from './SecurityStep';

describe('SecurityStep - consentement cloud conditionnel', () => {
  beforeEach(() => vi.clearAllMocks());

  it('autorise Ollama local sans consentement cloud ni persistance', () => {
    const onNext = vi.fn();
    render(<SecurityStep provider="ollama" onNext={onNext} onBack={vi.fn()} />);

    expect(screen.getByTestId('local-security-notice')).toHaveTextContent('Ollama traite les messages sur cette machine');
    expect(screen.queryByRole('checkbox')).not.toBeInTheDocument();
    const next = screen.getByTestId('onboarding-next-btn');
    expect(next).toBeEnabled();
    fireEvent.click(next);

    expect(onNext).toHaveBeenCalledTimes(1);
    expect(localStorage.setItem).not.toHaveBeenCalledWith('therese-cloud-consent', expect.anything());
  });

  it('exige et trace un accord contextualisé pour un fournisseur cloud actif', () => {
    const onNext = vi.fn();
    render(<SecurityStep provider="openai" onNext={onNext} onBack={vi.fn()} />);

    expect(screen.getByText(/vers OpenAI/)).toBeInTheDocument();
    // B-1986 : l'ancienne phrase « messages et le contexte utile » sous-estimait
    // l'envoi. Le libellé nomme toujours les messages et le contexte, puis accepte
    // l'ensemble annoncé.
    const accord = screen.getByRole('checkbox').closest('label')?.textContent ?? '';
    expect(accord).toMatch(/mes messages, le contexte utile/);
    expect(accord).toMatch(/ces données soient envoyées à OpenAI/);
    const next = screen.getByTestId('onboarding-next-btn');
    expect(next).toBeDisabled();

    fireEvent.click(screen.getByRole('checkbox'));
    fireEvent.click(next);

    expect(onNext).toHaveBeenCalledTimes(1);
    // Consentement v2 (revue 0.40) : finalité llm + ID du fournisseur en clé.
    expect(localStorage.setItem).toHaveBeenCalledWith(
      'therese-cloud-consent',
      expect.stringContaining('"llm:openai"'),
    );
  });

  it('autorise aussi la configuration différée sans consentement anticipé', () => {
    render(<SecurityStep provider={null} onNext={vi.fn()} onBack={vi.fn()} />);
    expect(screen.getByTestId('local-security-notice')).toHaveTextContent('Aucun fournisseur cloud n’est activé');
    expect(screen.getByTestId('onboarding-next-btn')).toBeEnabled();
  });
});
