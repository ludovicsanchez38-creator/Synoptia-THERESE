/**
 * B-802 (cycle 9) : l'interrupteur d'économie d'énergie n'avait ni type, ni
 * role="switch", ni nom accessible, quand ceux de l'onglet Accessibilité les ont.
 */
import { render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const getPerformanceStatus = vi.fn();
vi.mock('../../services/api', async () => {
  const actual = await vi.importActual<typeof import('../../services/api')>('../../services/api');
  return { ...actual, getPerformanceStatus: (...a: unknown[]) => getPerformanceStatus(...a), setBatterySaver: vi.fn(), triggerMemoryCleanup: vi.fn() };
});
import type { PerformanceStatus } from '../../services/api';
import { PerformanceTab } from './PerformanceTab';

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


describe('PerformanceTab - B-802, un interrupteur nommé', () => {
  beforeEach(() => {
    getPerformanceStatus.mockReset();
    getPerformanceStatus.mockResolvedValue(statut({ power: { health_check_interval: 30, conversation_sync_interval: 60, battery_saver_mode: true, reduce_animations: false } }));
  });

  it('expose un role switch, son état et un nom accessible', async () => {
    render(<PerformanceTab />);
    const interrupteur = await screen.findByRole('switch', { name: /économie d’énergie|économie d'énergie/ });
    expect(interrupteur).toHaveAttribute('aria-checked', 'true');
    expect(interrupteur).toHaveAttribute('type', 'button');
  });
});
