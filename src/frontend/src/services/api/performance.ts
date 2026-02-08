/**
 * THÉRÈSE v2 - Performance API Module
 *
 * Métriques de streaming, mémoire, recherche et gestion d'énergie.
 */

import { request } from './core';

export interface PerformanceMetrics {
  total_requests: number;
  total_tokens: number;
  active_streams: number;
  avg_first_token_ms: number;
  p95_first_token_ms: number;
  recent_metrics_count: number;
  meets_sla: boolean;
}

export interface StreamingMetric {
  conversation_id: string;
  first_token_ms: number | null;
  total_time_ms: number;
  total_tokens: number;
  tokens_per_second: number;
  provider: string;
  model: string;
}

export interface MemoryStats {
  uptime_hours: number;
  gc_stats: unknown[];
  last_cleanup_ago_minutes: number;
  registered_cleanups: number;
}

export interface PowerSettings {
  health_check_interval: number;
  conversation_sync_interval: number;
  battery_saver_mode: boolean;
  reduce_animations: boolean;
}

export interface SearchResult {
  id: string;
  title: string;
  score: number;
}

export interface PerformanceStatus {
  streaming: PerformanceMetrics;
  memory: MemoryStats;
  search_index: {
    indexed_conversations: number;
    unique_words: number;
    total_entries: number;
  };
  power: PowerSettings;
  conversations_total: number;
}

export async function getPerformanceMetrics(): Promise<PerformanceMetrics> {
  return request<PerformanceMetrics>('/api/perf/metrics');
}

export async function getRecentMetrics(limit = 20): Promise<{
  metrics: StreamingMetric[];
  count: number;
}> {
  return request(`/api/perf/metrics/recent?limit=${limit}`);
}

export async function getConversationsCount(): Promise<{ total: number }> {
  return request<{ total: number }>('/api/perf/conversations/count');
}

export async function searchConversations(
  query: string,
  limit = 50
): Promise<{
  results: SearchResult[];
  source: string;
  total: number;
}> {
  return request(`/api/perf/conversations/search?q=${encodeURIComponent(query)}&limit=${limit}`);
}

export async function reindexConversations(): Promise<{
  indexed: number;
  stats: {
    indexed_conversations: number;
    unique_words: number;
    total_entries: number;
  };
}> {
  return request('/api/perf/conversations/reindex', { method: 'POST' });
}

export async function getMemoryStats(): Promise<MemoryStats> {
  return request<MemoryStats>('/api/perf/memory');
}

export async function triggerMemoryCleanup(): Promise<{
  success: boolean;
  results: Record<string, unknown>;
  stats: MemoryStats;
}> {
  return request('/api/perf/memory/cleanup', { method: 'POST' });
}

export async function getPowerSettings(): Promise<PowerSettings> {
  return request<PowerSettings>('/api/perf/power');
}

export async function updatePowerSettings(
  settings: Partial<PowerSettings>
): Promise<PowerSettings> {
  const params = new URLSearchParams();
  if (settings.health_check_interval !== undefined) {
    params.append('health_check_interval', settings.health_check_interval.toString());
  }
  if (settings.conversation_sync_interval !== undefined) {
    params.append('conversation_sync_interval', settings.conversation_sync_interval.toString());
  }
  if (settings.battery_saver_mode !== undefined) {
    params.append('battery_saver_mode', settings.battery_saver_mode.toString());
  }
  if (settings.reduce_animations !== undefined) {
    params.append('reduce_animations', settings.reduce_animations.toString());
  }
  return request<PowerSettings>(`/api/perf/power?${params.toString()}`, {
    method: 'POST',
  });
}

export async function setBatterySaver(enabled: boolean): Promise<{
  battery_saver_enabled: boolean;
  settings: PowerSettings;
}> {
  return request(`/api/perf/power/battery-saver?enabled=${enabled}`, {
    method: 'POST',
  });
}

export async function getPerformanceStatus(): Promise<PerformanceStatus> {
  return request<PerformanceStatus>('/api/perf/status');
}
