/**
 * B-051 (reliquat frontend). « Rien à faire aujourd'hui » et « on n'a pas pu
 * savoir » ne doivent pas produire le même écran.
 *
 * Le backend nomme désormais ce qu'il n'a pas pu lire (`indisponibles`, lot
 * RE25), exactement comme son jumeau `/setup-status` le fait depuis la 0.49.
 * Tant que l'accueil ne déclare pas ce champ, une base verrouillée, une
 * migration en cours ou une corruption se présentent comme une journée calme,
 * sur l'écran d'ouverture de l'application.
 */
import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import type { TodayDashboard } from '../../services/api/dashboard';
import { TodayDashboardCard } from './TodayDashboardCard';

function journee(overrides: Partial<TodayDashboard> = {}): TodayDashboard {
  return {
    date: '2026-09-02',
    events: [],
    urgent_tasks: [],
    due_follow_ups: [],
    overdue_invoices: [],
    stale_prospects: [],
    indisponibles: [],
    summary: {
      events_count: 0,
      tasks_count: 0,
      follow_ups_count: 0,
      invoices_count: 0,
      prospects_count: 0,
    },
    ...overrides,
  };
}

function afficher(data: TodayDashboard) {
  return render(
    <TodayDashboardCard
      resource={{ status: 'ready', data, error: null }}
      onRetry={vi.fn()}
      onOpenView={vi.fn()}
    />,
  );
}

describe('Une panne de source ne se déguise pas en journée vide', () => {
  it('journée réellement vide : l’état vide habituel, sans alarme', () => {
    afficher(journee());

    expect(screen.getByTestId('today-dashboard-empty')).toBeInTheDocument();
    expect(screen.queryByTestId('today-dashboard-indisponible')).toBeNull();
  });

  it('journée vide ET source en panne : un écran distinct, pas « rien d’urgent »', () => {
    afficher(journee({ indisponibles: ['calendrier', 'factures'] }));

    expect(screen.queryByTestId('today-dashboard-empty')).toBeNull();
    expect(screen.getByTestId('today-dashboard-incomplet')).toBeInTheDocument();
    expect(screen.getByTestId('today-dashboard-indisponible')).toBeInTheDocument();
  });

  it('la panne est nommée même quand l’écran invite à brancher les mails', () => {
    // Le cas du nouvel utilisateur dont la base est verrouillée : l'invitation
    // « Branche tes mails » est la plus actionnable, mais elle ne doit pas
    // faire disparaître la panne, sinon rien ne la dit jamais.
    render(
      <TodayDashboardCard
        resource={{ status: 'ready', data: journee({ indisponibles: ['calendrier'] }), error: null }}
        onRetry={vi.fn()}
        onOpenView={vi.fn()}
        setup={{
          has_calendar: true, has_email: false, billing_complete: true,
          has_invoices: false, has_llm_key: true, indisponibles: [],
        }}
        onSetupEmail={vi.fn()}
      />,
    );

    expect(screen.getByTestId('today-dashboard-setup-email')).toBeInTheDocument();
    expect(screen.getByTestId('today-dashboard-indisponible')).toHaveTextContent('Agenda');
  });

  it('la source en panne est NOMMÉE, pas seulement signalée', () => {
    afficher(journee({ indisponibles: ['calendrier', 'relances_email'] }));

    const bloc = screen.getByTestId('today-dashboard-indisponible');
    expect(bloc).toHaveTextContent('Agenda');
    expect(bloc).toHaveTextContent('Relances');
  });

  it('une source en panne reste nommée même quand la journée a du contenu', () => {
    afficher(
      journee({
        indisponibles: ['factures'],
        urgent_tasks: [{
          id: 't1', title: 'Rappeler le notaire', status: 'todo', priority: 'high',
          due_date: '2026-09-02', project_id: null,
        }],
      }),
    );

    expect(screen.getByText('Rappeler le notaire')).toBeInTheDocument();
    expect(screen.getByTestId('today-dashboard-indisponible')).toHaveTextContent('Factures');
  });

  it('une source inconnue du client est dite telle quelle, jamais avalée', () => {
    afficher(journee({ indisponibles: ['tresorerie'] }));

    expect(screen.getByTestId('today-dashboard-indisponible')).toHaveTextContent('tresorerie');
  });

  it('un serveur d’une version antérieure, sans le champ, ne fait pas écran noir', () => {
    // Leçon du 01/09 : une réponse amputée d'une liste faisait tomber toute
    // l'application sur son écran « Oups ! ». Le champ manquant se lit comme
    // « rien à signaler », pas comme une exception.
    const ancienne = journee();
    delete (ancienne as unknown as Record<string, unknown>).indisponibles;

    afficher(ancienne);

    expect(screen.getByTestId('today-dashboard-empty')).toBeInTheDocument();
  });
});
