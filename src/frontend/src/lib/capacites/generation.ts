/**
 * Contrôle de génération du manifeste (0.44).
 *
 * Le manifeste vit en deux exemplaires : celui du bundle frontend et celui du
 * binaire sidecar. Rien ne garantit qu'un frontend et un sidecar packagés à
 * des moments différents en portent la même version — et une divergence
 * silencieuse ferait mentir l'aide, la palette ou le catalogue sur ce que le
 * backend sait réellement faire.
 *
 * Le contrôle : les deux côtés calculent une empreinte SHA-256 du JSON
 * CANONIQUE (clés triées, sans espaces — le bundler retransforme le fichier,
 * seuls les contenus sont comparables), et le frontend compare au démarrage.
 * Une divergence est signalée, jamais bloquante : un catalogue légèrement
 * décalé vaut mieux qu'une application qui refuse de démarrer.
 */
import donnees from '../../../../backend/app/data/capacites.json';

/** Sérialisation canonique : mêmes octets des deux côtés, quel que soit
 *  l'ordre des clés imposé par le parseur ou le bundler. */
export function serialisationCanonique(valeur: unknown): string {
  if (Array.isArray(valeur)) {
    return `[${valeur.map(serialisationCanonique).join(',')}]`;
  }
  if (valeur !== null && typeof valeur === 'object') {
    const entrees = Object.entries(valeur as Record<string, unknown>)
      .sort(([a], [b]) => (a < b ? -1 : a > b ? 1 : 0))
      .map(([cle, v]) => `${JSON.stringify(cle)}:${serialisationCanonique(v)}`);
    return `{${entrees.join(',')}}`;
  }
  return JSON.stringify(valeur);
}

export async function empreinteLocale(): Promise<string> {
  const octets = new TextEncoder().encode(serialisationCanonique(donnees));
  const condensat = await crypto.subtle.digest('SHA-256', octets);
  return Array.from(new Uint8Array(condensat))
    .map((o) => o.toString(16).padStart(2, '0'))
    .join('');
}

export interface VerdictGeneration {
  coherent: boolean;
  locale: string;
  distante: string;
}

/**
 * Compare le manifeste du bundle à celui du sidecar. À appeler au démarrage,
 * APRÈS l'initialisation de l'authentification : la revue a montré qu'un
 * `fetch` nu prenait un 401 (la route n'est pas exemptée du jeton de session),
 * et que le verdict « cohérent par défaut » sur toute réponse non-OK rendait le
 * contrôle incapable d'échouer — pour la seconde fois. D'où `apiFetch`, qui
 * porte le jeton, injectable pour les tests.
 *
 * Toute erreur (backend pas encore prêt, route absente) rend un verdict
 * cohérent par défaut : ce contrôle signale, il ne bloque jamais.
 */
export async function verifierGeneration(
  apiBase: string,
  fetcher?: (url: string) => Promise<Response>,
): Promise<VerdictGeneration> {
  const locale = await empreinteLocale();
  try {
    const appel =
      fetcher
      ?? (await import('../../services/api/core')).apiFetch;
    const reponse = await appel(`${apiBase}/api/config/capacites`);
    if (!reponse.ok) return { coherent: true, locale, distante: 'inconnue' };
    const corps = (await reponse.json()) as { empreinte?: string };
    const distante = corps.empreinte ?? 'inconnue';
    // Deux anomalies distinctes, deux messages : « absent » signifie que le
    // sidecar n'a pas PU lire son manifeste (fail-open côté backend), pas que
    // les générations divergent. L'annoncer comme un écart de packaging
    // enverrait le diagnostic dans la mauvaise direction.
    if (distante === 'absent') {
      console.warn(
        '[capacités] Le sidecar n\'a pas pu lire son manifeste : son aide et '
        + 'son catalogue seront incomplets. Voir les journaux du backend.',
      );
      return { coherent: false, locale, distante };
    }
    const coherent = distante === 'inconnue' || distante === locale;
    if (!coherent) {
      console.warn(
        '[capacités] Le manifeste du frontend et celui du sidecar divergent : '
        + 'les deux ont probablement été packagés à des moments différents. '
        + `Frontend ${locale.slice(0, 12)}…, sidecar ${distante.slice(0, 12)}…`,
      );
    }
    return { coherent, locale, distante };
  } catch {
    return { coherent: true, locale, distante: 'inconnue' };
  }
}
