/**
 * B-1433 (recette P-146, lot 1, A-6) : sans boîte branchée, l'Accueil disait
 * que le brief « ne voit ni messages à traiter ni relances », juste au-dessus
 * d'une relance posée sur une fiche. Ce que la boîte manquante empêche de
 * voir, ce sont les messages et les relances nées d'un e-mail.
 */
import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import type { TodayDashboard } from '../../services/api/dashboard';
import { TodayDashboardCard } from './TodayDashboardCard';

const JOURNEE = {
  date: '2026-09-25', events: [], urgent_tasks: [], due_follow_ups: [], overdue_invoices: [],
  stale_prospects: [], indisponibles: [],
  summary: { events_count: 0, tasks_count: 0, follow_ups_count: 0, invoices_count: 0 },
} as unknown as TodayDashboard;

describe('B-1433 : l’invitation à brancher les mails dit juste', () => {
  it('ne prétend pas que le brief ignore toutes les relances', () => {
    render(
      <TodayDashboardCard
        resource={{ status: 'ready', data: JOURNEE, error: null }}
        onRetry={vi.fn()}
        onOpenView={vi.fn()}
        setup={{ has_calendar: true, has_email: false, billing_complete: true, has_invoices: false, has_llm_key: true, indisponibles: [] }}
        onSetupEmail={vi.fn()}
      />,
    );
    const bloc = screen.getByTestId('today-dashboard-setup-email');
    expect(bloc).not.toHaveTextContent('ni relances');
    expect(bloc).toHaveTextContent('les relances nées d’un e-mail');
  });
});
