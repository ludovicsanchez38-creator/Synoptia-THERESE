"""Bind a closed G5 descriptor to the real G1 Session lifecycle.

The dispatcher authenticates a connected requester separately from file
content.  This adapter never treats a request's argv as authority: the exact
descriptor and command were emitted in the root binding before parent launch.
It starts each child through Session.start/gate and polls it without calling
Session.wait recursively.  CAPABILITIES and runtime admission remain closed
until independent OS qualification.
"""
from __future__ import annotations

import os
from pathlib import Path
import stat
import time
from typing import Any


IDENTITY_FIELDS = ("pid", "start_sec", "start_usec", "ppid", "uid", "pgid")
DESCRIPTOR_SCHEMA = "c17-g5-root-rpc-descriptor-v1"
CLEANUP_SCHEMA = "c17-g1-rpc-child-cleanup-v1"


class RpcAdapterError(RuntimeError):
    """Uncertain instrumentation, never a product failure."""


def need(condition: bool, message: str) -> None:
    if not condition:
        raise RpcAdapterError(message)


def same_identity(left: dict[str, Any], right: dict[str, Any]) -> bool:
    return (isinstance(left, dict) and isinstance(right, dict)
            and all(left.get(field) == right.get(field) for field in IDENTITY_FIELDS))


class SessionRpcAdapter:
    def __init__(self, session: Any, api: dict[str, Any], *, protocol: Any,
                 context: dict[str, Any], enrollments: dict[str, dict[str, Any]]) -> None:
        self.session = session
        self.api = api
        self.root: Path = session.root
        self.protocol = protocol
        self.context = context
        self.enrollments = enrollments
        try:
            protocol.validate_context(context, self.root)
        except Exception as error:
            raise RpcAdapterError("Contexte RPC root non exact") from error
        self._tokens: dict[str, dict[str, Any]] = {}
        self._seen_nonces: set[str] = set()
        self._observed: dict[str, dict[str, Any]] = {}

    def _live_requester(self, requester_id: str, observed_requester: dict[str, Any]) -> dict[str, Any]:
        session = self.session
        need(self.api["_ACTIVE_SESSION"] is session and not session.closed,
             "RPC hors Session G1 active")
        handle = session.handles.get(requester_id)
        need(isinstance(handle, dict) and handle.get("role") == "stage-" + requester_id
             and session._released_birth(handle) and handle["process"].poll() is None,
             "Demandeur RPC non lancé/vivant")
        session.ledger.attribute()
        canonical = handle["root_identity"]
        current = session.ledger.info(canonical["pid"])
        need(isinstance(observed_requester, dict) and same_identity(canonical, observed_requester)
             and same_identity(canonical, current) and current.get("status") != 5
             and session.ledger.unchanged(canonical, current),
             "Birth demandeur hors payload absente/changée")
        need(session.ledger.records.get(session.ledger.key(canonical)) == canonical,
             "Birth demandeur RPC non canonique")
        return canonical

    def observe_requester(self, enrollment: dict[str, Any], *,
                          observed_requester: dict[str, Any] | None) -> dict[str, Any]:
        """Compare an external peer observation, never a PID copied from JSON."""
        need(isinstance(enrollment, dict) and isinstance(enrollment.get("requester_id"), str),
             "Enrôlement RPC absent")
        requester_id = enrollment["requester_id"]
        need(requester_id in self.api["RPC_REQUESTERS"] and isinstance(observed_requester, dict),
             "Observation OS demandeur absente")
        need(self.enrollments.get(requester_id) == enrollment,
             "Enrôlement RPC différent de la table root")
        canonical = self._live_requester(requester_id, observed_requester)
        need(enrollment.get("schema") == "c17-g5-root-rpc-enrollment-v1"
             and enrollment.get("publication_protocol") == self.protocol.PROTOCOL
             and enrollment.get("actor") == self.context["actor"]
             and enrollment.get("round_id") == self.context["round_id"]
             and enrollment.get("head") == self.context["head"]
             and enrollment.get("context_id") == self.context["context_id"]
             and isinstance(enrollment.get("identity"), dict)
             and same_identity(enrollment["identity"], canonical)
             and enrollment.get("logical_parent_id") == requester_id
             and enrollment.get("parent_stage") == requester_id
             and isinstance(enrollment.get("source_refs"), list)
             and isinstance(enrollment.get("gate_ref"), dict),
             "Enrôlement RPC non lié à la birth/parent exacts")
        # Recheck the referenced parent gate/source without inferring that
        # the JSON author is the connected peer.
        self._check_refs(enrollment["source_refs"])
        gate_ref = enrollment["gate_ref"]
        handle = self.session.handles[requester_id]
        need(handle.get("gate_ref") == gate_ref
             and self.api["reference"](Path(gate_ref["path"])) == gate_ref
             and self.api["read_published_json"](self.root, Path(gate_ref["path"]))["stage"] == requester_id,
             "Gate parent RPC changé après enrollment")
        path = self.root / "session-rpc" / "enrollment" / (requester_id + ".json")
        need(enrollment.get("enrollment_path") == str(path)
             and self.api["read_published_json"](self.root, path) == enrollment,
             "Enrollment publié RPC changé")
        self._observed[requester_id] = dict(observed_requester)
        return {"identity": dict(canonical), "live": True, "enrolled": True,
                "owning_session_active": True}

    def _check_refs(self, refs: list[dict[str, Any]]) -> None:
        need(isinstance(refs, list) and bool(refs), "Sources RPC non référencées")
        for ref in refs:
            need(isinstance(ref, dict) and isinstance(ref.get("path"), str),
                 "Référence source RPC invalide")
            path = Path(ref["path"])
            source = (self.session.product_source_root if self.session.round_name == 'WRAPPER_CANARY'
                      else self.api['SOURCE'])
            need(path.is_absolute() and path.resolve(strict=True) == path
                 and not path.is_symlink() and any(path.is_relative_to(base) for base in
                 (self.root, source, self.api["HERE"])),
                 "Source RPC hors QA exacte")
            if self.session.round_name == "RPC_CANARY":
                need(path.is_relative_to(self.root), "Source hors QA dans canari RPC")
            info = path.stat()
            need(stat.S_ISREG(info.st_mode) and info.st_uid == os.getuid()
                 and 0 < info.st_size <= 16_000_000
                 and self.api["reference"](path) == ref,
                 "Source RPC SHA/owner/taille différente")

    def _command_spec(self, descriptor: dict[str, Any]) -> dict[str, Any]:
        return {"argv": descriptor["argv"], "role": descriptor["role"],
                "mode": descriptor["mode"], "timeout_seconds": descriptor["timeout_seconds"],
                "env": descriptor["environment"], "cwd": descriptor["cwd"],
                "stdout_path": descriptor["stdout_path"], "stderr_path": descriptor["stderr_path"],
                "combine_stderr": False, "derived_deadline": "start_monotonic_plus_exact_timeout",
                "logical_parent_id": descriptor["logical_parent_id"]}

    def _close_auxiliary_before_prelaunch_refusal(self, token: str) -> None:
        """Aucun enfant feuille ne signifie pas aucun Chrome déjà enregistré."""
        slot = self._tokens[token]
        if self.session.round_name != 'WRAPPER_CANARY' or slot['name'] not in self.protocol.CHROME_JOBS:
            return
        name = 'aux-chrome-' + slot['name']
        handle = self.session.handles.get(name)
        if handle is None:
            return
        slot['auxiliary_entry'] = handle  # conservé même si finish/save refuse.
        try:
            need(handle.get('name') == name and handle.get('role') == 'auxiliary-' + name,
                 'Auxiliaire prélaunch autre handle/rôle')
            self.session.finish({handle['role']})
            ref = handle.get('terminal_receipt_ref')
            raw = self.api['checked_json_ref'](ref, self.root)
            need(raw.get('termination_proved') is True and raw.get('output_archived') is True
                 and raw.get('output_archive_errors') == [] and raw.get('cleanup_deadline_met') is True
                 and self.protocol.finite(raw.get('cleanup_elapsed_seconds'))
                 and 0 <= raw['cleanup_elapsed_seconds'] <= self.protocol.CLEANUP_SECONDS
                 and raw.get('cleanup', {}).get('clean') is True
                 and raw['cleanup'].get('remaining_attributed') == raw['cleanup'].get('ambiguities') == raw['cleanup'].get('errors') == [],
                 'Auxiliaire prélaunch non fermé physiquement')
            for channel in ('stdout', 'stderr'):
                self.protocol.read_reference(raw[channel], root=self.root)
            slot['auxiliary_prelaunch_cleanup_ref'] = ref
        except BaseException as error:
            raise self.protocol.RpcCleanupUncertain(
                'Feuille non lancée mais Chrome enregistré non fermé', token=token) from error

    def begin(self, descriptor: dict[str, Any], request_ref: dict[str, Any]) -> str:
        """Start only a root-prebound descriptor; return without waiting for child."""
        need(isinstance(descriptor, dict) and descriptor.get("schema") == DESCRIPTOR_SCHEMA,
             "Descriptor RPC sans schéma root fermé")
        try:
            self.protocol.validate_descriptor(descriptor, self.context, self.root)
        except Exception as error:
            raise RpcAdapterError("Descriptor RPC invalide selon le protocole fermé") from error
        name = descriptor.get("stage_name")
        sites = self.api["RPC_CHILDREN"]
        need(isinstance(name, str) and name in sites and descriptor.get("id") == name,
             "Site RPC hors quinze lignes fermées")
        requester, bound, mode = sites[name]
        need(descriptor.get("requester_id") == requester
             and descriptor.get("logical_parent_id") == requester
             and descriptor.get("role") == "stage-" + name
             and descriptor.get("timeout_seconds") == bound
             and descriptor.get("mode") == mode,
             "Descriptor RPC parent/borne/mode différent")
        nonce = descriptor.get("nonce")
        need(isinstance(nonce, str) and len(nonce) == 32
             and all(char in "0123456789abcdef" for char in nonce)
             and nonce not in self._seen_nonces and name not in self.session.handles,
             "Nonce ou child RPC rejoué")
        table = self.session.binding.get("rpc_descriptors")
        need(isinstance(table, dict) and set(table) == set(sites)
             and table.get(name) == descriptor
             and self.session.binding.get("commands", {}).get(name) == self._command_spec(descriptor),
             "Descriptor/commande RPC non préémis par root")
        need(requester in self._observed, "Demandeur RPC non observé hors payload")
        self._live_requester(requester, self._observed[requester])
        need(isinstance(descriptor.get("source_refs"), list), "Sources descriptor RPC absentes")
        self.session.validate_sources()
        self._check_refs(descriptor["source_refs"])
        need(isinstance(request_ref, dict) and isinstance(request_ref.get("path"), str),
             "Référence requête RPC absente")
        request_path = Path(request_ref["path"])
        need(request_path == self.protocol.event_path(self.root, descriptor, "request")
             and self.api["reference"](request_path) == request_ref,
             "Requête RPC hors transport/pin")
        request = self.api["read_published_json"](self.root, request_path)
        try:
            self.protocol.validate_request(request, descriptor, self.context,
                                           self.enrollments[requester], time.monotonic())
            self.protocol.fresh_budget(time.monotonic(), descriptor, self.context,
                                       self.enrollments[requester])
        except Exception as error:
            raise RpcAdapterError("Requête/budget RPC non exacts selon protocole fermé") from error
        token = name + ":" + nonce
        self._seen_nonces.add(nonce)
        self._tokens[token] = {"name": name, "requester_id": requester,
                               "logical_parent_id": requester, "nonce": nonce,
                               "state": "starting", "descriptor": descriptor,
                               "request_ref": request_ref, "entry": None, "terminal": None}
        try:
            entry = self.session.start(name, "stage-" + name, list(descriptor["argv"]),
                mode=mode, timeout=bound, env=dict(descriptor["environment"]),
                cwd=Path(descriptor["cwd"]), stdout_path=Path(descriptor["stdout_path"]),
                stderr_path=Path(descriptor["stderr_path"]), combine_stderr=False,
                logical_parent_id=requester, rpc_request_ref=request_ref,
                rpc_observed_requester=dict(self._observed[requester]))
            self._tokens[token]["entry"] = entry
            self._tokens[token]["state"] = "running"
        except BaseException as launch_error:
            self._tokens[token]["exception_diagnostic"] = self.protocol.exception_diagnostic(launch_error)
            self.session.log_stability_tainted = True
            self._tokens[token]["state"] = "launch_error"
            recorded = self.session.handles.get(name)
            if recorded is None:
                # Session.start records a handle before Popen.  No handle is
                # therefore a real pre-Popen refusal, not an inferred PID.
                self._close_auxiliary_before_prelaunch_refusal(token)
                raise self.protocol.RpcPrelaunchRefused(
                    "RPC refusé avant enregistrement de tout handle") from launch_error
            self._tokens[token]["entry"] = recorded
            if recorded.get("process") is None or recorded.get("root_identity") is None:
                try:
                    self.session.finish({"stage-" + name})
                except BaseException:
                    pass  # preserve the first raw failure and block ACK.
                raise self.protocol.RpcCleanupUncertain(
                    "RPC handle enregistré mais birth/cleanup non prouvés", token=token) from launch_error
            try:
                self._finish(self._tokens[token], terminal_state="error:launch_failure")
            except BaseException as cleanup_error:
                raise self.protocol.RpcCleanupUncertain(
                    "RPC child lancé, nettoyage exact encore incertain", token=token) from cleanup_error
            return token  # dispatcher observes a terminal error with real receipts before ACK.
        return token

    def _finish(self, slot: dict[str, Any], *, terminal_state: str) -> dict[str, Any]:
        entry = slot["entry"]
        need(entry is not None, "RPC sans handle lancé")
        # A helper such as rpc-all-test_runner is itself a requester.  Its
        # physical parent must not be finalized while any logical child is
        # still alive, even if its own process has already exited.
        if entry["name"] in self.api["RPC_REQUESTERS"]:
            dispatcher = self.session._rpc_dispatcher
            need(dispatcher is not None, "Dispatcher absent pour fermeture helper RPC")
            if not dispatcher.parent_quiescent(entry["name"]):
                self.session.log_stability_tainted = True
                dispatcher.abort_parent(entry["name"], "requester_exited_with_active_descendants")
                need(all(child["terminal"] is not None for child in self._tokens.values()
                         if child["requester_id"] == entry["name"]),
                     "Descendants RPC non nettoyés avant fermeture du helper")
                terminal_state = "error:requester_exited_with_active_descendants"
        if terminal_state != "complete":
            self.session.log_stability_tainted = True
            if terminal_state == "timeout":
                entry["timed_out"] = True
            else:
                entry["interruption"] = {"type": "rpc_protocol_abort", "message": terminal_state}
        self.session.finish({entry["role"]})  # only this direct child and its attributed descendants.
        receipt_ref = entry.get("terminal_receipt_ref")
        need(isinstance(receipt_ref, dict), "RPC sans reçu terminal G1")
        receipt = self.api["checked_json_ref"](receipt_ref, self.root)
        cleanup = receipt.get("cleanup")
        need(isinstance(cleanup, dict), "RPC sans nettoyage réel G1")
        stdout_ref, stderr_ref = receipt.get("stdout"), receipt.get("stderr")
        need(isinstance(stdout_ref, dict) and isinstance(stderr_ref, dict),
             "RPC canaux bruts non référencés")
        clean = (cleanup.get("clean") is True and cleanup.get("remaining_attributed") == []
                 and cleanup.get("ambiguities") == [] and cleanup.get("errors") == []
                 and receipt.get("termination_proved") is True
                 and receipt.get("output_archived") is True
                 and receipt.get("output_archive_errors") == [])
        normal = (terminal_state == "complete" and clean
                  and receipt.get("log_stability_proved") is True
                  and cleanup.get("signals") == [] and not receipt.get("timed_out")
                  and receipt.get("interruption") is None)
        if terminal_state == "complete" and not normal:
            self.session.log_stability_tainted = True
        deadline_met = receipt.get("cleanup_deadline_met") is True
        state = ("complete" if normal else "timeout" if terminal_state == "timeout"
                 and clean and deadline_met else "error")
        auxiliary_ref = None
        if self.session.round_name == 'WRAPPER_CANARY' and slot['name'] in self.protocol.CHROME_JOBS:
            proof = self.session.checked_auxiliary_terminal(slot['name'], receipt_ref)
            need(isinstance(proof, dict) and proof.get('reference') == entry.get('auxiliary_terminal_ref')
                 and proof.get('leaf_exit_code') == receipt.get('exit_code'), 'Auxiliary root handle join absent')
            auxiliary_ref = proof['reference']
            self.protocol.validate_auxiliary_terminal(auxiliary_ref, slot['descriptor'], self.root,
                self.context, receipt_ref, normal=normal, binding_sha256=self.session.binding_ref['sha256'])
        summary = {"schema": CLEANUP_SCHEMA, "stage": slot["name"],
            "requester_id": slot["requester_id"], "logical_parent_id": slot["logical_parent_id"],
            "child_identity": dict(entry["root_identity"]), "receipt_ref": receipt_ref,
            "request_ref": slot["request_ref"], "exit_code": receipt.get("exit_code"),
            "state": state, "clean": clean, "termination_proved": receipt.get("termination_proved") is True,
            "log_stability_proved": normal, "remaining_attributed": cleanup.get("remaining_attributed"),
            "ambiguities": cleanup.get("ambiguities"), "errors": cleanup.get("errors"),
            "signals": cleanup.get("signals"),
            "cleanup_elapsed_seconds": receipt.get("cleanup_elapsed_seconds"),
            "cleanup_deadline_met": deadline_met,
            "stdout_ref": stdout_ref, "stderr_ref": stderr_ref,
            "tainted": self.session.log_stability_tainted or state != "complete"}
        diagnostic = self.protocol.validated_exception_diagnostic(slot.get("exception_diagnostic"))
        if diagnostic is not None:
            summary["exception_diagnostic"] = diagnostic
        if auxiliary_ref is not None:
            summary['auxiliary_terminal_ref'] = auxiliary_ref
        cleanup_path = entry["folder"] / "rpc-cleanup.json"
        self.api["save"](self.root, cleanup_path, summary)
        result = {"state": state, "child_identity": dict(entry["root_identity"]),
            "exit_code": receipt.get("exit_code"), "receipt_ref": receipt_ref,
            "cleanup_ref": self.api["reference"](cleanup_path), "stdout_ref": stdout_ref,
            "stderr_ref": stderr_ref, "clean": clean,
            "termination_proved": receipt.get("termination_proved") is True,
            "log_stability_proved": normal, "signals": cleanup.get("signals"),
            "tainted": summary["tainted"], "cleanup_deadline_met": summary["cleanup_deadline_met"]}
        if diagnostic is not None:
            result["exception_diagnostic"] = diagnostic
        if auxiliary_ref is not None:
            result['auxiliary_terminal_ref'] = auxiliary_ref
        slot["terminal"] = result
        slot["state"] = state
        return result

    def poll(self, token: str) -> dict[str, Any]:
        slot = self._tokens.get(token)
        need(isinstance(slot, dict), "Token RPC inconnu")
        if slot["terminal"] is not None:
            return dict(slot["terminal"])
        entry = slot["entry"]
        need(isinstance(entry, dict), "Child RPC non lancé")
        self.session.ledger.attribute()
        if entry["process"].poll() is not None:
            return self._finish(slot, terminal_state="complete")
        if time.monotonic() >= entry["outer_deadline_monotonic"]:
            return self._finish(slot, terminal_state="timeout")
        return {"state": "pending"}

    def abort(self, token: str, reason: str) -> dict[str, Any]:
        slot = self._tokens.get(token)
        need(isinstance(slot, dict) and isinstance(reason, str) and reason,
             "Abort RPC sans token/reason exact")
        if slot["terminal"] is not None:
            return dict(slot["terminal"])
        self.session.log_stability_tainted = True
        if slot["entry"] is None:
            slot["state"] = "error"
            result = {"state": "error", "tainted": True, "reason": reason,
                      "receipt_ref": None, "cleanup_ref": None}
            slot["terminal"] = result
            return result
        return self._finish(slot, terminal_state="error:" + reason)
