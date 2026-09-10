/**
 * DA « Application affinée », lot 1 (10/09/2026) : la coque.
 *
 * `base.css` de la DA validée : barre de 3,25 rem, rail de 3,5 rem à boutons
 * de 2,5 rem (actif = teinte d'accent, pas le cyan plein), colonne de 56 rem,
 * composeur flottant qui porte l'établi des cinq verbes en tête, bouton
 * d'envoi de 2,25 rem sans bordure d'encre. Le badge « Interface unifiée »
 * (persona 08 : « je ne sais pas ce que c'est ») disparaît.
 *
 * Tailwind ne génère que ce qu'il lit littéralement : ces classes doivent
 * être dans le JSX telles quelles, d'où des assertions sur `className`.
 */
import { act, fireEvent, render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { useChatStore } from '../../stores/chatStore';
import { useNavigationStore } from '../../stores/navigationStore';
import { usePanelStore } from '../../stores/panelStore';
import { usePersonalisationStore } from '../../stores/personalisationStore';
import { _clearEscapeHandlers } from '../../lib/escapeStack';
import { ConversationCanvasPrototype } from './ConversationCanvasPrototype';
import { Ligne } from '../ui/Ligne';

vi.mock('../../services/api/voice', async (importOriginal) => ({
  ...(await importOriginal<object>()),
}));

// Lot 2 DA : le brief reçoit un jour connu et une seule source présente,
// pour vérifier la ligne du jour (date en français, sources, heure).
const briefDuLot2 = vi.hoisted(() => ({
  date: '2026-09-10',
  events: [],
  urgent_tasks: [{ id: 't1', title: 'Relancer Claire Roux', status: 'todo', priority: 'high', due_date: '2026-09-08', project_id: null }],
  due_follow_ups: [],
  overdue_invoices: [],
  stale_prospects: [],
  indisponibles: [],
  summary: { events_count: 0, tasks_count: 1, follow_ups_count: 0, invoices_count: 0, prospects_count: 0 },
}));
vi.mock('../../services/api/dashboard', async (importOriginal) => ({
  ...(await importOriginal<object>()),
  fetchTodayDashboard: vi.fn(async () => briefDuLot2),
  fetchSetupStatus: vi.fn(async () => ({ has_calendar: true, has_email: true, billing_complete: true, has_invoices: true, has_llm_key: true, indisponibles: [] })),
}));

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
  useNavigationStore.setState({ activeView: 'chat', history: [] });
  usePersonalisationStore.setState({ skipDashboard: false });
});

describe('La coque prend la forme de la DA', () => {
  it('le rail fait 3,5 rem sur fond de surface, ses boutons 2,5 rem', () => {
    render(<ConversationCanvasPrototype />);
    const rail = screen.getByRole('navigation', { name: 'Navigation principale' });
    expect(rail.className).toMatch(/\bw-14\b/);
    expect(rail.className).not.toMatch(/\bw-16\b/);
    expect(rail.className).toMatch(/\bbg-surface\b/);
    const accueil = screen.getByRole('button', { name: 'Accueil' });
    expect(accueil.className).toMatch(/\bh-10\b/);
    expect(accueil.className).toMatch(/\bw-10\b/);
    expect(accueil.className).toMatch(/\brounded-sm\b/);
  });

  it('le rail dit où l’on est : Accueil porte aria-current à l’accueil, Projets quand la vue Projets est ouverte', async () => {
    render(<ConversationCanvasPrototype />);
    const accueil = screen.getByRole('button', { name: 'Accueil' });
    expect(accueil).toHaveAttribute('aria-current', 'page');
    // Actif = teinte d'accent, jamais le cyan plein (réservé au geste principal).
    expect(accueil.className).toMatch(/\bbg-accent-tint\b/);
    expect(accueil.className).not.toMatch(/\bbg-accent-fill\b/);

    // Revue Grok du diff (P1) : presser un verbe de l'établi ne quitte pas
    // l'accueil conversationnel (ni vue, ni chat) : Accueil reste la page.
    await act(async () => {
      fireEvent.click(screen.getByRole('button', { name: 'Retrouver' }));
    });
    expect(screen.getByRole('button', { name: 'Accueil' })).toHaveAttribute('aria-current', 'page');

    await act(async () => {
      fireEvent.click(screen.getByRole('button', { name: 'Projets' }));
    });
    expect(screen.getByRole('button', { name: 'Projets' })).toHaveAttribute('aria-current', 'page');
    expect(screen.getByRole('button', { name: 'Accueil' })).not.toHaveAttribute('aria-current');
  });

  it('la barre n’affiche plus « Interface unifiée » et garde l’espace de travail', () => {
    render(<ConversationCanvasPrototype />);
    expect(screen.queryByText('Interface unifiée')).toBeNull();
    expect(screen.getByTestId('workspace-label')).toBeInTheDocument();
  });

  /**
   * Recette du 10/09 à 800 px : la marque « THÉRÈSE » était écrasée par
   * l'indicateur de connexion (« THÉRÈSEur actif 10ms »). La DA masque
   * l'état secondaire et le mot « Rechercher » sous 840 px ; l'indicateur
   * de connexion reste (Finding 10) mais se tronque au lieu d'écraser.
   */
  it('à moins de 840 px, la marque ne s’écrase pas et la recherche se replie sur son icône', () => {
    render(<ConversationCanvasPrototype />);
    const marque = screen.getByText('THÉRÈSE', { selector: 'span' });
    expect(marque.className).toMatch(/\bshrink-0\b/);
    expect((marque.previousElementSibling as HTMLElement).className).toMatch(/\bshrink-0\b/);
    expect(marque.className).toMatch(/\bwhitespace-nowrap\b/);
    const etat = screen.getByTestId('etat-connexion-coque');
    expect(etat.className).toMatch(/\bmin-w-0\b/);
    expect(etat.className).toMatch(/\boverflow-hidden\b/);
    const rechercher = screen.getByText('Rechercher', { selector: 'span' });
    expect(rechercher.className).toMatch(/max-\[840px\]:hidden/);
  });

  it('la colonne et le composeur partagent la largeur de 56 rem', () => {
    render(<ConversationCanvasPrototype />);
    const fil = screen.getByTestId('prototype-conversation-scroll');
    expect((fil.firstElementChild as HTMLElement).className).toMatch(/\bmax-w-colonne\b/);
    const carte = screen.getByTestId('composeur-carte');
    expect((carte.parentElement as HTMLElement).className).toMatch(/\bmax-w-colonne\b/);
  });

  it('l’établi est le premier enfant de la carte du composeur, et le verbe pressé est en teinte', async () => {
    render(<ConversationCanvasPrototype />);
    const carte = screen.getByTestId('composeur-carte');
    const etabli = screen.getByTestId('etabli-composeur');
    expect(carte.firstElementChild).toBe(etabli);
    // Le libellé reste celui que les tests de l'établi cherchent.
    expect(etabli).toHaveTextContent('Par où commencer');

    await act(async () => {
      fireEvent.click(screen.getByRole('button', { name: 'Retrouver' }));
    });
    const retrouver = screen.getByRole('button', { name: 'Retrouver' });
    expect(retrouver).toHaveAttribute('aria-pressed', 'true');
    expect(retrouver.className).toMatch(/\bbg-accent-tint\b/);
    expect(retrouver.className).not.toMatch(/\bbg-accent-fill\b/);
    // Plus de bloc « Par où commencer » au bas de la colonne.
    expect(screen.getAllByText('Par où commencer')).toHaveLength(1);
  });

  it('la carte du composeur porte l’ombre et l’anneau des jetons, le bouton d’envoi fait 2,25 rem sans bordure d’encre', () => {
    render(<ConversationCanvasPrototype />);
    const carte = screen.getByTestId('composeur-carte');
    expect(carte.className).toMatch(/\bshadow-lg\b/);
    expect(carte.className).not.toMatch(/rgba/);
    const envoyer = screen.getByRole('button', { name: 'Poursuivre dans le chat' });
    expect(envoyer.className).toMatch(/\bh-9\b/);
    expect(envoyer.className).toMatch(/\bw-9\b/);
    expect(envoyer.className).not.toMatch(/\bborder-text\b/);
    expect(envoyer.className).not.toMatch(/translate/);
  });

  it('le titre d’accueil laisse la couche base poser sa taille', () => {
    render(<ConversationCanvasPrototype />);
    const h1 = screen.getByRole('heading', { level: 1 });
    expect(h1.className).not.toMatch(/\btext-2xl\b/);
    expect(h1.className).not.toMatch(/tracking-\[/);
  });
});

describe('Lot 2 DA : l’en-tête de l’Accueil', () => {
  it('sur le brief : portrait rond, titre éditorial, ligne du jour avec date, sources et heure, plus de ligne « THÉRÈSE · »', async () => {
    render(<ConversationCanvasPrototype />);
    const jour = await screen.findByTestId('accueil-jour');
    // La date vient du backend (jamais `new Date('AAAA-MM-JJ')`, BUG-125) ;
    // seul le premier caractère est en capitale ; l'heure est celle de la coque.
    await screen.findByRole('button', { name: 'Relancer Claire Roux' });
    expect(jour.textContent).toMatch(/^Jeudi 10 septembre · Sources : tâches · Rafraîchi à \d{1,2}:\d{2}$/);
    expect(screen.queryByText('THÉRÈSE', { selector: 'div' })).toBeNull();
    const h1 = screen.getByRole('heading', { level: 1 });
    expect(h1.className).toMatch(/\bfont-editorial\b/);
    const entete = screen.getByTestId('accueil-entete');
    expect(entete.className).toMatch(/grid-cols-\[2rem_1fr\]/);
    expect((entete.firstElementChild as HTMLElement).className).toMatch(/\brounded-full\b/);
    expect((entete.firstElementChild as HTMLElement).className).not.toMatch(/\bborder\b/);
  });

  it('sur Retrouver (mémoire) : la ligne « THÉRÈSE · heure » est intacte', async () => {
    render(<ConversationCanvasPrototype />);
    await screen.findByTestId('accueil-jour');
    await act(async () => {
      fireEvent.click(screen.getByRole('button', { name: 'Retrouver' }));
    });
    expect(screen.getByText('THÉRÈSE', { selector: 'div' }).textContent).toMatch(/\d{1,2}:\d{2}/);
    expect(screen.queryByTestId('accueil-jour')).toBeNull();
  });
});

describe('Lot 2 DA : le composeur reste au-dessus des lignes du brief', () => {
  it('le fond du composeur porte un plan (z-20) supérieur au z-10 de la zone droite d’une Ligne', async () => {
    // Recette du 11/09 à 800 px : l'étiquette « À traiter » d'une ligne
    // repliée sous le composeur se dessinait PAR-DESSUS lui. La `Ligne`
    // pose `relative z-10` sur sa zone droite ; sans plan, le fond du
    // composeur (plus loin dans le DOM, sans z-index) perdait.
    render(<ConversationCanvasPrototype />);
    await screen.findByTestId('accueil-jour');
    const fond = screen.getByTestId('prototype-composer-backdrop');
    const planDuFond = Number(/\bz-(\d+)\b/.exec(fond.className)?.[1]);
    expect(planDuFond).toBe(20);
    // Revue Grok du diff : la relation de plans se mesure des deux côtés.
    const { container } = render(<Ligne titre="L" droite={<span>d</span>} onClick={() => {}} />);
    const droite = container.querySelector('[class*="z-"]') as HTMLElement;
    const planDeLaLigne = Number(/\bz-(\d+)\b/.exec(droite.className)?.[1]);
    expect(planDeLaLigne).toBe(10);
    expect(planDeLaLigne).toBeLessThan(planDuFond);
  });
});
