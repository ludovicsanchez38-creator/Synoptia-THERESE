/**
 * DA « Application affinée », lot 9 : la rubrique Service d'IA.
 *
 * Gardes mécaniques du design (version 6) : la grille des quatorze
 * fournisseurs en boutons `aria-pressed` sans roving, les étiquettes d'état,
 * le pluriel d'Ollama, la carte unique du service (clé ou statut, puis modèle
 * et effort), et l'`aria-invalid` qui ne survit pas à son alerte.
 */
import { fireEvent, render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { LLMTab, PROVIDERS } from './LLMTab';
import type { OllamaStatus } from '../../services/api';

vi.mock('../../services/api', async (importOriginal) => ({
  ...(await importOriginal<typeof import('../../services/api')>()),
  getLLMConfig: vi.fn().mockResolvedValue({ provider: 'openai', model: 'gpt-5.6-luna', effort: 'auto' }),
  setLLMConfig: vi.fn().mockResolvedValue(undefined),
}));

const GIB = 1024 ** 3;

function statutOllama(partiel: Partial<OllamaStatus> = {}): OllamaStatus {
  return {
    available: true,
    base_url: 'http://127.0.0.1:11434',
    models: [],
    error: null,
    ...partiel,
  } as OllamaStatus;
}

type Props = Partial<React.ComponentProps<typeof LLMTab>>;

function rendre(props: Props = {}) {
  return render(
    <LLMTab
      selectedProvider="anthropic"
      selectedModel="claude-sonnet-4-6"
      apiKeys={{}}
      corruptedKeys={[]}
      apiKeyInput=""
      setApiKeyInput={vi.fn()}
      showApiKey={false}
      setShowApiKey={vi.fn()}
      ollamaStatus={null}
      ollamaModels={[]}
      systemResources={null}
      saving={false}
      saved={false}
      error={null}
      setError={vi.fn()}
      onSelectProvider={vi.fn()}
      onSelectModel={vi.fn()}
      onSaveApiKey={vi.fn()}
      {...props}
    />,
  );
}

/** La carte d'un fournisseur, par son nom de catalogue. */
function carte(nom: string | RegExp): HTMLElement {
  return screen.getByRole('button', { name: nom });
}

beforeEach(() => {
  vi.clearAllMocks();
});

describe('lot 9, garde 2 : la grille des fournisseurs', () => {
  it('quatorze boutons `aria-pressed`, aucun radio, aucun radiogroup', () => {
    rendre();

    const groupe = screen.getByRole('group', { name: 'Choix du service d’IA' });
    const cartes = groupe.querySelectorAll('button[aria-pressed]');
    expect(cartes).toHaveLength(PROVIDERS.length);
    expect(screen.queryAllByRole('radio')).toHaveLength(0);
    expect(document.querySelector('[role="radiogroup"]')).toBeNull();

    // `setLLMConfig` est un POST : la flèche ne doit pas l'appeler, donc le
    // motif APG radio n'est pas tenable ici (décision 3 du design).
    expect(carte(/Anthropic/)).toHaveAttribute('aria-pressed', 'true');
    expect(carte(/GPT \(OpenAI\)/)).toHaveAttribute('aria-pressed', 'false');
  });

  it('deux colonnes à toutes les largeurs, sans aucune classe de césure', () => {
    rendre();

    const groupe = screen.getByRole('group', { name: 'Choix du service d’IA' });
    expect(groupe.className).toMatch(/grid-cols-2/);
    expect(groupe.className).not.toMatch(/min-\[840px\]:/);
    expect(groupe.className).not.toMatch(/\bmd:/);
    expect(groupe.className).not.toMatch(/\blg:/);
  });

  it('un fournisseur muni d’une clé reste visible et le dit, même hors sélection (P-018)', () => {
    rendre({ apiKeys: { openai: true } });

    const openai = carte(/GPT \(OpenAI\)/);
    expect(openai).toHaveAttribute('aria-pressed', 'false');
    expect(openai).toHaveTextContent('Clé enregistrée');
  });

  it('le fournisseur courant sans clé porte « Actif » ET « Sans clé »', () => {
    rendre({ selectedProvider: 'anthropic', apiKeys: {} });

    const anthropic = carte(/Anthropic/);
    expect(anthropic).toHaveTextContent('Actif');
    expect(anthropic).toHaveTextContent('Sans clé');
    expect(anthropic).toHaveTextContent('Recommandé');
  });

  it('une clé corrompue prend la place de l’état de clé', () => {
    rendre({ apiKeys: { openai: true }, corruptedKeys: ['openai'] });

    const openai = carte(/GPT \(OpenAI\)/);
    expect(openai).toHaveTextContent('Clé corrompue');
    expect(openai).not.toHaveTextContent('Clé enregistrée');
  });

  it('les étiquettes d’une carte ont un parent commun calé à droite', () => {
    // Anthropic courant et muni d'une clé en porte trois. Posées en enfants
    // directs de la grille `grid-cols-[1fr_auto]`, la deuxième et la
    // troisième retomberaient en colonne 1 d'une nouvelle rangée.
    rendre({ selectedProvider: 'anthropic', apiKeys: { anthropic: true } });

    const anthropic = carte(/Anthropic/);
    const pilules = Array.from(anthropic.querySelectorAll('[data-etiquette]'));
    expect(pilules).toHaveLength(3);

    const parents = new Set(pilules.map((pilule) => pilule.parentElement));
    expect(parents.size).toBe(1);
    const parent = pilules[0].parentElement;
    expect(parent).not.toBe(anthropic);
    expect(parent?.className).toMatch(/justify-self-end/);
  });
});

describe('lot 9, garde 2 bis : le clavier de la grille', () => {
  it('aucune carte ne porte de `tabIndex`', () => {
    rendre();

    screen
      .getByRole('group', { name: 'Choix du service d’IA' })
      .querySelectorAll('button')
      .forEach((bouton) => {
        expect(bouton.hasAttribute('tabindex'), `${bouton.textContent} porte un tabindex`).toBe(false);
      });
  });

  it('les flèches, Home et End n’enregistrent rien et ne déplacent pas le focus', () => {
    const onSelectProvider = vi.fn();
    rendre({ onSelectProvider });

    const anthropic = carte(/Anthropic/);
    anthropic.focus();
    for (const key of ['ArrowDown', 'ArrowRight', 'ArrowUp', 'Home', 'End']) {
      fireEvent.keyDown(anthropic, { key });
    }

    expect(onSelectProvider).not.toHaveBeenCalled();
    expect(document.activeElement).toBe(anthropic);
  });

  it('Ollama courant et indisponible : sa carte est désactivée, les treize autres restent au clavier', () => {
    rendre({
      selectedProvider: 'ollama',
      selectedModel: '',
      ollamaStatus: statutOllama({ available: false, error: 'Service local injoignable' }),
    });

    const groupe = screen.getByRole('group', { name: 'Choix du service d’IA' });
    const cartes = Array.from(groupe.querySelectorAll('button'));
    const ollama = cartes.find((c) => /Ollama/.test(c.textContent ?? ''));
    expect(ollama).toBeDefined();
    expect(ollama).toBeDisabled();

    const autres = cartes.filter((c) => c !== ollama);
    expect(autres).toHaveLength(PROVIDERS.length - 1);
    for (const c of autres) {
      expect(c).not.toBeDisabled();
      expect(c.getAttribute('tabindex')).toBeNull();
    }
  });
});

describe('lot 9, garde 3 : ce que dit la carte Ollama', () => {
  function rendreOllama(models: { name: string; gere_les_outils?: boolean }[], selectedModel = '') {
    rendre({
      selectedProvider: 'ollama',
      selectedModel,
      ollamaModels: models.map((m) => m.name),
      ollamaStatus: statutOllama({
        models: models.map((m) => ({
          name: m.name,
          size: 4 * GIB,
          modified_at: null,
          digest: null,
          ...(m.gere_les_outils === undefined ? {} : { gere_les_outils: m.gere_les_outils }),
        })),
      }) as OllamaStatus,
    });
  }

  it('service injoignable : « Service local injoignable »', () => {
    rendre({
      selectedProvider: 'ollama',
      selectedModel: '',
      ollamaStatus: statutOllama({ available: false }),
    });

    const cartes = Array.from(document.querySelectorAll('button[aria-pressed]'));
    const ollama = cartes.find((c) => /Ollama/.test(c.textContent ?? ''));
    expect(ollama).toHaveTextContent('Service local injoignable');
    expect(ollama).not.toHaveTextContent('Aucune clé API requise');
  });

  it('aucun modèle installé', () => {
    rendreOllama([]);
    const ollama = carte(/Ollama/);
    expect(ollama).toHaveTextContent('Aucun modèle installé');
  });

  it('un seul modèle : le singulier, et le modèle courant devant', () => {
    rendreOllama([{ name: 'gemma4-tia' }], 'gemma4-tia');
    const ollama = carte(/Ollama/);
    expect(ollama).toHaveTextContent('gemma4-tia · 1 modèle installé');
  });

  it('deux modèles : le pluriel', () => {
    rendreOllama([{ name: 'gemma4-tia' }, { name: 'qwen:8b' }], 'gemma4-tia');
    const ollama = carte(/Ollama/);
    expect(ollama).toHaveTextContent('gemma4-tia · 2 modèles installés');
  });

  it('« · outils pris en charge » seulement quand la fiche du modèle le dit', () => {
    rendreOllama([{ name: 'gemma4-tia', gere_les_outils: true }], 'gemma4-tia');
    expect(carte(/Ollama/)).toHaveTextContent('· outils pris en charge');
  });

  it('la mention est absente si la fiche ne le dit pas', () => {
    rendreOllama([{ name: 'gemma4-tia' }], 'gemma4-tia');
    expect(carte(/Ollama/)).not.toHaveTextContent('outils pris en charge');
  });

  it('hors Ollama, la mention n’apparaît jamais', () => {
    rendre({ apiKeys: { anthropic: true } });
    expect(document.body.textContent).not.toContain('outils pris en charge');
  });
});

describe('lot 9, garde 4 : la clé du service', () => {
  it('« Enregistrer » sans clé, « Remplacer » avec', () => {
    const { unmount } = rendre({ selectedProvider: 'openai', apiKeys: {}, apiKeyInput: 'sk-x' });
    expect(screen.getByRole('button', { name: 'Enregistrer' })).toBeInTheDocument();
    unmount();

    rendre({ selectedProvider: 'openai', apiKeys: { openai: true }, apiKeyInput: 'sk-x' });
    expect(screen.getByRole('button', { name: 'Remplacer' })).toBeInTheDocument();
  });

  it('`aria-invalid` seulement quand le refus de clé est à l’écran', () => {
    const REFUS = 'La clé API doit commencer par "sk-"';
    const { unmount } = rendre({
      selectedProvider: 'openai',
      error: REFUS,
      cleInvalide: true,
    });
    expect(document.getElementById('settings-api-key')).toHaveAttribute('aria-invalid', 'true');
    expect(screen.getByRole('alert')).toHaveTextContent(REFUS);
    unmount();

    // Un `error` venu de `setLLMConfig` n'est pas un refus de clé : ni
    // `aria-invalid`, ni alerte dans la rubrique (la coque la rend, une fois).
    rendre({ selectedProvider: 'openai', error: 'Le fournisseur IA n’a pas pu être enregistré.' });
    expect(document.getElementById('settings-api-key')).not.toHaveAttribute('aria-invalid');
    expect(screen.queryByRole('alert')).toBeNull();
  });

  it('le refus n’a pas de bouton de reprise (B-201)', () => {
    rendre({
      selectedProvider: 'openai',
      error: 'La clé API doit commencer par "sk-"',
      cleInvalide: true,
    });

    const alerte = screen.getByRole('alert');
    expect(alerte.querySelector('button')).toBeNull();
  });

  it('la clé corrompue garde ses mots et sa couleur, sans rôle', () => {
    rendre({ selectedProvider: 'openai', apiKeys: { openai: true }, corruptedKeys: ['openai'] });

    const consigne = screen.getByText('Clé API corrompue - ressaisis-la');
    expect(consigne.className).toMatch(/text-error/);
    expect(consigne.className).toMatch(/text-sm/);
    expect(consigne.closest('[role]')).toBeNull();
  });

  it('Qwen : le bouton d’adresse ne s’appelle pas « Enregistrer »', async () => {
    rendre({ selectedProvider: 'qwen', selectedModel: 'qwen3.8-max', apiKeys: {}, apiKeyInput: 'sk-x' });

    expect(await screen.findByRole('button', { name: 'Enregistrer l’adresse' })).toBeInTheDocument();
    expect(screen.getAllByRole('button', { name: 'Enregistrer' })).toHaveLength(1);
  });
});

describe('lot 9, garde 5 : « Réessayer l’effort » porte son propre nom', () => {
  it('un enregistrement d’effort refusé donne un bouton nommé, distinct des autres reprises', async () => {
    const api = await import('../../services/api');
    vi.mocked(api.setLLMConfig).mockRejectedValueOnce(new Error('L’effort n’a pas pu être enregistré.'));

    rendre({ selectedProvider: 'openai', selectedModel: 'gpt-5.6-luna', apiKeys: { openai: true } });

    const select = await screen.findByLabelText('Effort de raisonnement');
    fireEvent.change(select, { target: { value: 'high' } });

    expect(await screen.findByRole('button', { name: 'Réessayer l’effort' })).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Réessayer' })).toBeNull();
  });

  // Revue du diff, point 4 : l'`Alerte` et son geste étaient conditionnés à
  // `error`, alors que `failedEffort` seul dit qu'il y a quelque chose à
  // rejouer. La lecture de l'effort qui échoue AU MONTAGE pose `error` sans
  // `failedEffort` : le bouton s'affichait et ne faisait rien
  // (`onClick={() => failedEffort && …}`). L'annonce reste, le geste inerte part.
  it('une lecture d’effort en échec annonce, sans bouton de reprise inerte', async () => {
    const api = await import('../../services/api');
    vi.mocked(api.getLLMConfig).mockRejectedValueOnce(
      new Error('Effort de raisonnement indisponible.'),
    );

    rendre({ selectedProvider: 'openai', selectedModel: 'gpt-5.6-luna', apiKeys: { openai: true } });

    expect(await screen.findByRole('alert')).toHaveTextContent(
      'Effort de raisonnement indisponible.',
    );
    expect(
      screen.queryByRole('button', { name: 'Réessayer l’effort' }),
      'un bouton de reprise sans effort à rejouer',
    ).toBeNull();
  });

  it('sans échec d’effort, aucun bouton de reprise', async () => {
    rendre({ selectedProvider: 'openai', selectedModel: 'gpt-5.6-luna', apiKeys: { openai: true } });
    await screen.findByLabelText('Effort de raisonnement');

    expect(screen.queryByRole('button', { name: /Réessayer/ })).toBeNull();
  });

  it('l’aide de l’effort est décrite au Select, avec la mention quand elle est là', async () => {
    rendre({ selectedProvider: 'openai', selectedModel: 'gpt-5.6-luna', apiKeys: { openai: true } });

    const select = await screen.findByLabelText('Effort de raisonnement');
    // Deux valeurs, jamais `undefined` : l'aide d'abord, la mention ensuite.
    expect(select).toHaveAttribute('aria-describedby', 'llm-effort-aide llm-effort-outils');
    expect(document.getElementById('llm-effort-aide')?.className).toMatch(/text-sm/);
    expect(screen.getByTestId('effort-mention-outils').className).toMatch(/text-sm/);
    expect(screen.getByTestId('effort-mention-outils').className).not.toMatch(/text-xs/);
  });
});

describe('lot 9, garde 4 bis : une seule carte de service', () => {
  it('OpenAI avec clé : un seul h3, au nom du fournisseur, qui contient clé, modèle et effort', async () => {
    rendre({ selectedProvider: 'openai', selectedModel: 'gpt-5.6-luna', apiKeys: { openai: true } });

    const titres = screen.getAllByRole('heading', { level: 3 });
    expect(titres).toHaveLength(1);
    expect(titres[0]).toHaveTextContent('GPT (OpenAI)');
    expect(titres[0].textContent).not.toMatch(/Clé API/);

    const carteService = titres[0].closest('section, article');
    expect(carteService).not.toBeNull();
    expect(carteService?.querySelector('#settings-api-key')).not.toBeNull();
    expect(carteService?.querySelector('#settings-llm-model')).not.toBeNull();
    expect(await screen.findByLabelText('Effort de raisonnement')).toBeInTheDocument();
    expect(carteService?.querySelector('#llm-effort')).not.toBeNull();
  });

  it('Ollama disponible : le titre du catalogue, le statut dans la carte, pas de champ de clé', () => {
    rendre({
      selectedProvider: 'ollama',
      selectedModel: 'gemma4-tia',
      ollamaModels: ['gemma4-tia'],
      ollamaStatus: statutOllama({
        models: [{ name: 'gemma4-tia', size: 4 * GIB, modified_at: null, digest: null }],
      }),
      onRetestOllama: vi.fn(),
    });

    const titre = screen.getByRole('heading', { level: 3, name: 'Ollama (Local)' });
    const carteService = titre.closest('section, article');
    expect(document.getElementById('settings-api-key')).toBeNull();
    expect(carteService?.querySelector('[role="status"]')).not.toBeNull();
    expect(carteService).toHaveTextContent('Ollama connecté (http://127.0.0.1:11434)');
    expect(screen.getByRole('button', { name: 'Re-tester la connexion Ollama' })).toBeInTheDocument();
  });

  it('Ollama indisponible : le statut dit quoi faire, et ce n’est pas une alerte', () => {
    rendre({
      selectedProvider: 'ollama',
      selectedModel: '',
      ollamaStatus: statutOllama({ available: false, error: 'Ollama ne répond pas' }),
      onRetestOllama: vi.fn(),
    });

    const statut = screen.getByRole('status');
    expect(statut).toHaveTextContent('Ollama ne répond pas');
    expect(statut).toHaveTextContent('Démarrez Ollama pour utiliser des modèles locaux.');
    expect(statut.className).toMatch(/text-warning/);
    expect(screen.queryByRole('alert')).toBeNull();
  });

  it('sans `onRetestOllama`, le bouton Re-tester n’existe pas', () => {
    rendre({
      selectedProvider: 'ollama',
      selectedModel: '',
      ollamaStatus: statutOllama({ available: false }),
    });

    expect(screen.queryByRole('button', { name: 'Re-tester la connexion Ollama' })).toBeNull();
  });

  it('fournisseur inconnu du catalogue : la carte et la clé restent, les deux Select partent', () => {
    rendre({
      selectedProvider: 'venu-du-serveur' as never,
      selectedModel: '',
      apiKeys: {},
    });

    const titre = screen.getByRole('heading', { level: 3 });
    expect(titre).toHaveTextContent('venu-du-serveur');
    expect(document.getElementById('settings-api-key')).not.toBeNull();
    expect(document.getElementById('settings-llm-model')).toBeNull();
    expect(document.getElementById('llm-effort')).toBeNull();
  });

  it('modèle hors catalogue : l’option « (personnalisé) » existe et le select la porte (BUG-084)', () => {
    rendre({
      selectedProvider: 'openai',
      selectedModel: 'gpt-maison-42',
      apiKeys: { openai: true },
    });

    const select = document.getElementById('settings-llm-model') as HTMLSelectElement;
    expect(select).not.toBeNull();
    const option = Array.from(select.options).find((o) => o.value === 'gpt-maison-42');
    expect(option, 'l’option du modèle enregistré a disparu').toBeDefined();
    expect(option?.textContent).toContain('gpt-maison-42 (personnalisé)');
    expect(select.value).toBe('gpt-maison-42');
    expect(screen.getByText(/Modèle personnalisé actif : gpt-maison-42/)).toBeInTheDocument();
  });

  it('Ollama sans modèle installé et sans modèle choisi : le select est nommé et inerte', () => {
    rendre({
      selectedProvider: 'ollama',
      selectedModel: '',
      ollamaModels: [],
      ollamaStatus: statutOllama({ models: [] }),
    });

    const select = document.getElementById('settings-llm-model') as HTMLSelectElement;
    expect(select).not.toBeNull();
    expect(select.options).toHaveLength(1);
    expect(select.options[0].textContent).toContain('Aucun modèle installé');
    expect(select.options[0].disabled).toBe(true);
  });
});
