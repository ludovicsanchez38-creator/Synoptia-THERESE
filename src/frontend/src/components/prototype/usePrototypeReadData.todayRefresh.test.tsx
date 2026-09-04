import { act, renderHook, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const { fetchTodayDashboardMock } = vi.hoisted(() => ({
  fetchTodayDashboardMock: vi.fn(),
}));

vi.mock('../../services/api/dashboard', () => ({
  fetchTodayDashboard: fetchTodayDashboardMock,
}));

import { useTodayDashboardResource } from './usePrototypeReadData';

const DASHBOARD = {
  date: '2026-09-04',
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
    stale_prospects_count: 0,
    total_items: 0,
  },
};

describe('B-317 : fraîcheur du brief du jour', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    fetchTodayDashboardMock.mockResolvedValue(DASHBOARD);
  });

  it('relit les données quand l application reprend le focus', async () => {
    renderHook(() => useTodayDashboardResource());
    await waitFor(() => expect(fetchTodayDashboardMock).toHaveBeenCalledTimes(1));

    act(() => window.dispatchEvent(new Event('focus')));

    await waitFor(() => expect(fetchTodayDashboardMock).toHaveBeenCalledTimes(2));
  });
});
