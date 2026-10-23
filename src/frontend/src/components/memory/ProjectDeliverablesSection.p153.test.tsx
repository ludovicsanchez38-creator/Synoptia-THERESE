/**
 * P-153 (recette P-146, lot 2, O9 ; acceptée le 25/09) : ajouter un livrable
 * passait par la capacité « Livrables et suivi client » ; la fenêtre du
 * projet ne montrait ni ne créait ses livrables.
 */
import { act, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const api = vi.hoisted(() => ({ listDeliverables: vi.fn(), createDeliverable: vi.fn() }));
vi.mock('../../services/api/crm-extended', async (importOriginal) => ({
  ...(await importOriginal<object>()),
  ...api,
}));

import { ProjectDeliverablesSection } from './ProjectDeliverablesSection';

describe('P-153 : les livrables dans la fenêtre du projet', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    api.listDeliverables.mockResolvedValue([
      { id: 'd1', project_id: 'p1', title: 'Plans cotés', description: null, status: 'en_cours', due_date: null, completed_at: null, created_at: '', updated_at: '' },
    ]);
    api.createDeliverable.mockImplementation(async (d: { title: string }) => ({
      id: 'd2', project_id: 'p1', title: d.title, description: null, status: 'a_faire', due_date: null, completed_at: null, created_at: '', updated_at: '',
    }));
  });

  it('liste les livrables du projet', async () => {
    render(<ProjectDeliverablesSection projectId="p1" />);
    expect(await screen.findByText('Plans cotés')).toBeInTheDocument();
    expect(screen.getByText('En cours')).toBeInTheDocument();
    expect(api.listDeliverables).toHaveBeenCalledWith({ project_id: 'p1' });
  });

  it('en ajoute un sans quitter la fenêtre', async () => {
    render(<ProjectDeliverablesSection projectId="p1" />);
    await screen.findByText('Plans cotés');
    fireEvent.change(screen.getByLabelText('Nouveau livrable'), { target: { value: 'Pose de la cuisine' } });
    fireEvent.click(screen.getByRole('button', { name: 'Ajouter le livrable' }));
    await waitFor(() => expect(api.createDeliverable).toHaveBeenCalledWith({ project_id: 'p1', title: 'Pose de la cuisine', status: 'a_faire' }));
    expect(await screen.findByText('Pose de la cuisine')).toBeInTheDocument();
  });

  it('en lecture seule (démo), pas d’ajout', async () => {
    render(<ProjectDeliverablesSection projectId="p1" lectureSeule />);
    await screen.findByText('Plans cotés');
    expect(screen.queryByRole('button', { name: 'Ajouter le livrable' })).toBeNull();
  });
});

it('B-1094 : une lecture échouée ne dit pas que la liste est vide', async () => {
  api.listDeliverables.mockRejectedValue(new Error('500'));
  render(<ProjectDeliverablesSection projectId="erreur" lectureSeule />);
  expect(await screen.findByRole('alert')).toHaveTextContent('Les livrables n’ont pas pu être lus.');
  expect(screen.queryByText('Aucun livrable pour ce projet.')).toBeNull();
});

it.each(['projet-terrasse', 'projet-grange', 'projet-atelier', 'projet-toiture', 'projet-cuisine', 'projet-salon', 'projet-jardin', 'projet-bureau', 'projet-garage', 'projet-cave'])('Rejeu B-1094 : %s', async (projectId) => {
  api.listDeliverables.mockRejectedValue(new Error(`Lecture impossible pour ${projectId}`));
  render(<ProjectDeliverablesSection projectId={projectId} lectureSeule />);
  await screen.findByRole('alert');
  expect(screen.queryByText('Aucun livrable pour ce projet.')).toBeNull();
});

it('B-1094 : un ajout ne répare pas une lecture ; seule une relecture réussie efface l’alerte', async () => {
  api.listDeliverables.mockClear().mockRejectedValue(new Error('500'));
  api.createDeliverable.mockResolvedValue({ id: 'ajout', title: 'Notice de montage', status: 'a_faire' });
  render(<ProjectDeliverablesSection projectId="p-incomplet" />);
  expect(await screen.findByRole('alert')).toHaveTextContent('Les livrables n’ont pas pu être lus.');
  fireEvent.change(screen.getByLabelText('Nouveau livrable'), { target: { value: 'Notice de montage' } });
  fireEvent.click(screen.getByRole('button', { name: 'Ajouter le livrable' }));
  await screen.findByText('Notice de montage');
  expect(screen.getByRole('alert')).toHaveTextContent('Les livrables n’ont pas pu être lus.');
  expect(screen.getByRole('alert')).toHaveTextContent('La liste peut être incomplète.');
  expect(screen.queryByText('Aucun livrable pour ce projet.')).toBeNull();
  // Une autre panne garde l'alerte.
  fireEvent.click(screen.getByRole('button', { name: 'Relire les livrables' }));
  await waitFor(() => expect(api.listDeliverables).toHaveBeenCalledTimes(2));
  expect(screen.getByRole('alert')).toBeInTheDocument();
  await waitFor(() => expect(screen.getByRole('button', { name: 'Relire les livrables' })).not.toBeDisabled());
  api.listDeliverables.mockResolvedValue([
    { id: 'ancien', title: 'Rapport existant', status: 'valide' },
    { id: 'ajout', title: 'Notice de montage', status: 'a_faire' },
  ]);
  fireEvent.click(screen.getByRole('button', { name: 'Relire les livrables' }));
  await screen.findByText('Rapport existant');
  expect(screen.getByText('Notice de montage')).toBeInTheDocument();
  expect(screen.queryByRole('alert')).toBeNull();
});

it.each(['lecture puis écriture', 'écriture puis lecture'])('B-1094 : une lecture commencée avant un ajout ne l’efface pas (%s)', async (ordre) => {
  let relire!: (liste: unknown[]) => void;
  let creer!: (livrable: object) => void;
  const lecture = new Promise<unknown[]>((resolve) => { relire = resolve; });
  const ecriture = new Promise<object>((resolve) => { creer = resolve; });
  api.listDeliverables.mockReset().mockRejectedValueOnce(new Error('500')).mockReturnValueOnce(lecture);
  api.createDeliverable.mockReset().mockReturnValueOnce(ecriture);
  render(<ProjectDeliverablesSection projectId="p-course" />);
  await screen.findByRole('alert');
  fireEvent.click(screen.getByRole('button', { name: 'Relire les livrables' }));
  await waitFor(() => expect(api.listDeliverables).toHaveBeenCalledTimes(2));
  fireEvent.change(screen.getByLabelText('Nouveau livrable'), { target: { value: 'Dossier de réception' } });
  fireEvent.click(screen.getByRole('button', { name: 'Ajouter le livrable' }));
  const nouveau = { id: 'nouveau', title: 'Dossier de réception', status: 'a_faire' };
  if (ordre === 'lecture puis écriture') {
    await act(async () => { relire([]); });
    await act(async () => { creer(nouveau); });
  } else {
    await act(async () => { creer(nouveau); });
    expect(screen.getByText('Dossier de réception')).toBeInTheDocument();
    await act(async () => { relire([]); });
    // La réponse antérieure n'a pas relu l'ajout : l'alerte reste justifiée.
    expect(screen.getByRole('alert')).toHaveTextContent('La liste peut être incomplète.');
  }
  expect(screen.getByText('Dossier de réception')).toBeInTheDocument();
  expect(screen.queryByText('Aucun livrable pour ce projet.')).toBeNull();
});

it('B-1094 : une première lecture lente terminée après un ajout garde les livrables existants', async () => {
  // Astra v4 : la réponse antérieure à l'ajout était jetée, les livrables
  // qu'elle seule connaissait disparaissaient sans alerte.
  let relire!: (liste: unknown[]) => void;
  const lecture = new Promise<unknown[]>((resolve) => { relire = resolve; });
  api.listDeliverables.mockReset().mockReturnValueOnce(lecture);
  api.createDeliverable.mockReset().mockResolvedValueOnce({ id: 'notice', title: 'Notice après travaux', status: 'a_faire' });
  render(<ProjectDeliverablesSection projectId="p-lent" />);
  fireEvent.change(screen.getByLabelText('Nouveau livrable'), { target: { value: 'Notice après travaux' } });
  fireEvent.click(screen.getByRole('button', { name: 'Ajouter le livrable' }));
  expect(await screen.findByText('Notice après travaux')).toBeInTheDocument();
  await act(async () => { relire([{ id: 'plans', title: 'Plans déjà déposés', status: 'valide' }]); });
  expect(screen.getByText('Plans déjà déposés')).toBeInTheDocument();
  expect(screen.getByText('Notice après travaux')).toBeInTheDocument();
  expect(screen.queryByRole('alert')).toBeNull();
});

// Rejeu de la fusion, entrées inventées après le correctif : existants de 0 à
// 4, ajout déjà présent ou non dans la réponse tardive (jamais en double).
it.each([
  [[], false], [['Devis signé'], false], [['Devis signé', 'Plans'], false], [['A', 'B', 'C'], false],
  [['A', 'B', 'C', 'D'], false], [[], true], [['Devis signé'], true], [['Métré', 'Photos'], true],
  [['Réception'], false], [['Réserves', 'Levée des réserves'], true],
])('Rejeu fusion B-1094 : existants %j, ajout déjà relu %s', async (titres, dejaRelu) => {
  let relire!: (liste: unknown[]) => void;
  api.listDeliverables.mockReset().mockReturnValueOnce(new Promise<unknown[]>((resolve) => { relire = resolve; }));
  const ajout = { id: 'ajout', title: 'Notice', status: 'a_faire' };
  api.createDeliverable.mockReset().mockResolvedValueOnce(ajout);
  render(<ProjectDeliverablesSection projectId={`p-${titres.length}-${dejaRelu}`} />);
  fireEvent.change(screen.getByLabelText('Nouveau livrable'), { target: { value: 'Notice' } });
  fireEvent.click(screen.getByRole('button', { name: 'Ajouter le livrable' }));
  await screen.findByText('Notice');
  const lus = (titres as string[]).map((t, i) => ({ id: `e${i}`, title: t, status: 'a_faire' }));
  await act(async () => { relire(dejaRelu ? [...lus, ajout] : lus); });
  for (const t of titres as string[]) expect(screen.getByText(t)).toBeInTheDocument();
  expect(screen.getAllByText('Notice')).toHaveLength(1);
  expect(screen.queryByRole('alert')).toBeNull();
});

it('B-1094 : une lecture qui contient déjà l’ajout, arrivée avant la réponse de création, ne le double pas', async () => {
  let relire!: (liste: unknown[]) => void;
  let creer!: (livrable: object) => void;
  api.listDeliverables.mockReset().mockReturnValueOnce(new Promise<unknown[]>((resolve) => { relire = resolve; }));
  api.createDeliverable.mockReset().mockReturnValueOnce(new Promise<object>((resolve) => { creer = resolve; }));
  render(<ProjectDeliverablesSection projectId="p-ordre" />);
  fireEvent.change(screen.getByLabelText('Nouveau livrable'), { target: { value: 'Notice' } });
  fireEvent.click(screen.getByRole('button', { name: 'Ajouter le livrable' }));
  const ajout = { id: 'ajout', title: 'Notice', status: 'a_faire' };
  await act(async () => { relire([{ id: 'plans', title: 'Plans', status: 'valide' }, ajout]); });
  await act(async () => { creer(ajout); });
  expect(screen.getAllByText('Notice')).toHaveLength(1);
  expect(screen.getByText('Plans')).toBeInTheDocument();
});
