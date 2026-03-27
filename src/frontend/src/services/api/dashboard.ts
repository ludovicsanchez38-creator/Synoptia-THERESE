/**
 * THÉRÈSE v2 - Dashboard API (US-005)
 *
 * Client API pour le tableau de bord "Ma journée".
 */

import { apiFetch } from './core';

// ============================================================
// Types
// ============================================================

export interface DashboardEvent {
  id: string;
  summary: string;
  start_datetime: string | null;
  start_date: string | null;
  end_datetime: string | null;
  location: string | null;
  all_day: boolean;
}

export interface DashboardTask {
  id: string;
  title: string;
  status: string;
  priority: string;
  due_date: string | null;
  project_id: string | null;
}

export interface DashboardInvoice {
  id: string;
  invoice_number: string;
  contact_id: string;
  total_ttc: number;
  currency: string;
  due_date: string | null;
  status: string;
}

export interface DashboardProspect {
  id: string;
  name: string;
  company: string | null;
  stage: string;
  email: string | null;
  last_interaction: string | null;
}

export interface DashboardSummary {
  events_count: number;
  tasks_count: number;
  invoices_count: number;
  prospects_count: number;
}

export interface TodayDashboard {
  date: string;
  events: DashboardEvent[];
  urgent_tasks: DashboardTask[];
  overdue_invoices: DashboardInvoice[];
  stale_prospects: DashboardProspect[];
  summary: DashboardSummary;
}

// ============================================================
// API
// ============================================================

/**
 * Récupère les données du tableau de bord "Ma journée".
 * Données 100% locales, se charge en <500ms.
 */
export async function fetchTodayDashboard(): Promise<TodayDashboard> {
  return apiFetch('/api/dashboard/today');
}
