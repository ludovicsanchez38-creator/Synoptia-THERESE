import { act, renderHook, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

vi.mock('../../services/api/memory', () => ({ getContact: vi.fn(), listProjects: vi.fn() }));
vi.mock('../../services/api/crm-extended', () => ({ listDeliverables: vi.fn() }));
vi.mock('../../services/api/invoices', () => ({ listInvoices: vi.fn() }));
vi.mock('../../services/api/tasks', () => ({ listTasks: vi.fn() }));

import { getContact, listProjects, type Contact, type Project } from '../../services/api/memory';
import { listDeliverables, type DeliverableResponse } from '../../services/api/crm-extended';
import { listInvoices, type Invoice } from '../../services/api/invoices';
import { listTasks, type Task } from '../../services/api/tasks';
import {
  usePrototypeDeliverableProjectData,
  usePrototypeDeliverablesProjects,
} from './usePrototypeDeliverablesData';

const project: Project = {
  id: 'project-1', name: 'Accompagnement réel', description: null, contact_id: 'contact-1',
  status: 'active', budget: 5000, notes: null, tags: [], created_at: '2026-07-01', updated_at: '2026-07-12',
};
const contact: Contact = {
  id: 'contact-1', first_name: 'Camille', last_name: 'Martin', company: 'Client réel', email: 'camille@example.com',
  phone: null, notes: null, tags: [], stage: 'active', score: 0, source: 'local', last_interaction: null,
  created_at: '2026-07-01', updated_at: '2026-07-12',
};
const deliverable: DeliverableResponse = {
  id: 'deliverable-1', project_id: project.id, title: 'Rapport réel', description: null, status: 'en_cours',
  due_date: '2026-07-20T10:00:00Z', completed_at: null, created_at: '2026-07-01', updated_at: '2026-07-12',
};
const task: Task = {
  id: 'task-1', title: 'Relire le rapport', description: null, status: 'todo', priority: 'high',
  due_date: null, project_id: project.id, tags: [], completed_at: null, created_at: '2026-07-01', updated_at: '2026-07-12',
};
const invoice: Invoice = {
  id: 'invoice-1', invoice_number: 'F-2026-001', contact_id: contact.id, document_type: 'facture',
  tva_applicable: true, currency: 'EUR', issue_date: '2026-07-01', due_date: '2026-07-30', status: 'sent',
  subtotal_ht: 1000, total_tax: 200, total_ttc: 1200, notes: null, payment_terms: null, payment_method: null,
  late_penalty_rate: null, legal_mentions: null, converted_from_id: null, validite_jours: null, payment_date: null,
  created_at: '2026-07-01', updated_at: '2026-07-12', lines: [],
};

describe('données Livrables 0.40', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(listProjects).mockResolvedValue([project]);
    vi.mocked(getContact).mockResolvedValue(contact);
    vi.mocked(listDeliverables).mockResolvedValue([deliverable]);
    vi.mocked(listInvoices).mockResolvedValue([invoice]);
    vi.mocked(listTasks).mockResolvedValue([task]);
  });

  it('charge uniquement l’index borné des projets à l’ouverture', async () => {
    const { result } = renderHook(() => usePrototypeDeliverablesProjects());
    await waitFor(() => expect(result.current.resource.status).toBe('ready'));

    expect(listProjects).toHaveBeenCalledWith(0, 200);
    expect(listDeliverables).not.toHaveBeenCalled();
    expect(listInvoices).not.toHaveBeenCalled();
  });

  it('charge les relations exactes du projet sélectionné', async () => {
    const { result } = renderHook(() => usePrototypeDeliverableProjectData(project));
    await waitFor(() => expect(result.current.data?.deliverables.status).toBe('ready'));

    expect(getContact).toHaveBeenCalledWith(contact.id);
    expect(listDeliverables).toHaveBeenCalledWith({ project_id: project.id });
    expect(listInvoices).toHaveBeenCalledWith({ contact_id: contact.id, limit: 100 });
    expect(listTasks).toHaveBeenCalledWith({ project_id: project.id, limit: 1000 });
    expect(result.current.data?.invoices.data).toEqual([invoice]);
  });

  it('distingue une source indisponible d’une liste vide', async () => {
    vi.mocked(listInvoices).mockRejectedValue(new Error('Facturation arrêtée'));
    const { result } = renderHook(() => usePrototypeDeliverableProjectData(project));
    await waitFor(() => expect(result.current.data?.invoices.status).toBe('error'));

    expect(result.current.data?.deliverables.status).toBe('ready');
    expect(result.current.data?.invoices.data).toBeNull();
    expect(result.current.data?.invoices.error).toContain('indisponible');
  });

  it('ne recherche ni contact ni facture pour un projet sans contact', async () => {
    const withoutContact = { ...project, id: 'project-no-contact', contact_id: null };
    const { result } = renderHook(() => usePrototypeDeliverableProjectData(withoutContact));
    await waitFor(() => expect(result.current.data?.deliverables.status).toBe('ready'));

    expect(getContact).not.toHaveBeenCalled();
    expect(listInvoices).not.toHaveBeenCalled();
    expect(result.current.data?.contact).toEqual({ status: 'ready', data: null, error: null });
    expect(result.current.data?.invoices).toEqual({ status: 'ready', data: [], error: null });
  });

  it('ignore la réponse tardive d’un ancien projet', async () => {
    let resolveFirst: ((value: DeliverableResponse[]) => void) | undefined;
    const secondProject = { ...project, id: 'project-2', name: 'Deuxième projet' };
    vi.mocked(listDeliverables).mockImplementation(({ project_id }) => {
      if (project_id === project.id) return new Promise((resolve) => { resolveFirst = resolve; });
      return Promise.resolve([{ ...deliverable, id: 'deliverable-2', project_id: secondProject.id }]);
    });
    const { result, rerender } = renderHook(
      ({ selected }) => usePrototypeDeliverableProjectData(selected),
      { initialProps: { selected: project } },
    );
    await waitFor(() => expect(result.current.data?.projectId).toBe(project.id));

    rerender({ selected: secondProject });
    await waitFor(() => expect(result.current.data?.deliverables.status).toBe('ready'));
    expect(result.current.data?.projectId).toBe(secondProject.id);

    await act(async () => resolveFirst?.([deliverable]));
    expect(result.current.data?.projectId).toBe(secondProject.id);
    expect(result.current.data?.deliverables.data?.[0]?.project_id).toBe(secondProject.id);
  });
});
