"""Composition fermée CDP -> Git -> listener, sur définitions épinglées.

Préparation seulement. Aucun import du renderer historique, de Node, G1 ou
du produit. Cette fonction pure ne crée ni checkout, ni snapshot, ni ronde.
"""
from __future__ import annotations

from hashlib import sha256
from typing import Mapping


# Les onze textes réels du gel Git, plus ownership-only qui n'y était pas porté.
SOURCES = {
    "runtime/recette-c17.mjs": ("c95be80e6dfcfa0acdde63c26a06fc8dcce41c3a888529f926b0000a7a447bf2", 7321),
    "runtime/recette-facturation-p160-v2.mjs": ("11f29b24795479ef68a10bbe588b66be9521da6d9c1890b0810b4f7eec4dead4", 7376),
    "runtime/recette-crm-focus.mjs": ("b3937b6c6b304150f4adc8e12b9f400def70a578566213a9d855aea1cab52f19", 5621),
    "runtime/couverture-ecran-c17.mjs": ("3d30adcfe5169fb32ae87c1f2c2456fc7d62836d3e3342d48024112f857a41c9", 34607),
    "complements/instruments/b1713-clavier-v3.mjs": ("690b3f82a8342dc415802fc41fc43fd693d328ad9fb6af43c4eb12c9a80ebb64", 7405),
    "complements/instruments/p157-pipeline-root-oracle.mjs": ("a80fd37f3db40d3bda491fbdd5a6354619f10d69052264a1ac8b3647785e5d40", 14451),
    "complements/instruments/b1755-garde-v3.mjs": ("f461a931f8f5f2dd68f233067ba4b775cb1f5849dedd2b68331342aad149af08", 3921),
    "complements/instruments/p162-colonnes-v3.mjs": ("b341e9bba0a6940988b49690ce2dfd4d8689cda630bbb7236020dbd40a6185af", 18168),
    "complements/instruments/p162-garde-get-v3.mjs": ("fef15097299ed92444f272bbc983592101644f173995192ae53b0e5f38c1dbcb", 2511),
    "complements/instruments/contexte-v3.mjs": ("9960ba63b5984dd00a918e73292a541729e1579582952d3a7ec14860ebbda38f", 7244),
    "trace-chrome.mjs": ("93f3fef0b0a02c2dda0357c25766b87b604da2afcfc15431d803a285eaac1f2f", 2936),
    "complements/instruments/ownership-only.mjs": ("41eb7fcd151e66a675935608379bfc29e49e13e0cae3d63ee94af3de0964aa90", 2095),
}
HELPER_SHA = "f302e0fd1cb6f64d87c606eabcf6a8b7184b1ca05654024bfd52ec569c1478db"
HELPER_BYTES = 15031
CONTEXT_SHA, CONTEXT_BYTES = SOURCES["complements/instruments/contexte-v3.mjs"]
CHANGED_PATHS = frozenset(("complements/instruments/ownership-only.mjs", "trace-chrome.mjs", "runtime/couverture-ecran-c17.mjs"))
RUNTIME_ENABLED = False
OS_STARTUP_QUALIFIED = False
ADMISSIONS: dict = {}
CAPABILITIES: dict = {}


class Refused(ValueError):
    """Texte différent : nouvelle définition et revue nécessaires."""


def digest(value: str) -> str:
    return sha256(value.encode("utf-8")).hexdigest()


def pin(value: str, reference: Mapping[str, object], expected: tuple[str, int]) -> None:
    if set(reference) != {"sha256", "bytes"}:
        raise Refused("Référence SHA/bytes exacte requise")
    observed = (digest(value), len(value.encode("utf-8")))
    if type(reference["bytes"]) is not int or (reference["sha256"], reference["bytes"]) != observed:
        raise Refused("Texte et référence différents")
    if observed != expected:
        raise Refused("Préimage autre que le gel Git épinglé")


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
    """Douze sorties, dont trois ports ; helper et contexte Git restent exacts.

    Le caller doit conserver le helper fourni au SHA f302e0fd. Ce résultat
    ne rend pas les chemins historiques opérationnels dans une ronde A/B.
    """
    if set(definitions) != set(SOURCES) or set(source_refs) != set(SOURCES):
        raise Refused("Douze définitions Git/listener et pins exacts requis")
    for path, expected in SOURCES.items():
        pin(definitions[path], source_refs[path], expected)
    pin(helper_source, helper_ref, (HELPER_SHA, HELPER_BYTES))
    pin(context_source, context_ref, (CONTEXT_SHA, CONTEXT_BYTES))
    if context_source != definitions["complements/instruments/contexte-v3.mjs"]:
        raise Refused("Deux représentations du contexte Git divergent")
    if "export const requestOwnedListener = port => getAuxiliary().listener(port);" not in helper_source:
        raise Refused("API helper owned-listener absente")
    if "const root = context.root, scans = new Map();" not in helper_source or "scans.delete(port)" not in helper_source:
        raise Refused("Coalescence en vol sans TTL non observée dans le helper")
    if helper_source.count("export function ownedGitHead(source, environment = process.env)") != 1:
        raise Refused("Port Git exact absent")
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
    outputs = dict(definitions)
    outputs.update({
        "complements/instruments/ownership-only.mjs": OWNERSHIP,
        "trace-chrome.mjs": trace,
        "runtime/couverture-ecran-c17.mjs": coverage,
    })
    if {path for path in SOURCES if outputs[path] != definitions[path]} != CHANGED_PATHS:
        raise Refused("Port autre que les trois différences listener")
    return outputs
