"""Port texte seulement, après le rendu CDP/Git explicitement épinglé.

Cette fonction ne lit aucun profil, ne crée aucun fichier de ronde et ne lance
ni Node, ni lsof, ni Session. Trois textes sortent, à trois chemins fermés.
"""
from __future__ import annotations

from hashlib import sha256
from typing import Mapping


SOURCES = {
    "complements/instruments/ownership-only.mjs": "41eb7fcd151e66a675935608379bfc29e49e13e0cae3d63ee94af3de0964aa90",
    "trace-chrome.mjs": "93f3fef0b0a02c2dda0357c25766b87b604da2afcfc15431d803a285eaac1f2f",
    "runtime/couverture-ecran-c17.mjs": "3d30adcfe5169fb32ae87c1f2c2456fc7d62836d3e3342d48024112f857a41c9",
}
HELPER_SHA = "64555c1d39590d944bce79a84479bc7deca7d1bdcdfd4552f842651bc307baf3"


class Refused(ValueError):
    """Préimage ou liaison différente : nouveau port et revue nécessaires."""


def digest(value: str) -> str:
    return sha256(value.encode("utf-8")).hexdigest()


def pin(value: str, reference: Mapping[str, object], expected: str | None = None) -> None:
    if set(reference) != {"sha256", "bytes"}:
        raise Refused("Référence SHA/bytes exacte requise")
    if reference["sha256"] != digest(value) or reference["bytes"] != len(value.encode("utf-8")):
        raise Refused("Texte et référence différents")
    if expected is not None and digest(value) != expected:
        raise Refused("Préimage autre que le gel CDP examiné")


def once(value: str, old: str, new: str) -> str:
    if value.count(old) != 1:
        raise Refused("Ancre absente ou multiple dans la préimage")
    return value.replace(old, new, 1)


OWNERSHIP = """import {requestOwnedListener} from '../../auxiliary-ports/runtime/aux_node.mjs';

// L'API appelée par contexte-v3 reste identique. Le parent Session vivant
// possède seul lsof et attribue le PID/birth sur deux scans globaux frais.
export async function verifierListenerPossede(port) {
  if (port !== 17593 && port !== 5173) {
    throw new Error('Port ou processus QA non attribué');
  }
  await requestOwnedListener(port);
}
"""

FETCH_GUARD = """// Les cinq sites complementaires passent deja par contexte-v3. Les trois
// recettes runtime et la couverture sont autonomes : leur fetch Node attend
// la meme observation root, avant toute emission, sans second lsof local.
const directFetchStages=new Set(['recipe-general','recipe-invoices','recipe-crm','coverage']);
if(directFetchStages.has(process.env.C17_SESSION_STAGE)){
  const fetchOriginal=globalThis.fetch.bind(globalThis);
  globalThis.fetch=async(input,options={})=>{
    const address=typeof input==='string'||input instanceof URL?String(input):input?.url;
    const url=new URL(address);
    if(url.protocol!=='http:'||url.hostname!=='127.0.0.1'||
       !['17593','5173'].includes(url.port)||url.username||url.password||url.hash)
      throw new Error('Fetch Node hors ports QA attribues');
    await requestOwnedListener(Number(url.port));
    return fetchOriginal(input,options);
  };
}
"""

ROUTE_HTTP = """      if (requeteAutorisee(requete.method(), requete.url())) {
        try {
          await requestOwnedListener(Number(new URL(requete.url()).port));
        } catch {
          garde.bloquees.push({ methode: requete.method(), url: adresseSansSecrets(requete.url()) });
          return route.abort('blockedbyclient');
        }
        return route.continue();
      }
"""

ROUTE_WS = """      if (autorisee) {
        try {
          await requestOwnedListener(5173);
        } catch {
          garde.websockets_bloques.push(adresseSansSecrets(route.url()));
          return route.close();
        }
        return route.connectToServer();
      }
"""


def render(
    definitions: Mapping[str, str],
    source_refs: Mapping[str, Mapping[str, object]],
    *,
    helper_source: str,
    helper_ref: Mapping[str, object],
    context_source: str,
    context_ref: Mapping[str, object],
) -> dict[str, str]:
    """Dérive exactement trois sorties; ne rend pas les anciens chemins QA."""
    if set(definitions) != set(SOURCES) or set(source_refs) != set(SOURCES):
        raise Refused("Trois définitions et pins exacts requis")
    for path, expected in SOURCES.items():
        pin(definitions[path], source_refs[path], expected)
    pin(helper_source, helper_ref, HELPER_SHA)
    if "export const requestOwnedListener = port => getAuxiliary().listener(port);" not in helper_source:
        raise Refused("API helper owned-listener absente")
    if "const root = context.root, scans = new Map();" not in helper_source or "scans.delete(port)" not in helper_source:
        raise Refused("Coalescence en vol sans TTL non observée dans le helper")
    pin(context_source, context_ref)
    ordered = ("const ownershipReady=import(new URL('./ownership-only.mjs',import.meta.url).href)",
               "await ownershipReady;", "await verifierListener(Number(u.port));", "return fetchOriginal(input,")
    if any(context_source.count(anchor) != 1 for anchor in ordered) or [context_source.index(anchor) for anchor in ordered] != sorted(context_source.index(anchor) for anchor in ordered):
        raise Refused("Contexte : import/await/fetch non préservés")

    trace = definitions["trace-chrome.mjs"]
    trace = once(trace,
                 "import {connectOwnedChrome} from './auxiliary-ports/runtime/aux_node.mjs';",
                 "import {connectOwnedChrome,requestOwnedListener} from './auxiliary-ports/runtime/aux_node.mjs';")
    trace = once(trace, "const originalLaunch=options=>connectOwnedChrome(chromium,options);",
                 FETCH_GUARD + "const originalLaunch=options=>connectOwnedChrome(chromium,options);")

    coverage = definitions["runtime/couverture-ecran-c17.mjs"]
    coverage = once(coverage,
                    'import { chromium } from "/Users/synoptia/Desktop/Dev Synoptia/Synoptia-THERESE-c15-codex/node_modules/playwright/index.mjs";',
                    'import { chromium } from "/Users/synoptia/Desktop/Dev Synoptia/Synoptia-THERESE-c15-codex/node_modules/playwright/index.mjs";\nimport { requestOwnedListener } from \'../auxiliary-ports/runtime/aux_node.mjs\';')
    coverage = once(coverage, "contexte.route('**/*', (route) => {", "contexte.route('**/*', async (route) => {")
    coverage = once(coverage,
                    "      if (requeteAutorisee(requete.method(), requete.url())) return route.continue();\n",
                    ROUTE_HTTP)
    coverage = once(coverage, "contexte.routeWebSocket(/.*/, (route) => {", "contexte.routeWebSocket(/.*/, async (route) => {")
    coverage = once(coverage, "      if (autorisee) return route.connectToServer();\n", ROUTE_WS)

    if "child_process" in OWNERSHIP or "/usr/sbin/lsof" in trace:
        raise Refused("Lancement lsof Node réintroduit")
    return {
        "complements/instruments/ownership-only.mjs": OWNERSHIP,
        "trace-chrome.mjs": trace,
        "runtime/couverture-ecran-c17.mjs": coverage,
    }
