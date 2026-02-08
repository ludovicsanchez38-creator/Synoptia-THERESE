/**
 * THÉRÈSE v2 - Escalation API Module
 *
 * Limites de tokens, coûts, historique d'usage et détection d'incertitude.
 */

import { request } from './core';

export interface CostEstimate {
  model: string;
  input_tokens: number;
  output_tokens: number;
  estimated_cost_eur: number;
}

export interface TokenPrice {
  input_per_1m: number;
  output_per_1m: number;
  input_per_1k: number;
  output_per_1k: number;
}

export interface TokenLimits {
  max_input_tokens: number;
  max_output_tokens: number;
  daily_input_limit: number;
  daily_output_limit: number;
  monthly_budget_eur: number;
  warn_at_percentage: number;
}

export interface LimitCheckResult {
  allowed: boolean;
  warnings: string[];
  errors: string[];
}

export interface DailyUsage {
  date: string;
  input_tokens: number;
  output_tokens: number;
  total_tokens: number;
  cost_eur: number;
  input_limit: number;
  output_limit: number;
  input_usage_pct: number;
  output_usage_pct: number;
}

export interface MonthlyUsage {
  month: string;
  input_tokens: number;
  output_tokens: number;
  total_tokens: number;
  cost_eur: number;
  budget_eur: number;
  budget_usage_pct: number;
}

export interface UsageRecord {
  timestamp: string;
  conversation_id: string;
  model: string;
  provider: string;
  input_tokens: number;
  output_tokens: number;
  cost_eur: number;
  context_truncated: boolean;
  truncated_messages: number;
}

export interface UsageStats {
  daily: DailyUsage;
  monthly: MonthlyUsage;
  limits: TokenLimits;
  history_count: number;
}

export interface UncertaintyResult {
  is_uncertain: boolean;
  uncertainty_phrases: string[];
  confidence_score: number;
  confidence_level: 'high' | 'medium' | 'low';
  should_verify: boolean;
}

export interface ContextInfo {
  context_limits: Record<string, number>;
  truncation_policy: {
    strategy: string;
    description: string;
    keep_system_prompt: boolean;
    keep_last_n_messages: number;
    warning_threshold_pct: number;
  };
  recommendation: string;
}

export interface EscalationStatus {
  daily_usage: DailyUsage;
  monthly_usage: MonthlyUsage;
  limits: TokenLimits;
  recent_history_count: number;
}

export async function estimateCost(
  model: string,
  inputTokens: number,
  outputTokens: number
): Promise<CostEstimate> {
  return request<CostEstimate>('/api/escalation/estimate-cost', {
    method: 'POST',
    body: JSON.stringify({
      model,
      input_tokens: inputTokens,
      output_tokens: outputTokens,
    }),
  });
}

export async function getTokenPrices(): Promise<{
  prices: Record<string, TokenPrice>;
  currency: string;
}> {
  return request('/api/escalation/prices');
}

export async function getTokenLimits(): Promise<TokenLimits> {
  return request<TokenLimits>('/api/escalation/limits');
}

export async function setTokenLimits(limits: TokenLimits): Promise<TokenLimits> {
  return request<TokenLimits>('/api/escalation/limits', {
    method: 'POST',
    body: JSON.stringify(limits),
  });
}

export async function checkTokenLimits(
  inputTokens: number,
  outputTokens?: number
): Promise<LimitCheckResult> {
  const params = new URLSearchParams({ input_tokens: inputTokens.toString() });
  if (outputTokens !== undefined) {
    params.append('output_tokens', outputTokens.toString());
  }
  return request<LimitCheckResult>(`/api/escalation/check-limits?${params.toString()}`, {
    method: 'POST',
  });
}

export async function getDailyUsage(): Promise<DailyUsage> {
  return request<DailyUsage>('/api/escalation/usage/daily');
}

export async function getMonthlyUsage(): Promise<MonthlyUsage> {
  return request<MonthlyUsage>('/api/escalation/usage/monthly');
}

export async function getUsageHistory(
  limit = 50,
  conversationId?: string
): Promise<{ history: UsageRecord[]; count: number }> {
  const params = new URLSearchParams({ limit: limit.toString() });
  if (conversationId) {
    params.append('conversation_id', conversationId);
  }
  return request(`/api/escalation/usage/history?${params.toString()}`);
}

export async function getUsageStats(): Promise<UsageStats> {
  return request<UsageStats>('/api/escalation/usage/stats');
}

export async function checkUncertainty(response: string): Promise<UncertaintyResult> {
  return request<UncertaintyResult>('/api/escalation/check-uncertainty', {
    method: 'POST',
    body: JSON.stringify({ response }),
  });
}

export async function getContextInfo(): Promise<ContextInfo> {
  return request<ContextInfo>('/api/escalation/context-info');
}

export async function getEscalationStatus(): Promise<EscalationStatus> {
  return request<EscalationStatus>('/api/escalation/status');
}
