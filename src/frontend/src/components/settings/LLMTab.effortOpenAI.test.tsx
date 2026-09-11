/** P-045 (lecteur c4-R11, B-594) : l'effort choisi est neutralisé pour les GPT-5/o-series dès qu'un outil est fourni ; l'écran doit le dire, sans surpromettre. */
import { render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const apiMocks = vi.hoisted(() => ({ getLLMConfig: vi.fn(), setLLMConfig: vi.fn() }));
vi.mock('../../services/api', () => apiMocks);

import { EffortSelector } from './LLMTab';

describe('EffortSelector : mention outils + raisonnement (P-045)', () => {
  beforeEach(() => {
    apiMocks.getLLMConfig.mockResolvedValue({ provider: 'openai', model: 'gpt-5.6-luna', effort: 'high' });
  });

  it('openai + gpt-5.6 : la mention explique la neutralisation avec outils et décrit le sélecteur', async () => {
    render(<EffortSelector selectedProvider="openai" selectedModel="gpt-5.6-luna" />);
    const mention = await screen.findByTestId('effort-mention-outils');
    expect(mention).toHaveTextContent(/désactivé pour ce modèle dès qu.une conversation utilise des outils/i);
    expect(mention).toHaveTextContent(/Sans outils, ce réglage est transmis/i);
    // Lot 9 : l'aide du champ a un `id` et est décrite au Select en toutes
    // circonstances ; la mention s'y AJOUTE, dans cet ordre.
    await waitFor(() => expect(screen.getByLabelText('Effort de raisonnement')).toHaveAttribute('aria-describedby', 'llm-effort-aide llm-effort-outils'));
  });

  it('openai + gpt-5.5 : la mention ne promet pas que l’effort passe sans outils', async () => {
    render(<EffortSelector selectedProvider="openai" selectedModel="gpt-5.5" />);
    const mention = await screen.findByTestId('effort-mention-outils');
    expect(mention).toHaveTextContent(/n.est pas transmis à ce modèle/i);
  });

  it('anthropic, ou gpt-4.1 : aucune mention', async () => {
    const { unmount } = render(<EffortSelector selectedProvider="anthropic" selectedModel="claude-sonnet-4-6" />);
    await screen.findByLabelText('Effort de raisonnement');
    expect(screen.queryByTestId('effort-mention-outils')).toBeNull();
    expect(screen.getByLabelText('Effort de raisonnement')).toHaveAttribute('aria-describedby', 'llm-effort-aide');
    unmount();
    render(<EffortSelector selectedProvider="openai" selectedModel="gpt-4.1" />);
    await screen.findByLabelText('Effort de raisonnement');
    expect(screen.queryByTestId('effort-mention-outils')).toBeNull();
  });
});
