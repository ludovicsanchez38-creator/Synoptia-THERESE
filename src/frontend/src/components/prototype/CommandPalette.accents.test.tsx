/**
 * B-211 - la palette replie les accents comme elle replie la casse.
 *
 * Constat du 02/09/2026 (persona A1 Sophie, reproduction RP14c) : dans une
 * application française, « tache » ne trouvait rien là où « tâche » trouvait
 * la destination Tâches. Le filtre ne repliait que la casse
 * (`query.toLowerCase()` puis `includes`), jamais les diacritiques, alors que
 * le backend replie les deux depuis le catalogue documentaire.
 *
 * Les mesures sont APPARIÉES : le même terme, avec et sans accent, sur le
 * catalogue réel. Le témoin de casse prouve que l'instrument mesure bien
 * quelque chose quand il rend deux fois le même compte.
 *
 * Le filtre vit à TROIS endroits : les capacités et les commandes de la
 * palette réellement rendue (ConversationCanvasPrototype) et la palette
 * historique de components/chat. Les trois sont couverts ici, sinon un repli
 * retiré d'une seule section passerait au vert.
 */
import { fireEvent, render, screen, within } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { useChatStore } from '../../stores/chatStore';
import { useNavigationStore } from '../../stores/navigationStore';
import { usePanelStore } from '../../stores/panelStore';
import { usePersonalisationStore } from '../../stores/personalisationStore';
import { _clearEscapeHandlers } from '../../lib/escapeStack';
import { ConversationCanvasPrototype } from './ConversationCanvasPrototype';
import { CommandPalette as PaletteHistorique } from '../chat/CommandPalette';

vi.mock('../../services/api/voice', async (importOriginal) => ({
  ...(await importOriginal<object>()),
}));

// jsdom n'implémente pas scrollIntoView, dont la palette historique se sert
// pour suivre la sélection au clavier.
Element.prototype.scrollIntoView = () => {};

function ouvrirLaPalette() {
  render(<ConversationCanvasPrototype />);
  fireEvent.click(screen.getByRole('button', { name: /^Rechercher(Ctrl\+K|⌘K)$/ }));
  const champ = screen.getByRole('combobox', {
    name: 'Rechercher une commande, un parcours ou une capacité',
  });
  const resultats = screen.getByRole('listbox', { name: 'Résultats' });
  return {
    chercher(terme: string) {
      fireEvent.change(champ, { target: { value: terme } });
      return within(resultats)
        .queryAllByRole('option')
        .map((option) => option.textContent ?? '');
    },
  };
}

describe('B-211 - la recherche replie les accents', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    window.history.replaceState({}, '', '/?interface=conversation-canvas');
    useChatStore.setState({ conversations: [], currentConversationId: null, isStreaming: false });
    usePanelStore.setState({
      showSettings: false, requestedSettingsTab: null, showSaveCommand: false,
      showContactModal: false, showProjectModal: false, showBoardPanel: false,
      showShortcuts: false, showPromptLibrary: false, showCommandPalette: false,
      showConversationSidebar: false,
    });
    _clearEscapeHandlers();
    useNavigationStore.setState(useNavigationStore.getInitialState());
    usePersonalisationStore.setState({ skipDashboard: false });
  });

  it.each([
    ['tâche', 'tache'],
    ['décision', 'decision'],
    ['rédaction', 'redaction'],
  ])('« %s » et « %s » rendent le même catalogue', (avecAccent, sansAccent) => {
    const palette = ouvrirLaPalette();
    const resultatsAccentues = palette.chercher(avecAccent);
    const resultatsNus = palette.chercher(sansAccent);

    expect(
      resultatsAccentues.length,
      `« ${avecAccent} » ne trouve rien : le témoin de la mesure est vide`,
    ).toBeGreaterThan(0);
    expect(
      resultatsNus,
      `« ${sansAccent} » rend ${resultatsNus.length} résultat(s) contre ` +
        `${resultatsAccentues.length} pour « ${avecAccent} »`,
    ).toEqual(resultatsAccentues);
  });

  it('témoin : la casse est bien repliée, elle (l’instrument mesure)', () => {
    const palette = ouvrirLaPalette();
    const minuscules = palette.chercher('agenda');
    const majuscules = palette.chercher('AGENDA');

    expect(minuscules.length).toBeGreaterThan(0);
    expect(majuscules).toEqual(minuscules);
  });

  it('les deux sections de la palette replient : capacités ET commandes', () => {
    const palette = ouvrirLaPalette();
    const resultats = palette.chercher('tache');

    // Capacité « Tâches » (CapabilityCenter) : titre puis description.
    expect(
      resultats.some((texte) => /^Tâches/.test(texte)),
      `aucune capacité « Tâches » parmi ${JSON.stringify(resultats)}`,
    ).toBe(true);
    // Commande « Ouvrir les Tâches » (registre d'actions).
    expect(
      resultats.some((texte) => texte.includes('Ouvrir les Tâches')),
      `aucune commande « Ouvrir les Tâches » parmi ${JSON.stringify(resultats)}`,
    ).toBe(true);
  });

  it('la palette historique de components/chat replie aussi', () => {
    render(<PaletteHistorique isOpen onClose={() => {}} />);
    const champ = screen.getByRole('textbox', { name: 'Rechercher une commande' });

    fireEvent.change(champ, { target: { value: 'tache' } });
    expect(screen.queryByText('Ouvrir les Tâches')).not.toBeNull();

    fireEvent.change(champ, { target: { value: 'decision' } });
    expect(screen.queryByText('Décision')).not.toBeNull();
  });
});
