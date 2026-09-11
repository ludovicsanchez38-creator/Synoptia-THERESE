/**
 * DA « Application affinée », lot 9 : la coque de l'écran Paramètres.
 *
 * Gardes mécaniques du design `docs/plans/2026-09-11-da-lot9-parametres-design.md`
 * (version 6) : la césure du corps, la nav en grille sous 1024 px, les neuf
 * rubriques et leurs libellés, le titre de niveau 1, le chargement en
 * squelettes, un Réessayer par action et le focus qui survit à la reprise, le
 * lexique des noms accessibles, et la règle « une erreur ne s'annonce qu'une
 * fois ».
 */
import { readFileSync } from 'node:fs';
import { join } from 'node:path';

import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { SettingsModal } from './SettingsModal';
import { usePersonalisationStore } from '../../stores/personalisationStore';

vi.mock('../../services/api', async (importOriginal) => ({
  ...(await importOriginal<typeof import('../../services/api')>()),
  getApiKeysWithCorrupted: vi.fn().mockResolvedValue({ keys: {}, corrupted: [], sources: {} }),
  getLLMConfig: vi.fn().mockResolvedValue({
    provider: 'anthropic',
    model: 'claude-sonnet-4-6',
    available_models: [],
    effort: 'auto',
  }),
  setLLMConfig: vi.fn().mockResolvedValue({}),
  getPreferences: vi.fn().mockResolvedValue({}),
  getStats: vi.fn().mockResolvedValue(null),
  getProfile: vi.fn().mockResolvedValue(null),
  getWorkingDirectory: vi.fn().mockResolvedValue({ path: null, exists: false }),
  getOllamaStatus: vi.fn().mockResolvedValue(null),
  getSystemResources: vi.fn().mockResolvedValue(null),
  hasGroqKey: vi.fn().mockResolvedValue(false),
  getWebSearchStatus: vi.fn().mockResolvedValue({
    enabled: true,
    providers: { gemini: 'indisponible', others: 'indisponible' },
    description: '',
  }),
}));

function source(fichier: string): string {
  return readFileSync(join(process.cwd(), 'src/components/settings', fichier), 'utf8');
}

async function ouvrir(onglet?: string) {
  const rendu = render(<SettingsModal isOpen onClose={vi.fn()} />);
  await waitFor(() => expect(screen.getByTestId('settings-modal')).toBeInTheDocument());
  if (onglet) fireEvent.click(screen.getByTestId(`settings-tab-${onglet}`));
  return rendu;
}

/** Le panneau de la rubrique visible. */
function panneau(): HTMLElement {
  const modale = screen.getByTestId('settings-modal');
  const actif = modale.getAttribute('data-active-tab');
  const element = modale.querySelector(`#settings-panel-${actif}`);
  if (!(element instanceof HTMLElement)) throw new Error('panneau introuvable');
  return element;
}

beforeEach(async () => {
  vi.clearAllMocks();
  // `clearAllMocks` efface les APPELS, pas les implémentations : sans cette
  // remise à zéro, la promesse pendante du test de chargement resterait posée
  // pour tous les suivants.
  const api = await import('../../services/api');
  vi.mocked(api.getApiKeysWithCorrupted).mockResolvedValue({ keys: {}, corrupted: [], sources: {} });
  vi.mocked(api.setLLMConfig).mockResolvedValue(undefined as never);
  usePersonalisationStore.setState({ uxMode: 'contributeur' });
});

describe('lot 9, garde 1 : la coque bascule à 1024 px, plus à 640', () => {
  // Les quatre `className` du lot (corps :784, nav :786, son premier enfant
  // :788, les boutons role="tab" :830) n'ont plus AUCUNE variante `sm:`.
  // Laisser une seule de ces seize fait se croiser les bordures entre 640 et
  // 1023 px, la nav étant alors AU-DESSUS du panneau et non à sa gauche.
  const SM_DU_LOT = [
    'sm:flex-row',
    'sm:block',
    'sm:w-44',
    'sm:overflow-y-auto',
    'sm:border-b-0',
    'sm:border-r',
    'sm:py-2',
    'sm:mb-2',
    'sm:min-w-0',
    'sm:border-b',
    'sm:border-r-0',
    'sm:px-4',
    'sm:py-3',
    'sm:w-full',
    'sm:gap-3',
    'sm:border-r-2',
  ];

  // Les trois bordures de l'onglet, SANS préfixe : aucune des seize ne les
  // touche (revue v5, point 2). Chacune est unique au fichier.
  const BORDURES_DE_L_ONGLET = ['border-b-2', 'border-transparent', 'border-accent-cyan'];

  it('aucune des seize classes `sm:` du lot ne subsiste', () => {
    const src = source('SettingsModal.tsx');
    for (const classe of SM_DU_LOT) {
      expect(src, `classe ${classe} encore présente`).not.toContain(classe);
    }
  });

  it('l’onglet n’a plus de bordure du tout, c’est le fond teinté qui porte l’état', () => {
    const src = source('SettingsModal.tsx');
    for (const classe of BORDURES_DE_L_ONGLET) {
      expect(src, `bordure ${classe} encore présente`).not.toContain(classe);
    }
    expect(src).toContain('bg-accent-tint');
  });

  it('les quatre groupes `sm:` hors périmètre ne sont pas démontés', () => {
    // Cadre, tête, pied, tabpanel : le lot ne les touche pas, et la garde ne
    // doit pas pousser à les démonter.
    const src = source('SettingsModal.tsx');
    expect(src).toContain('sm:max-h-[85vh]');
    expect(src).toContain('sm:px-6');
    expect(src).toContain('sm:py-4');
    expect(src).toContain('sm:p-6');
  });

  it('la césure passe en 1024 px : corps en ligne, nav en grille de trois colonnes', () => {
    const src = source('SettingsModal.tsx');
    expect(src).toContain('min-[1024px]:flex-row');
    expect(src).toContain('max-[1023px]:grid-cols-3');
    expect(src).toContain('min-[1024px]:block');
    expect(src).toContain('min-[1024px]:w-60');
    expect(src).toContain('max-[1023px]:col-span-3');
  });

  it('les neuf rubriques gardent leurs ids et prennent les libellés de la maquette', async () => {
    await ouvrir();

    const attendus: [string, string][] = [
      ['profile', 'Profil'],
      ['ai', 'Service d’IA'],
      ['services', 'Services et connecteurs'],
      ['accessibility', 'Accessibilité et affichage'],
      ['tools', 'Outils'],
      ['agents', 'Agents'],
      ['privacy', 'Sécurité et confidentialité'],
      ['advanced', 'Avancé'],
      ['about', 'À propos et mise à jour'],
    ];

    for (const [id, libelle] of attendus) {
      const onglet = screen.getByTestId(`settings-tab-${id}`);
      expect(onglet, `libellé de ${id}`).toHaveTextContent(libelle);
      expect(onglet).toHaveAttribute('role', 'tab');
    }

    expect(screen.getByTestId('settings-tab-profile')).toHaveAttribute('aria-selected', 'true');
    expect(screen.getByTestId('settings-tab-ai')).toHaveAttribute('aria-selected', 'false');
    expect(screen.getByTestId('ux-mode-toggle')).toBeInTheDocument();
  });

  it('en mode standard, les trois rubriques masquées restent nommées (BUG-159)', async () => {
    usePersonalisationStore.setState({ uxMode: 'standard' });
    await ouvrir();

    expect(screen.getByTestId('settings-hidden-tabs')).toHaveTextContent(
      'Masquées ici : Outils, Agents, Avancé.',
    );
  });
});

describe('lot 9, garde 8 : le titre de la modale est un h1', () => {
  it('h1#settings-title « Paramètres », sans font-editorial', async () => {
    await ouvrir();

    const titre = screen.getByRole('heading', { level: 1, name: 'Paramètres' });
    expect(titre).toHaveAttribute('id', 'settings-title');
    expect(titre.className).not.toMatch(/font-editorial/);
    expect(screen.getByTestId('settings-modal')).toHaveAttribute(
      'aria-labelledby',
      'settings-title',
    );
    // Le filet reste : un nom accessible même si le titre disparaissait.
    expect(screen.getByTestId('settings-modal')).toHaveAttribute('aria-label', 'Paramètres');
  });
});

describe('lot 9, garde 2 : le chargement montre six squelettes, pas un spinner', () => {
  it('six barres en grille de deux colonnes et un role="status" qui dit la lecture', async () => {
    const api = await import('../../services/api');
    vi.mocked(api.getApiKeysWithCorrupted).mockReturnValueOnce(new Promise(() => {}));

    render(<SettingsModal isOpen onClose={vi.fn()} />);
    await waitFor(() => expect(screen.getByTestId('settings-modal')).toBeInTheDocument());

    const statut = screen.getByRole('status');
    expect(statut).toHaveTextContent('Lecture des réglages…');

    const grille = panneau().querySelector('.grid-cols-2');
    expect(grille, 'la grille des squelettes est absente').not.toBeNull();
    expect(grille?.className).toMatch(/gap-2\.5/);
    expect(grille?.querySelectorAll('[aria-hidden="true"]').length).toBe(6);
  });

  it('pendant le chargement, error et operationStatus sont tus', () => {
    // `loadSettings` ne vide pas `error` au début : un refus précédent
    // resterait affiché sous les squelettes.
    const src = source('SettingsModal.tsx');
    expect(src).toMatch(/!loading && operationStatus|operationStatus && !loading/);
  });
});

describe('lot 9, garde 5 : un Réessayer par action, jamais un pour trois', () => {
  it('sans erreur ni lecture en échec, aucun Réessayer sur la rubrique IA', async () => {
    await ouvrir('ai');
    await waitFor(() => expect(document.getElementById('settings-api-key')).not.toBeNull());

    expect(screen.queryByRole('button', { name: /Réessayer/ })).toBeNull();
  });

  it('une lecture en échec donne « Réessayer le chargement », et lui seul', async () => {
    const api = await import('../../services/api');
    vi.mocked(api.getApiKeysWithCorrupted).mockRejectedValueOnce(new Error('lecture refusée'));

    await ouvrir();
    await waitFor(() => expect(screen.getByTestId('settings-load-warning')).toBeInTheDocument());

    expect(screen.getByRole('button', { name: 'Réessayer le chargement' })).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Réessayer' })).toBeNull();
  });

  it('les deux Réessayer coexistent quand les deux états sont vrais', async () => {
    const api = await import('../../services/api');
    vi.mocked(api.getApiKeysWithCorrupted).mockRejectedValueOnce(new Error('lecture refusée'));
    vi.mocked(api.setLLMConfig).mockRejectedValueOnce(new Error('Le service a refusé'));

    await ouvrir('ai');
    await waitFor(() => expect(document.getElementById('settings-api-key')).not.toBeNull());
    fireEvent.click(screen.getByRole('button', { name: /Mistral AI/ }));

    await waitFor(() =>
      expect(screen.getByRole('button', { name: 'Réessayer' })).toBeInTheDocument(),
    );
    // Deux actions distinctes, deux boutons, jamais fusionnés.
    expect(screen.getByRole('button', { name: 'Réessayer le chargement' })).toBeInTheDocument();
  });

  it('le seul « Enregistrer » à testid du profil reste au pied de la modale', async () => {
    await ouvrir();
    await waitFor(() => expect(screen.getAllByTestId('settings-save-btn')).toHaveLength(1));
    expect(screen.getByTestId('settings-save-btn')).toHaveTextContent('Enregistrer');
  });

  it('le bandeau de lecture partielle passe par Alerte, ton attention', async () => {
    const api = await import('../../services/api');
    vi.mocked(api.getApiKeysWithCorrupted).mockRejectedValueOnce(new Error('lecture refusée'));

    await ouvrir();
    const bandeau = await screen.findByTestId('settings-load-warning');

    expect(bandeau).toHaveAttribute('role', 'alert');
    expect(bandeau.className).toContain('bg-[var(--color-warning-tint)]');
    // La forme d'`Alerte`, pas celle du bandeau maison : le titre est un `b`,
    // le corps un `p` sous lui, le geste dans un conteneur `mt-2`.
    expect(bandeau.className).toMatch(/items-start/);
    expect(bandeau.className).toMatch(/gap-3/);
    expect(bandeau.className).toMatch(/px-4/);
    expect(bandeau.className).toMatch(/py-3/);
    expect(bandeau.className).toMatch(/rounded-sm/);
    expect(bandeau.querySelector('b')?.className).toMatch(/text-warning/);
    expect(bandeau).toHaveTextContent('Ce réglage n’a pas pu être lu : clés API.');
    expect(bandeau).toHaveTextContent(
      'Les valeurs affichées ici sont des valeurs par défaut, pas ta configuration réelle.',
    );
  });
});

describe('lot 9, garde 5 bis : le focus survit à la reprise du chargement', () => {
  it('« Réessayer le chargement » ne porte jamais `disabled`, seulement `aria-disabled`', () => {
    // Un `disabled` posé sur l'élément qui a le focus le renvoie au `body` :
    // c'est exactement le défaut qu'on répare.
    const src = source('SettingsModal.tsx');
    expect(src).toMatch(/aria-disabled=\{loading\}/);
    expect(src).toContain('aria-disabled:cursor-wait');
  });

  it('après une reprise réussie, le focus passe au tabpanel et non au body', async () => {
    const api = await import('../../services/api');
    vi.mocked(api.getApiKeysWithCorrupted).mockRejectedValueOnce(new Error('lecture refusée'));

    await ouvrir();
    const bouton = await screen.findByRole('button', { name: 'Réessayer le chargement' });
    bouton.focus();
    expect(document.activeElement).toBe(bouton);

    fireEvent.click(bouton);

    await waitFor(() => expect(screen.queryByTestId('settings-load-warning')).toBeNull());
    expect(document.activeElement).not.toBe(document.body);
    expect(document.activeElement).toBe(
      screen.getByTestId('settings-modal').querySelector('#settings-panel-profile'),
    );
  });

  it('`loadSettings` rend la liste des lectures en échec, après le finally', () => {
    const src = source('SettingsModal.tsx');
    expect(src).toMatch(/async function loadSettings\(\): Promise<string\[\]>/);
    // Le `return` est la DERNIÈRE instruction : un `return` avant le `try`
    // sauterait l'application des données et ouvrirait la modale vide.
    expect(src).toMatch(/finally \{\s*\n\s*setLoading\(false\);\s*\n\s*\}\s*\n\s*return restants;/);
  });
});

describe('lot 9, garde 4 : une erreur ne s’annonce qu’une fois', () => {
  it('un refus d’enregistrement du fournisseur ne donne qu’une alerte, celle de la coque', async () => {
    const api = await import('../../services/api');
    vi.mocked(api.setLLMConfig).mockRejectedValueOnce(new Error('Le service a refusé'));

    await ouvrir('ai');
    await waitFor(() => expect(document.getElementById('settings-api-key')).not.toBeNull());
    await waitFor(() =>
      expect(screen.getByRole('button', { name: /Mistral AI/ })).toBeInTheDocument(),
    );

    fireEvent.click(screen.getByRole('button', { name: /Mistral AI/ }));

    await waitFor(() => expect(screen.getAllByRole('alert').length).toBeGreaterThan(0));
    const alertes = screen.getAllByRole('alert');
    expect(alertes).toHaveLength(1);
    expect(alertes[0]).toHaveTextContent('Le service a refusé');
    // `cleInvalide` est faux : le champ de clé ne se déclare pas invalide.
    expect(document.getElementById('settings-api-key')).not.toHaveAttribute('aria-invalid');
  });
});

describe('lot 9, garde 7 : rien sous 14 px au contact d’un interactif', () => {
  it('aucun bouton `sm` dans les trois fichiers de la rubrique', () => {
    for (const fichier of ['SettingsModal.tsx', 'LLMTab.tsx', 'ProfileTab.tsx']) {
      expect(source(fichier), `${fichier} garde un bouton sm`).not.toContain('size="sm"');
    }
  });

  it('l’aide « Fonctions avancées » est hors du label de l’interrupteur', async () => {
    await ouvrir();

    const interrupteur = screen.getByTestId('ux-mode-toggle');
    const label = interrupteur.closest('label');
    expect(label, 'l’interrupteur n’est plus dans un label').not.toBeNull();
    expect(label).toHaveTextContent('Mode Contributeur');
    expect(label).not.toHaveTextContent('Fonctions avancées');
    expect(screen.getByText('Fonctions avancées').className).toMatch(/text-xs/);
  });

  it('aucun texte en 12 px dans le sous-arbre d’un interactif du panneau', async () => {
    await ouvrir('ai');
    // Attendre la FIN du chargement : sinon le panneau ne contient que
    // l'attente, et la garde serait verte sans avoir rien regardé.
    await waitFor(() => expect(document.getElementById('settings-api-key')).not.toBeNull());

    const fautifs: string[] = [];
    panneau()
      .querySelectorAll('button, a[href], input, select, textarea, [role="switch"]')
      .forEach((interactif) => {
        const cible = [interactif, ...Array.from(interactif.querySelectorAll('*'))];
        for (const noeud of cible) {
          if (noeud.className && String(noeud.className).includes('text-xs')) {
            fautifs.push(`${interactif.tagName.toLowerCase()} > ${noeud.tagName.toLowerCase()}`);
          }
        }
      });

    expect(fautifs, `12 px sous un interactif : ${fautifs.join(', ')}`).toEqual([]);
  });

  it('l’interrupteur du mode contributeur a un curseur centré dans sa piste', () => {
    // Piste 40 x 24 px, curseur 20 px, inset 2 px, course 16 px : 2 + 20 + 16
    // = 38 pour 40, symétrique aux 2 px de départ.
    const src = source('SettingsModal.tsx');
    expect(src).toMatch(/w-10 h-6/);
    expect(src).toMatch(/w-5 h-5/);
    expect(src).toContain('peer-checked:translate-x-4');
    expect(src).not.toMatch(/w-9 h-5/);
  });
});

describe('lot 9, garde 9 : les noms accessibles suivent le lexique', () => {
  // Recopie du tableau INTERDITS de `src/lib/lexique.test.ts:27-37` : ce
  // fichier-là ne lit que des registres exportés, il ne peut pas voir un nom
  // accessible rendu. Ici la garde est un test de RENDU.
  const INTERDITS: [string, RegExp][] = [
    ['sidecar', /\bsidecar\b/i],
    ['Qdrant', /\bqdrant\b/i],
    ['tools (anglais)', /\btools?\b/],
    ['BYOK', /\bBYOK\b/],
    ['LLM', /\bLLMs?\b/],
    ['MCP', /\bMCP\b/],
    ['provider', /\bproviders?\b/i],
  ];

  function nomsAccessibles(): string[] {
    const modale = screen.getByTestId('settings-modal');
    const noms: string[] = [];
    modale.querySelectorAll('[aria-label]').forEach((element) => {
      noms.push(element.getAttribute('aria-label') ?? '');
    });
    modale
      .querySelectorAll('button, [role="group"], [role="tablist"], [role="switch"], h1, h2, h3')
      .forEach((element) => {
        if (!element.hasAttribute('aria-label')) noms.push(element.textContent ?? '');
      });
    noms.push(modale.getAttribute('aria-label') ?? '');
    return noms.filter(Boolean);
  }

  function violations(): string[] {
    return nomsAccessibles().flatMap((nom) =>
      INTERDITS.filter(([, motif]) => motif.test(nom)).map(([terme]) => `${terme} dans « ${nom} »`),
    );
  }

  it('rubrique IA : aucun terme interdit, et le groupe s’appelle « Choix du service d’IA »', async () => {
    await ouvrir('ai');
    await waitFor(() => expect(document.getElementById('settings-api-key')).not.toBeNull());

    expect(
      screen.getByRole('group', { name: 'Choix du service d’IA' }),
    ).toBeInTheDocument();
    expect(violations()).toEqual([]);
  });

  it('rubrique Profil : aucun terme interdit', async () => {
    await ouvrir();
    expect(violations()).toEqual([]);
  });
});
