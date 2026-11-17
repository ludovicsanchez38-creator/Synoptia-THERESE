import { beforeEach, expect, it, vi } from 'vitest';

const { apiFetch } = vi.hoisted(() => ({ apiFetch: vi.fn() }));
vi.mock('./core', () => ({ API_BASE: 'http://test', apiFetch }));

import { deleteEvent, getEvent, listEvents, updateEvent } from './calendar';

beforeEach(() => {
  apiFetch.mockReset();
  apiFetch.mockResolvedValue({ ok: true, json: async () => [] });
});

it.each([
  ['liste', () => listEvents('compte', 'primary')],
  ['lecture', () => getEvent('evenement', 'primary', 'compte')],
  ['modification', () => updateEvent('evenement', { summary: 'Modifié' }, 'primary', 'compte')],
  ['suppression', () => deleteEvent('evenement', 'primary', 'compte')],
] as const)('passe 3 : %s distingue la sélection SQL primary de l’alias Google', async (_nom, appeler) => {
  await appeler();
  const url = new URL(apiFetch.mock.calls[0][0]);
  expect(url.searchParams.get('calendar_id')).toBe('primary');
  expect(url.searchParams.get('account_id')).toBe('compte');
  expect(url.searchParams.get('calendar_id_is_stored')).toBe('true');
});

it('la liste sans sélection garde l’alias historique', async () => {
  await listEvents('compte');
  const url = new URL(apiFetch.mock.calls[0][0]);
  expect(url.searchParams.get('calendar_id')).toBe('primary');
  expect(url.searchParams.has('calendar_id_is_stored')).toBe(false);
});
