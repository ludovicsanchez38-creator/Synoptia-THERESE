/**
 * B-062, moitié frontend - une échéance de relance est un JOUR CIVIL.
 *
 * Le dépôt écrit la règle depuis le lot RE21 : `echeance_de_relance()`
 * (civil_time.py) normalise toute échéance en jour civil Europe/Paris suivi de
 * la constante de remplissage `T09:00:00`, et les trois lecteurs backend
 * tronquent à dix caractères avant toute comparaison. L'écran ne collectait
 * déjà qu'une date (`input type="date"`).
 *
 * Restaient deux écarts, dans ce seul composant :
 *  - « En retard » se calculait sur un INSTANT (`new Date(due_date) < now`),
 *    donc basculait à 09 h 01 le jour même de l'échéance ;
 *  - `formatDueDate` affichait `timeStyle: 'short'`, ce qui donnait à l'heure
 *    de remplissage l'apparence d'une donnée métier que personne n'a choisie.
 *
 * L'horloge est figée à midi UTC : Paris, UTC et Toronto partagent alors le
 * même jour civil, donc le test ne dépend pas du fuseau de la machine.
 */
import { render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { FollowUpsWorkspaceCanvas } from './FollowUpsWorkspaceCanvas';
import { deleteFollowUp, listFollowUps, updateFollowUp } from '../../services/api/follow-ups';

vi.mock('../../services/api/follow-ups', () => ({
  listFollowUps: vi.fn(),
  updateFollowUp: vi.fn(),
  deleteFollowUp: vi.fn(),
}));

const RELANCE = {
  id: 'follow-up-civil',
  email_message_id: 'message-1',
  contact_id: null,
  note: '',
  status: 'pending' as const,
  created_at: '2026-09-01T09:00:00',
  email_subject: 'Proposition à valider',
  email_from: 'Camille Martin',
  contact_name: null,
};

function rendre(due_date: string) {
  vi.mocked(listFollowUps).mockResolvedValue([{ ...RELANCE, due_date }]);
  return render(<FollowUpsWorkspaceCanvas onClose={vi.fn()} onOpenEmail={vi.fn()} />);
}

/** Le bandeau d'échéance de la seule carte rendue. */
async function ligneDEcheance(): Promise<HTMLElement> {
  await screen.findByText('Proposition à valider');
  const carte = screen.getByTestId('follow-up-row');
  const ligne = Array.from(carte.querySelectorAll('div')).find((noeud) =>
    /^(En retard|Échéance) ·/.test(noeud.textContent ?? ''),
  );
  if (!ligne) throw new Error(`aucune ligne d'échéance dans : ${carte.textContent}`);
  return ligne as HTMLElement;
}

describe('B-062 (frontend) - l’échéance d’une relance est un jour civil', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.useFakeTimers({ toFake: ['Date'] });
    // 18 h UTC : plus tard que l'heure de remplissage 09:00 ET que 17:30,
    // mais toujours le 10 septembre à Paris comme à Toronto.
    vi.setSystemTime(new Date('2026-09-10T18:00:00Z'));
    vi.mocked(updateFollowUp).mockImplementation(async (_id, update) => ({
      ...RELANCE,
      due_date: '2026-09-10T09:00:00',
      ...update,
    }));
    vi.mocked(deleteFollowUp).mockResolvedValue({ deleted: true, id: RELANCE.id });
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('une échéance du jour n’est pas « En retard », même passé l’heure de remplissage', async () => {
    rendre('2026-09-10T09:00:00');

    await waitFor(async () => {
      expect((await ligneDEcheance()).textContent).toMatch(/^Échéance ·/);
    });
  });

  it('une échéance posée à 17 h 30 hors interface reste du jour même', async () => {
    // Reserve honnête de la reproduction RP05 : une relance créée hors
    // interface peut porter une autre heure. Elle reste un jour civil.
    rendre('2026-09-10T17:30:00');

    await waitFor(async () => {
      expect((await ligneDEcheance()).textContent).toMatch(/^Échéance ·/);
    });
  });

  it('l’écran n’affiche jamais l’heure de remplissage', async () => {
    rendre('2026-09-10T09:00:00');

    const ligne = await ligneDEcheance();
    expect(ligne.textContent).not.toMatch(/\d{1,2}:\d{2}/);
    expect(ligne.textContent).toContain('10 sept. 2026');
  });

  it('témoin : la veille est bien « En retard »', async () => {
    rendre('2026-09-09T09:00:00');

    await waitFor(async () => {
      expect((await ligneDEcheance()).textContent).toMatch(/^En retard ·/);
    });
  });
});
