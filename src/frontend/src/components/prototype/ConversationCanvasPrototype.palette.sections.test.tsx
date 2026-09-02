/**
 * B-244 - la palette nomme ses sections, et annonce ce qu'elle affiche.
 *
 * Constat du 02/09/2026 (reproduction RP18c) : dès qu'une requête était
 * saisie, le premier en-tête de section cessait d'être un nom de catégorie
 * (« Capacités fréquentes ») pour devenir un compteur « N résultat », rendu
 * par le MÊME `SectionLabel` que « Commandes de l'application » juste en
 * dessous - même graisse, même capitale, même interlettrage. Une catégorie et
 * un compte de résultats se lisaient donc pareil.
 *
 * Ce N ne comptait par ailleurs que les capacités, quand l'annonce sr-only
 * `role="status"` porte `optionCount`, capacités PLUS commandes : deux
 * chiffres pour un même écran, qui divergent dès qu'une commande correspond.
 *
 * Forme de référence ailleurs dans l'app : PromptLibrary annonce « 1 résultat
 * pour "relance" » hors du slot de titre.
 */
import { fireEvent, render, screen, within } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { useChatStore } from '../../stores/chatStore';
import { useNavigationStore } from '../../stores/navigationStore';
import { usePanelStore } from '../../stores/panelStore';
import { usePersonalisationStore } from '../../stores/personalisationStore';
import { _clearEscapeHandlers } from '../../lib/escapeStack';
import { ConversationCanvasPrototype } from './ConversationCanvasPrototype';

const COMPTEUR_NU = /^\d+\s+résultats?$/;

function ouvrirEtChercher(terme: string) {
  render(<ConversationCanvasPrototype />);
  fireEvent.click(screen.getByRole('button', { name: /^Rechercher(Ctrl\+K|⌘K)$/ }));
  const champ = screen.getByRole('combobox', {
    name: 'Rechercher une commande, un parcours ou une capacité',
  });
  fireEvent.change(champ, { target: { value: terme } });

  const resultats = screen.getByRole('listbox', { name: 'Résultats' });
  return {
    resultats,
    /** Les en-têtes de section, dans l'ordre du rendu. */
    entetes: Array.from(resultats.querySelectorAll('[role="presentation"]')).map(
      (noeud) => noeud.textContent?.trim() ?? '',
    ),
    options: within(resultats).queryAllByRole('option'),
    annonce: resultats.querySelector('[role="status"]')?.textContent?.trim() ?? '',
  };
}

describe('B-244 - un en-tête de section porte un nom, pas un compte', () => {
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

  it('sous une requête, aucun en-tête de section n’est un compteur', () => {
    const { entetes } = ouvrirEtChercher('facture');

    expect(entetes.length, 'aucun en-tête rendu : la mesure serait vide').toBeGreaterThan(0);
    const compteurs = entetes.filter((texte) => COMPTEUR_NU.test(texte));
    expect(
      compteurs,
      `en-tête(s) réduit(s) à un compte parmi ${JSON.stringify(entetes)}`,
    ).toEqual([]);
  });

  it('au repos, la section garde son nom de capacités mises en avant', () => {
    const { entetes } = ouvrirEtChercher('');

    expect(entetes).toContain('Capacités fréquentes');
  });

  it('sous une requête, le premier en-tête est un nom de catégorie', () => {
    // Au repos la section liste les capacités MISES EN AVANT
    // (`featuredCapabilities`) ; sous une requête elle liste toutes celles qui
    // correspondent. Le nom suit donc le contenu, mais reste un nom :
    // « fréquentes » deviendrait faux sous un filtre, un compteur ne serait
    // plus une catégorie.
    const { entetes } = ouvrirEtChercher('facture');

    expect(entetes[0]).toBe('Capacités');
  });

  it('l’annonce vocale compte les options réellement affichées', () => {
    // « facture » ramène à la fois une capacité et la commande « Ouvrir les
    // Devis et factures » : c'est le cas où les deux bases divergeaient.
    const { annonce, options } = ouvrirEtChercher('facture');

    expect(options.length, 'aucune option : la mesure serait vide').toBeGreaterThan(0);
    expect(annonce).toBe(`${options.length} résultat${options.length > 1 ? 's' : ''}`);
  });
});
