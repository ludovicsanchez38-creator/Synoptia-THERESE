/**
 * B-229 - le badge de la palette dit la combinaison réelle, pas la lettre nue.
 *
 * Constat du 02/09/2026 (reproduction RP16c) : le registre d'actions stocke la
 * lettre SEULE ('I', 'T', 'P', '⇧C', ',', '/'), valeur qui n'a de sens que
 * préfixée du modificateur - `useKeyboardShortcuts` sort par `if (!modKey)
 * return` avant toute correspondance de lettre, donc « I » tout court ne
 * déclenche rien. Les deux autres consommateurs le savent et préfixent :
 * `components/chat/CommandPalette.tsx` compose `${mod}${a.shortcut}`, et
 * `ShortcutsModal` écrit « ⌘ + I » pour Devis et factures.
 *
 * La palette réellement rendue par la coque, elle, rendait `action.shortcut`
 * brut, alors qu'elle connaît la plateforme huit lignes plus bas (« ⌘K » dans
 * son propre pied de page).
 *
 * On mesure les DEUX plateformes : un badge figé sur « ⌘ » mentirait sous
 * Windows autant que la lettre nue ment partout.
 */
import { fireEvent, render, screen, within } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { useChatStore } from '../../stores/chatStore';
import { useNavigationStore } from '../../stores/navigationStore';
import { usePanelStore } from '../../stores/panelStore';
import { usePersonalisationStore } from '../../stores/personalisationStore';
import { _clearEscapeHandlers } from '../../lib/escapeStack';
import { ConversationCanvasPrototype } from './ConversationCanvasPrototype';

const plateformeOriginale = Object.getOwnPropertyDescriptor(window.navigator, 'platform');

function poserPlateforme(valeur: string) {
  Object.defineProperty(window.navigator, 'platform', { value: valeur, configurable: true });
}

/** Ouvre la palette et rend le badge de raccourci d'une commande donnée. */
function badgeDeLaCommande(libelle: string, terme: string): string | null {
  render(<ConversationCanvasPrototype />);
  fireEvent.click(screen.getByRole('button', { name: /^Rechercher(Ctrl\+K|⌘K)$/ }));
  const champ = screen.getByRole('combobox', {
    name: 'Rechercher une commande, un parcours ou une capacité',
  });
  fireEvent.change(champ, { target: { value: terme } });

  const resultats = screen.getByRole('listbox', { name: 'Résultats' });
  const option = within(resultats)
    .getAllByRole('option')
    .find((noeud) => noeud.textContent?.includes(libelle));
  expect(option, `commande « ${libelle} » absente des résultats pour « ${terme} »`).toBeDefined();

  return option?.querySelector('kbd')?.textContent ?? null;
}

describe('B-229 - le badge de la palette désigne la combinaison réelle', () => {
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

  afterEach(() => {
    if (plateformeOriginale) {
      Object.defineProperty(window.navigator, 'platform', plateformeOriginale);
    }
  });

  it('sur Mac : « Devis et factures » se lit ⌘I, jamais la lettre nue', () => {
    poserPlateforme('MacIntel');

    const badge = badgeDeLaCommande('Ouvrir les Devis et factures', 'facture');

    expect(badge).not.toBe('I');
    expect(badge).toBe('⌘I');
  });

  it('sur Mac : le raccourci à deux touches de l’Agenda se lit ⌘⇧C', () => {
    poserPlateforme('MacIntel');

    const badge = badgeDeLaCommande("Ouvrir l'Agenda", 'agenda');

    expect(badge).not.toBe('⇧C');
    expect(badge).toBe('⌘⇧C');
  });

  it('sur Windows : le même badge se lit Ctrl+I, sans glyphe Mac', () => {
    poserPlateforme('Win32');

    const badge = badgeDeLaCommande('Ouvrir les Devis et factures', 'facture');

    expect(badge).not.toBe('I');
    expect(badge).toBe('Ctrl+I');
  });
});
