/**
 * DA « Application affinée », lot 7 : l'écran Décision (Board) prend la
 * forme de la maquette `decision.html` en consommant les primitives du
 * lot 1. Design : `docs/plans/2026-09-11-da-lot7-decision-design.md` (v7),
 * § 6 « Gardes mécaniques ». Mêmes données, mêmes états, mêmes
 * destinations : aucune de ces gardes ne porte sur un appel réseau, un
 * store ou une navigation.
 *
 * Ce que jsdom ne peut pas voir (nombre de colonnes rendu, clip du bouton
 * étiré, largeur des barres de chargement, poids visuel d'un bouton sur son
 * fond) est prouvé par la recette du § 8.3, pas ici.
 */
import { fireEvent, render, screen, within } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import type { AdvisorInfo, AdvisorRole, BoardDecisionDetail } from '../../services/api/board';
import { BoardHistoryCard, BoardWorkspaceCanvas } from './BoardConversationCard';
import type { BoardRunState, BoardWorkspaceData, PrototypeAdvisorState } from './usePrototypeBoardData';

const ORDRE: AdvisorRole[] = ['analyst', 'strategist', 'devil', 'pragmatic', 'visionary'];

const QUESTION = 'Faut-il accepter la mission du Garage Benali à 840 € en trois semaines ?';

const advisors: AdvisorInfo[] = [
  { role: 'analyst', name: "L'Analyste", emoji: '', color: '', personality: 'Données et mesures' },
  { role: 'strategist', name: 'Le Stratège', emoji: '', color: '', personality: 'Vision et positionnement' },
  { role: 'devil', name: "L'Avocat du Diable", emoji: '', color: '', personality: 'Ce qui peut mal tourner' },
  { role: 'pragmatic', name: 'Le Pragmatique', emoji: '', color: '', personality: 'Faisabilité' },
  { role: 'visionary', name: 'Le Visionnaire', emoji: '', color: '', personality: 'Innovation' },
];

const synthese = {
  consensus_points: ['Un acompte sécurise la trésorerie'],
  divergence_points: ['Le délai de trois semaines'],
  recommendation: 'Accepter, à deux conditions.',
  confidence: 'high' as const,
  next_steps: ['Confirmer l’acompte'],
};

const decision: BoardDecisionDetail = {
  id: 'decision-1',
  question: QUESTION,
  context: 'Agenda déjà chargé la semaine du 22',
  opinions: [{ role: 'analyst', name: "L'Analyste", emoji: '', content: 'Mesurer avant extension.' }],
  synthesis: synthese,
  mode: 'sovereign',
  created_at: '2026-07-13T10:00:00Z',
};

const runIdle: BoardRunState = {
  status: 'idle', question: '', context: '', mode: 'cloud', phase: '',
  isSearchingWeb: false, advisors: {}, synthesis: null, decisionId: null, error: null,
};

const workspace: BoardWorkspaceData = {
  advisors,
  decisions: [{
    id: decision.id, question: decision.question, context: decision.context,
    recommendation: synthese.recommendation, confidence: 'high', mode: 'sovereign',
    created_at: decision.created_at,
  }],
};

function avis(role: AdvisorRole, patch: Partial<PrototypeAdvisorState> = {}): PrototypeAdvisorState {
  return { role, name: role, provider: 'ollama', content: '', isRunning: false, isComplete: false, ...patch };
}

function run(patch: Partial<BoardRunState> = {}): BoardRunState {
  return { ...runIdle, question: QUESTION, mode: 'cloud', ...patch };
}

/** N conseillers terminés, les autres pas encore partis. */
function runEnCours(termines: number): BoardRunState {
  const etats: Record<string, PrototypeAdvisorState> = {};
  ORDRE.slice(0, termines).forEach((role) => {
    etats[role] = avis(role, { content: 'Avis rendu.', isComplete: true });
  });
  return run({ status: 'running', phase: 'Consultation des conseillers', advisors: etats });
}

/** `chunk.type === 'error'` ne touche pas `advisors` : les avis restent. */
function runPartiel(rendus: number, cinquiemeAvecTexte = false): BoardRunState {
  const etats: Record<string, PrototypeAdvisorState> = {};
  ORDRE.slice(0, rendus).forEach((role) => {
    etats[role] = avis(role, { content: 'Avis rendu.', isComplete: true });
  });
  if (cinquiemeAvecTexte) {
    etats[ORDRE[4]] = avis(ORDRE[4], { content: 'Avis interrompu en cours de route.', isRunning: true });
  }
  return run({
    status: 'error', phase: 'Délibération interrompue', advisors: etats,
    error: 'La délibération s’est interrompue avant sa sauvegarde.',
  });
}

type PropsCanevas = Parameters<typeof BoardWorkspaceCanvas>[0];
type PropsCarte = Parameters<typeof BoardHistoryCard>[0];

function carte(extra: Partial<PropsCarte> = {}) {
  return render(<BoardHistoryCard
    resource={{ status: 'ready', data: workspace, error: null }}
    run={runIdle}
    onRetry={vi.fn()} onOpenDecision={vi.fn()} onNewBoard={vi.fn()}
    onOpenCurrent={vi.fn()} onOpenClassic={vi.fn()}
    {...extra}
  />);
}

function canevas(extra: Partial<PropsCanevas> = {}) {
  return render(<BoardWorkspaceCanvas
    resource={{ status: 'ready', data: workspace, error: null }}
    decisionResource={null}
    run={runIdle}
    target="new-board"
    onRetry={vi.fn()} onRetryDecision={vi.fn()} onStart={vi.fn()}
    onCancel={vi.fn()} onReset={vi.fn()} onOpenClassic={vi.fn()}
    {...extra}
  />);
}

function detail(data: BoardDecisionDetail = decision, extra: Partial<PropsCanevas> = {}) {
  return canevas({
    decisionResource: { status: 'ready', data, error: null },
    target: data.id,
    ...extra,
  });
}

const GRILLE_AVIS = '[class*="minmax(16rem,1fr)"]';
const RANGEE = '[class*="grid-cols-[2rem_1fr_auto]"]';

function classes(n: Element): string {
  const brut = (n as HTMLElement).className;
  if (typeof brut === 'string') return brut;
  const svg = (n as SVGElement).className;
  return typeof svg === 'object' && svg && 'baseVal' in svg ? svg.baseVal : '';
}

/**
 * Un fond posé sur l'élément, pas le `hover:bg-surface-2` que `Ligne` porte
 * pour toutes ses rangées : on découpe en jetons et on ignore les variantes.
 */
function porteUnFond(n: Element): boolean {
  return classes(n).split(/\s+/).some((jeton) => /^bg-/.test(jeton));
}

function precede(a: Element, b: Element): boolean {
  return Boolean(a.compareDocumentPosition(b) & Node.DOCUMENT_POSITION_FOLLOWING);
}

function occurrences(racine: HTMLElement, motif: RegExp): number {
  return (racine.textContent ?? '').match(new RegExp(motif.source, 'g'))?.length ?? 0;
}

/** Plancher typographique du lot 3 : un interactif et son sous-arbre. */
function interactifsSousLePlancher(racine: HTMLElement): string[] {
  const fautifs: string[] = [];
  for (const el of racine.querySelectorAll('button, input, select, textarea, a, [role="radio"]')) {
    for (const n of [el, ...Array.from(el.querySelectorAll('*'))]) {
      if (/\btext-xs\b/.test(classes(n))) {
        fautifs.push(((el as HTMLElement).textContent ?? el.tagName).trim().slice(0, 48));
        break;
      }
    }
  }
  return fautifs;
}

// ---------------------------------------------------------------------------
// Garde 1 : la carte d'historique
// ---------------------------------------------------------------------------

describe('Lot 7 DA : les rangées de l’historique sont des Ligne', () => {
  it('une rangée = un seul bouton, grille 2rem 1fr auto, détail non concaténé', () => {
    carte();
    const titre = screen.getByRole('button', { name: QUESTION });
    const rangee = titre.closest(RANGEE) as HTMLElement;
    expect(rangee).not.toBeNull();
    expect(within(rangee).getAllByRole('button')).toHaveLength(1);

    const detailLigne = within(rangee).getByText(synthese.recommendation);
    expect(detailLigne.tagName).toBe('P');
    expect(detailLigne.textContent).toBe(synthese.recommendation);
    expect(classes(detailLigne)).toMatch(/\btruncate\b/);

    expect(classes(titre)).toMatch(/\bblock\b/);
    expect(classes(titre)).toMatch(/\bw-full\b/);
    expect(classes(titre)).toMatch(/\btruncate\b/);
    expect(classes(titre)).not.toMatch(/\brelative\b/);
  });

  it('la droite porte la date, le mode sans le mot « Mode », puis l’étiquette', () => {
    carte();
    const rangee = screen.getByRole('button', { name: QUESTION }).closest(RANGEE) as HTMLElement;
    const droite = rangee.children[2] as HTMLElement;
    const dateAttendue = new Date(decision.created_at).toLocaleString('fr-FR', {
      day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit',
    });
    expect(droite.textContent).toContain(dateAttendue);
    expect(droite.textContent).toContain('Souverain');
    expect(droite.textContent).not.toContain('Mode souverain');
    const badge = droite.querySelector('[data-etiquette]') as HTMLElement;
    expect(badge).not.toBeNull();
    expect(badge.textContent).toBe('Consensus élevé');
  });

  it('sans mode enregistré, ni « Souverain », ni « Cloud », ni le séparateur', () => {
    const sansMode = {
      ...workspace,
      decisions: [{ ...workspace.decisions[0], mode: undefined }],
    };
    carte({ resource: { status: 'ready', data: sansMode, error: null } });
    const rangee = screen.getByRole('button', { name: QUESTION }).closest(RANGEE) as HTMLElement;
    const droite = rangee.children[2] as HTMLElement;
    expect(droite.textContent).not.toContain('Souverain');
    expect(droite.textContent).not.toContain('Cloud');
    const dateAttendue = new Date(decision.created_at).toLocaleString('fr-FR', {
      day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit',
    });
    const segment = droite.querySelector('span') as HTMLElement;
    expect(segment.textContent).toBe(dateAttendue);
  });

  it('un consensus faible ou moyen n’est jamais une erreur', () => {
    for (const confidence of ['low', 'medium']) {
      const { unmount } = carte({
        resource: {
          status: 'ready',
          data: { ...workspace, decisions: [{ ...workspace.decisions[0], confidence }] },
          error: null,
        },
      });
      const badge = screen.getByTestId('board-history-card').querySelector('[data-etiquette]') as HTMLElement;
      expect(classes(badge)).not.toMatch(/text-error/);
      unmount();
    }
  });

  it('la carte coupe ce qui dépasse et le run en cours n’est pas une rangée peinte', () => {
    carte({ run: runEnCours(2) });
    expect(classes(screen.getByTestId('board-history-card'))).toMatch(/\boverflow-hidden\b/);

    const enveloppe = screen.getByTestId('board-current-run');
    expect(porteUnFond(enveloppe)).toBe(false);
    const rangee = enveloppe.querySelector(RANGEE) as HTMLElement;
    expect(rangee).not.toBeNull();
    expect(porteUnFond(rangee)).toBe(false);
    expect(rangee.getAttribute('data-testid')).toBeNull();
  });
});

// ---------------------------------------------------------------------------
// Garde 2 : l'ordre du corps
// ---------------------------------------------------------------------------

describe('Lot 7 DA : la synthèse est présentée tôt', () => {
  it('précède la première carte d’avis en run complet, en détail et en attente', () => {
    const montages: Array<() => ReturnType<typeof render>> = [
      () => canevas({ run: run({ status: 'complete', synthesis: synthese, decisionId: 'd-1', advisors: runEnCours(5).advisors }), target: 'current' }),
      () => detail(),
      () => canevas({ run: runEnCours(2), target: 'current' }),
    ];
    for (const monter of montages) {
      const { container, unmount } = monter();
      const synthesePanneau = screen.getByTestId('board-synthesis');
      const grille = container.querySelector(GRILLE_AVIS) as HTMLElement;
      expect(grille).not.toBeNull();
      expect(precede(synthesePanneau, grille.firstElementChild as HTMLElement)).toBe(true);
      expect(within(synthesePanneau).queryByRole('heading', { level: 2 })).toBeNull();
      unmount();
    }
  });

  it('en attente, le placeholder remplace la synthèse sans laisser de trou', () => {
    canevas({ run: runEnCours(2), target: 'current' });
    const panneau = screen.getByTestId('board-synthesis');
    expect(panneau.textContent).toContain('Synthèse en préparation, elle arrive après le dernier avis.');
    expect(screen.queryByRole('heading', { name: 'Où les avis divergent' })).toBeNull();
  });

  it('la barre de progression précède la synthèse, qui précède les avis', () => {
    const { container } = canevas({ run: runEnCours(2), target: 'current' });
    const barre = screen.getByRole('progressbar');
    const panneau = screen.getByTestId('board-synthesis');
    const grille = container.querySelector(GRILLE_AVIS) as HTMLElement;
    expect(precede(barre, panneau)).toBe(true);
    expect(precede(panneau, grille.firstElementChild as HTMLElement)).toBe(true);
  });

  it('les extraits et l’usage viennent après les divergences', () => {
    const avecSources: BoardDecisionDetail = {
      ...decision,
      web_sources: [{ title: 'Article', url: 'https://exemple.test/a', snippet: 'Extrait' }],
      synthesis_usage: { provider: 'ollama', model: 'mistral' },
    };
    detail(avecSources);
    const divergences = screen.getByRole('heading', { name: 'Où les avis divergent' });
    const extraits = screen.getByRole('heading', { name: 'Extraits du moteur de recherche' });
    expect(precede(divergences, extraits)).toBe(true);
  });

  it('les deux conteneurs gardent leur testid et la grille son gabarit', () => {
    const { container, unmount } = canevas({ run: runEnCours(2), target: 'current' });
    expect(screen.getByTestId('board-run-view')).toBeInTheDocument();
    expect(container.querySelector(GRILLE_AVIS)).not.toBeNull();
    expect(container.querySelector('[class*="sm:grid-cols-2"]')).toBeNull();
    expect(container.querySelector('[class*="xl:grid-cols-2"]')).toBeNull();
    unmount();

    const { container: c2 } = detail();
    expect(screen.getByTestId('board-decision-detail')).toBeInTheDocument();
    expect(c2.querySelector(GRILLE_AVIS)).not.toBeNull();
    expect(c2.querySelector('[class*="xl:grid-cols-2"]')).toBeNull();
  });
});

// ---------------------------------------------------------------------------
// Garde 3 : l'état d'un avis
// ---------------------------------------------------------------------------

describe('Lot 7 DA : un avis dit ce qu’il est', () => {
  function carteDe(container: HTMLElement, rang: number): HTMLElement {
    const grille = container.querySelector(GRILLE_AVIS) as HTMLElement;
    return grille.children[rang] as HTMLElement;
  }

  it('« Réfléchit… » seulement pendant un run, sur un avis sans contenu', () => {
    const enCours = run({
      status: 'running', phase: 'Consultation des conseillers',
      advisors: { analyst: avis('analyst', { isRunning: true }) },
    });
    const { container } = canevas({ run: enCours, target: 'current' });
    const premiere = carteDe(container, 0);
    expect(premiere.textContent).toContain('Réfléchit…');
    expect(premiere.textContent).not.toContain('Avis non rendu');
    // Le conseiller qui n'est pas encore parti a le squelette, sans étiquette.
    const seconde = carteDe(container, 1);
    expect(seconde.textContent).not.toContain('Réfléchit…');
    expect(seconde.textContent).not.toContain('Avis non rendu');
  });

  it('hors run, un avis vide est « Avis non rendu », sans bouton ni spinner', () => {
    const { container } = canevas({ run: runPartiel(4), target: 'current' });
    const cinquieme = carteDe(container, 4);
    expect(cinquieme.textContent).toContain('Avis non rendu');
    expect(cinquieme.textContent).not.toContain('Réfléchit…');
    expect(within(cinquieme).queryByRole('button')).toBeNull();
    expect(cinquieme.querySelector('.animate-spin')).toBeNull();
  });

  it('un avis interrompu AVEC du texte reste lisible, en Markdown', () => {
    const interrompu = run({
      status: 'error', phase: 'Délibération interrompue',
      advisors: { analyst: avis('analyst', { content: '### Points de vigilance\n\n- **Budget** à borner', isRunning: true }) },
      error: 'Le flux s’est interrompu.',
    });
    const { container } = canevas({ run: interrompu, target: 'current' });
    const premiere = carteDe(container, 0);
    expect(premiere.textContent).not.toContain('Avis non rendu');
    expect(within(premiere).getByRole('heading', { name: 'Points de vigilance' })).toBeInTheDocument();
    expect(premiere.textContent).not.toContain('###');
    expect(premiere.querySelector('.animate-spin')).toBeNull();
  });

  it('le contenu d’un avis en cours n’est pas passé au Markdown', () => {
    const enCours = run({
      status: 'running', phase: 'Consultation des conseillers',
      advisors: { analyst: avis('analyst', { content: '### Titre en cours', isRunning: true }) },
    });
    const { container } = canevas({ run: enCours, target: 'current' });
    const premiere = carteDe(container, 0);
    expect(premiere.textContent).toContain('### Titre en cours');
    expect(within(premiere).queryByRole('heading', { name: 'Titre en cours' })).toBeNull();
  });
});

// ---------------------------------------------------------------------------
// Garde 4 : le statut, une seule fois, dans la meta de la question
// ---------------------------------------------------------------------------

describe('Lot 7 DA : un seul statut, dans la meta de la question', () => {
  function carteQuestion(): HTMLElement {
    return screen.getByRole('heading', { name: QUESTION, level: 3 }).closest('section') as HTMLElement;
  }

  it('un détail sauvegardé est enregistré, quoi que fasse le run en arrière-plan', () => {
    detail(decision, { run: runEnCours(2) });
    const vue = screen.getByTestId('board-decision-detail');
    expect(carteQuestion().querySelectorAll('[data-etiquette]')).toHaveLength(1);
    expect(carteQuestion().textContent).toContain('Décision enregistrée');
    expect(vue.textContent).not.toContain('Délibération en cours');
    expect(occurrences(vue, /Décision enregistrée/)).toBe(1);
  });

  it('la meta d’un détail compte les avis qu’il affiche, et rien d’autre', () => {
    const { unmount } = detail();
    expect(carteQuestion().textContent).toContain('1 conseiller');
    expect(carteQuestion().textContent).not.toContain('5 conseillers');
    expect(carteQuestion().textContent).toContain('Mode souverain');
    unmount();

    const deux: BoardDecisionDetail = {
      ...decision,
      opinions: [decision.opinions[0], { role: 'strategist', name: 'Le Stratège', emoji: '', content: 'Accepter.' }],
    };
    const { unmount: u2 } = detail(deux);
    expect(carteQuestion().textContent).toContain('2 conseillers');
    u2();

    detail({ ...decision, mode: undefined });
    expect(carteQuestion().textContent).not.toContain('Mode cloud');
    expect(carteQuestion().textContent).not.toContain('Mode souverain');
  });

  it('un run en cours dit N/5, un run complet dit enregistrée', () => {
    const { unmount } = canevas({ run: runEnCours(2), target: 'current' });
    expect(carteQuestion().textContent).toContain('Délibération en cours · 2/5 avis');
    expect(carteQuestion().textContent).toContain('5 conseillers');
    expect(carteQuestion().textContent).toContain('Mode cloud');
    unmount();

    canevas({
      run: run({ status: 'complete', synthesis: synthese, decisionId: 'd-42', advisors: runEnCours(5).advisors }),
      target: 'current',
    });
    expect(carteQuestion().textContent).toContain('Décision enregistrée');
    expect(carteQuestion().textContent).toContain('Identifiant : d-42');
  });

  it('une délibération partielle compte les avis rendus, sans dénominateur', () => {
    const { unmount } = canevas({ run: runPartiel(4), target: 'current' });
    expect(carteQuestion().textContent).toContain('Délibération partielle · 4 avis rendus');
    expect(screen.getByTestId('board-run-view').textContent).not.toContain('/5 avis');
    unmount();

    const { unmount: u2 } = canevas({ run: runPartiel(4, true), target: 'current' });
    expect(carteQuestion().textContent).toContain('Délibération partielle · 5 avis rendus');
    expect(screen.getByTestId('board-run-view').textContent).not.toContain('5/5');
    u2();

    canevas({ run: runPartiel(1), target: 'current' });
    expect(carteQuestion().textContent).toContain('Délibération partielle · 1 avis rendu');
    expect(carteQuestion().textContent).not.toContain('1 avis rendus');
  });

  it('un échec sans aucun avis n’a pas d’étiquette de statut', () => {
    canevas({ run: runPartiel(0), target: 'current' });
    expect(carteQuestion().querySelectorAll('[data-etiquette]')).toHaveLength(0);
    expect(screen.getByTestId('board-run-view').textContent).toContain('Délibération incomplète.');
  });

  it('la meta de la synthèse ne compte rien, dans les trois montages', () => {
    const phrase = 'Ce que les avis ont en commun, et ce qui les sépare';
    const montages = [
      () => canevas({ run: runEnCours(2), target: 'current' }),
      () => canevas({ run: run({ status: 'complete', synthesis: synthese, advisors: runEnCours(5).advisors }), target: 'current' }),
      () => detail(),
    ];
    for (const monter of montages) {
      const { unmount } = monter();
      const panneau = screen.getByTestId('board-synthesis');
      expect(panneau.textContent).toContain(phrase);
      expect(panneau.textContent).not.toContain('cinq avis');
      expect(panneau.textContent).not.toContain('quatre avis');
      unmount();
    }
  });

  it('la zone de progression ne répète pas le compte et porte son icône', () => {
    const { container, unmount } = canevas({ run: runEnCours(2), target: 'current' });
    const vue = screen.getByTestId('board-run-view');
    expect(vue.textContent).not.toContain('conseillers terminés');
    const barre = screen.getByRole('progressbar');
    expect(barre).toHaveAttribute('aria-valuenow', '2');
    expect(barre).toHaveAttribute('aria-valuetext', '2 conseillers sur 5 terminés');
    // Sans recherche web, la roue du Spinner (aria-hidden, sans role status).
    const zone = barre.parentElement as HTMLElement;
    expect(zone.querySelector('.animate-spin')).not.toBeNull();
    expect(container.querySelectorAll('[role="status"][aria-label]')).toHaveLength(0);
    unmount();

    const { container: c2 } = canevas({
      run: { ...runEnCours(2), isSearchingWeb: true, phase: 'Recherche web en cours' },
      target: 'current',
    });
    const pulse = c2.querySelector('.animate-pulse');
    expect(pulse).not.toBeNull();
    expect(pulse?.getAttribute('aria-hidden')).toBe('true');
  });

  it('la zone de progression garde le conteneur teinté qu’elle avait', () => {
    /* Reprise de la revue du diff, point 3 : le bloc phase + barre était une
       carte teintée avant le lot, laissée en `div` nu sans qu’aucune ligne du
       design l’autorise. Dans un panneau qui défile, la teinte est ce qui
       désigne la zone vivante. */
    canevas({ run: runEnCours(2), target: 'current' });
    const zone = screen.getByRole('progressbar').parentElement as HTMLElement;
    const jetons = classes(zone).split(/\s+/);
    for (const attendu of ['rounded-md', 'border', 'border-accent-cyan/30', 'bg-accent-tint', 'p-3']) {
      expect(jetons, classes(zone)).toContain(attendu);
    }
  });
});

// ---------------------------------------------------------------------------
// Garde 5 : un seul Réessayer, une Nouvelle question sur tout run arrêté
// ---------------------------------------------------------------------------

describe('Lot 7 DA : un seul Réessayer, un seul geste de sortie', () => {
  const compteReessayer = (racine: HTMLElement) => within(racine).queryAllByRole('button', { name: 'Réessayer' }).length;

  it('un Réessayer sur chaque erreur, zéro ailleurs', () => {
    const { unmount } = carte({ resource: { status: 'error', data: null, error: 'Lecture impossible' } });
    expect(compteReessayer(screen.getByTestId('board-history-card'))).toBe(1);
    unmount();

    const { unmount: u2, container: c2 } = carte({ resource: { status: 'ready', data: { ...workspace, decisions: [] }, error: null } });
    expect(compteReessayer(c2 as unknown as HTMLElement)).toBe(0);
    expect(screen.getByTestId('board-history-empty')).toBeInTheDocument();
    u2();

    const { unmount: u3, container: c3 } = carte({ resource: { status: 'loading', data: null, error: null } });
    expect(compteReessayer(c3 as unknown as HTMLElement)).toBe(0);
    u3();

    const { unmount: u4, container: c4 } = canevas({ resource: { status: 'error', data: null, error: 'Board indisponible' } });
    expect(compteReessayer(c4 as unknown as HTMLElement)).toBe(1);
    u4();

    const { container: c5 } = canevas({
      decisionResource: { status: 'error', data: null, error: 'Décision introuvable' },
      target: decision.id,
    });
    expect(compteReessayer(c5 as unknown as HTMLElement)).toBe(1);
  });

  it('« Nouvelle question » sur tout run arrêté, jamais pendant qu’il tourne', () => {
    for (const etat of ['complete', 'cancelled', 'error', 'persistence_error'] as const) {
      const { unmount } = canevas({
        run: run({ status: etat, advisors: runEnCours(5).advisors, synthesis: etat === 'complete' ? synthese : null, error: 'Interrompue' }),
        target: 'current',
      });
      const vue = screen.getByTestId('board-run-view');
      expect(within(vue).getByRole('button', { name: 'Nouvelle question' })).toBeInTheDocument();
      expect(compteReessayer(vue)).toBe(0);
      unmount();
    }
    canevas({ run: runEnCours(2), target: 'current' });
    const vue = screen.getByTestId('board-run-view');
    expect(within(vue).queryByRole('button', { name: 'Nouvelle question' })).toBeNull();
    expect(within(vue).getByRole('button', { name: 'Annuler la délibération' })).toBeInTheDocument();
  });
});

// ---------------------------------------------------------------------------
// Garde 6 : la tête du canevas
// ---------------------------------------------------------------------------

describe('Lot 7 DA : la tête du canevas dit « Décision »', () => {
  it('plus de « Board réel », et le bandeau garde sa réserve pour le bouton Fermer', () => {
    const { container } = canevas();
    expect(container.textContent).not.toContain('Board réel');
    expect(container.textContent).not.toContain('Délibération stratégique');
    const titre = screen.getByRole('heading', { name: 'Décision', level: 2 });
    expect(titre).toBeInTheDocument();
    const bandeau = titre.closest('div') as HTMLElement;
    expect(classes(bandeau)).toBe('border-b border-border px-5 py-4 pr-16');
    /* Reprise de la revue du diff, point 9 : `mt-2` réservait l’écart au
       sur-titre « Board réel », parti avec le lot. Il poussait le titre de
       8 px sans plus rien au-dessus de lui. */
    expect(classes(titre)).toBe('text-xl font-bold tracking-[-0.02em] text-text');
  });
});

// ---------------------------------------------------------------------------
// Garde 7 : plancher typographique et jetons
// ---------------------------------------------------------------------------

describe('Lot 7 DA : plancher typographique', () => {
  const avecSources: BoardDecisionDetail = {
    ...decision,
    web_sources: [{ title: 'Article', url: 'https://exemple.test/a', snippet: 'Extrait du moteur' }],
  };

  /* Le § 6.7 annonce « carte + canevas » et la première écriture de cette
     garde ne visitait que trois montages (revue du diff, point 4) : ni les
     deux confirmations, ni le run en cours du canevas, ni les états vide,
     erreur et chargement n'étaient balayés. Un plancher qui ne balaie pas
     tout l'écran ne dit rien de l'écran. */
  const montages: Array<[string, () => ReturnType<typeof render>]> = [
    ['formulaire', () => canevas()],
    ['détail avec extraits web', () => detail(avecSources)],
    ['carte, run en cours', () => carte({ run: runEnCours(2) })],
    ['canevas, run en cours', () => canevas({ run: runEnCours(2), target: 'current' })],
    ['canevas, détail en chargement', () => canevas({
      decisionResource: { status: 'loading', data: null, error: null }, target: decision.id,
    })],
    ['canevas, décision en erreur', () => canevas({
      decisionResource: { status: 'error', data: null, error: 'Décision illisible' }, target: decision.id,
    })],
    ['carte, historique vide', () => carte({
      resource: { status: 'ready', data: { ...workspace, decisions: [] }, error: null },
    })],
    ['carte, historique en panne', () => carte({
      resource: { status: 'error', data: null, error: 'Lecture impossible' },
    })],
    ['carte, historique en chargement', () => carte({
      resource: { status: 'loading', data: null, error: null },
    })],
    ['confirmation de lancement', () => {
      const rendu = canevas();
      fireEvent.change(screen.getByLabelText('Question stratégique'), { target: { value: QUESTION } });
      fireEvent.click(screen.getByRole('button', { name: 'Préparer la délibération' }));
      return rendu;
    }],
    ['confirmation d’annulation', () => {
      const rendu = canevas({ run: runEnCours(2), target: 'current' });
      fireEvent.click(screen.getByRole('button', { name: 'Annuler la délibération' }));
      return rendu;
    }],
  ];

  it('aucune classe text-xs sur un interactif ni dans son sous-arbre', () => {
    for (const [nom, monter] of montages) {
      const { container, unmount } = monter();
      expect(interactifsSousLePlancher(container as unknown as HTMLElement), nom).toEqual([]);
      unmount();
    }
  });
});

// ---------------------------------------------------------------------------
// Garde 8 : les primitives, les marges et les glyphes
// ---------------------------------------------------------------------------

describe('Lot 7 DA : les primitives portent l’écran', () => {
  it('la carte d’historique nomme sa section par le titre de sa tête', () => {
    carte();
    const section = screen.getByTestId('board-history-card');
    expect(section.tagName).toBe('SECTION');
    expect(section.getAttribute('aria-labelledby')).toBe('board-history-title');
    expect(screen.getByRole('heading', { name: 'Décision', level: 2 }).id).toBe('board-history-title');
  });

  it('les trois états de la carte transmettent leur testid et rendent leur geste', () => {
    const { unmount } = carte({ resource: { status: 'error', data: null, error: 'Lecture impossible' } });
    const alerte = screen.getByTestId('board-history-error');
    expect(alerte.getAttribute('role')).toBe('alert');
    expect(alerte.querySelector('svg')).not.toBeNull();
    expect(classes(alerte.parentElement as HTMLElement)).toBe('px-4 pt-3 pb-4');
    unmount();

    carte({ resource: { status: 'ready', data: { ...workspace, decisions: [] }, error: null } });
    const vide = screen.getByTestId('board-history-empty');
    expect(within(vide).getByRole('button', { name: 'Convoquer le Board' })).toBeInTheDocument();
    expect(vide.querySelector('svg')).toBeNull();
  });

  it('les deux chargements du canevas empilent un texte annoncé et deux barres', () => {
    const { container, unmount } = canevas({ resource: { status: 'loading', data: null, error: null } });
    const zone = screen.getByRole('status');
    expect(zone.textContent).toContain('Chargement du Board…');
    expect(classes(zone.parentElement as HTMLElement)).toMatch(/\bflex-col\b/);
    expect(container.querySelectorAll('[aria-hidden="true"] > div[class*="animate-"]').length).toBeGreaterThanOrEqual(2);
    unmount();

    canevas({ decisionResource: { status: 'loading', data: null, error: null }, target: decision.id });
    expect(screen.getByRole('status').textContent).toContain('Chargement de la décision…');
  });

  it('le formulaire relie ses libellés à ses champs', () => {
    canevas();
    const contexte = screen.getByLabelText('Contexte utile, facultatif');
    expect(contexte.id).toBe('board-context');
    expect(contexte).toHaveAttribute('placeholder', 'Contraintes, hypothèses, chiffres ou échéance…');
    expect(classes(contexte)).toMatch(/\bh-24\b/);
    expect(screen.getByLabelText('Question stratégique').id).toBe('board-question');
  });

  it('la carte de mode active garde la couleur de domaine', () => {
    canevas();
    const souverain = screen.getByRole('radio', { name: /Souverain/ });
    const cloud = screen.getByRole('radio', { name: /Cloud/ });
    expect(classes(cloud)).toMatch(/border-domaine-prospects/);
    expect(classes(cloud)).toMatch(/bg-domaine-prospects-tint/);
    expect(classes(cloud)).not.toMatch(/bg-accent-tint/);
    expect(classes(souverain)).not.toMatch(/bg-domaine-prospects-tint/);
  });

  it('la tête de la synthèse porte la pastille de domaine, jamais une balance', () => {
    detail();
    const panneau = screen.getByTestId('board-synthesis');
    const pastille = panneau.querySelector('[aria-hidden="true"][class*="rounded-full"]') as HTMLElement;
    expect(pastille).not.toBeNull();
    expect(classes(pastille)).toBe('grid h-8 w-8 shrink-0 place-items-center rounded-full bg-accent-tint text-accent');
    expect(within(panneau).getByRole('heading', { name: 'Synthèse', level: 3 })).toBeInTheDocument();
  });

  it('l’intitulé « Recommandation : » est frère de la donnée, jamais collé à elle', () => {
    detail();
    const panneau = screen.getByTestId('board-synthesis');
    const donnee = within(panneau).getByText(synthese.recommendation);
    expect(donnee.tagName).toBe('B');
    expect(donnee.textContent).toBe(synthese.recommendation);
    const bloc = donnee.closest('[class*="bg-accent-tint"]') as HTMLElement;
    expect(bloc).not.toBeNull();
    expect(classes(bloc)).toBe('flex items-start gap-3 rounded-sm bg-accent-tint p-3');
    expect(bloc.textContent).toContain('Recommandation : ');
  });

  it('les titres de la synthèse et des extraits sont au même rang typographique', () => {
    const avecSources: BoardDecisionDetail = {
      ...decision,
      web_sources: [{ title: 'Article', url: 'https://exemple.test/a', snippet: 'Extrait' }],
      synthesis_usage: { provider: 'ollama', model: 'mistral' },
    };
    detail(avecSources);
    for (const nom of ['Consensus', 'Prochaines étapes', 'Extraits du moteur de recherche']) {
      const titre = screen.getByRole('heading', { name: nom, level: 4 });
      expect(classes(titre)).toBe('text-sm font-bold text-text');
    }
    const usage = screen.getByText(/^Synthèse : ollama/);
    expect(classes(usage)).toMatch(/\btext-sm\b/);
    expect(classes(usage)).not.toMatch(/\btext-xs\b/);
  });

  it('les trois marges intérieures sont posées', () => {
    const { container } = detail();
    const carteQuestion = screen.getByRole('heading', { name: QUESTION, level: 3 }).closest('section') as HTMLElement;
    expect(classes(carteQuestion)).toMatch(/\bp-4\b/);
    const corpsSynthese = screen.getByTestId('board-synthesis').querySelector('[class*="px-4"][class*="pb-4"]');
    expect(corpsSynthese).not.toBeNull();
    const premierAvis = (container.querySelector(GRILLE_AVIS) as HTMLElement).firstElementChild as HTMLElement;
    expect(premierAvis.tagName).toBe('SECTION');
    expect(classes(premierAvis)).toMatch(/\bp-3\b/);
  });

  it('la meta d’un avis est coupée, et absente quand rien n’est mesuré', () => {
    const { container, unmount } = canevas({ run: runEnCours(5), target: 'current' });
    const premier = (container.querySelector(GRILLE_AVIS) as HTMLElement).firstElementChild as HTMLElement;
    const meta = premier.querySelector('p') as HTMLElement;
    expect(classes(meta)).toMatch(/\btruncate\b/);
    expect(classes(meta)).toMatch(/\btext-sm\b/);
    const nom = within(premier).getByText("L'Analyste");
    expect(nom.tagName).toBe('STRONG');
    expect(classes(nom)).toBe('block text-sm font-semibold');
    unmount();

    const { container: c2 } = detail();
    const carteAvis = (c2.querySelector(GRILLE_AVIS) as HTMLElement).firstElementChild as HTMLElement;
    expect(carteAvis.textContent).not.toContain('provider inconnu');
    expect(carteAvis.textContent).not.toContain('modèle non mesuré');
  });

  it('la confirmation de lancement garde ses deux gestes', () => {
    canevas();
    fireEvent.change(screen.getByLabelText('Question stratégique'), { target: { value: QUESTION } });
    fireEvent.click(screen.getByRole('button', { name: 'Préparer la délibération' }));
    const bloc = screen.getByTestId('board-confirmation');
    expect(within(bloc).getByRole('button', { name: 'Annuler' })).toBeInTheDocument();
    const lancer = within(bloc).getByRole('button', { name: 'Confirmer et lancer' });
    expect(lancer).not.toBeDisabled();
    /* Le `disabled={run.status === 'running'}` du design (§ 4) N'EST PAS
       observable depuis la surface exportée : `showRun` remplace le
       formulaire par `BoardRunView` dès que `run.status !== 'idle'`
       (`BoardWorkspaceCanvas`), donc ce bouton n'existe jamais pendant un
       run. C'est un filet contre un second POST dans la fenêtre où le
       parent n'a pas encore basculé l'état ; il est conservé dans le code
       sans garde mécanique possible ici, faute de montage qui l'atteigne. */
  });

  it('le bloc d’annulation ne peint pas son bouton de la couleur de son fond', () => {
    canevas({ run: runEnCours(2), target: 'current' });
    fireEvent.click(screen.getByRole('button', { name: 'Annuler la délibération' }));
    const bloc = screen.getByTestId('board-cancel-confirmation');
    expect(classes(bloc)).toMatch(/\bbg-surface\b/);
    expect(classes(bloc)).not.toMatch(/color-error-tint/);
    expect(within(bloc).getByRole('button', { name: 'Confirmer l’annulation' })).toBeInTheDocument();
    expect(within(bloc).getByRole('button', { name: 'Continuer en arrière-plan' })).toBeInTheDocument();
  });

  it('les glyphes décoratifs des rangées et des têtes d’avis sont masqués', () => {
    /* Décision 8 : une icône décorative porte `aria-hidden`, sauf celles
       qu'un `Button` ou une prop `icone` nomme déjà par leur libellé. Les
       glyphes que ce lot passe en `puce` et en `droite` ne sont ni l'un ni
       l'autre, et `Ligne` pose l'attribut sur le `span` vide, jamais sur
       celui qui porte un glyphe (revue du diff, point 6). */
    const nonMasques = (racine: HTMLElement, zone: string): string[] => {
      const fautifs: string[] = [];
      for (const bloc of racine.querySelectorAll(zone)) {
        for (const svg of bloc.querySelectorAll('svg')) {
          if (svg.closest('button')) continue;
          if (!svg.closest('[aria-hidden="true"]')) fautifs.push(classes(svg));
        }
      }
      return fautifs;
    };

    const montages: Array<[string, string, () => ReturnType<typeof render>]> = [
      ['carte, run en cours', RANGEE, () => carte({ run: runEnCours(2) })],
      ['carte, run terminé', RANGEE, () => carte({ run: run({ status: 'complete', decisionId: 'decision-1' }) })],
      ['carte, run en échec', RANGEE, () => carte({ run: runPartiel(2) })],
      ['canevas, têtes d’avis', GRILLE_AVIS, () => canevas({ run: runEnCours(2), target: 'current' })],
    ];
    const fautifs: string[] = [];
    for (const [nom, zone, monter] of montages) {
      const { container, unmount } = monter();
      for (const c of nonMasques(container as unknown as HTMLElement, zone)) fautifs.push(`${nom} : ${c}`);
      unmount();
    }
    expect(fautifs).toEqual([]);
  });

  it('tout glyphe est en 18 px, sauf la roue nommée du Spinner', () => {
    const montages = [
      () => carte({ run: runEnCours(2) }),
      () => canevas(),
      () => canevas({ run: runEnCours(2), target: 'current' }),
      () => detail({
        ...decision,
        web_sources: [{ title: 'Article', url: 'https://exemple.test/a', snippet: 'Extrait' }],
      }),
    ];
    for (const monter of montages) {
      const { container, unmount } = monter();
      const fautifs: string[] = [];
      for (const svg of container.querySelectorAll('svg')) {
        const c = classes(svg);
        if (/\banimate-spin\b/.test(c)) continue;
        if (!/h-\[18px\]/.test(c) || !/w-\[18px\]/.test(c)) fautifs.push(c);
      }
      expect(fautifs).toEqual([]);
      /* Les `Button` de la DA sont en `inline-flex` : une icône y colle au
         libellé sans `gap`. Les cartes du radiogroup empilent leur contenu,
         elles ne sont pas concernées. */
      for (const bouton of container.querySelectorAll('button[class*="inline-flex"]')) {
        if (bouton.querySelector('svg') && (bouton.textContent ?? '').trim().length > 0) {
          expect(classes(bouton), bouton.textContent ?? '').toMatch(/\bgap-/);
        }
      }
      unmount();
    }
  });
});
