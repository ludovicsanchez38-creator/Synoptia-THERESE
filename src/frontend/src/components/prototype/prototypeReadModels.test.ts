import { describe, expect, it } from 'vitest';
import type { Contact } from '../../services/api/memory';
import type { TodayDashboard } from '../../services/api/dashboard';
import {
  buildTodayAttentionItems,
  contactDisplayName,
  contactInitials,
  selectRecentContacts,
} from './prototypeReadModels';

function dashboard(): TodayDashboard {
  return {
    date: '2026-07-13',
    events: [{
      id: 'e1', summary: 'Point client', start_datetime: '2026-07-13T09:30:00+02:00',
      start_date: null, end_datetime: null, location: 'Manosque', all_day: false,
      attendees_count: 1, crm_contact_ids: ['c1'],
    }],
    urgent_tasks: [
      { id: 't1', title: 'Tâche en retard', status: 'todo', priority: 'high', due_date: '2026-07-12', project_id: null },
      { id: 't2', title: 'Tâche du jour', status: 'todo', priority: 'medium', due_date: '2026-07-13', project_id: null },
    ],
    due_follow_ups: [{
      id: 'f1', due_date: '2026-07-13T12:00:00', note: 'Rappeler après le devis',
      email_subject: 'Proposition commerciale', email_from: 'Camille', contact_id: 'c1',
      contact_name: 'Camille Martin',
    }],
    overdue_invoices: [{
      id: 'i1', invoice_number: 'FA-001', contact_id: 'c1', total_ttc: 1200,
      currency: 'EUR', due_date: '2026-07-10', status: 'sent',
    }],
    stale_prospects: [{
      id: 'p1', name: 'Camille Martin', company: 'Cérès', stage: 'discovery', email: null, last_interaction: null,
    }],
    summary: { events_count: 1, tasks_count: 2, follow_ups_count: 1, invoices_count: 1, prospects_count: 1 },
  };
}

const contact = (id: string, updatedAt: string, over: Partial<Contact> = {}): Contact => ({
  id,
  first_name: 'Camille',
  last_name: 'Martin',
  company: null,
  email: null,
  phone: null,
  notes: null,
  tags: null,
  stage: 'lead',
  score: 0,
  source: null,
  last_interaction: null,
  created_at: updatedAt,
  updated_at: updatedAt,
  ...over,
});

describe('prototypeReadModels', () => {
  it('place les urgences avant les éléments de lecture courante', () => {
    const items = buildTodayAttentionItems(dashboard());
    expect(items.map((item) => item.id)).toEqual([
      'task-t1', 'invoice-i1', 'event-e1', 'follow-up-f1', 'task-t2', 'prospect-p1',
    ]);
    expect(items[0]).toMatchObject({ urgent: true, targetView: 'tasks', badge: 'En retard' });
    expect(items[2]).toMatchObject({ targetView: 'calendar', title: 'Point client' });
  });

  it('masque le personnel solo sans enjeu et relègue les événements solo restants', () => {
    const data = dashboard();
    data.events = [
      { ...data.events[0], id: 'lunch', summary: 'Déjeuner', attendees_count: 0, crm_contact_ids: [] },
      { ...data.events[0], id: 'focus', summary: 'Préparer le dossier', attendees_count: 0, crm_contact_ids: [] },
      data.events[0],
    ];

    const items = buildTodayAttentionItems(data);
    expect(items.map((item) => item.id)).not.toContain('event-lunch');
    expect(items.map((item) => item.id).indexOf('event-e1')).toBeLessThan(
      items.map((item) => item.id).indexOf('event-focus'),
    );
  });

  it('construit un nom et des initiales sans inventer de donnée', () => {
    expect(contactDisplayName(contact('c1', '2026-07-01'))).toBe('Camille Martin');
    expect(contactInitials(contact('c1', '2026-07-01'))).toBe('CM');
    expect(contactDisplayName(contact('c2', '2026-07-01', {
      first_name: null, last_name: null, company: null, email: null,
    }))).toBe('Contact sans nom');
  });

  it('sélectionne les contacts les plus récemment mis à jour', () => {
    const contacts = [contact('old', '2026-06-01'), contact('new', '2026-07-12')];
    expect(selectRecentContacts(contacts, 1)[0].id).toBe('new');
  });
});
