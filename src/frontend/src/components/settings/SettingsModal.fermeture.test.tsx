/**
 * BUG-156 (27/07/2026) - Les Paramètres se fermaient au moindre clic à côté.
 *
 * Le fond sombre portait `onClick={onClose}` : un clic hors du cadre fermait la
 * fenêtre et faisait perdre la saisie en cours (clés API, chemins), en obligeant
 * à retrouver le bon onglet. La fermeture doit passer par « Fermer » ou Échap.
 */
import { render, screen, fireEvent } from '@testing-library/react';
import { describe, expect, it, vi, beforeEach } from 'vitest';

import { SettingsModal } from './SettingsModal';
import { usePersonalisationStore } from '../../stores/personalisationStore';

// Mock PARTIEL (leçon 22/07 : un mock total masque des exports et fait
// remonter des erreurs non gérées). Seuls les appels réseau sont neutralisés.
vi.mock('../../services/api', async (importOriginal) => ({
  ...(await importOriginal<typeof import('../../services/api')>()),
  getSettings: vi.fn().mockResolvedValue({}),
  updateSettings: vi.fn().mockResolvedValue({}),
  getApiKeysWithCorrupted: vi.fn().mockResolvedValue({ keys: {}, corrupted: [] }),
  getLLMConfig: vi.fn().mockResolvedValue({
    provider: 'ollama',
    model: 'x',
    available_models: [],
    available: true,
  }),
  setLLMConfig: vi.fn().mockResolvedValue({}),
}));

describe('SettingsModal - fermeture', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('un clic sur le fond ne ferme pas les Paramètres', () => {
    const onClose = vi.fn();
    const { container } = render(<SettingsModal isOpen onClose={onClose} />);

    const backdrop = container.querySelector('[data-dialog-backdrop]');
    expect(backdrop).not.toBeNull();
    fireEvent.click(backdrop as Element);

    expect(onClose).not.toHaveBeenCalled();
  });

  it('le bouton Fermer ferme bien les Paramètres', () => {
    const onClose = vi.fn();
    render(<SettingsModal isOpen onClose={onClose} />);

    fireEvent.click(screen.getByTestId('settings-close-btn'));

    expect(onClose).toHaveBeenCalledTimes(1);
  });

  // BUG-159 : le testeur cherchait le chemin du dépôt local des agents. En mode
  // standard, l'onglet Agents disparaît sans rien dire - il a conclu qu'il
  // avait été supprimé.
  it('en mode standard, les rubriques masquées sont nommées', () => {
    usePersonalisationStore.setState({ uxMode: 'standard' });
    render(<SettingsModal isOpen onClose={vi.fn()} />);

    const mention = screen.getByTestId('settings-hidden-tabs');
    expect(mention).toHaveTextContent('Outils');
    expect(mention).toHaveTextContent('Agents');
    expect(mention).toHaveTextContent('Avancé');
  });

  it('en mode contributeur, plus rien n’est masqué', () => {
    usePersonalisationStore.setState({ uxMode: 'contributeur' });
    render(<SettingsModal isOpen onClose={vi.fn()} />);

    expect(screen.queryByTestId('settings-hidden-tabs')).toBeNull();
    expect(screen.getByTestId('settings-tab-agents')).toBeInTheDocument();
  });
});
