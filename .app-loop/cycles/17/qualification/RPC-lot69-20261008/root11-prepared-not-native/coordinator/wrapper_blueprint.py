"""Table instrument-only des 15 RPC et six processus directs de WRAPPER_CANARY.

Pure : aucun G1, lancement, socket, Git ou module produit importé. Les valeurs
dynamiques sont les références physiques root déjà gelées, pas un payload helper.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re

import rpc_instrument_contract as contract


HEAD = "2d69e30c9c6dd18823ee6102271876003a6a67cc"
QA_SOURCE = Path("/private/tmp/therese-c17-wrapper-source-kGvU1hdx/source")
QA_PYTHON = QA_SOURCE / ".venv-conforme/bin/python"
NODE_ROOT = Path("/Users/synoptia/.nvm/versions/node/v22.19.0")
NODE = NODE_ROOT / "bin/node"
FRONT = QA_SOURCE / "src/frontend"
SQL_CONTRACT_SHA = 'f53d7e7159cf81b473a3b47a202e24ab841b18c922152d4b0f20beeb2b9d0c4e'
PROFILE_LABEL = "service"
DIRECT_ORDER = ("backend", "vite", "calibrate", "B1753", "B1760", "B1753-power")


def need(ok: bool, reason: str) -> None:
    if not ok:
        raise ValueError(reason)


def exact_root(root: Path) -> Path:
    root = Path(root)
    need(root.is_absolute() and root.parent == Path("/private/tmp")
         and re.fullmatch(r"therese-c17-wrapper-canary-[a-z0-9_]{8,64}", root.name) is not None,
         "Racine WRAPPER_CANARY hors table")
    return root


def paths(root: Path) -> dict[str, Path]:
    root = exact_root(root)
    profile = root / "profiles" / PROFILE_LABEL
    return {"root": root, "profile": profile, "home": profile / "home",
            "tmp": profile / "tmp", "data": profile / "data",
            "test_data": profile / "test-data", "logs_data": profile / "logs-data",
            "overlay": root / "auxiliary-ports", "runtime": root / "runtime",
            "front": FRONT, "source": QA_SOURCE,
            "vite_config": root / "runtime/vite.runtime.config.mjs",
            "vite_canonical": root / "runtime/vite.canonique.mjs",
            "vite_cache": root / "runtime/vite-cache",
            "git_snapshot": root / "authorization/git-snapshot.json",
            "playwright_unused": root / "auxiliary/playwright-unused",
            "logs_run": root / "runtime/calibration/logs-rpc"}


def ref_text(reference: dict) -> str:
    need(type(reference) is dict and set(reference) == {"path", "sha256", "bytes"}
         and type(reference["path"]) is str and Path(reference["path"]).is_absolute()
         and re.fullmatch(r"[a-f0-9]{64}", reference["sha256"]) is not None
         and type(reference["bytes"]) is int and reference["bytes"] > 0,
         "Référence root SHA/bytes absente")
    return json.dumps(reference, sort_keys=True)


def auxiliary_metadata(root: Path, *, git_ref: dict,
                       chrome_context_refs: dict[str, dict]) -> dict[str, dict[str, str]]:
    """Les huit ajouts exacts du transport, jamais hérités d'un env libre."""
    git = ref_text(git_ref)
    jobs = ("rpc-all-runtime_ui-visual_capture-network_capture", "rpc-screen-negative",
            "rpc-screen-positive-visual", "rpc-screen-positive-network", "rpc-screen-restored")
    need(set(chrome_context_refs) == set(jobs), "Cinq contextes Chrome préémis absents")
    result = {"rpc-all-test_runner": {"C17_AUX_GIT_SNAPSHOT_REF": git},
              "rpc-all-logs": {"C17_AUX_GIT_SNAPSHOT_REF": git,
                               "C17_AUX_LOGS_RUN": str(paths(root)["logs_run"])},
              "rpc-all-screen_coverage": {"C17_AUX_GIT_SNAPSHOT_REF": git}}
    for job in jobs:
        result[job] = {"C17_AUX_CONTEXT_REF": ref_text(chrome_context_refs[job])}
    result[jobs[0]]["C17_AUX_GIT_SNAPSHOT_REF"] = git
    return result


def web_environment(root: Path, *, data_dir: Path | None = None) -> dict[str, str]:
    p = paths(root)
    chosen = data_dir or p["data"]
    need(chosen in (p["data"], p["test_data"]), "Profil web non jetable/fermé")
    return {"PATH": str(NODE_ROOT / "bin") + ":/usr/bin:/bin:/usr/sbin:/sbin:/opt/homebrew/bin",
        "HOME": str(p["home"]), "CFFIXED_USER_HOME": str(p["home"]),
        "TMPDIR": str(p["profile"]), "LANG": "en_US.UTF-8", "LC_ALL": "en_US.UTF-8",
        "PYTHONPATH": str(p["overlay"] / "runtime") + ":" + str(QA_SOURCE) + ":" + str(QA_SOURCE / "src/backend"),
        "PYTHONUNBUFFERED": "1", "PYTHONDONTWRITEBYTECODE": "1", "PYTHONNOUSERSITE": "1",
        "THERESE_DATA_DIR": str(chosen), "DATA_DIR": str(chosen),
        "DB_PATH": str(chosen / "therese.db"), "QDRANT_PATH": str(chosen / "qdrant"),
        "PORT": "17593", "HOST": "127.0.0.1", "VITE_THERESE_BACKEND_PORT": "17593",
        "PYTHON_KEYRING_BACKEND": "keyring.backends.null.Keyring", "THERESE_DB_PLAINTEXT": "1",
        "THERESE_SKIP_SERVICES": "1", "HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1",
        "THERESE_SONDE_CATALOGUE": "off", "OLLAMA_BASE_URL": "http://127.0.0.1:9",
        "PLAYWRIGHT_BROWSERS_PATH": str(p["playwright_unused"])}


def top_environment(root: Path, git_ref: dict, *, sql: bool, owner_uid: int) -> dict[str, str]:
    p = paths(root)
    need(type(owner_uid) is int and owner_uid >= 0, "UID owner physique absent")
    env = {"__CF_USER_TEXT_ENCODING": f"0x{owner_uid:X}:0:0",
        "PATH": str(NODE_ROOT / "bin") + ":/usr/bin:/bin:/usr/sbin:/sbin",
        "HOME": str(p["home"]), "CFFIXED_USER_HOME": str(p["home"]),
        "TMPDIR": str(p["tmp"]), "LANG": "en_US.UTF-8", "LC_ALL": "en_US.UTF-8",
        "PYTHONNOUSERSITE": "1", "PYTHONDONTWRITEBYTECODE": "1", "PYTHONUNBUFFERED": "1",
        "PYTHONPATH": str(QA_SOURCE) + ":" + str(QA_SOURCE / "src/backend"),
        "HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1",
        "PYTHON_KEYRING_BACKEND": "keyring.backends.null.Keyring",
        "THERESE_SKIP_SERVICES": "1", "THERESE_SONDE_CATALOGUE": "off",
        "OLLAMA_BASE_URL": "http://127.0.0.1:9",
        "THERESE_DATA_DIR": str(p["data"]), "DATA_DIR": str(p["data"]),
        "C17_AUX_GIT_SNAPSHOT_REF": ref_text(git_ref)}
    if sql:
        env |= {"C16_ACTOR": "/root", "C16_ROUND_ID": p["root"].name,
                "C16_REVIEWED_SHA256": SQL_CONTRACT_SHA}
    else:
        env |= {"PORT": "17593", "HOST": "127.0.0.1",
                "VITE_THERESE_BACKEND_PORT": "17593", "THERESE_DB_PLAINTEXT": "1",
                "DB_PATH": str(p["data"] / "therese.db"),
                "QDRANT_PATH": str(p["data"] / "qdrant"),
                "PLAYWRIGHT_BROWSERS_PATH": str(p["playwright_unused"])}
    return env


def sql_child_environment(root: Path, group: str) -> dict[str, str]:
    need(group in ("B1753", "B1760", "B1753-power"), "Groupe SQL hors table")
    alloc = contract.expected_allocations(root)
    label = "sql-" + group.lower()
    profile, out = Path(alloc[label + "-profile"]), Path(alloc[label + "-output"])
    copy = profile / "checkout"
    selectors = (["tests/test_actions_traitement.py::TestLaRouteHistoriqueEstCanonique::test_delete_passe_par_le_traitement_durable",
                  ".c16_instruments/test_b1753_frontiere_suivante.py::test_frontiere_suivante_ne_recoit_aucune_tache_du_temoin"]
                 if group != "B1760" else ["tests/test_b1760_echeance_mentions.py"])
    return {"PATH": "/usr/bin:/bin:/usr/sbin:/sbin:/opt/homebrew/bin",
        "HOME": str(profile / "home"), "TMPDIR": str(profile / "tmp"), "LANG": "en_US.UTF-8",
        "THERESE_ENV": "test", "THERESE_DATA_DIR": str(profile / "data"),
        "THERESE_SKIP_SERVICES": "1", "THERESE_DB_KEY": "ad" * 32,
        "PYTHON_KEYRING_BACKEND": "keyring.backends.null.Keyring",
        "PYTHONDONTWRITEBYTECODE": "1", "HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1",
        "OLLAMA_BASE_URL": "http://127.0.0.1:9", "THERESE_SONDE_CATALOGUE": "off",
        "C16_COPY": str(copy), "C16_GROUP": "B1753" if group == "B1753-power" else group,
        "C16_ACTOR": "/root", "C16_ROUND_ID": root.name,
        "C16_EXECUTION_HEAD": HEAD, "C16_SELECTORS": json.dumps(selectors),
        "C16_XML": str(out / "harness.xml"),
        "C16_MODULE_RECEIPT": str(out / "modules-executes.json"),
        "ENQUETE_REPO": str(copy), "ENQUETE_TRACE": str(out / "frontieres.jsonl"),
        "ENQUETE_MODE": "controle", "B1760_PREUVES": str(out / "exports")}


def row(root: Path, context: dict, label: str, *, argv: list[str], cwd: Path,
        environment: dict[str, str], stdout: Path, stderr: Path, source_refs: list[dict]) -> dict:
    requester, index, mode, bound = contract.SITE_SPECS[label]
    name = "rpc-" + label
    return {"schema": "c17-g5-root-rpc-descriptor-v1", "id": name,
        "stage_name": name, "context_id": context["context_id"],
        "requester_id": requester, "logical_parent_id": requester, "index": index,
        "nonce": hashlib.sha256((root.name + ":" + label).encode()).hexdigest()[:32],
        "source_refs": source_refs, "argv": argv, "cwd": str(cwd),
        "environment": environment, "stdout_path": str(stdout), "stderr_path": str(stderr),
        "timeout_seconds": bound, "mode": mode, "label": label, "role": "stage-" + name}


def descriptors(root: Path, context: dict, envelopes: dict, *,
                metadata_by_job: dict[str, dict[str, str]],
                source_refs: list[dict]) -> list[dict]:
    """Reconstruit les quinze arguments écrits par les cinq wrappers, sans les lancer."""
    p, alloc = paths(root), contract.expected_allocations(root)
    need(set(metadata_by_job) == {
        "rpc-all-test_runner", "rpc-all-logs",
        "rpc-all-runtime_ui-visual_capture-network_capture", "rpc-all-screen_coverage",
        "rpc-screen-negative", "rpc-screen-positive-visual",
        "rpc-screen-positive-network", "rpc-screen-restored"},
        "Métadonnées auxiliaires huit jobs hors table")
    base = web_environment(root)
    def with_metadata(label: str, env: dict[str, str]) -> dict[str, str]:
        additions = metadata_by_job.get("rpc-" + label, {})
        need(type(additions) is dict and all(type(k) is str and type(v) is str
             and k not in env for k, v in additions.items()),
             "Métadonnées auxiliaires non exactes pour " + label)
        return dict(env, **additions)
    result = []
    all_out = Path(alloc["all"])
    all_commands = {
        "all-test_runner": [str(QA_PYTHON), str(p["overlay"] / "runtime/calibrate-test-runner.py")],
        "all-logs": [str(QA_PYTHON), str(p["runtime"] / "calibrate-logs.py")],
        "all-runtime_ui-visual_capture-network_capture": [str(NODE), str(p["overlay"] / "runtime/calibrate-browser.mjs")],
        "all-screen_coverage": [str(QA_PYTHON), str(p["overlay"] / "runtime/calibrate-screen.py")],
    }
    for label, argv in all_commands.items():
        name = label[4:]
        env = with_metadata(label, base)
        if label in ("all-test_runner", "all-screen_coverage"):
            env["C17_RPC_CONTEXT_REF"] = ref_text(envelopes["rpc-" + label])
        result.append(row(root, context, label, argv=argv, cwd=p["profile"],
            environment=env, stdout=all_out / (name + ".stdout"),
            stderr=all_out / (name + ".stderr"), source_refs=source_refs))
    test_out = Path(alloc["test-runner"])
    for tool in ("pytest", "vitest"):
        for variant in ("positive", "negative"):
            label = "test-" + tool + "-" + variant
            xml = test_out / (tool + "-" + variant + ".xml")
            env = web_environment(root, data_dir=p["test_data"])
            if variant == "positive":
                env["C17_TEST_RUNNER_DEFECT"] = "1"
            if tool == "pytest":
                argv = [str(QA_PYTHON), "-m", "pytest", "--noconftest",
                        "--rootdir=" + str(test_out), str(test_out / "test_temoin_c17.py"), "--junitxml=" + str(xml),
                        "-p", "no:cacheprovider"]
            else:
                argv = [str(FRONT / "node_modules/.bin/vitest"), "run", "--config",
                        str(test_out / "vitest.runtime.config.mjs"), "--reporter=junit",
                        "--outputFile=" + str(xml)]
            result.append(row(root, context, label, argv=argv,
                cwd=QA_SOURCE if tool == "pytest" else FRONT, environment=env,
                stdout=test_out / (tool + "-" + variant + ".stdout"),
                stderr=test_out / (tool + "-" + variant + ".stderr"), source_refs=source_refs))
    screen_out = Path(alloc["screen"])
    for label in ("screen-negative", "screen-positive-visual", "screen-positive-network", "screen-restored"):
        short = label.removeprefix("screen-")
        env = with_metadata(label, base)
        if short in ("positive-visual", "positive-network"):
            env["C17_SCREEN_WITNESS"] = short.removeprefix("positive-")
        argv = [str(NODE), str(screen_out / "couverture-ecran-calibree.mjs"),
                "--base", "http://127.0.0.1:5173/?port=17593",
                "--expected-data-dir", str(p["data"]), "--sortie", str(screen_out / short),
                "--ecrans", "accueil", "--largeurs", "1440", "--themes", "light"]
        result.append(row(root, context, label, argv=argv, cwd=QA_SOURCE,
            environment=env, stdout=screen_out / (short + ".stdout"),
            stderr=screen_out / (short + ".stderr"), source_refs=source_refs))
    for group in ("B1753", "B1760", "B1753-power"):
        label = "sql-" + group.lower()
        profile = Path(alloc[label + "-profile"])
        out = Path(alloc[label + "-output"])
        result.append(row(root, context, label,
            argv=[str(QA_PYTHON), str(out / "bootstrap-prive.py")],
            cwd=profile / "checkout", environment=sql_child_environment(root, group),
            stdout=out / "harness.stdout", stderr=out / "harness.stderr",
            source_refs=source_refs))
    need([item["label"] for item in result] == list(contract.SITE_SPECS),
         "Ordre/quantité des quinze RPC changé")
    return result


def direct_commands(root: Path, envelopes: dict, *, git_ref: dict,
                    owner_uid: int) -> dict[str, dict]:
    p, alloc = paths(root), contract.expected_allocations(root)
    web = top_environment(root, git_ref, sql=False, owner_uid=owner_uid)
    sql = top_environment(root, git_ref, sql=True, owner_uid=owner_uid)
    commands = {}
    def insert(name: str, argv: list[str], mode: str, timeout: int, env: dict,
               cwd: Path, stdout: Path, stderr: Path, combined: bool = False) -> None:
        commands[name] = {"argv": argv, "role": ("persistent-" if combined else "stage-") + name,
            "mode": mode, "timeout_seconds": timeout, "env": env, "cwd": str(cwd),
            "stdout_path": str(stdout), "stderr_path": str(stderr),
            "combine_stderr": combined, "derived_deadline": "start_monotonic_plus_exact_timeout"}
    insert("backend", [str(QA_PYTHON), "-m", "uvicorn",
        "tests.couverture.backend_offline:create_app", "--factory", "--loop", "asyncio",
        "--host", "127.0.0.1", "--port", "17593"], "web", 50, dict(web), p["profile"],
        p["runtime"] / "backend-runtime.log", p["runtime"] / "backend-runtime.log", True)
    insert("vite", [str(FRONT / "node_modules/.bin/vite"), "--host", "127.0.0.1",
        "--port", "5173", "--strictPort", "--config", str(p["vite_config"]),
        "--configLoader", "native"], "web", 50, dict(web), FRONT,
        p["runtime"] / "vite-runtime.log", p["runtime"] / "vite-runtime.log", True)
    cal_env = dict(web, C17_RPC_CONTEXT_REF=ref_text(envelopes["calibrate"]))
    insert("calibrate", [str(QA_PYTHON), str(p["overlay"] / "runtime/calibrate-all.py")],
        "web", 1200, cal_env, p["profile"], p["root"] / "output/calibrate.stdout",
        p["root"] / "output/calibrate.stderr")
    for group in ("B1753", "B1760", "B1753-power"):
        label = "sql-" + group.lower()
        script = ("preparer-harness-b1753-power.py" if group == "B1753-power"
                  else "preparer-et-executer-harness-root-stack.py")
        args_group = "B1753" if group == "B1753-power" else group
        argv = [str(QA_PYTHON), str(p["overlay"] / "complements/instruments" / script),
                "--group", args_group, "--actor", "/root", "--round-id", root.name,
                "--out", alloc[label + "-output"],
                "--reviewed-contract-sha", SQL_CONTRACT_SHA]
        env = dict(sql, C17_RPC_CONTEXT_REF=ref_text(envelopes[group]))
        insert(group, argv, "sql", 360, env, root,
               root / "output" / (group + ".stdout"),
               root / "output" / (group + ".stderr"))
    need(set(commands) == set(DIRECT_ORDER), "Six processus directs hors table")
    return commands


def rpc_commands(items: list[dict]) -> dict[str, dict]:
    commands = {}
    for item in items:
        commands[item["id"]] = {"argv": item["argv"], "role": item["role"],
            "mode": item["mode"], "timeout_seconds": item["timeout_seconds"],
            "env": item["environment"], "cwd": item["cwd"],
            "stdout_path": item["stdout_path"], "stderr_path": item["stderr_path"],
            "combine_stderr": False, "derived_deadline": "start_monotonic_plus_exact_timeout",
            "logical_parent_id": item["logical_parent_id"]}
    need(len(commands) == 15, "Quinze commandes RPC non distinctes")
    return commands


def prepared_stack(root: Path, *, prepared_at: str) -> dict:
    p = paths(root)
    return {"cycle": 17, "status": "prepared", "prepared_at": prepared_at,
        "repo": str(QA_SOURCE), "head_at_preparation": HEAD,
        "temporary_root": str(p["profile"]), "home": str(p["home"]),
        "data_dir": str(p["data"]),
        "backend": {"host": "127.0.0.1", "port": 17593,
                    "log": str(p["runtime"] / "backend-runtime.log")},
        "vite": {"host": "127.0.0.1", "port": 5173,
                 "log": str(p["runtime"] / "vite-runtime.log"),
                 "config": str(p["vite_config"]), "cache_dir": str(p["vite_cache"])}}


def render_vite_configs(root: Path, canonical_ts: str) -> dict[str, str]:
    """Deux configs QA dérivées de l'octet source Git frais, sans lancer Vite."""
    p = paths(root)
    need(type(canonical_ts) is str and canonical_ts, "Config Vite Git absente")
    vite = FRONT / "node_modules/vite/dist/node/index.js"
    react = FRONT / "node_modules/@vitejs/plugin-react/dist/index.js"
    tailwind = FRONT / "node_modules/@tailwindcss/vite/dist/index.mjs"
    canonical = canonical_ts
    for before, after in (
        ("import { defineConfig } from 'vite';", "import { defineConfig } from " + json.dumps(str(vite)) + ";"),
        ("import react from '@vitejs/plugin-react';", "import react from " + json.dumps(str(react)) + ";"),
        ("import tailwindcss from '@tailwindcss/vite';", "import tailwindcss from " + json.dumps(str(tailwind)) + ";"),
        ("resolve(__dirname, 'src')", json.dumps(str(FRONT / "src"))),
    ):
        need(canonical.count(before) == 1, "Ancre Vite canonique différente : " + before)
        canonical = canonical.replace(before, after, 1)
    runtime = f'''import {{ defineConfig, mergeConfig }} from {json.dumps(str(vite))};
import canonical from {json.dumps(str(p["vite_canonical"]))};
export default defineConfig(async () => {{
  const configEnv = {{command: 'serve', mode: 'development'}};
  const canonicalConfig = await Promise.resolve(typeof canonical === 'function' ? canonical(configEnv) : canonical);
  if (!canonicalConfig) throw new Error('Configuration Vite canonique absente');
  return mergeConfig(canonicalConfig, {{
    root: {json.dumps(str(FRONT))}, envDir: {json.dumps(str(p["profile"]))}, cacheDir: {json.dumps(str(p["vite_cache"]))},
    server: {{host: '127.0.0.1', port: 5173, strictPort: true,
      fs: {{allow: [{json.dumps(str(QA_SOURCE))}, {json.dumps(str((FRONT / "node_modules").resolve()))}]}}}}
  }});
}});
'''
    return {str(p["vite_canonical"]): canonical,
            str(p["vite_config"]): runtime}


def build_plan(protocol, root: Path, *, owner_identity: dict,
               deadline_monotonic: float, source_refs: list[dict],
               git_ref: dict, chrome_context_refs: dict[str, dict]) -> dict:
    """Table pure : owner physique fourni, aucun PID ou GO fabriqué ici."""
    root = exact_root(root)
    metadata = auxiliary_metadata(root, git_ref=git_ref,
                                  chrome_context_refs=chrome_context_refs)
    context_id = hashlib.sha256((root.name + ":context").encode()).hexdigest()[:32]
    draft = contract.draft_context_envelopes(protocol, root=root, scope="WRAPPER_CANARY",
        actor="/root", round_id=root.name, head=HEAD, context_id=context_id,
        owner_identity=owner_identity, deadline_monotonic=deadline_monotonic,
        allocations=contract.expected_allocations(root))
    items = descriptors(root, draft["context"],
        {name: row["ref"] for name, row in draft["envelopes"].items()},
        metadata_by_job=metadata, source_refs=source_refs)
    commands = direct_commands(root,
        {name: row["ref"] for name, row in draft["envelopes"].items()},
        git_ref=git_ref, owner_uid=owner_identity["uid"])
    sealed = contract.seal_plan(protocol, draft, items,
        {name: commands[name] for name in contract.DIRECT_PARENTS})
    all_commands = dict(commands, **rpc_commands(items))
    need(len(all_commands) == 21, "Table G1 21 commandes incomplète")
    return {"sealed": sealed, "descriptors": items, "commands": all_commands,
            "metadata_by_job": metadata}
