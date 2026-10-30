import { installLocalStorageStub } from '../test/localStorage-stub';
import { beforeEach, expect, it, vi } from 'vitest';
const request = vi.hoisted(() => vi.fn());
vi.mock('../services/api/core', () => ({ request }));
import { flushConsentDecisions, synchroniserConsentements } from './consentSync';
import { CLOUD_CONSENT_KEY, grantCloudConsent, hasCloudConsent, revokeCloudConsent } from './consent';

beforeEach(async () => {
  request.mockResolvedValue({ grants: [] });
  await flushConsentDecisions();
  installLocalStorageStub();
  localStorage.setItem('therese:data-profile', '/profils/test');
  request.mockClear();
});

it('transmet au moteur les accords et retraits avec la version du texte', async () => {
  grantCloudConsent('documents', 'OpenAI', ['documents']);
  await flushConsentDecisions();
  revokeCloudConsent('documents', 'OpenAI');
  await flushConsentDecisions();
  const decisions = request.mock.calls.map(([, options]) => JSON.parse(options.body));
  expect(decisions.map(d => d.granted)).toEqual([true, false]);
  expect(decisions.every(d => d.provider === 'openai' && d.text_version === '3' && d.occurred_at && d.event_id)).toBe(true);
});

it('reprend la date v2 et remplace le cache par les décisions du moteur', async () => {
  const old = { purpose: 'llm', provider: 'openai', timestamp: '2026-01-01T12:00:00Z' };
  localStorage.setItem(CLOUD_CONSENT_KEY, JSON.stringify({ version: '2', grants: { 'llm:openai': old } }));
  await synchroniserConsentements();
  expect(JSON.parse(request.mock.calls[0][1].body).grants).toEqual([old]);
  expect(hasCloudConsent('llm', 'openai')).toBe(false);
});

it('conserve une décision non enregistrée et refuse de laisser passer un envoi', async () => {
  request.mockRejectedValue(new Error('Moteur indisponible'));
  grantCloudConsent('llm', 'openai');
  await expect(flushConsentDecisions()).rejects.toThrow('Moteur indisponible');
  request.mockResolvedValue({ grants: [] });
  await flushConsentDecisions();
  expect(request).toHaveBeenCalledTimes(2);
  const ids = request.mock.calls.map(([, options]) => JSON.parse(options.body).event_id);
  expect(ids[0]).toBe(ids[1]);
});
