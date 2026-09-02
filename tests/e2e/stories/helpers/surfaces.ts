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
export async function passerLaMiseEnRoute(requete: APIRequestContext): Promise<void> {
  const jeton = await lireUneFoisDePlusSiLaConnexionLache(requete, `${BACKEND_URL}/api/auth/token`);
  const { token } = (await jeton.json()) as { token: string };
  const entetes = { 'X-Therese-Token': token };

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
 * Préparer une page prête à l'emploi : mise en route passée, coque montée,
 * registre publié.
 */
export async function ouvrirLApplication(page: Page, requete: APIRequestContext): Promise<void> {
  await passerLaMiseEnRoute(requete);
  await page.goto('/');
  await page.waitForLoadState('networkidle', { timeout: 15000 });
  await page.waitForSelector('[data-testid="app-main"]', { timeout: 15000 });
  await attendreLeRegistre(page);
}
