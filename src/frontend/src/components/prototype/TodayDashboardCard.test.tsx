import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import type { TodayDashboard } from '../../services/api/dashboard';
import { TodayDashboardCard } from './TodayDashboardCard';

function dashboard(overrides: Partial<TodayDashboard> = {}): TodayDashboard {
  return {
    date: '2026-07-13',
    events: [],
    urgent_tasks: [],
    due_follow_ups: [],
    overdue_invoices: [],
    stale_prospects: [],
    summary: { events_count: 0, tasks_count: 0, follow_ups_count: 0, invoices_count: 0, prospects_count: 0 },
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
              attendees_count: 1, crm_contact_ids: [],
            }],
          }),
        }}
        onRetry={vi.fn()}
        onOpenView={onOpenView}
      />,
    );

    expect(screen.getByText('Rendez-vous réel')).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'Un point mérite ton attention' })).toBeInTheDocument();
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

describe('L’état vide honnête (B1, 0.48)', () => {
  const setup = (has_email: boolean) => ({
    has_calendar: true,
    has_email,
    billing_complete: true,
    has_llm_key: true,
  });

  it('sans compte email : invite à brancher les mails, avec le bouton', () => {
    const onSetupEmail = vi.fn();
    render(
      <TodayDashboardCard
        resource={{ status: 'ready', error: null, data: dashboard() }}
        onRetry={vi.fn()}
        onOpenView={vi.fn()}
        setup={setup(false)}
        onSetupEmail={onSetupEmail}
      />,
    );

    expect(
      screen.getByText('Branche tes mails pour que je te prépare la journée'),
    ).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Brancher mes mails' }));
    expect(onSetupEmail).toHaveBeenCalledTimes(1);
  });

  it('branché et vide : le message positif réel', () => {
    render(
      <TodayDashboardCard
        resource={{ status: 'ready', error: null, data: dashboard() }}
        onRetry={vi.fn()}
        onOpenView={vi.fn()}
        setup={setup(true)}
        onSetupEmail={vi.fn()}
      />,
    );

    expect(screen.getByText('Rien d’urgent pour le moment')).toBeInTheDocument();
    expect(
      screen.queryByText('Branche tes mails pour que je te prépare la journée'),
    ).toBeNull();
  });
});
