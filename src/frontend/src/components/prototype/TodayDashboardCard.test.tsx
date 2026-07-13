import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import type { TodayDashboard } from '../../services/api/dashboard';
import { TodayDashboardCard } from './TodayDashboardCard';

function dashboard(overrides: Partial<TodayDashboard> = {}): TodayDashboard {
  return {
    date: '2026-07-13',
    events: [],
    urgent_tasks: [],
    overdue_invoices: [],
    stale_prospects: [],
    summary: { events_count: 0, tasks_count: 0, invoices_count: 0, prospects_count: 0 },
    ...overrides,
  };
}

describe('TodayDashboardCard', () => {
  it('affiche les données réelles et ouvre leur vue classique', () => {
    const onOpenView = vi.fn();
    render(
      <TodayDashboardCard
        resource={{
          status: 'ready',
          error: null,
          data: dashboard({
            events: [{
              id: 'e1', summary: 'Rendez-vous réel', start_datetime: null,
              start_date: '2026-07-13', end_datetime: null, location: null, all_day: true,
            }],
          }),
        }}
        onRetry={vi.fn()}
        onOpenView={onOpenView}
      />,
    );

    expect(screen.getByText('Rendez-vous réel')).toBeInTheDocument();
    expect(screen.getByText('1 élément issu de tes données')).toBeInTheDocument();
    fireEvent.click(screen.getByText('Rendez-vous réel'));
    expect(onOpenView).toHaveBeenCalledWith('calendar');
  });

  it('distingue les états erreur et vide', () => {
    const retry = vi.fn();
    const { rerender } = render(
      <TodayDashboardCard
        resource={{ status: 'error', data: null, error: 'Indisponible.' }}
        onRetry={retry}
        onOpenView={vi.fn()}
      />,
    );
    expect(screen.getByTestId('today-dashboard-error')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Réessayer' }));
    expect(retry).toHaveBeenCalledTimes(1);

    rerender(
      <TodayDashboardCard
        resource={{ status: 'ready', data: dashboard(), error: null }}
        onRetry={retry}
        onOpenView={vi.fn()}
      />,
    );
    expect(screen.getByTestId('today-dashboard-empty')).toBeInTheDocument();
  });
});
