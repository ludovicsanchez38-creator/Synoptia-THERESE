/**
 * Revue 30/08 : Réglages > Performances ne doit pas affirmer
 * un SLA, des tokens ou un index qui n'ont pas été mesurés.
 */
import { render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { PerformanceTab } from './PerformanceTab';
import type { PerformanceStatus } from '../../services/api/performance';

const getPerformanceStatus = vi.fn();

vi.mock('../../services/api', async () => {
  const actual = await vi.importActual<typeof import('../../services/api')>('../../services/api');
  return {
    ...actual,
    getPerformanceStatus: (...args: unknown[]) => getPerformanceStatus(...args),
    triggerMemoryCleanup: vi.fn(),
    setBatterySaver: vi.fn(),
  };
});

function statut(over: Partial<PerformanceStatus> = {}): PerformanceStatus {
  return {
    streaming: {
      total_requests: 0,
      total_tokens: 0,
      tokens_measured: false,
      active_streams: 0,
      avg_first_token_ms: 0,
      p95_first_token_ms: 0,
      recent_metrics_count: 0,
      meets_sla: null,
    },
    memory: {
      uptime_hours: 1,
      gc_stats: [],
      last_cleanup_ago_minutes: 10,
      registered_cleanups: 0,
    },
    search_index: {
      indexed_conversations: 0,
      unique_words: 0,
      total_entries: 0,
    },
    power: {
      health_check_interval: 30,
      conversation_sync_interval: 60,
      battery_saver_mode: false,
      reduce_animations: false,
    },
    conversations_total: 12,
    ...over,
  };
}

describe('PerformanceTab — vérité des compteurs', () => {
  beforeEach(() => {
    getPerformanceStatus.mockReset();
  });

  it('n’affiche pas « SLA respecté » sans aucune mesure', async () => {
    getPerformanceStatus.mockResolvedValue(statut());
    render(<PerformanceTab />);
    expect(await screen.findByText(/SLA non mesuré/i)).toBeInTheDocument();
    expect(screen.queryByText(/SLA respecté/i)).toBeNull();
  });

  it('n’affiche pas un nombre de tokens s’ils n’ont pas été mesurés', async () => {
    getPerformanceStatus.mockResolvedValue(statut());
    render(<PerformanceTab />);
    expect(await screen.findByText(/non mesurés/i)).toBeInTheDocument();
    expect(screen.queryByText('Tokens générés')).toBeNull();
  });

  it('affiche le nombre réellement indexé, pas le total SQL', async () => {
    getPerformanceStatus.mockResolvedValue(statut({
      conversations_total: 12,
      search_index: { indexed_conversations: 0, unique_words: 0, total_entries: 0 },
    }));
    render(<PerformanceTab />);
    const label = await screen.findByText('Conversations indexées');
    expect(label.previousElementSibling).toHaveTextContent('0');
  });
});
