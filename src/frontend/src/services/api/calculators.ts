/**
 * THÉRÈSE v2 - Calculators API Module
 *
 * Calculatrices business (ROI, ICE, RICE, NPV, Break-Even).
 */

import { request } from './core';

export interface ROIResult {
  investment: number;
  gain: number;
  roi_percent: number;
  profit: number;
  interpretation: string;
}

export interface ICEResult {
  impact: number;
  confidence: number;
  ease: number;
  score: number;
  interpretation: string;
}

export interface RICEResult {
  reach: number;
  impact: number;
  confidence: number;
  effort: number;
  score: number;
  interpretation: string;
}

export interface NPVResult {
  initial_investment: number;
  cash_flows: number[];
  discount_rate: number;
  npv: number;
  interpretation: string;
}

export interface BreakEvenResult {
  fixed_costs: number;
  variable_cost_per_unit: number;
  price_per_unit: number;
  break_even_units: number;
  break_even_revenue: number;
  interpretation: string;
}

export interface CalculatorInfo {
  name: string;
  endpoint: string;
  description: string;
  formula: string;
  params: string[];
}

export async function calculateROI(
  investment: number,
  gain: number
): Promise<ROIResult> {
  return request('/api/calc/roi', {
    method: 'POST',
    body: JSON.stringify({ investment, gain }),
  });
}

export async function calculateICE(
  impact: number,
  confidence: number,
  ease: number
): Promise<ICEResult> {
  return request('/api/calc/ice', {
    method: 'POST',
    body: JSON.stringify({ impact, confidence, ease }),
  });
}

export async function calculateRICE(
  reach: number,
  impact: number,
  confidence: number,
  effort: number
): Promise<RICEResult> {
  return request('/api/calc/rice', {
    method: 'POST',
    body: JSON.stringify({ reach, impact, confidence, effort }),
  });
}

export async function calculateNPV(
  initial_investment: number,
  cash_flows: number[],
  discount_rate: number
): Promise<NPVResult> {
  return request('/api/calc/npv', {
    method: 'POST',
    body: JSON.stringify({ initial_investment, cash_flows, discount_rate }),
  });
}

export async function calculateBreakEven(
  fixed_costs: number,
  variable_cost_per_unit: number,
  price_per_unit: number
): Promise<BreakEvenResult> {
  return request('/api/calc/break-even', {
    method: 'POST',
    body: JSON.stringify({ fixed_costs, variable_cost_per_unit, price_per_unit }),
  });
}

export async function getCalculatorsHelp(): Promise<{ calculators: CalculatorInfo[] }> {
  return request('/api/calc/help');
}
