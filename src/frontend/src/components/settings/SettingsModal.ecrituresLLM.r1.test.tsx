import { act, fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { beforeEach, expect, it, vi } from 'vitest';
import { SettingsModal } from './SettingsModal';
import { usePersonalisationStore } from '../../stores/personalisationStore';
import * as api from '../../services/api';
import { ChatInput } from '../chat/ChatInput';
import { useStatusStore } from '../../stores/statusStore';

vi.mock('../../services/api', async (importOriginal) => ({
  ...(await importOriginal<typeof import('../../services/api')>()),
  getApiKeysWithCorrupted: vi.fn().mockResolvedValue({ keys: { mistral: true, openai: true, qwen: true }, corrupted: [] }),
  getLLMConfig: vi.fn(),
  setLLMConfig: vi.fn(),
  getPreferences: vi.fn().mockResolvedValue({}),
  getStats: vi.fn().mockResolvedValue(null),
  getProfile: vi.fn().mockResolvedValue(null),
  getWorkingDirectory: vi.fn().mockResolvedValue({ path: null, exists: false }),
  getOllamaStatus: vi.fn().mockResolvedValue(null),
  getSystemResources: vi.fn().mockResolvedValue(null),
  hasGroqKey: vi.fn().mockResolvedValue(false),
  getWebSearchStatus: vi.fn().mockResolvedValue({ enabled: true, providers: {}, description: '' }),
}));

let enregistree: api.LLMConfig;
beforeEach(() => {
  vi.clearAllMocks();
  usePersonalisationStore.setState({ uxMode: 'contributeur' });
  enregistree = { provider: 'mistral', model: 'mistral-medium-latest', effort: 'auto', available_models: [] };
  vi.mocked(api.getLLMConfig).mockReset().mockImplementation(async () => ({ ...enregistree }));
  vi.mocked(api.setLLMConfig).mockReset().mockImplementation(async (provider, model, effort, baseUrl) => {
    enregistree = { ...enregistree, provider, model, effort: effort ?? enregistree.effort, base_url: baseUrl ?? enregistree.base_url };
    return enregistree;
  });
  vi.mocked(api.getStats).mockReset().mockResolvedValue(null as unknown as api.Stats);
  vi.mocked(api.getOllamaStatus).mockReset().mockResolvedValue(null as unknown as api.OllamaStatus);
});

async function ouvrir() {
  const rendu = render(<SettingsModal isOpen requestedTab="ai" onClose={vi.fn()} />);
  await waitFor(() => expect(screen.getByLabelText('Modèle')).toHaveValue(enregistree.model));
  return rendu;
}

it.each(['effort', 'adresse'])('R1-3 : une sauvegarde lente de %s ne rétablit pas l’ancien modèle', async (option) => {
  if (option === 'adresse') enregistree = { ...enregistree, provider: 'qwen', model: 'qwen3.8-max' };
  await ouvrir();
  const select = screen.getByLabelText('Modèle') as HTMLSelectElement;
  const suivant = Array.from(select.options).find(opt => opt.value !== enregistree.model)!.value;
  const enregistrer = vi.mocked(api.setLLMConfig).getMockImplementation()!;
  let terminer!: () => void;
  let actifs = 0;
  let maximumActifs = 0;
  vi.mocked(api.setLLMConfig).mockImplementation(async (...args) => {
    maximumActifs = Math.max(maximumActifs, ++actifs);
    if (vi.mocked(api.setLLMConfig).mock.calls.length === 1) await new Promise<void>(resolve => { terminer = resolve; });
    const resultat = await enregistrer(...args);
    actifs--;
    return resultat;
  });
  if (option === 'effort') {
    fireEvent.change(screen.getByLabelText('Effort de raisonnement'), { target: { value: 'high' } });
  } else {
    fireEvent.change(screen.getByLabelText('Adresse de ton espace de travail'), { target: { value: 'https://exemple.invalid/v1' } });
    fireEvent.click(screen.getByRole('button', { name: 'Enregistrer l’adresse' }));
  }
  await waitFor(() => expect(terminer).toBeTypeOf('function'));
  fireEvent.change(select, { target: { value: suivant } });
  await act(async () => {});
  await act(async () => { terminer(); });

  expect(enregistree.model).toBe(suivant);
  expect(screen.getByLabelText('Modèle')).toHaveValue(suivant);
  expect(maximumActifs).toBe(1);
  if (option === 'effort') {
    expect(enregistree.effort).toBe('high');
    expect(screen.getByLabelText('Effort de raisonnement')).toHaveValue('high');
  } else {
    expect(enregistree.base_url).toBe('https://exemple.invalid/v1');
  }
});

it('R2-2 : le sélecteur du chat attend le POST des réglages fermés', async () => {
  enregistree.available_models = ['mistral-medium-latest', 'mistral-small-2603', 'mistral-large-latest'];
  useStatusStore.setState({ connectionState: 'connected' });
  const vue = (isOpen: boolean) => <>
    <ChatInput />
    <SettingsModal isOpen={isOpen} requestedTab="ai" onClose={vi.fn()} />
  </>;
  const { rerender } = render(vue(true));
  await waitFor(() => expect(screen.getByLabelText('Modèle')).toHaveValue(enregistree.model));
  const enregistrer = vi.mocked(api.setLLMConfig).getMockImplementation()!;
  let terminer!: () => void;
  let actifs = 0;
  let maximumActifs = 0;
  vi.mocked(api.setLLMConfig).mockImplementation(async (...args) => {
    maximumActifs = Math.max(maximumActifs, ++actifs);
    if (vi.mocked(api.setLLMConfig).mock.calls.length === 1) await new Promise<void>(resolve => { terminer = resolve; });
    const resultat = await enregistrer(...args);
    actifs--;
    return resultat;
  });
  fireEvent.change(screen.getByLabelText('Modèle'), { target: { value: 'mistral-small-2603' } });
  await waitFor(() => expect(terminer).toBeTypeOf('function'));
  rerender(vue(false));
  fireEvent.click(screen.getByRole('button', { name: 'Modèle de conversation' }));
  fireEvent.change(screen.getByRole('listbox', { name: 'Choisir le modèle' }), { target: { value: 'mistral-large-latest' } });
  await act(async () => {});
  await act(async () => { terminer(); });

  expect(enregistree.model).toBe('mistral-large-latest');
  expect(maximumActifs).toBe(1);
  expect(api.setLLMConfig).toHaveBeenCalledTimes(2);
  expect(screen.getByRole('button', { name: 'Modèle de conversation' })).toHaveTextContent('Mistral Large');
});

it('R1-3 : régler l’effort pendant le choix d’un modèle conserve ce modèle', async () => {
  await ouvrir();
  const enregistrer = vi.mocked(api.setLLMConfig).getMockImplementation()!;
  let terminer!: () => void;
  vi.mocked(api.setLLMConfig).mockImplementationOnce(async (...args) => {
    await new Promise<void>(resolve => { terminer = resolve; });
    return enregistrer(...args);
  });
  fireEvent.change(screen.getByLabelText('Modèle'), { target: { value: 'mistral-small-2603' } });
  await waitFor(() => expect(terminer).toBeTypeOf('function'));
  fireEvent.change(screen.getByLabelText('Effort de raisonnement'), { target: { value: 'high' } });
  await act(async () => { terminer(); });

  expect(enregistree.model).toBe('mistral-small-2603');
  expect(enregistree.effort).toBe('high');
  expect(screen.getByLabelText('Modèle')).toHaveValue('mistral-small-2603');
});

it('R2-4 : l’option normalise xhigh quand elle reprend un modèle en attente de lecture', async () => {
  enregistree = { ...enregistree, provider: 'openai', model: 'gpt-6.1-sol' };
  await ouvrir();
  const avant = { ...enregistree };
  let terminer!: () => void;
  vi.mocked(api.getLLMConfig).mockImplementationOnce(() => new Promise(resolve => { terminer = () => resolve(avant); }));
  fireEvent.change(screen.getByLabelText('Modèle'), { target: { value: 'gpt-5.6-luna' } });
  expect(screen.getByLabelText('Modèle')).toHaveValue('gpt-6.1-sol');
  fireEvent.change(screen.getByLabelText('Effort de raisonnement'), { target: { value: 'xhigh' } });
  await waitFor(() => expect(api.setLLMConfig).toHaveBeenCalled());
  await act(async () => { terminer(); });

  expect(enregistree.model).toBe('gpt-5.6-luna');
  expect(enregistree.effort).toBe('auto');
  expect(screen.getByLabelText('Modèle')).toHaveValue('gpt-5.6-luna');
  expect(screen.getByLabelText('Effort de raisonnement')).toHaveValue('auto');
  expect(screen.queryByRole('option', { name: /Très élevé/ })).toBeNull();
  expect(api.setLLMConfig).toHaveBeenCalledTimes(1);
});

it.each(['réussite', 'refus'])('R2-9 : la sauvegarde d’adresse clôt le statut du modèle repris après %s', async (issue) => {
  enregistree = { ...enregistree, provider: 'qwen', model: 'qwen3.8-max', base_url: 'https://exemple.invalid/v1' };
  await ouvrir();
  await waitFor(() => expect(screen.getByLabelText('Adresse de ton espace de travail')).toHaveValue(enregistree.base_url));
  const avant = { ...enregistree };
  let terminer!: () => void;
  vi.mocked(api.getLLMConfig).mockImplementationOnce(() => new Promise(resolve => { terminer = () => resolve(avant); }));
  if (issue === 'refus') vi.mocked(api.setLLMConfig).mockRejectedValueOnce(new Error('Adresse refusée'));
  const select = screen.getByLabelText('Modèle') as HTMLSelectElement;
  const suivant = Array.from(select.options).find(opt => opt.value !== enregistree.model)!.value;
  fireEvent.change(select, { target: { value: suivant } });
  expect(screen.getByText('Enregistrement du modèle IA…')).toBeInTheDocument();
  fireEvent.click(screen.getByRole('button', { name: 'Enregistrer l’adresse' }));
  await waitFor(() => expect(api.setLLMConfig).toHaveBeenCalledTimes(1));
  await act(async () => { terminer(); });

  expect(screen.queryByText('Enregistrement du modèle IA…')).toBeNull();
  if (issue === 'réussite') {
    expect(enregistree.model).toBe(suivant);
    expect(screen.getByLabelText('Modèle')).toHaveValue(suivant);
    expect(screen.getByText('Modèle IA enregistré.')).toBeInTheDocument();
  } else {
    expect(enregistree.model).toBe(avant.model);
    expect(screen.getByRole('alert')).toHaveTextContent('Adresse refusée');
    expect(screen.queryByText('Modèle IA enregistré.')).toBeNull();
  }
});

it.each(['effort', 'adresse'])('R1-3 : le refus de %s laisse son erreur lisible et la file réutilisable', async (option) => {
  if (option === 'adresse') enregistree = { ...enregistree, provider: 'qwen', model: 'qwen3.8-max' };
  await ouvrir();
  vi.mocked(api.setLLMConfig).mockRejectedValueOnce(new Error('Option refusée'));
  if (option === 'effort') {
    fireEvent.change(screen.getByLabelText('Effort de raisonnement'), { target: { value: 'high' } });
  } else {
    fireEvent.change(screen.getByLabelText('Adresse de ton espace de travail'), { target: { value: 'https://exemple.invalid/v1' } });
    fireEvent.click(screen.getByRole('button', { name: 'Enregistrer l’adresse' }));
  }
  expect(await screen.findByRole('alert')).toHaveTextContent('Option refusée');
  expect(enregistree.effort).toBe('auto');
  expect(enregistree.base_url).toBeUndefined();
  if (option === 'effort') {
    fireEvent.click(screen.getByRole('button', { name: 'Réessayer l’effort' }));
    await waitFor(() => expect(enregistree.effort).toBe('high'));
    expect(screen.getByLabelText('Effort de raisonnement')).toHaveValue('high');
  } else {
    fireEvent.click(screen.getByRole('button', { name: 'Enregistrer l’adresse' }));
    await waitFor(() => expect(enregistree.base_url).toBe('https://exemple.invalid/v1'));
  }
  expect(screen.queryByRole('alert')).toBeNull();
});

it.each(['effort', 'adresse'])('R2-3 : le refus concurrent de %s reste annoncé après le succès du modèle', async (option) => {
  enregistree = { ...enregistree, provider: 'qwen', model: 'qwen3.8-max' };
  await ouvrir();
  let refuser!: (erreur: Error) => void;
  vi.mocked(api.setLLMConfig).mockImplementationOnce(() => new Promise((_resolve, reject) => { refuser = reject; }));
  if (option === 'adresse') {
    fireEvent.change(screen.getByLabelText('Adresse de ton espace de travail'), { target: { value: 'https://exemple.invalid/v1' } });
    fireEvent.click(screen.getByRole('button', { name: 'Enregistrer l’adresse' }));
  } else {
    fireEvent.change(screen.getByLabelText('Effort de raisonnement'), { target: { value: 'high' } });
  }
  await waitFor(() => expect(refuser).toBeTypeOf('function'));
  const select = screen.getByLabelText('Modèle') as HTMLSelectElement;
  const suivant = Array.from(select.options).find(opt => opt.value !== enregistree.model)!.value;
  fireEvent.change(select, { target: { value: suivant } });
  await act(async () => {});
  await act(async () => { refuser(new Error('Option concurrente refusée')); });

  expect(enregistree.model).toBe(suivant);
  expect(enregistree.base_url).toBeUndefined();
  expect(enregistree.effort).toBe('auto');
  expect(screen.getByRole('alert')).toHaveTextContent('Option concurrente refusée');
  expect(screen.getByLabelText('Modèle')).toHaveValue(suivant);
});

it.each(['avant', 'après'])('R1-4 : la réouverture, terminée %s le POST, garde le fournisseur enregistré', async (ordre) => {
  const { rerender } = await ouvrir();
  const enregistrer = vi.mocked(api.setLLMConfig).getMockImplementation()!;
  let terminerPost!: () => void;
  let terminerStats!: () => void;
  vi.mocked(api.setLLMConfig).mockImplementationOnce(async (...args) => {
    await new Promise<void>(resolve => { terminerPost = resolve; });
    return enregistrer(...args);
  });
  fireEvent.click(screen.getByRole('button', { name: /GPT \(OpenAI\)/ }));
  await waitFor(() => expect(terminerPost).toBeTypeOf('function'));
  const attenteStats = new Promise<api.Stats>(resolve => { terminerStats = () => resolve(null as unknown as api.Stats); });
  vi.mocked(api.getStats).mockReturnValueOnce(attenteStats);
  rerender(<SettingsModal isOpen={false} requestedTab="ai" onClose={vi.fn()} />);
  rerender(<SettingsModal isOpen requestedTab="ai" onClose={vi.fn()} />);
  await act(async () => {});
  await act(async () => { if (ordre === 'avant') terminerStats(); else terminerPost(); });
  await act(async () => { if (ordre === 'avant') terminerPost(); else terminerStats(); });

  expect(enregistree.provider).toBe('openai');
  expect(screen.getByRole('button', { name: /GPT \(OpenAI\)/ })).toHaveAttribute('aria-pressed', 'true');
  expect(screen.getByLabelText('Modèle')).toHaveValue(enregistree.model);

  // La référence de restauration doit elle aussi rester la configuration confirmée.
  vi.mocked(api.setLLMConfig).mockRejectedValueOnce(new Error('Choix suivant refusé'));
  fireEvent.click(screen.getByRole('button', { name: /Mistral AI/ }));
  await screen.findByText('Choix suivant refusé');
  expect(screen.getByRole('button', { name: /GPT \(OpenAI\)/ })).toHaveAttribute('aria-pressed', 'true');
  expect(screen.getByLabelText('Modèle')).toHaveValue(enregistree.model);
});

it('R1-4 : une première relecture terminée ne périme pas la réouverture suivante', async () => {
  const { rerender } = await ouvrir();
  let terminerPremiere!: () => void;
  let terminerSeconde!: () => void;
  vi.mocked(api.getStats)
    .mockReturnValueOnce(new Promise(resolve => { terminerPremiere = () => resolve(null as unknown as api.Stats); }))
    .mockReturnValueOnce(new Promise(resolve => { terminerSeconde = () => resolve(null as unknown as api.Stats); }));
  rerender(<SettingsModal isOpen={false} requestedTab="ai" onClose={vi.fn()} />);
  rerender(<SettingsModal isOpen requestedTab="ai" onClose={vi.fn()} />);
  await act(async () => {});
  enregistree = { ...enregistree, model: 'mistral-small-2603' };
  rerender(<SettingsModal isOpen={false} requestedTab="ai" onClose={vi.fn()} />);
  rerender(<SettingsModal isOpen requestedTab="ai" onClose={vi.fn()} />);
  await act(async () => {});
  await act(async () => { terminerPremiere(); });
  await act(async () => { terminerSeconde(); });

  expect(screen.getByLabelText('Modèle')).toHaveValue('mistral-small-2603');
  expect(api.setLLMConfig).not.toHaveBeenCalled();
});

it.each(['réussite', 'refus'])('R1-9 : Ollama sans modèle clôt le statut avant la %s du POST précédent', async (issue) => {
  vi.mocked(api.getOllamaStatus).mockResolvedValue({ available: true, base_url: 'http://127.0.0.1:9', models: [], error: null });
  await ouvrir();
  const enregistrer = vi.mocked(api.setLLMConfig).getMockImplementation()!;
  let terminer!: () => void;
  vi.mocked(api.setLLMConfig).mockImplementationOnce(async (...args) => {
    await new Promise<void>(resolve => { terminer = resolve; });
    if (issue === 'refus') throw new Error('Refus du fournisseur quitté');
    return enregistrer(...args);
  });
  fireEvent.click(screen.getByRole('button', { name: /GPT \(OpenAI\)/ }));
  await waitFor(() => expect(terminer).toBeTypeOf('function'));
  expect(screen.getByText('Enregistrement du fournisseur IA…')).toBeInTheDocument();
  fireEvent.click(within(screen.getByRole('group', { name: 'Choix du service d’IA' })).getByRole('button', { name: /Ollama/ }));
  const statutApresChoix = screen.queryByText('Enregistrement du fournisseur IA…');
  await act(async () => { terminer(); });

  expect(statutApresChoix).toBeNull();
  expect(screen.queryByText('Enregistrement du fournisseur IA…')).toBeNull();
  expect(screen.queryByText('Fournisseur IA enregistré.')).toBeNull();
  expect(screen.queryByText('Refus du fournisseur quitté')).toBeNull();
  expect(api.setLLMConfig).toHaveBeenCalledTimes(1);
});
