import { render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import type { TodayDashboard } from '../../services/api/dashboard';
import { useDemoStore } from '../../stores/demoStore';
import { TodayDashboardCard } from './TodayDashboardCard';

function dashboard(overrides: Partial<TodayDashboard> = {}): TodayDashboard {
  return {
    date: '2026-09-01',
    events: [],
    urgent_tasks: [],
    due_follow_ups: [],
    overdue_invoices: [],
    stale_prospects: [],
    indisponibles: [],
    summary: { events_count: 0, tasks_count: 0, follow_ups_count: 0, invoices_count: 0, prospects_count: 0 },
    ...overrides,
  };
}

describe('TodayDashboardCard en mode démo', () => {
  beforeEach(() => {
    useDemoStore.setState({ enabled: false, replacementMap: new Map() });
  });

  // Reproduit dans l'application lancée le 01/09/2026, données réelles :
  // Cmd+Shift+D bascule bien le store, et l'accueil continue d'afficher
  // « Relancer Nathalie BALLOT (Lou Bio) », « FORMACOM », « TOOGGY ». Le masque
  // est consommé par six surfaces — sidebar, tâches, kanban, messages, mémoire,
  // CRM — mais pas par la coque conversationnelle, qui est l'écran par défaut.
  // C'est précisément l'écran qu'on montre en démonstration.
  it('ne laisse aucun nom réel à l’écran quand le mode est actif', () => {
    useDemoStore.setState({
      enabled: true,
      replacementMap: new Map([['Nathalie BALLOT', 'Claire Fontaine']]),
    });

    render(
      <TodayDashboardCard
        resource={{
          status: 'ready',
          error: null,
          data: dashboard({
            urgent_tasks: [{
              id: 't1', title: 'Relancer Nathalie BALLOT', due_date: '2026-09-01',
              priority: 'high', status: 'todo',
            } as TodayDashboard['urgent_tasks'][number]],
          }),
        }}
        onRetry={vi.fn()}
        onOpenView={vi.fn()}
      />,
    );

    expect(screen.queryByText(/Nathalie BALLOT/)).not.toBeInTheDocument();
    expect(screen.getByText(/Claire Fontaine/)).toBeInTheDocument();
  });

  it('laisse le texte intact quand le mode est éteint', () => {
    render(
      <TodayDashboardCard
        resource={{
          status: 'ready',
          error: null,
          data: dashboard({
            urgent_tasks: [{
              id: 't1', title: 'Relancer Nathalie BALLOT', due_date: '2026-09-01',
              priority: 'high', status: 'todo',
            } as TodayDashboard['urgent_tasks'][number]],
          }),
        }}
        onRetry={vi.fn()}
        onOpenView={vi.fn()}
      />,
    );

    expect(screen.getByText(/Nathalie BALLOT/)).toBeInTheDocument();
  });
});
