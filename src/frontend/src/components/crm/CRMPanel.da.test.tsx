/**
 * DA « Application affinée », lot 4 : l'écran Pipeline
 * (`docs/plans/2026-09-11-da-lot4-contacts-design.md`, § 9).
 * Mêmes données, mêmes états, mêmes destinations.
 */
import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { useCRMStore } from '../../stores/crmStore';
import { useContactsStore } from '../../stores/contactsStore';
import { CLASSES_SEGMENTS } from '../ui/segments.classes';
import type { Contact } from '../../services/api';

const api = vi.hoisted(() => ({
  listProjects: vi.fn(),
  listActivities: vi.fn(),
  listContacts: vi.fn(),
}));

vi.mock('../../services/api', async () => {
  const reel = await vi.importActual<typeof import('../../services/api')>('../../services/api');
  return {
    ...reel,
    listProjects: (...a: unknown[]) => api.listProjects(...a),
    listActivities: (...a: unknown[]) => api.listActivities(...a),
  };
});

vi.mock('../../services/api/memory', async () => {
  const reel = await vi.importActual<typeof import('../../services/api/memory')>(
    '../../services/api/memory',
  );
  return { ...reel, listContacts: (...a: unknown[]) => api.listContacts(...a) };
});

vi.mock('../../services/api/prestations', async () => {
  const reel = await vi.importActual<typeof import('../../services/api/prestations')>(
    '../../services/api/prestations',
  );
  return { ...reel, listerLesPrestations: vi.fn().mockResolvedValue([]) };
});

import { CRMPanel } from './CRMPanel';

const marie = {
  id: 'ct-1',
  first_name: 'Marie',
  last_name: 'Lefevre',
  company: 'Lefevre Conseil',
  email: null,
  phone: null,
  notes: null,
  tags: null,
  scope: 'global',
  stage: 'contact',
  score: 50,
  source: 'site-web',
  created_at: '2026-08-01T00:00:00Z',
  updated_at: '2026-08-01T00:00:00Z',
} as unknown as Contact;

const COULEUR_EN_DUR =
  /#[0-9A-Fa-f]{3,8}\b|(?<![A-Za-z])rgba?\(|(?<![A-Za-z])hsla?\(|\bcolor-mix\(|\bbg-black\b/;

function classesDUnNoeud(n: Element): string {
  const brut = (n as HTMLElement).className;
  if (typeof brut === 'string') return brut;
  const svg = (n as SVGElement).className;
  return typeof svg === 'object' && svg && 'baseVal' in svg ? svg.baseVal : '';
}

function couleursEnDurSous(racine: HTMLElement): string[] {
  const fautifs: string[] = [];
  const visiter = (n: Element) => {
    const classes = classesDUnNoeud(n);
    if (COULEUR_EN_DUR.test(classes)) fautifs.push(classes.slice(0, 80));
    const style = (n as HTMLElement).getAttribute?.('style') ?? '';
    if (COULEUR_EN_DUR.test(style)) fautifs.push(style.slice(0, 80));
    for (const enfant of Array.from(n.children)) visiter(enfant);
  };
  visiter(racine);
  return fautifs;
}

function interactifsSousLePlancher(racine: HTMLElement): string[] {
  const fautifs: string[] = [];
  for (const el of racine.querySelectorAll(
    'button, input, select, textarea, a, [role="button"], [role="tab"]',
  )) {
    const noeuds = [el, ...Array.from(el.querySelectorAll('*'))];
    for (const n of noeuds) {
      if (/\btext-xs\b/.test(classesDUnNoeud(n))) {
        fautifs.push(((el as HTMLElement).textContent ?? el.tagName).trim().slice(0, 48));
        break;
      }
    }
  }
  return fautifs;
}

function poser(
  extra: {
    activeTab?: 'pipeline' | 'activities';
    contacts?: Contact[];
    selectedContactId?: string | null;
    truncated?: boolean;
  } = {},
) {
  useCRMStore.setState({ projects: [], activeTab: extra.activeTab ?? 'pipeline' });
  useContactsStore.setState({
    contacts: extra.contacts ?? [],
    searchResults: null,
    loading: false,
    loaded: true,
    error: null,
    selectedContactId: extra.selectedContactId ?? null,
    truncated: extra.truncated ?? false,
  });
}

beforeEach(() => {
  vi.clearAllMocks();
  api.listProjects.mockResolvedValue([]);
  api.listActivities.mockResolvedValue([]);
  api.listContacts.mockResolvedValue([]);
  poser();
});

describe('Lot 4 DA : bandeau Pipeline / Activités', () => {
  it('le tablist consomme CLASSES_SEGMENTS et le source n’a plus de layoutId', async () => {
    render(<CRMPanel standalone />);
    const bandeau = await screen.findByRole('tablist');
    for (const jeton of CLASSES_SEGMENTS.split(/\s+/)) {
      expect(bandeau.className, jeton).toMatch(new RegExp(`\\b${jeton.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}\\b`));
    }
    const source = readFileSync(join(__dirname, 'CRMPanel.tsx'), 'utf8');
    expect(source).not.toMatch(/layoutId/);
  });
});

describe('Lot 4 DA : un seul Réessayer, aux états qui en ont déjà un', () => {
  it('la panne du fil d’activités a un seul Réessayer', async () => {
    api.listActivities.mockRejectedValue(new Error('boom'));
    poser({ activeTab: 'activities' });
    render(<CRMPanel standalone />);
    expect(await screen.findByTestId('crm-activites-erreur')).toHaveTextContent(
      /n’ont pas pu être lues/,
    );
    expect(screen.getAllByRole('button', { name: 'Réessayer' })).toHaveLength(1);
  });

  it('l’erreur de chargement CRM n’a pas de Réessayer', async () => {
    api.listProjects.mockRejectedValue(new Error('Le serveur ne répond pas'));
    poser({ contacts: [marie] });
    api.listContacts.mockResolvedValue([marie]);
    render(<CRMPanel standalone />);
    expect(await screen.findByTestId('crm-erreur')).toHaveTextContent(/Le serveur ne répond pas/);
    expect(screen.queryByRole('button', { name: 'Réessayer' })).toBeNull();
  });

  it('le fil vide n’a pas de Réessayer', async () => {
    poser({ activeTab: 'activities' });
    render(<CRMPanel standalone />);
    expect(await screen.findByTestId('crm-activites-vide')).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Réessayer' })).toBeNull();
  });
});

describe('Lot 4 DA : Nouveau contact', () => {
  it('ouvre la même modale que « Ajouter un contact »', async () => {
    render(<CRMPanel standalone />);
    const nouveau = await screen.findByRole('button', { name: /Nouveau contact/i });
    expect(nouveau.className).toMatch(/\bgap-2\b/);
    expect(screen.getByRole('button', { name: /Importer \(\.vcf\)/ }).className).toMatch(/\bgap-2\b/);
    fireEvent.click(nouveau);
    expect(await screen.findByRole('dialog', { name: 'Nouveau contact CRM' })).toBeInTheDocument();
  });
});

describe('Lot 4 DA : plancher et jetons', () => {
  const activite = {
    id: 'a1',
    contact_id: 'ct-1',
    type: 'note' as const,
    title: 'Appel de suivi',
    description: 'Point commercial',
    extra_data: null,
    created_at: '2026-08-01T00:00:00Z',
  };

  async function verifierPlancher(attendre: () => void) {
    const { unmount } = render(<CRMPanel standalone />);
    await waitFor(attendre);
    const panneau = screen.getByTestId('crm-panel');
    expect(interactifsSousLePlancher(panneau)).toEqual([]);
    expect(couleursEnDurSous(panneau)).toEqual([]);
    unmount();
  }

  it('aucun interactif n’est en text-xs, aucune couleur en dur dans le standalone', async () => {
    poser({ contacts: [marie] });
    api.listContacts.mockResolvedValue([marie]);
    await verifierPlancher(() => expect(screen.getByText('Marie Lefevre')).toBeInTheDocument());

    api.listContacts.mockResolvedValue([]);
    poser();
    await verifierPlancher(() =>
      expect(screen.getAllByRole('heading', { level: 3 })).toHaveLength(7),
    );

    api.listActivities.mockResolvedValue([]);
    poser({ activeTab: 'activities' });
    await verifierPlancher(() => expect(screen.getByTestId('crm-activites-vide')).toBeInTheDocument());

    api.listActivities.mockRejectedValue(new Error('boom'));
    poser({ activeTab: 'activities' });
    await verifierPlancher(() =>
      expect(screen.getByTestId('crm-activites-erreur')).toBeInTheDocument(),
    );

    api.listProjects.mockRejectedValue(new Error('Le serveur ne répond pas'));
    api.listContacts.mockResolvedValue([marie]);
    poser({ contacts: [marie] });
    await verifierPlancher(() => expect(screen.getByTestId('crm-erreur')).toBeInTheDocument());
    api.listProjects.mockResolvedValue([]);

    api.listActivities.mockResolvedValue([activite]);
    api.listContacts.mockResolvedValue([marie]);
    poser({ activeTab: 'activities', contacts: [marie], selectedContactId: 'ct-1' });
    await verifierPlancher(() =>
      expect(screen.getByRole('button', { name: 'Ajouter une activité' })).toBeInTheDocument(),
    );
  });
});
