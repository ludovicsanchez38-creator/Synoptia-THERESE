import { act, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { SettingsModal } from './SettingsModal';
import './ProfileTab';
import { ConversationCanvasPrototype } from '../prototype/ConversationCanvasPrototype';
import { useChatStore } from '../../stores/chatStore';
import { usePanelStore } from '../../stores/panelStore';
import { useNavigationStore } from '../../stores/navigationStore';
import { usePersonalisationStore } from '../../stores/personalisationStore';
import { _clearEscapeHandlers } from '../../lib/escapeStack';

// Mock PARTIEL (leçon 22/07) : seuls les appels réseau sont neutralisés.
vi.mock('../../services/api', async (importOriginal) => ({
  ...(await importOriginal<typeof import('../../services/api')>()),
  getApiKeysWithCorrupted: vi
    .fn()
    .mockResolvedValue({ keys: { mistral: true, openai: true }, corrupted: [] }),
  getLLMConfig: vi.fn().mockResolvedValue({
    provider: 'mistral',
    model: 'mistral-medium-latest',
    available_models: [],
    available: true,
  }),
  setLLMConfig: vi.fn().mockResolvedValue({}),
  getPreferences: vi.fn().mockResolvedValue({}),
  getStats: vi.fn().mockResolvedValue(null),
  getProfile: vi.fn().mockResolvedValue(null),
  getWorkingDirectory: vi.fn().mockResolvedValue({ path: null, exists: false }),
  getOllamaStatus: vi.fn().mockResolvedValue(null),
  getSystemResources: vi.fn().mockResolvedValue(null),
  hasGroqKey: vi.fn().mockResolvedValue(false),
  getWebSearchStatus: vi.fn().mockResolvedValue({
    enabled: true,
    providers: { gemini: 'indisponible', others: 'indisponible' },
    description: '',
  }),
}));


beforeEach(() => {
  vi.clearAllMocks();
  window.history.replaceState({}, '', '/?interface=conversation-canvas');
  useChatStore.setState({ conversations: [], currentConversationId: null, isStreaming: false });
  usePanelStore.setState(usePanelStore.getInitialState());
  useNavigationStore.setState(useNavigationStore.getInitialState());
  usePersonalisationStore.setState({ skipDashboard: false, uxMode: 'contributeur' });
  _clearEscapeHandlers();
});
afterEach(() => vi.useRealTimers());

async function enregistrerModele() {
  render(<SettingsModal isOpen onClose={vi.fn()} requestedTab="ai" />);
  await screen.findByLabelText('Modèle');
  vi.useFakeTimers();
  await act(async () => {
    fireEvent.change(screen.getByLabelText('Modèle'), { target: { value: 'mistral-small-2603' } });
  });
  expect(screen.getByText('Modèle IA enregistré.')).toBeInTheDocument();
}

describe('R6 : recherche et retours des réglages', () => {
  it('efface le reçu de sauvegarde au bout de quatre secondes', async () => {
    await enregistrerModele();
    act(() => vi.advanceTimersByTime(4000));
    expect(screen.queryByText('Modèle IA enregistré.')).not.toBeInTheDocument();
  });

  it('efface le reçu dès le prochain changement de rubrique', async () => {
    await enregistrerModele();
    fireEvent.click(screen.getByTestId('settings-tab-profile'));
    expect(screen.queryByText('Modèle IA enregistré.')).not.toBeInTheDocument();
  });

  it('ouvre la vraie palette avec Ctrl+K depuis les réglages et rend le focus au champ après Échap', async () => {
    render(<><ConversationCanvasPrototype /><SettingsModal isOpen onClose={vi.fn()} /></>);
    const champ = await screen.findByLabelText(/Nom complet/);
    fireEvent.change(champ, { target: { value: 'Camille, brouillon conservé' } });
    champ.focus();
    fireEvent.keyDown(champ, { key: 'k', ctrlKey: true, metaKey: true });
    const palette = screen.getByRole('dialog', { name: 'Rechercher une commande, une capacité ou une donnée' });
    expect(palette.contains(document.activeElement)).toBe(true);
    fireEvent.keyDown(document.activeElement!, { key: 'Escape' });
    await waitFor(() => expect(document.activeElement).toBe(champ));
    expect(champ).toHaveValue('Camille, brouillon conservé');
    expect(screen.getByTestId('settings-modal')).toBeInTheDocument();
  });
});

it('R6 : garde un exemple neutre dans le contexte des réglages', async () => {
  render(<SettingsModal isOpen onClose={vi.fn()} requestedTab="profile" />);
  const champ = await screen.findByLabelText('Ce que Thérèse doit savoir');
  expect(champ.getAttribute('placeholder')).toContain('entreprise de plomberie');
  expect(champ.getAttribute('placeholder')).not.toMatch(/FORGER|Synopt|490/);
});
