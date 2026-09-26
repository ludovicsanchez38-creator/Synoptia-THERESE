/**
 * P-132, seconde moitié, lot 2 : l'étape « Perdu » à l'écran
 * (`docs/plans/2026-09-26-rfc-p132-vocabulaire-unique-perdu.md`, §4 et §7).
 *
 * Le pipeline n'avait pas de mot pour une vente perdue : Archive servait à la
 * fois pour « terminé », « perdu » et « effacé au titre du RGPD ». Perdu est
 * la huitième colonne, entre Actif et Archive ; la fiche la propose, le
 * formulaire de création ne la propose pas (on ne crée pas une fiche déjà
 * perdue, comme on ne la crée pas archivée).
 */
import { act, fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import type { Announcements, DragEndEvent } from '@dnd-kit/core';

import type { ActivityResponse, ContactResponse } from '../../services/api';
import { useCRMStore } from '../../stores/crmStore';
import { useContactsStore } from '../../stores/contactsStore';
import { presenterActivite } from '../../lib/activitesCrm';

const capture: {
  onDragEnd?: (event: DragEndEvent) => void;
  annonces?: Announcements;
} = {};

vi.mock('@dnd-kit/core', async () => {
  const reel = await vi.importActual<typeof import('@dnd-kit/core')>('@dnd-kit/core');
  return {
    ...reel,
    DndContext: (props: Parameters<typeof reel.DndContext>[0]) => {
      capture.onDragEnd = props.onDragEnd;
      capture.annonces = props.accessibility?.announcements;
      return <reel.DndContext {...props} />;
    },
  };
});

const elodie = vi.hoisted(() => ({
  id: 'ct-1', first_name: 'Élodie', last_name: 'Martin', company: 'Boulangerie Martin',
  email: 'elodie@boulangerie-exemple.fr', phone: null, address: null, notes: null, tags: null,
  scope: 'global', stage: 'proposition', score: 105, source: null, last_interaction: null,
  created_at: '2026-09-01T00:00:00Z', updated_at: '2026-09-01T00:00:00Z',
}));
const contactsLus = vi.hoisted(() => vi.fn());
const etapeChangee = vi.hoisted(() => vi.fn());

vi.mock('../../services/api', async () => {
  const reel = await vi.importActual<typeof import('../../services/api')>('../../services/api');
  return {
    ...reel,
    listProjects: vi.fn().mockResolvedValue([]),
    listActivities: vi.fn().mockResolvedValue([]),
    updateContactStage: (...a: unknown[]) => etapeChangee(...a),
  };
});
vi.mock('../../services/api/memory', async () => {
  const reel = await vi.importActual<typeof import('../../services/api/memory')>('../../services/api/memory');
  return { ...reel, listContacts: (...a: unknown[]) => contactsLus(...a) };
});
vi.mock('../../services/api/prestations', async () => {
  const reel = await vi.importActual<typeof import('../../services/api/prestations')>('../../services/api/prestations');
  return { ...reel, listerLesPrestations: vi.fn().mockResolvedValue([]) };
});

import { PipelineView } from './PipelineView';
import { CRMPanel } from './CRMPanel';
import { PIPELINE_ETAPES, etiquetteDEtape, libelleDEtape } from './pipelineEtapes';

function contact(patch: Partial<ContactResponse> = {}): ContactResponse {
  return { ...elodie, ...patch } as unknown as ContactResponse;
}

describe('P-132 : Perdu dans le Kanban', () => {
  it('huit colonnes nommées, Perdu entre Actif et Archive', () => {
    render(<PipelineView contacts={[]} onContactClick={vi.fn()} onStageChange={vi.fn()} />);

    expect(screen.getAllByRole('heading', { level: 3 }).map((h) => h.textContent)).toEqual([
      'Contact', 'Découverte', 'Proposition', 'Signature', 'Livraison', 'Actif', 'Perdu', 'Archive',
    ]);
  });

  it('déposer une carte sur Perdu l’annonce par son nom et appelle le moteur avec lost', () => {
    const onStageChange = vi.fn();
    render(<PipelineView contacts={[contact()]} onContactClick={vi.fn()} onStageChange={onStageChange} />);

    const evenement = { active: { id: 'ct-1' }, over: { id: 'lost' } } as unknown as DragEndEvent;
    expect(capture.annonces?.onDragEnd?.(evenement as never)).toMatch(/la colonne Perdu/);
    act(() => capture.onDragEnd?.(evenement));

    expect(onStageChange).toHaveBeenCalledWith('ct-1', 'lost');
  });

  it('Perdu porte le ton neutre, comme Archive : le mot porte le sens, pas la couleur', () => {
    expect(etiquetteDEtape('lost')).toEqual({ ton: 'neutre' });
    expect(etiquetteDEtape('lost')).toEqual(etiquetteDEtape('archive'));
  });
});

describe('P-132 : Perdu sur la fiche et à la création', () => {
  beforeEach(() => {
    contactsLus.mockResolvedValue([elodie]);
    etapeChangee.mockResolvedValue({ ...elodie, stage: 'lost', score: 5 });
    useCRMStore.setState({ projects: [], activeTab: 'activities' });
    useContactsStore.setState({
      contacts: [elodie] as never, loaded: true, loading: false, error: null, selectedContactId: 'ct-1', truncated: false,
    });
  });

  it('le champ « Étape » de la fiche propose Perdu et le choisit par le moteur', async () => {
    render(<CRMPanel standalone />);
    const fiche = await screen.findByRole('region', { name: 'Fiche de Élodie Martin' });
    const etape = within(fiche).getByLabelText('Étape') as HTMLSelectElement;

    expect(Array.from(etape.options).map((o) => o.text)).toContain('Perdu');
    fireEvent.change(etape, { target: { value: 'lost' } });

    await waitFor(() => expect(etapeChangee).toHaveBeenCalledWith('ct-1', 'lost'));
  });

  it('dans la fiche, un seul contrôle s’appelle « Étape » : celui du contact', async () => {
    // Revue du diff, constat 5 : le champ de création d'une prestation
    // portait le même nom accessible que l'étape du contact, qui, elle,
    // change la fiche dès le choix. Il est groupé sous « Nouvelle prestation ».
    render(<CRMPanel standalone />);
    const fiche = await screen.findByRole('region', { name: 'Fiche de Élodie Martin' });
    await screen.findByRole('group', { name: 'Nouvelle prestation' });

    const etapes = screen.getAllByLabelText('Étape');
    expect(etapes).toHaveLength(1);
    expect(within(fiche).getByLabelText('Étape')).toBe(etapes[0]);
    expect(
      within(screen.getByRole('group', { name: 'Nouvelle prestation' })).getByLabelText(
        'Étape de la nouvelle prestation',
      ),
    ).toBeInTheDocument();
  });

  it('le formulaire de création ne propose ni Perdu ni Archive', async () => {
    useCRMStore.setState({ projects: [], activeTab: 'pipeline' });
    render(<CRMPanel standalone />);
    fireEvent.click(await screen.findByRole('button', { name: /Nouveau contact/ }));

    const etape = screen.getByLabelText('Étape') as HTMLSelectElement;
    const libelles = Array.from(etape.options).map((o) => o.text);
    expect(libelles).not.toContain('Perdu');
    expect(libelles).not.toContain('Archive');
    expect(libelles).toContain('Actif');
  });
});

describe('P-132 : Perdu dans la frise', () => {
  it('un passage en Perdu se lit « Étape : Proposition → Perdu »', () => {
    const activite = {
      id: 'a1', contact_id: 'ct-1', type: 'stage_change', title: 'Stage: proposition -> lost',
      description: 'Changement de stage dans le pipeline commercial',
      extra_data: '{"old_stage": "proposition", "new_stage": "lost"}', created_at: '2026-09-26T10:00:00Z',
    } as ActivityResponse;

    expect(presenterActivite(activite).titre).toBe('Étape : Proposition → Perdu');
  });

  it('libelleDEtape connaît Perdu et la grille en compte huit', () => {
    expect(libelleDEtape('lost')).toBe('Perdu');
    expect(PIPELINE_ETAPES.map((e) => e.id)).toEqual([
      'contact', 'discovery', 'proposition', 'signature', 'delivery', 'active', 'lost', 'archive',
    ]);
  });
});
