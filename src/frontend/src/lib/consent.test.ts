/**
 * Revue 0.40 : le consentement cloud ne stockait qu'UN fournisseur - consentir
 * aux images écrasait le consentement LLM, et la dictée (qui exige Groq)
 * devenait indéblocable. V2 : un consentement par finalité ET fournisseur.
 */
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import {
  CLOUD_CONSENT_KEY,
  grantCloudConsent,
  hasCloudConsent,
  revokeCloudConsent,
  listCloudConsents,
} from './consent';

// Le setup global mocke localStorage avec des vi.fn() non persistants ; on
// installe ici un localStorage à mémoire réelle pour tester écriture + relecture.
describe('consentement cloud v2 - par finalité et fournisseur (US-003 RGPD-4)', () => {
  beforeEach(() => {
    const store: Record<string, string> = {};
    vi.stubGlobal('localStorage', {
      getItem: (k: string) => store[k] ?? null,
      setItem: (k: string, v: string) => {
        store[k] = v;
      },
      removeItem: (k: string) => {
        delete store[k];
      },
      clear: () => {
        for (const k of Object.keys(store)) delete store[k];
      },
    });
  });

  afterEach(() => vi.unstubAllGlobals());

  it('accorde et vérifie un consentement par finalité et fournisseur', () => {
    expect(hasCloudConsent('voice', 'Groq')).toBe(false);
    grantCloudConsent('voice', 'Groq', ['audio de la dictée']);
    expect(hasCloudConsent('voice', 'Groq')).toBe(true);
    expect(hasCloudConsent('voice', 'OpenAI')).toBe(false);
    expect(hasCloudConsent('llm', 'Groq')).toBe(false);
  });

  it('est insensible à la casse du fournisseur', () => {
    grantCloudConsent('llm', 'OpenAI');
    expect(hasCloudConsent('llm', 'openai')).toBe(true);
    expect(hasCloudConsent('llm', 'OPENAI')).toBe(true);
  });

  it('sans fournisseur précisé, vérifie la finalité seule', () => {
    expect(hasCloudConsent('llm')).toBe(false);
    grantCloudConsent('llm', 'anthropic');
    expect(hasCloudConsent('llm')).toBe(true);
    expect(hasCloudConsent('images')).toBe(false);
  });

  it('deux finalités coexistent : les images n’écrasent plus le LLM (bug 0.40)', () => {
    grantCloudConsent('llm', 'openai');
    grantCloudConsent('images', 'openai');
    grantCloudConsent('voice', 'groq');
    expect(hasCloudConsent('llm', 'openai')).toBe(true);
    expect(hasCloudConsent('images', 'openai')).toBe(true);
    expect(hasCloudConsent('voice', 'groq')).toBe(true);
  });

  it('révoque un consentement sans toucher les autres', () => {
    grantCloudConsent('llm', 'openai');
    grantCloudConsent('voice', 'groq');
    revokeCloudConsent('voice', 'groq');
    expect(hasCloudConsent('voice', 'groq')).toBe(false);
    expect(hasCloudConsent('llm', 'openai')).toBe(true);
  });

  it('liste les consentements accordés avec horodatage', () => {
    grantCloudConsent('llm', 'openai', ['messages']);
    grantCloudConsent('voice', 'groq', ['audio']);
    const grants = listCloudConsents();
    expect(grants).toHaveLength(2);
    const voice = grants.find((g) => g.purpose === 'voice');
    expect(voice?.provider).toBe('groq');
    expect(voice?.dataCategories).toEqual(['audio']);
    expect(voice?.timestamp).toBeTruthy();
  });

  it('migre un enregistrement v1 accepté vers un consentement LLM seul', () => {
    localStorage.setItem(
      CLOUD_CONSENT_KEY,
      JSON.stringify({
        accepted: true,
        version: '1',
        timestamp: '2026-07-01T10:00:00.000Z',
        provider: 'OpenAI',
        dataCategories: ['messages'],
      }),
    );
    expect(hasCloudConsent('llm', 'OpenAI')).toBe(true);
    expect(hasCloudConsent('llm')).toBe(true);
    // Le consentement v1 ne valait PAS pour la voix ni les images.
    expect(hasCloudConsent('voice', 'Groq')).toBe(false);
    expect(hasCloudConsent('images')).toBe(false);
  });

  it('un enregistrement v1 refusé ne migre rien', () => {
    localStorage.setItem(
      CLOUD_CONSENT_KEY,
      JSON.stringify({ accepted: false, version: '1', timestamp: '2026-07-01T10:00:00.000Z' }),
    );
    expect(hasCloudConsent('llm')).toBe(false);
    expect(listCloudConsents()).toHaveLength(0);
  });

  it('survit à un localStorage corrompu', () => {
    localStorage.setItem(CLOUD_CONSENT_KEY, '{pas du json');
    expect(hasCloudConsent('llm')).toBe(false);
    grantCloudConsent('llm', 'openai');
    expect(hasCloudConsent('llm', 'openai')).toBe(true);
  });
});
