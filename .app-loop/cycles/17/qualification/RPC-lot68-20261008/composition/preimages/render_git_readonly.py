"""Pure Git metadata port, applied after the closed CDP definition renderer.

No filesystem, subprocess, Session, admission, checkout allocation or HEAD
production occurs here. Inputs must be the caller's newly prepared/pinned C17
definitions. Historical fixture bytes are not a current A/B checkout.
"""
from __future__ import annotations

from hashlib import sha256

RUNTIME_ENABLED = False
OS_STARTUP_QUALIFIED = False
ADMISSION_TABLE: dict = {}
CAPABILITIES: dict = {}
OLD_HELPER_PIN = {"sha256": "64555c1d39590d944bce79a84479bc7deca7d1bdcdfd4552f842651bc307baf3", "bytes": 14247}
HELPER_PATH = "auxiliary-ports/runtime/aux_node.mjs"
TRACE_PATH = "trace-chrome.mjs"
CONTEXT_PATH = "complements/instruments/contexte-v3.mjs"
GUARD_PATH = "complements/instruments/p162-garde-get-v3.mjs"
RECIPE_PATHS = frozenset({
    "runtime/recette-c17.mjs", "runtime/recette-facturation-p160-v2.mjs",
    "runtime/recette-crm-focus.mjs", "runtime/couverture-ecran-c17.mjs",
    "complements/instruments/b1713-clavier-v3.mjs",
    "complements/instruments/p157-pipeline-root-oracle.mjs",
    "complements/instruments/b1755-garde-v3.mjs",
    "complements/instruments/p162-colonnes-v3.mjs",
})
REQUIRED_PATHS = RECIPE_PATHS | {TRACE_PATH, CONTEXT_PATH, GUARD_PATH}
COMPACT_GIT = "execFileSync('git',['rev-parse','HEAD'],{cwd:repo,encoding:'utf8'}).trim()"
SPACED_GIT = "execFileSync('git', ['rev-parse', 'HEAD'], {cwd: repo, encoding: 'utf8'}).trim()"
CDP_IMPORT = "import {connectOwnedChrome} from './auxiliary-ports/runtime/aux_node.mjs';\n"
CDP_ANCHOR = "const originalLaunch=chromium.launch.bind(chromium);"
CDP_REPLACEMENT = "const originalLaunch=options=>connectOwnedChrome(chromium,options);"
GIT_SITES = {
    "runtime/recette-c17.mjs": ("import {execFileSync} from 'node:child_process';", COMPACT_GIT),
    "runtime/recette-facturation-p160-v2.mjs": ("import {execFileSync} from 'node:child_process';", COMPACT_GIT),
    "runtime/recette-crm-focus.mjs": ("import {execFileSync} from 'node:child_process';", COMPACT_GIT),
    "complements/instruments/b1713-clavier-v3.mjs": ("import { execFileSync } from 'node:child_process';", SPACED_GIT),
    "complements/instruments/p162-colonnes-v3.mjs": ("import {execFileSync} from 'node:child_process';", COMPACT_GIT),
    CONTEXT_PATH: ("import {execFileSync} from 'node:child_process';", COMPACT_GIT),
}
OWNED_GIT_ADDITION = """
// Fresh A/B metadata only: no cached context/head and no Git subprocess fallback.
export function ownedGitHead(source, environment = process.env) {
  const context = environmentContext(environment);
  need(context.scope === 'runtime78_exact_round' && AB_DIRECT_JOBS.includes(context.stage)
    && context.product_source_root === source, 'Git metadata hors source/site A-B exact');
  const snapshotRef = JSON.parse(environment.C17_AUX_GIT_SNAPSHOT_REF);
  need(same(snapshotRef, context.git_snapshot_ref)
    && snapshotRef.path === `${context.root}/authorization/git-snapshot.json`,
    'Git snapshot env autre que le contexte A-B exact');
  const head = gitHead(snapshotRef, source);
  need(head === context.head, 'HEAD physique autre que le contexte A-B exact');
  return head;
}
"""


def need(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def pin(text: str) -> dict:
    raw = text.encode("utf-8")
    return {"sha256": sha256(raw).hexdigest(), "bytes": len(raw)}


def render(definitions: dict[str, str], source_pins: dict[str, dict], *,
           helper_source: str, helper_pin: dict,
           trace_before_cdp: str, trace_before_cdp_pin: dict) -> dict:
    need(set(definitions) == REQUIRED_PATHS and set(source_pins) == REQUIRED_PATHS,
         "Exact eight recipes/context/trace/P162 guard required")
    for path, source in definitions.items():
        need(type(source) is str and pin(source) == source_pins[path],
             "Definition SHA/bytes mismatch: " + path)
    need(pin(helper_source) == helper_pin == OLD_HELPER_PIN,
         "Exact pre-CDP64555 helper required")
    need(pin(trace_before_cdp) == trace_before_cdp_pin
         and trace_before_cdp.count(CDP_ANCHOR) == 1
         and CDP_IMPORT not in trace_before_cdp and CDP_REPLACEMENT not in trace_before_cdp,
         "Exact pristine CDP input required")
    expected_trace = CDP_IMPORT + trace_before_cdp.replace(CDP_ANCHOR, CDP_REPLACEMENT)
    need(definitions[TRACE_PATH] == expected_trace, "CDP-before-Git composition required")
    need("ownedGitHead" not in helper_source and helper_source.endswith("\n"),
         "Helper must be pristine before Git addition")
    # Entire old helper is retained, not reconstructed by a weaker reader.
    need(helper_source.count("export function gitHead(snapshotRef, source) {") == 1
         and helper_source.count("export function environmentContext(environment = process.env) {") == 1
         and helper_source.count("&& gitHead(context.git_snapshot_ref, context.product_source_root) === context.head,") == 1,
         "Physical Git/environment reader anchors absent")
    output = definitions.copy()
    for path, (import_anchor, git_anchor) in GIT_SITES.items():
        text = definitions[path]
        need(text.count(import_anchor) == 1 and text.count(git_anchor) == 1
             and text.count("execFileSync(") == 1 and "ownedGitHead" not in text,
             "Unique pristine Git/import anchor required: " + path)
        relative = "../auxiliary-ports/runtime/aux_node.mjs" if path.startswith("runtime/") else "../../auxiliary-ports/runtime/aux_node.mjs"
        import_new = f"import {{ownedGitHead}} from '{relative}';"
        changed = text.replace(import_anchor, import_new).replace(git_anchor, "ownedGitHead(repo)")
        restored = changed.replace(import_new, import_anchor).replace("ownedGitHead(repo)", git_anchor)
        need(restored == text and "child_process" not in changed and "execFileSync" not in changed,
             "Git-only delta not exactly reversible: " + path)
        output[path] = changed
    need(all(output[path] == definitions[path] for path in REQUIRED_PATHS - GIT_SITES.keys()),
         "Non-Git recipe/trace/GET guard changed")
    helper_output = helper_source + OWNED_GIT_ADDITION
    need(helper_output[:-len(OWNED_GIT_ADDITION)] == helper_source
         and OWNED_GIT_ADDITION.count("environmentContext(environment)") == 1
         and OWNED_GIT_ADDITION.count("gitHead(snapshotRef, source)") == 1,
         "Helper addition not exactly append-only/fresh")
    need(definitions[CONTEXT_PATH].count("head()") == output[CONTEXT_PATH].count("head()") == 2,
         "Context pre/post HEAD calls changed")
    return {"schema": "c17-ab-git-readonly-definition-render-v1", "scope": "preparation_only",
            "definitions": output, "output_pins": {name: pin(value) for name, value in output.items()},
            "helper_source": helper_output, "helper_pin": pin(helper_output),
            "changed_paths": list(GIT_SITES) + [HELPER_PATH],
            "composition": ["closed CDP renderer with original helper64555", "this Git-only renderer with new helper pin"],
            "input_helper_pin": helper_pin.copy(), "runtime_enabled": False,
            "os_startup_qualified": False, "admission_table": {}, "capabilities": {},
            "required_current_sources": ["Exact caller-prepared C17 definitions, not historical fixture identity",
                "Fresh A/B binding/checkout and root/authorization/git-snapshot.json",
                "Root GitSnapshot.verify_worktree proof linking commit/tree/blob/modes before admission"],
            "limits": ["No HEAD, checkout, snapshot, Session or root authority is produced",
                "JS gitHead rechecks physical refs; recursive tree verification remains a root obligation",
                "Existing Git/environment readers remain byte-exact; no cache or subprocess fallback",
                "Existing lsof calls/ownership-only and physical A/B lifecycle remain separate",
                "No historical schema/result is a current A/B proof"]}
