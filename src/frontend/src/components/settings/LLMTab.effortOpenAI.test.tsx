/** P-045 (lecteur c4-R11, B-594) : l'effort choisi est neutralisé pour les GPT-5/o-series dès qu'un outil est fourni ; l'écran doit le dire, sans surpromettre. */
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
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

  it('gpt-6.1-sol propose très élevé, un autre modèle non', async () => {
    const { unmount } = render(<EffortSelector selectedProvider="openai" selectedModel="gpt-6.1-sol" />);
    await screen.findByLabelText('Effort de raisonnement');
    expect(screen.getByRole('option', { name: /Très élevé/ })).toBeTruthy();
    fireEvent.change(screen.getByLabelText('Effort de raisonnement'), { target: { value: 'xhigh' } });
    await waitFor(() => {
      expect(apiMocks.setLLMConfig).toHaveBeenCalledWith('openai', 'gpt-6.1-sol', 'xhigh');
    });
    unmount();
    render(<EffortSelector selectedProvider="openai" selectedModel="gpt-5.6-luna" />);
    await screen.findByLabelText('Effort de raisonnement');
    expect(screen.queryByRole('option', { name: /Très élevé/ })).toBeNull();
  });

  it('gpt-6.1-sol : l’effort reste quand la conversation utilise des outils', async () => {
    render(<EffortSelector selectedProvider="openai" selectedModel="gpt-6.1-sol" />);
    const mention = await screen.findByTestId('effort-mention-conserve');
    expect(mention).toHaveTextContent(/Avec des outils, l'effort que tu choisis est conservé pour ce modèle/);
    expect(screen.queryByText(/désactivé pour ce modèle/i)).toBeNull();
  });

  it('gpt-6.1-terra propose très élevé et garde l’effort avec les outils', async () => {
    render(<EffortSelector selectedProvider="openai" selectedModel="gpt-6.1-terra" />);
    await screen.findByLabelText('Effort de raisonnement');
    expect(screen.getByRole('option', { name: /Très élevé/ })).toBeTruthy();
    const mention = await screen.findByTestId('effort-mention-conserve');
    expect(mention).toHaveTextContent(/Avec des outils, l'effort que tu choisis est conservé pour ce modèle/);
    expect(screen.queryByText(/désactivé pour ce modèle/i)).toBeNull();
    fireEvent.change(screen.getByLabelText('Effort de raisonnement'), { target: { value: 'xhigh' } });
    await waitFor(() => {
      expect(apiMocks.setLLMConfig).toHaveBeenCalledWith('openai', 'gpt-6.1-terra', 'xhigh');
    });
  });

  it('gpt-6-astra : l’effort reste quand la conversation utilise des outils', async () => {
    render(<EffortSelector selectedProvider="openai" selectedModel="gpt-6-astra" />);
    const mention = await screen.findByTestId('effort-mention-conserve');
    expect(mention).toHaveTextContent(/Avec des outils, l'effort que tu choisis est conservé pour ce modèle/);
    expect(screen.queryByText(/désactivé pour ce modèle/i)).toBeNull();
  });

  it.each(['gpt-6.2-astra', 'gpt-6.2-sol'])('%s laisse le modèle choisir son effort, y compris avec des outils', async (modele) => {
    apiMocks.getLLMConfig.mockResolvedValue({ provider: 'openai', model: modele, effort: 'high' });
    render(<EffortSelector selectedProvider="openai" selectedModel={modele} />);

    const select = screen.getByRole('combobox', { name: 'Effort de raisonnement' });
    await waitFor(() => expect(apiMocks.getLLMConfig).toHaveBeenCalled());
    expect(screen.queryByText(/désactivé pour ce modèle/i)).not.toBeInTheDocument();
    expect(select).toBeDisabled();
    expect(select).toHaveValue('auto');
    expect(select).toHaveAccessibleDescription(/le modèle choisit son effort, même avec des outils/i);
  });

  it.each([
    ['gpt-6.2-astra', 'auto'],
    ['gpt-6.2-astra', 'low'],
    ['gpt-6.2-astra', 'medium'],
    ['gpt-6.2-astra', 'xhigh'],
    ['gpt-6.2-astra', 'max'],
    ['gpt-6.2-sol', 'auto'],
    ['gpt-6.2-sol', 'low'],
    ['gpt-6.2-sol', 'medium'],
    ['gpt-6.2-sol', 'xhigh'],
    ['gpt-6.2-sol', 'max'],
  ])('%s affiche Auto après un changement de modèle avec la préférence %s', async (modele, effort) => {
    const precedent = effort === 'xhigh' ? 'gpt-6.1-sol' : 'gpt-6-sol';
    apiMocks.setLLMConfig.mockClear();
    apiMocks.getLLMConfig.mockResolvedValueOnce({ provider: 'openai', model: precedent, effort });
    const { rerender } = render(<EffortSelector selectedProvider="openai" selectedModel={precedent} />);
    const select = screen.getByRole('combobox', { name: 'Effort de raisonnement' });
    await waitFor(() => expect(select).toHaveValue(effort));
    expect(select).toBeEnabled();

    apiMocks.getLLMConfig.mockResolvedValueOnce({ provider: 'openai', model: modele, effort });
    rerender(<EffortSelector selectedProvider="openai" selectedModel={modele} />);
    await waitFor(() => expect(select).toHaveValue('auto'));
    expect(select).toBeDisabled();
    fireEvent.change(select, { target: { value: 'high' } });
    expect(apiMocks.setLLMConfig).not.toHaveBeenCalled();
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
