import { useCallback, useEffect, useRef, useState } from 'react';
import { getContact, listProjects, type Contact, type Project } from '../../services/api/memory';
import { listDeliverables, type DeliverableResponse } from '../../services/api/crm-extended';
import { listInvoices, type Invoice } from '../../services/api/invoices';
import { listTasks, type Task } from '../../services/api/tasks';
import type { ReadResource } from './usePrototypeReadData';

export type SectionResource<T> = ReadResource<T>;

export interface DeliverableProjectData {
  projectId: string;
  contact: SectionResource<Contact | null>;
  deliverables: SectionResource<DeliverableResponse[]>;
  invoices: SectionResource<Invoice[]>;
  tasks: SectionResource<Task[]>;
  invoiceLimitReached: boolean;
  taskLimitReached: boolean;
}

const loading = <T>(): SectionResource<T> => ({ status: 'loading', data: null, error: null });

function resultResource<T>(result: PromiseSettledResult<T>, error: string): SectionResource<T> {
  return result.status === 'fulfilled'
    ? { status: 'ready', data: result.value, error: null }
    : { status: 'error', data: null, error };
}

export function usePrototypeDeliverablesProjects() {
  const [resource, setResource] = useState<ReadResource<Project[]>>(loading<Project[]>());

  const refresh = useCallback(async () => {
    setResource(loading<Project[]>());
    try {
      const projects = await listProjects(0, 200);
      setResource({ status: 'ready', data: projects, error: null });
    } catch {
      setResource({ status: 'error', data: null, error: 'Le référentiel des projets est indisponible.' });
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  return { resource, refresh, limitReached: resource.status === 'ready' && resource.data.length === 200 };
}

export function usePrototypeDeliverableProjectData(project: Project | null) {
  const [data, setData] = useState<DeliverableProjectData | null>(null);
  const requestIdRef = useRef(0);

  const refresh = useCallback(async () => {
    if (!project) {
      requestIdRef.current += 1;
      setData(null);
      return;
    }

    const requestId = requestIdRef.current + 1;
    requestIdRef.current = requestId;
    setData({
      projectId: project.id,
      contact: project.contact_id ? loading<Contact | null>() : { status: 'ready', data: null, error: null },
      deliverables: loading<DeliverableResponse[]>(),
      invoices: project.contact_id ? loading<Invoice[]>() : { status: 'ready', data: [], error: null },
      tasks: loading<Task[]>(),
      invoiceLimitReached: false,
      taskLimitReached: false,
    });

    const [contactResult, deliverablesResult, invoicesResult, tasksResult] = await Promise.allSettled([
      project.contact_id ? getContact(project.contact_id) : Promise.resolve(null),
      listDeliverables({ project_id: project.id }),
      project.contact_id ? listInvoices({ contact_id: project.contact_id, limit: 100 }) : Promise.resolve([]),
      listTasks({ project_id: project.id, limit: 1000 }),
    ]);

    if (requestIdRef.current !== requestId) return;
    const invoices = resultResource(invoicesResult, 'La facturation du contact est momentanément indisponible.');
    const tasks = resultResource(tasksResult, 'Les tâches du projet sont momentanément indisponibles.');
    setData({
      projectId: project.id,
      contact: resultResource(contactResult, 'Le contact du projet est momentanément indisponible.'),
      deliverables: resultResource(deliverablesResult, 'Les livrables du projet sont momentanément indisponibles.'),
      invoices,
      tasks,
      invoiceLimitReached: invoices.status === 'ready' && invoices.data.length === 100,
      taskLimitReached: tasks.status === 'ready' && tasks.data.length === 1000,
    });
  }, [project]);

  useEffect(() => {
    void refresh();
    return () => {
      requestIdRef.current += 1;
    };
  }, [refresh]);

  return { data, refresh };
}
