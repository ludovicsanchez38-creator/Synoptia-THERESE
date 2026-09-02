/**
 * THÉRÈSE v2 - Dashboard API (US-005)
 *
 * Client API pour le tableau de bord "Ma journée".
 */

import { request } from './core';

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
  attendees_count: number;
  crm_contact_ids: string[];
  calendar_name?: string | null;
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
  // B4 : le brief titrait « Facture FACT-2026-001 » — une référence, pas un
  // client. Rempli par le join côté API.
  contact_name?: string | null;
  total_ttc: number;
  currency: string;
  due_date: string | null;
  status: string;
}

export interface DashboardFollowUp {
  id: string;
  due_date: string;
  note: string | null;
  /** Entrée 8 : l'identifiant du message à rouvrir, quand il existe encore. */
  email_message_id: string | null;
  email_subject: string | null;
  email_from: string | null;
  contact_id: string | null;
  contact_name: string | null;
}

export interface DashboardProspect {
  id: string;
  name: string;
  company: string | null;
  stage: string;
  email: string | null;
  last_interaction: string | null;
  /** La date de relance DÉCIDÉE. C'est elle qui justifie la ligne au brief. */
  next_follow_up: string | null;
}

export interface DashboardSummary {
  events_count: number;
  tasks_count: number;
  follow_ups_count: number;
  invoices_count: number;
  prospects_count: number;
}

export interface TodayDashboard {
  date: string;
  events: DashboardEvent[];
  urgent_tasks: DashboardTask[];
  due_follow_ups: DashboardFollowUp[];
  overdue_invoices: DashboardInvoice[];
  stale_prospects: DashboardProspect[];
  /**
   * Ce que le serveur n'a PAS PU lire, nommément (« calendrier », « taches »,
   * « relances_email », « factures », « prospects »).
   *
   * B-051 : sans cette liste, les cinq lectures de /today dégradaient en
   * listes vides. Une base verrouillée, une migration en cours ou une
   * corruption arrivaient à l'écran sous la forme d'une journée calme, sur le
   * premier écran de l'application. « Rien à faire » et « on n'a pas pu
   * savoir » sont deux réponses.
   */
  indisponibles: string[];
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
  return request<TodayDashboard>('/api/dashboard/today');
}

export interface SetupStatus {
  has_calendar: boolean;
  has_email: boolean;
  billing_complete: boolean;
  /**
   * 0.55 : au moins un devis, une facture ou un avoir enregistré. L'accueil
   * masque le verbe « Facturer » tant que rien n'a été facturé et que les
   * infos de société ne sont pas renseignées.
   */
  has_invoices: boolean;
  /** US-012 : au moins une clé LLM cloud configurée (env ou DB) */
  has_llm_key: boolean;
  /**
   * Ce que le serveur n'a PAS PU vérifier, nommément (« calendrier »,
   * « email », « facturation »). Sans cette liste, un échec de lecture
   * sortait en `false`, indistinguable d'un « non configuré » : l'écran
   * réclamait de brancher ce qui l'était déjà.
   */
  indisponibles: string[];
}

/** Mise en route : ce qui reste à brancher (Accueil). 100 % local. */
export async function fetchSetupStatus(): Promise<SetupStatus> {
  return request<SetupStatus>('/api/dashboard/setup-status');
}
