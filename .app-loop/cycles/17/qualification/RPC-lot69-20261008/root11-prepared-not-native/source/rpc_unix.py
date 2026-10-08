"""Serveur Unix root : octets request → peer hors payload → ACK même connexion.

Aucun G1 importé. Les sockets ne sont créés que par create_server explicitement,
après validation de la registry root fermée ; jamais à l'import. Tests par doubles.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import socket
import stat
import struct
import time

import rpc_peer
import rpc_protocol as p


def _registry(root, context, descriptors):
    root = p.canonical_root(root)
    p.validate_context(context, root)
    p.require(len(descriptors) == 15 and {row["label"] for row in descriptors} == set(p.SITE_SPECS),
              "Unix root closed 15-job registry required before socket")
    for row in descriptors:
        p.validate_descriptor(row, context, root)
    p.require(len({row["id"] for row in descriptors}) == 15
        and len({row["nonce"] for row in descriptors}) == 15
        and len({row[k] for row in descriptors for k in ("stdout_path", "stderr_path")}) == 30,
        "Unix unique root registry/sinks")
    return root


def create_server(root, context, descriptors, ledger, *, socket_factory=socket.socket,
                  clock=time.monotonic):
    """Factory OS future, à appeler uniquement sous GO exact ; aucun test OS ici."""
    root = _registry(root, context, descriptors)
    p.same_identity(ledger.owner, context["owner_identity"])
    path = p.inside(root, root / "session-rpc/peer.sock", absent=True)
    listener = socket_factory(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        listener.bind(str(path))
        os.chmod(path, 0o600, follow_symlinks=False)
        listener.listen(15)
        listener.setblocking(False)
        return UnixRpcServer(root, context, descriptors, listener, ledger, clock=clock)
    except BaseException:
        listener.close()
        raise  # aucune suppression d'un fichier socket inconnu ou création avortée.


class UnixRpcServer:
    def __init__(self, root, context, descriptors, listener, ledger, *, clock=time.monotonic,
                 peer_capture=rpc_peer.capture_peer, synthetic_peer=False):
        self.root = _registry(root, context, descriptors)
        self.context = json.loads(json.dumps(context))
        self.descriptors = json.loads(json.dumps(descriptors))
        self.plan_digest = p.digest(self.descriptors)
        self.rows = {row["id"]: row for row in self.descriptors}
        self.listener, self.ledger, self.clock = listener, ledger, clock
        self.peer_capture, self.synthetic_peer = peer_capture, synthetic_peer
        p.require(type(synthetic_peer) is bool, "Unix synthetic declaration explicit")
        p.require(synthetic_peer or peer_capture is rpc_peer.capture_peer,
                  "Unix substituted peer observer must be explicitly synthetic")
        p.same_identity(ledger.owner, context["owner_identity"])
        self.listener.setblocking(False)
        self.dispatcher = None
        self.slots, self.by_request, self.seen, self.errors = [], {}, set(), []
        self.closed = False

    def attach_dispatcher(self, dispatcher):
        p.require(self.dispatcher is None and dispatcher.root == self.root
            and p.same(dispatcher.context, self.context)
            and p.same(dispatcher.descriptors, self.descriptors), "Unix exact owning dispatcher registry")
        self.dispatcher = dispatcher

    def _fail(self, slot, error):
        record = {"type": type(error).__name__, "reason": str(error),
                  "id": slot.get("row", {}).get("id"), "synthetic_peer": self.synthetic_peer}
        if len(self.errors) < 16:
            self.errors.append(record)
        slot["failed"] = record
        if self.dispatcher is not None and slot.get("row") is not None:
            self.dispatcher.transport_failed(slot["row"]["id"], str(error))
        slot["connection"].close()
        slot["closed"] = True

    def _receive(self, slot):
        connection = slot["connection"]
        try:
            data = connection.recv(65536)
        except BlockingIOError:
            return
        if slot.get("ack_sent"):
            p.require(data == b"", "Unix extra bytes after complete ACK refused")
            connection.close()
            slot["closed"] = True
            slot["client_disconnected_after_ack_sent"] = True
            return  # LOCAL_PEERPID n'est plus revalidable après EOF attendu.
        p.require(bool(data), "Unix peer EOF before ACK")
        p.require(slot.get("request_ref") is None, "Unix extra frame/replay on request connection")
        slot["buffer"].extend(data)
        p.require(len(slot["buffer"]) <= p.MAX_MESSAGE_BYTES + 4, "Unix bounded incoming frame")
        if len(slot["buffer"]) < 4:
            return
        size = struct.unpack("!I", slot["buffer"][:4])[0]
        p.require(0 < size <= p.MAX_MESSAGE_BYTES, "Unix frame length refused")
        p.require(len(slot["buffer"]) <= size + 4, "Unix trailing bytes/multiple frames refused")
        if len(slot["buffer"]) < size + 4:
            return
        raw = bytes(slot["buffer"][4:])
        value = json.loads(raw)
        p.require(isinstance(value, dict) and isinstance(value.get("id"), str), "Unix request object/id")
        row = self.rows.get(value["id"])
        p.require(row is not None, "Unix unplanned descriptor id")
        slot["row"] = row
        key = (row["id"], row["nonce"])
        p.require(key not in self.seen and value.get("nonce") == row["nonce"], "Unix request nonce replay/mismatch")
        self.seen.add(key)
        # Path/ref NE viennent PAS du JSON. La registry root les détermine.
        path = p.event_path(self.root, row, "request")
        committed = p.read_committed(self.root, path)
        ref = p.reference(path)
        p.require(raw == p.read_reference(ref, root=self.root)
            and p.same(value, committed), "Unix request wire bytes differ from root-derived committed artifact")
        peer = self.peer_capture(connection, self.ledger, {"stage-" + row["requester_id"]})
        peer.revalidate(connection, self.ledger)
        slot.update(request_ref=ref, peer=peer, raw=raw)
        self.by_request[str(path)] = slot

    def ready(self, row, request_path):
        slot = self.by_request.get(str(request_path))
        return slot is not None and not slot["closed"] and slot["row"] == row

    def auth_observer(self, request_ref, row, enrollment):
        slot = self.by_request.get(request_ref["path"])
        p.require(slot is not None and not slot["closed"] and not slot.get("failed")
            and p.same(slot["row"], row) and slot["request_ref"] == request_ref,
            "Unix exact request bytes have no live authenticated peer")
        actual = slot["peer"].revalidate(slot["connection"], self.ledger)
        p.same_identity(actual, enrollment["identity"])
        p.require(p.read_reference(request_ref, root=self.root) == slot["raw"], "Unix authenticated request bytes changed")
        return {"authenticated": True, "identity": actual, "request_ref": request_ref,
                "method": "explicit-test-double" if self.synthetic_peer else "unix-local-peerpid+ledger-birth",
                "synthetic": self.synthetic_peer, "observed_monotonic": self.clock()}

    def _send_ack(self, slot):
        if slot.get("request_ref") is None or slot.get("ack_sent"):
            return
        if slot.get("outgoing") is None:
            path = p.event_path(self.root, slot["row"], "ack")
            if not path.exists() and not path.is_symlink():
                return
            ack = p.read_committed(self.root, path)
            p.require(ack.get("request_ref") == slot["request_ref"], "Unix ACK exact authenticated request")
            slot["peer"].revalidate(slot["connection"], self.ledger)
            ref = p.reference(path)
            raw = p.read_reference(ref, root=self.root, limit=p.MAX_MESSAGE_BYTES)
            slot.update(ack_ref=ref, outgoing=struct.pack("!I", len(raw)) + raw, sent=0)
        slot["peer"].revalidate(slot["connection"], self.ledger)
        p.read_reference(slot["ack_ref"], root=self.root, limit=p.MAX_MESSAGE_BYTES)
        try:
            count = slot["connection"].send(slot["outgoing"][slot["sent"]:])
        except BlockingIOError:
            return
        p.require(type(count) is int and count > 0, "Unix ACK send closed")
        slot["sent"] += count
        if slot["sent"] == len(slot["outgoing"]):
            slot["ack_sent"] = True
            slot["ack_sent_monotonic"] = self.clock()
            # Garder unp_conn vivant pour LOCAL_PEERPID côté client après
            # lecture ACK. Le client ferme après vérification, pas ce serveur.

    def pump(self):
        p.require(not self.closed and p.digest(self.descriptors) == self.plan_digest,
                  "Unix server closed/registry changed")
        # Bornes de cardinalité et de bytes, pas de wait ni de boucle workload.
        for _ in range(15):
            try:
                connection, _address = self.listener.accept()
            except BlockingIOError:
                break
            connection.setblocking(False)
            slot = {"connection": connection, "buffer": bytearray(), "closed": False,
                    "accepted_monotonic": self.clock(), "request_ref": None}
            if len(self.slots) >= 15:
                self._fail(slot, p.RpcInstrumentError("Unix maximum closed15 connections exceeded"))
                continue
            self.slots.append(slot)
        for slot in self.slots:
            if slot["closed"]:
                continue
            try:
                if slot["request_ref"] is None:
                    p.require(self.clock() <= slot["accepted_monotonic"] + p.CAPTURE_SECONDS,
                              "Unix request framing admission exceeded 5s")
                if slot.get("ack_sent"):
                    p.require(self.clock() <= slot["ack_sent_monotonic"] + p.CAPTURE_SECONDS,
                              "Unix client close after ACK exceeded 5s")
                self._receive(slot)
                self._send_ack(slot)
            except BaseException as error:
                self._fail(slot, error)
        return {"errors": list(self.errors), "active": sum(not s["closed"] for s in self.slots),
                "synthetic_peer": self.synthetic_peer, "OS_qualified": False, "FULL": False}

    def close(self):
        for slot in self.slots:
            if not slot["closed"]:
                slot["connection"].close()
                slot["closed"] = True
        self.listener.close()
        self.closed = True
        # Socket laissé comme artefact : aucune unlink d'un inode non attesté.
