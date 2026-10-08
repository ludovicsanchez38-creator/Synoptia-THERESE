"""Dispatch root non récursif : adapter injecté, jamais Session.wait/Popen ici."""
from __future__ import annotations

import json
from pathlib import Path
import time

import rpc_protocol as p


class RpcDispatcher:
    def __init__(self, root, context, descriptors, enrollments, adapter, *, clock=time.monotonic,
                 auth_observer=None):
        self.root = p.canonical_root(root)
        p.validate_context(context, self.root)
        self.context = json.loads(json.dumps(context))
        self.descriptors = json.loads(json.dumps(descriptors))
        p.require(len(self.descriptors) == 15 and {r["label"] for r in self.descriptors} == set(p.SITE_SPECS), "RPC full closed 15-job table")
        for row in self.descriptors:
            p.validate_descriptor(row, self.context, self.root)
        p.require(len({r["nonce"] for r in self.descriptors}) == 15
            and len({r["id"] for r in self.descriptors}) == 15
            and len({r[k] for r in self.descriptors for k in ("stdout_path", "stderr_path")}) == 30,
            "RPC unique ids/nonces/exclusive sinks")
        self.plan_digest = p.digest(self.descriptors)
        self.enrollments = json.loads(json.dumps(enrollments))
        for key, row in self.enrollments.items():
            p.require(key == row["requester_id"] and p.finite(row["parent_deadline_monotonic"]), "RPC enrollment identity/deadline")
            p.identity(row["identity"])
        self.adapter, self.clock, self.auth_observer = adapter, clock, auth_observer
        self.adapter.enrollments = self.enrollments  # registry root-only partagée, aucune requête ne l'alimente.
        self.jobs, self.next_index, self.tainted_requesters, self.errors = {}, {}, set(), []
        self.last_poll_work = 0
        self.transport = None
        self.transport_errors_seen = 0

    def attach_transport(self, transport):
        p.require(self.transport is None and transport.root == self.root
            and p.same(transport.context, self.context)
            and p.same(transport.descriptors, self.descriptors), "RPC exact root transport registry")
        transport.attach_dispatcher(self)
        self.transport = transport
        self.auth_observer = transport.auth_observer

    def transport_failed(self, descriptor_id, reason):
        row = next(row for row in self.descriptors if row["id"] == descriptor_id)
        self._taint(row["requester_id"])
        job = self.jobs.get(descriptor_id)
        if job is not None and job["state"] not in {"complete", "error", "timeout"}:
            job["abort_reason"] = "peer_transport: " + reason
            if job["token"] is not None:
                try:
                    self.adapter.abort(job["token"], job["abort_reason"])
                except BaseException as error:
                    job["state"] = "cleanup_pending"
                    job["last_cleanup_error"] = p.exception_fields(error)

    def _pump_transport(self):
        result = self.transport.pump()
        p.require(isinstance(result, dict) and isinstance(result.get("errors"), list), "RPC transport pump result")
        if result["errors"]:
            self.errors.extend({"phase": "unix_transport", **item}
                               for item in result["errors"][self.transport_errors_seen:])
            self.transport_errors_seen = len(result["errors"])
            # G1.wait doit passer à son finally/stop : aucun PID du payload adopté.
            raise p.RpcInstrumentError("RPC Unix transport instrument errors; owner cleanup required")

    def enroll_requester(self, enrollment):
        """Appelé par G1 après birth/gate vérifiés, AVANT release ; jamais par JSON request."""
        key = enrollment["requester_id"]
        p.require(key in {r["requester_id"] for r in self.descriptors}, "RPC root enrollment unknown role")
        p.identity(enrollment["identity"])
        p.require(enrollment.get("context_id") == self.context["context_id"]
            and enrollment.get("schema") == "c17-g5-root-rpc-enrollment-v1"
            and enrollment.get("publication_protocol") == p.PROTOCOL
            and p.finite(enrollment.get("parent_deadline_monotonic")), "RPC root enrollment context/deadline")
        for name, expected in p.common(self.context).items():
            p.require(enrollment.get(name) == expected, "RPC root enrollment " + name)
        path = p.inside(self.root, Path(enrollment["enrollment_path"]))
        p.require(p.same(p.read_committed(self.root, path), enrollment), "RPC root enrollment hardlink changed")
        plan_path = self.root / "session-rpc/plan.json"
        p.require(enrollment.get("plan_ref") == p.reference(plan_path), "RPC enrollment plan root pin mismatch")
        p.read_reference(enrollment["plan_ref"], root=self.root, limit=p.MAX_MESSAGE_BYTES)
        p.require(p.same(p.read_committed(self.root, plan_path).get("descriptors"), self.descriptors),
                  "RPC enrollment plan differs from root closed table")
        gate = p.checked_json(enrollment["gate_ref"], root=self.root)
        p.require(all(gate.get(k) == enrollment["identity"][k] for k in ("pid", "ppid", "uid", "pgid")),
                  "RPC root enrollment gate identity")
        if key in self.enrollments:
            p.require(p.same(self.enrollments[key], enrollment), "RPC enrolled birth cannot be replaced")
        else:
            self.enrollments[key] = json.loads(json.dumps(enrollment))
        return {"requester_id": key, "enrollment_ref": p.reference(path), "real_identity_authenticated_by_this_method": False}

    def _descendants(self, parent):
        result, frontier = set(), {parent}
        while frontier:
            children = {r["id"] for r in self.descriptors if r["logical_parent_id"] in frontier} - result
            result.update(children)
            frontier = children
        return result

    def _taint(self, requester):
        while requester not in self.tainted_requesters:
            self.tainted_requesters.add(requester)
            parent = next((r["logical_parent_id"] for r in self.descriptors if r["id"] == requester), None)
            if parent is None:
                break
            requester = parent

    def parent_quiescent(self, requester_id):
        descendants = self._descendants(requester_id)
        return not any(key in descendants and job["state"] not in {"complete", "error", "timeout"}
                       for key, job in self.jobs.items())

    def abort_parent(self, requester_id, reason):
        self._taint(requester_id)
        affected = self._descendants(requester_id)
        for key, job in self.jobs.items():
            if key in affected and job["state"] not in {"complete", "error", "timeout"}:
                job["abort_reason"] = reason
                if job["token"] is not None:
                    self.adapter.abort(job["token"], reason)
        return {"requester_id": requester_id, "reason": reason, "quiescent": self.parent_quiescent(requester_id)}

    def _authenticate(self, row, enrollment, request_ref):
        p.require(callable(self.auth_observer), "RPC file writer identity unproved: out-of-band observer absent")
        evidence = self.auth_observer(request_ref, row, enrollment)
        p.require(isinstance(evidence, dict) and evidence.get("authenticated") is True
            and evidence.get("request_ref") == request_ref and type(evidence.get("synthetic")) is bool
            and evidence.get("method") in {"explicit-test-double", "unix-local-peerpid+ledger-birth"}
            and (evidence["method"] != "explicit-test-double" or evidence["synthetic"] is True)
            and p.finite(evidence.get("observed_monotonic"))
            and 0 < evidence["observed_monotonic"] <= self.clock()
                <= evidence["observed_monotonic"] + p.CAPTURE_SECONDS,
            "RPC out-of-band authenticated evidence missing/stale")
        p.same_identity(evidence["identity"], enrollment["identity"])
        observed = self.adapter.observe_requester(enrollment, observed_requester=evidence["identity"])
        p.require(isinstance(observed, dict) and observed.get("live") is True
            and observed.get("enrolled") is True and observed.get("owning_session_active") is True,
            "RPC actual requester/owning Session inactive")
        p.same_identity(observed["identity"], enrollment["identity"])
        return evidence

    def _ack(self, row, request_ref, state, *, error=None, observation=None, evidence=None):
        payload = p.common(self.context) | {"schema": p.ACK_SCHEMA, "publication_protocol": p.PROTOCOL,
            "id": row["id"], "descriptor_digest": p.digest(row), "index": row["index"], "nonce": row["nonce"],
            "request_ref": request_ref, "state": state, "instrument_error": error,
            "synthetic_authentication": evidence["synthetic"] if evidence is not None else None,
            "real_peer_identity_qualified_by_file_transport": False, "runtime_admission": False,
            "FULL": False, "observed_monotonic": self.clock()}
        if observation is not None:
            payload.update({key: observation[key] for key in ("child_identity", "exit_code", "receipt_ref", "cleanup_ref",
                "stdout_ref", "stderr_ref", "termination_proved", "log_stability_proved", "signals",
                "tainted", "cleanup_deadline_met")})
            if observation.get('auxiliary_terminal_ref') is not None:
                payload['auxiliary_terminal_ref'] = observation['auxiliary_terminal_ref']
        else:
            payload.update({"tainted": True, "termination_proved": False, "log_stability_proved": False})
        return p.publish(self.root, p.event_path(self.root, row, "ack"), payload)

    def _refuse(self, row, request_ref, error):
        self._taint(row["requester_id"])
        record = {"id": row["id"], "phase": "accept_or_begin_refused"} | p.exception_fields(error)
        self.errors.append(record)
        ack_ref = self._ack(row, request_ref, "error", error=record)
        self.jobs[row["id"]] = {"row": row, "state": "error", "token": None, "request_ref": request_ref,
                                "ack_ref": ack_ref, "error": record}

    def _accept(self, row, path):
        request_ref = p.reference(path)
        begin_called = False
        try:
            p.require(row["requester_id"] in self.enrollments, "RPC requester unknown/un-enrolled")
            enrollment = self.enrollments[row["requester_id"]]
            p.require(row["requester_id"] not in self.tainted_requesters, "RPC requester monotone taint")
            p.require(row["index"] == self.next_index.get(row["requester_id"], 0), "RPC index out of order/replay")
            value = p.read_committed(self.root, path)
            p.validate_request(value, row, self.context, enrollment, self.clock())
            evidence = self._authenticate(row, enrollment, request_ref)
            p.fresh_budget(self.clock(), row, self.context, enrollment)
            for ref in row["source_refs"]:
                p.read_reference(ref)
            p.require(Path(row["cwd"]).resolve(strict=True) == Path(row["cwd"]), "RPC canonical actual cwd")
            for name in ("stdout_path", "stderr_path"):
                p.inside(self.root, row[name], absent=True)
            # Seule la ligne root, pas value/payload/argv du demandeur, entre dans adapter.
            begin_called = True
            token = self.adapter.begin(json.loads(json.dumps(row)), request_ref)
            self.jobs[row["id"]] = {"row": row, "state": "running", "token": token,
                "request_ref": request_ref, "request_value": value, "evidence": evidence,
                "started_monotonic": self.clock(), "abort_reason": None}
        except BaseException as error:
            if begin_called and not isinstance(error, p.RpcPrelaunchRefused):
                self._taint(row["requester_id"])
                record = {"id": row["id"], "phase": "begin_cleanup_uncertain"} | p.exception_fields(error)
                self.errors.append(record)
                self.jobs[row["id"]] = {"row": row, "state": "cleanup_pending",
                    "token": getattr(error, "token", None), "request_ref": request_ref,
                    "abort_reason": "partial_launch", "error": record}
            else:
                self._refuse(row, request_ref, error)

    def _validate_terminal(self, row, observation):
        p.require(isinstance(observation, dict) and observation.get("state") in {"complete", "timeout", "error"}, "RPC adapter terminal state")
        child = p.identity(observation["child_identity"])
        owner = p.identity(self.context["owner_identity"])
        p.require(child["ppid"] == owner["pid"] and child["uid"] == owner["uid"], "RPC observed physical parent must be root")
        raw = p.checked_json(observation["receipt_ref"], root=self.root)
        cleanup = p.checked_json(observation["cleanup_ref"], root=self.root)
        p.same_identity(raw["root_identity"], child)
        p.same_identity(cleanup["child_identity"], child)
        p.require(raw.get("argv") == row["argv"] and raw.get("cwd") == row["cwd"]
            and raw.get("exit_code") == observation["exit_code"]
            and cleanup.get("receipt_ref") == observation["receipt_ref"]
            and cleanup.get("stage") == row["stage_name"]
            and cleanup.get("requester_id") == row["requester_id"]
            and cleanup.get("logical_parent_id") == row["logical_parent_id"], "RPC terminal command/logical joins")
        p.require(observation.get("termination_proved") is True and raw.get("termination_proved") is True
            and cleanup.get("termination_proved") is True and observation.get("clean") is True
            and cleanup.get("clean") is True
            and cleanup.get("remaining_attributed") == cleanup.get("ambiguities") == cleanup.get("errors") == []
            and observation.get("cleanup_deadline_met") is True and cleanup.get("cleanup_deadline_met") is True
            and p.finite(cleanup.get("cleanup_elapsed_seconds"))
            and 0 <= cleanup["cleanup_elapsed_seconds"] <= p.CLEANUP_SECONDS,
            "RPC terminal birth/cleanup/8s unproved")
        p.require(observation["stdout_ref"]["path"] == row["stdout_path"]
            and observation["stderr_ref"]["path"] == row["stderr_path"]
            and raw.get("stdout") == observation["stdout_ref"] and raw.get("stderr") == observation["stderr_ref"], "RPC exact channel refs")
        for name in ("stdout_ref", "stderr_ref"):
            p.read_reference(observation[name], root=self.root)
        for ref in row["source_refs"]:
            p.read_reference(ref)
        if p.wrapper_scope(self.root) and row['id'] in p.CHROME_JOBS:
            p.require(cleanup.get('auxiliary_terminal_ref') == observation.get('auxiliary_terminal_ref'),
                      'RPC auxiliary observation/cleanup join')
            p.validate_auxiliary_terminal(observation.get('auxiliary_terminal_ref'), row,
                self.root, self.context, observation['receipt_ref'], normal=observation['state'] == 'complete',
                binding_sha256=self.adapter.session.binding_ref['sha256'])
        if observation["state"] == "complete":
            p.require(type(observation["exit_code"]) is int and observation.get("tainted") is False
                and observation.get("log_stability_proved") is True and raw.get("raw_stable") is True
                and raw.get("timed_out") is False and raw.get("log_stability_tainted") is False
                and raw.get("instrument_error") is None and cleanup.get("log_stability_proved") is True
                and observation.get("signals") == cleanup.get("signals") == [], "RPC normal lifecycle, not exit0 policy")
        else:
            p.require(observation.get("tainted") is True, "RPC timeout/error must be monotone instrument taint")

    def _poll_job(self, job):
        row = job["row"]
        cancel = p.event_path(self.root, row, "cancel")
        if cancel.exists() or cancel.is_symlink():
            value = p.read_committed(self.root, cancel)
            p.require(value.get("request_ref") == job["request_ref"] and value.get("nonce") == row["nonce"], "RPC cancel exact request")
            if job["abort_reason"] is None:
                job["abort_reason"] = "client_cancel"
                self._taint(row["requester_id"])
                self.adapter.abort(job["token"], job["abort_reason"])
        observation = self.adapter.poll(job["token"])
        if observation.get("state") == "pending":
            return
        # Un helper ne peut rendre normal tant que ses branches logiques vivent.
        if not self.parent_quiescent(row["id"]):
            self.abort_parent(row["id"], "requester_exited_with_active_descendants")
            job["abort_reason"] = "active_logical_descendants"
            self.adapter.abort(job["token"], job["abort_reason"])
            self._taint(row["requester_id"])
            job["state"] = "cleanup_pending"  # aucun ACK avant fermeture des branches attribuées.
            return
        try:
            self._validate_terminal(row, observation)
            evidence = self._authenticate(row, self.enrollments[row["requester_id"]], job["request_ref"])
            p.require(p.reference(Path(job["request_ref"]["path"])) == job["request_ref"], "RPC request changed after launch")
            p.require(job["abort_reason"] is None or observation["state"] != "complete", "RPC aborted job cannot be normal")
            state = observation["state"]
            if state != "complete":
                self._taint(row["requester_id"])
            error = None if state == "complete" else {"type": "instrument_" + state, "reason": job["abort_reason"]}
            if error is not None:
                diagnostic = p.validated_exception_diagnostic(observation.get("exception_diagnostic"))
                if diagnostic is not None:
                    error["diagnostic"] = diagnostic
            job["ack_ref"] = self._ack(row, job["request_ref"], state, error=error, observation=observation, evidence=evidence)
            job["state"] = state
            if state == "complete":
                self.next_index[row["requester_id"]] = row["index"] + 1
        except BaseException as error:
            self._taint(row["requester_id"])
            record = p.exception_fields(error)
            self.errors.append({"id": row["id"], "phase": "terminal_refusal"} | record)
            job["ack_ref"] = self._ack(row, job["request_ref"], "error", error=record)
            job["state"] = "error"

    def poll(self):
        p.require(p.digest(self.descriptors) == self.plan_digest, "RPC root table changed after closure")
        if self.transport is not None:
            self._pump_transport()  # octets + peer AVANT la découverte des artifacts request.
        allowed = {p.event_path(self.root, row, "request").name for row in self.descriptors}
        for path in (self.root / "session-rpc/request").iterdir():
            if path.name.endswith(".json"):
                p.require(path.name in allowed, "RPC unknown request filename; no adoption")
        self.last_poll_work = 0
        for row in self.descriptors:
            path = p.event_path(self.root, row, "request")
            if row["id"] not in self.jobs and (path.exists() or path.is_symlink()):
                if self.transport is not None and not self.transport.ready(row, path):
                    value = p.read_committed(self.root, path)
                    created = value.get("created_monotonic")
                    if p.finite(created) and 0 < created <= self.clock() <= created + p.CAPTURE_SECONDS:
                        continue  # frame pas encore arrivée ; aucun lancement/file-authority.
                self._accept(row, path)
                self.last_poll_work += 1
        # Descendants avant parents : les deux helpers all-* restent pilotables.
        ordered = sorted(self.jobs.values(), key=lambda j: len(self._descendants(j["row"]["id"])))
        for job in ordered:
            if job["state"] in {"running", "cleanup_pending"}:
                if job["state"] == "cleanup_pending" and job["token"] is None:
                    continue  # seul owner Session.stop peut résoudre ce handle incertain.
                try:
                    self._poll_job(job)
                except BaseException as error:
                    self._taint(job["row"]["requester_id"])
                    job["state"] = "cleanup_pending"
                    job["last_cleanup_error"] = p.exception_fields(error)
                self.last_poll_work += 1
        if self.transport is not None:
            self._pump_transport()  # ACK exact vers la connexion maintenue, après closure prouvée.
        return {"processed": self.last_poll_work, "pending": sum(j["state"] in {"running", "cleanup_pending"} for j in self.jobs.values()),
                "tainted_requesters": sorted(self.tainted_requesters), "errors": list(self.errors),
                "identity_OS_qualified": False, "FULL": False}
