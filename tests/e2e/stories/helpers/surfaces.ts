import type { APIRequestContext, Page } from '@playwright/test';

import { BACKEND_URL } from './backend';

/**
 * Ouvrir une surface sans dépendre du chemin qui y mène.
 *
 * 01/09/2026. Les parcours pressaient `Control+m`, `Control+k`… et cherchaient
 * `settings-btn`, `memory-panel`, `crm-panel`, `sidebar`. Ces identifiants
 * existent tous dans le code, mais la coque conversationnelle ne monte plus ni
 * l'en-tête de chat ni la barre latérale : ce sont un tiroir et une modale, sur
 * demande. Soixante-cinq parcours attendaient donc une interface disparue.
 *
 * Deux corrections valaient d'être faites, et une seule est honnête : le
 * raccourci lui-même mérite son test — un seul, dédié, dans
 * `parcours-06-navigation` — tandis que les parcours qui vérifient le CONTENU
 * d'une surface n'ont pas à rejouer le chemin d'accès à chaque fois. Ils
 * passent par le registre d'actions que l'application expose déjà, celui-là
 * même que sert la palette de commandes.
 *
 * Le registre est la source unique : si une action disparaît, tous les
 * parcours qui l'utilisent échouent d'un coup, ce qui est le comportement
 * voulu.
 */

/** Les actions du registre utilisées par les parcours. */
export type ActionDeSurface =
  | 'home.open'
  | 'memory.open'
  | 'crm.open'
  | 'email.open'
  | 'calendar.open'
  | 'tasks.open'
  | 'invoices.open'
  | 'projects.open'
  | 'files.open'
  | 'documents.open'
  | 'board.open'
  | 'actions.open'
  | 'settings.open'
  | 'shortcuts.open'
  | 'prompt-library.open'
  | 'guided.open'
  | 'conversations.toggle'
  | 'chat.new'
  | 'contact.new'
  | 'project.new';

type FenetreTherese = Window & {
  __therese?: {
    runAction: (id: string) => void;
    getActions: () => Array<{ id: string }>;
  };
};

/** Attendre que la coque ait publié son registre d'actions. */
export async function attendreLeRegistre(page: Page): Promise<void> {
  await page.waitForFunction(
    () => Boolean((window as unknown as FenetreTherese).__therese?.runAction),
    undefined,
    { timeout: 15000 },
  );
}

/**
 * Ouvrir une surface par son action de registre.
 *
 * Lève si l'action n'existe pas : un parcours qui viserait une action retirée
 * doit échouer bruyamment, pas attendre en silence un élément qui ne viendra
 * jamais.
 */
export async function ouvrirLaSurface(page: Page, action: ActionDeSurface): Promise<void> {
  await attendreLeRegistre(page);
  const connue = await page.evaluate((id) => {
    const t = (window as unknown as FenetreTherese).__therese;
    return (t?.getActions() ?? []).some((a) => a.id === id);
  }, action);
  if (!connue) {
    throw new Error(
      `action « ${action} » absente du registre : la surface a été renommée ou retirée`,
    );
  }
  await page.evaluate((id) => {
    (window as unknown as FenetreTherese).__therese?.runAction(id);
  }, action);
}

/** Fermer la surface du dessus, comme le ferait Échap. */
export async function fermerLaSurface(page: Page): Promise<void> {
  await page.keyboard.press('Escape');
}

/**
 * Relire une fois une lecture qui a échoué AU TRANSPORT, jamais sur un statut.
 *
 * 02/09/2026. Sur une exécution complète de contrôle, un seul test des
 * quatre-vingt-dix-huit est tombé en `apiRequestContext.get: read ECONNRESET`
 * sur `GET /api/auth/token` — l'amorçage, pas une assertion. Cinq workers
 * ouvrent leurs connexions vers un uvicorn qui vient de démarrer, et une
 * connexion gardée en vie peut être fermée par le serveur à l'instant même où
 * le client la réutilise. Relancé seul, le parcours repasse en entier.
 *
 * On tolère donc UNE reprise, et seulement quand l'appel LÈVE : une réponse
 * arrivée, fût-elle en 401 ou en 500, est une réponse et remonte telle quelle.
 * Rien ici ne masque un échec de l'application, seulement un hoquet de socket.
 */
async function lireUneFoisDePlusSiLaConnexionLache(
  requete: APIRequestContext,
  url: string,
): Promise<import('@playwright/test').APIResponse> {
  try {
    return await requete.get(url);
  } catch {
    await new Promise((resoudre) => setTimeout(resoudre, 500));
    return requete.get(url);
  }
}

/**
 * Passer la mise en route CÔTÉ BACKEND.
 *
 * Les parcours posaient `localStorage.setItem('onboarding_complete', 'true')`
 * et croyaient en avoir fini. Or `App.tsx` ne lit pas le stockage local : il
 * interroge `GET /api/config/onboarding-complete`. Sur la base jetable des
 * E2E, vierge par construction, la réponse est « non » — et l'assistant de
 * mise en route s'affiche PAR-DESSUS la surface que le test vient d'ouvrir.
 * Le test échouait alors sur un élément « introuvable » qui était simplement
 * recouvert. Diagnostiqué le 01/09/2026 en lisant la capture d'échec.
 */
/** En-têtes d'appel du backend jetable, jeton de session compris. */
async function entetesAuthentifies(
  requete: APIRequestContext,
): Promise<Record<string, string>> {
  const jeton = await lireUneFoisDePlusSiLaConnexionLache(requete, `${BACKEND_URL}/api/auth/token`);
  const { token } = (await jeton.json()) as { token: string };
  return { 'X-Therese-Token': token };
}

export async function passerLaMiseEnRoute(requete: APIRequestContext): Promise<void> {
  const entetes = await entetesAuthentifies(requete);

  const deja = await requete.get(`${BACKEND_URL}/api/config/onboarding-complete`, {
    headers: entetes,
  });
  if (deja.ok() && ((await deja.json()) as { completed?: boolean }).completed) return;

  // Les parcours tournent en parallèle sur une base unique : deux d'entre eux
  // peuvent poser la préférence en même temps et l'un des deux récolte un 500.
  // Ce qui compte n'est pas d'avoir gagné la course, c'est que l'état final
  // soit bien « terminé » — on le RELIT plutôt que de croire le code de retour.
  await requete
    .post(`${BACKEND_URL}/api/config/onboarding-complete`, { headers: entetes })
    .catch(() => undefined);

  const apres = await requete.get(`${BACKEND_URL}/api/config/onboarding-complete`, {
    headers: entetes,
  });
  const etat = apres.ok() ? ((await apres.json()) as { completed?: boolean }) : { completed: false };
  if (!etat.completed) {
    throw new Error("mise en route non passée : l'assistant recouvrira les surfaces");
  }
}

/**
 * Clé factice du fournisseur posé par la suite.
 *
 * Le backend ne fait AUCUN appel réseau à l'enregistrement : `POST
 * /api/config/api-key` vérifie le préfixe (`sk-ant-` pour Anthropic), chiffre
 * la valeur en Fernet dans la préférence `anthropic_api_key`, recharge son
 * cache de clés et remet le service LLM à zéro. C'est tout. Aucun parcours
 * n'envoie de message, donc cette chaîne ne part jamais chez un fournisseur ;
 * elle est écrite en clair ici pour qu'on ne la confonde pas avec une vraie.
 */
const CLE_FACTICE = 'sk-ant-e2e-cle-factice-aucun-appel-reseau';

/** Ce que le backend répond sur l'état du modèle courant. */
type EtatDuModele = { available?: boolean; model?: string };

async function lireLEtatDuModele(
  requete: APIRequestContext,
  entetes: Record<string, string>,
): Promise<EtatDuModele> {
  const reponse = await requete
    .get(`${BACKEND_URL}/api/config/llm`, { headers: entetes })
    .catch(() => undefined);
  if (!reponse || !reponse.ok()) return {};
  return (await reponse.json()) as EtatDuModele;
}

/**
 * Vrai une fois que CE travailleur a vu un modèle actif.
 *
 * Le backend jetable est unique et le modèle qu'on y pose ne s'en va pas. Un
 * travailleur vérifie donc une fois, puis passe son chemin, au lieu de
 * réinterroger le backend avant chacun de ses parcours.
 */
let modeleDejaPose = false;

/**
 * Poser un modèle ACTIF sur le backend jetable (B-265, 03/09/2026).
 *
 * Deux parcours du premier lancement tapaient dans le composeur. Sur le runner
 * GitHub, sans clé de fournisseur ni Ollama, `GET /api/config/llm` répond
 * `available: false` : `ChatInput` désactive alors le `<textarea>` et affiche
 * « Choisis d'abord un modèle ». `click()` et `fill()` attendaient trente
 * secondes un champ qui ne s'activerait jamais. En local, la même suite passait
 * parce que la machine, elle, avait de quoi répondre — le test mesurait le
 * poste de travail, pas l'application.
 *
 * Le backend est désormais aveugle à la machine (run-e2e-backend.sh), donc la
 * suite pose elle-même ce qu'elle exige : un fournisseur, une clé factice, un
 * modèle du catalogue. Rien n'est deviné — le modèle est celui que le backend
 * annonce en tête de sa propre liste.
 *
 * Idempotente et tolérante à la course : quatre-vingt-dix-huit parcours
 * partagent un seul backend et cinq travailleurs les lancent en parallèle. On
 * ne croit donc aucun code de retour, on RELIT l'état final — comme le fait
 * déjà `passerLaMiseEnRoute` pour la mise en route.
 */
export async function poserUnModeleActif(requete: APIRequestContext): Promise<void> {
  if (modeleDejaPose) return;
  const entetes = await entetesAuthentifies(requete);
  if ((await lireLEtatDuModele(requete, entetes)).available === true) {
    modeleDejaPose = true;
    return;
  }

  const catalogue = await requete
    .get(`${BACKEND_URL}/api/config/llm/models/anthropic`, { headers: entetes })
    .catch(() => undefined);
  const modeles = catalogue?.ok()
    ? ((await catalogue.json()) as { models?: string[] }).models ?? []
    : [];
  if (modeles.length === 0) {
    throw new Error(
      'catalogue Anthropic vide : GET /api/config/llm/models/anthropic ne sert plus de modèle',
    );
  }
  const modele = modeles[0];

  const poser = async () => {
    // Un 500 ici n'est PAS un échec : deux parcours peuvent écrire la même
    // préférence au même instant sur une base SQLite mono-écrivain.
    await requete
      .post(`${BACKEND_URL}/api/config/api-key`, {
        headers: entetes,
        data: { provider: 'anthropic', api_key: CLE_FACTICE },
      })
      .catch(() => undefined);
    await requete
      .post(`${BACKEND_URL}/api/config/llm`, {
        headers: entetes,
        data: { provider: 'anthropic', model: modele },
      })
      .catch(() => undefined);
  };

  await poser();
  if ((await lireLEtatDuModele(requete, entetes)).available === true) {
    modeleDejaPose = true;
    return;
  }

  // Une seule reprise : `POST /api-key` remet le service LLM à zéro, si bien
  // qu'un enregistrement de clé arrivé APRÈS le choix du modèle pouvait laisser
  // la lecture suivante sur un service reconstruit entre les deux écritures.
  await poser();
  const final = await lireLEtatDuModele(requete, entetes);
  if (final.available !== true) {
    throw new Error(
      `aucun modèle actif après pose (provider anthropic, modèle ${modele}) : ` +
        'le composeur restera désactivé et les parcours du chat expireront',
    );
  }
  modeleDejaPose = true;
}

/**
 * Préparer une page prête à l'emploi : mise en route passée, modèle actif posé,
 * coque montée, registre publié.
 *
 * La pose du modèle est un appel DISTINCT, jamais glissé dans
 * `passerLaMiseEnRoute` : celle-ci sort tôt dès que la mise en route est déjà
 * faite, et emporterait la pose avec elle à partir du deuxième parcours.
 *
 * AUCUNE attente sur le réseau ici (B-269, 03/09/2026). `waitForLoadState(
 * 'networkidle')` réclame une demi-seconde sans la moindre requête en vol :
 * c'est une propriété de la MACHINE, pas de l'application, et un poste chargé
 * ne l'offre pas dans le budget imparti alors même que la coque est montée
 * depuis longtemps. Mesuré sur ce dépôt à cinq travailleurs, charge 62 : douze
 * parcours sur quatre-vingt-dix-huit tombaient là, tous à l'AMORÇAGE, aucun
 * sur une assertion. Les deux attentes qui suivent disent mieux la même chose
 * et ne dépendent que de l'application : `app-main` prouve que la coque est
 * rendue, le registre d'actions qu'elle a fini de se déclarer. Si un jour un
 * parcours exige une requête terminée, on attendra CET état précis, jamais un
 * délai.
 */
export async function ouvrirLApplication(page: Page, requete: APIRequestContext): Promise<void> {
  await passerLaMiseEnRoute(requete);
  await poserUnModeleActif(requete);
  await page.goto('/');
  await page.waitForSelector('[data-testid="app-main"]', { timeout: 15000 });
  await attendreLeRegistre(page);
}
