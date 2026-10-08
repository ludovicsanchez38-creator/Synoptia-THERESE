"""Contrat pur de livraison externe root ; jamais une authentification par chaînes."""
from __future__ import annotations
from pathlib import PurePosixPath
import re

SCHEMA = "c17-runtime78-root-relay-v1"
PROTOCOL = "exclusive-pending-fsync-hardlink-v1"


def need(value: bool, message: str) -> None:
    if not value:
        raise ValueError(message)


def reference(value: dict) -> dict:
    need(isinstance(value, dict) and isinstance(value.get("path"), str)
         and PurePosixPath(value["path"]).is_absolute() and ".." not in PurePosixPath(value["path"]).parts
         and re.fullmatch(r"[a-f0-9]{64}", value.get("sha256", "")) is not None, "Relay référence exacte")
    need("bytes" not in value or type(value["bytes"]) is int and value["bytes"] >= 0, "Relay taille référence")
    return value


def context(value: dict, expected: dict) -> None:
    for key in ("actor", "round_id", "round_name", "head", "qa_root"):
        need(value.get(key) == expected[key], "Relay contexte : " + key)


def delivery(value: dict, expected: dict, plan: dict, request_ref: dict, *, stage: bool) -> None:
    context(value, expected)
    need(value.get("schema") == SCHEMA and value.get("publication_protocol") == PROTOCOL
         and value.get("provided_by") == "/root" and value.get("request") == request_ref,
         "Relay livraison exacte")
    need(value.get("kind") == ("stage-binding" if stage else "root-review"), "Relay type livraison")
    for key in ("decision", "origin") + (("binding",) if stage else ()):
        reference(value.get(key))
        need(value[key]["path"] == plan[key + "_path"], "Relay path planifié : " + key)
    if value.get("review") is not None:
        reference(value["review"])


def origin(value: dict, expected: dict, request_ref: dict, inspected_refs: dict, plan: dict) -> None:
    context(value, expected)
    need(value.get("schema") == "c17-runtime78-root-tool-review-origin-v1"
         and value.get("provided_by") == "/root" and value.get("origin_kind") == "actual_root_tool_review"
         and value.get("request") == request_ref and value.get("inspected_refs") == inspected_refs,
         "Relay origine/revue d’une autre demande")
    reference(value.get("root_tool_record"))
    need(value["root_tool_record"]["path"] == plan["tool_record_path"], "Relay origine outil non planifiée")
    # L’origine réelle de ce record doit être vérifiée par root hors workload.
    # Aucun provided_by/boolean/SHA écrit ici ne prouve cette autorité.


def stage_admission(binding: dict, decision: dict, packet: dict, expected: dict,
                    name: str, command: dict, initial_ref: dict, plan: dict) -> None:
    context(binding, expected); context(decision, expected)
    need(binding.get("schema") == "c17-runtime78-stage-binding-v1"
         and decision.get("schema") == "c17-runtime78-stage-go-v1", "Relay schémas étape")
    need(binding.get("stage_id") == decision.get("stage_id") == name
         and binding.get("initial_binding") == decision.get("initial_binding") == initial_ref,
         "Relay étape/binding initial étranger")
    need(binding.get("command") == command and command.get("timeout_seconds") == plan["timeout_seconds"],
         "Relay commande/borne différente")
    need(decision.get("provided_by") == "/root" and decision.get("stage_binding") == packet["binding"]
         and decision.get("root_review_origin") == packet["origin"], "Relay décision étape/origine différente")
    need("decision_ref" not in binding and binding.get("planned_decision") == plan["decision"]
         == {"path": packet["decision"]["path"], "decision_id": decision.get("decision_id")},
         "Relay hash inverse/path/id de décision")


def review_decision(value: dict, packet: dict, expected: dict, phase: str,
                    inspected_refs: dict, plan: dict) -> None:
    context(value, expected)
    need(value.get("schema") == "c17-runtime78-successor-admission-v1"
         and value.get("provided_by") == "/root" and value.get("phase") == phase
         and value.get("decision_id") == plan["decision_id"]
         and value.get("root_review_origin") == packet["origin"], "Relay décision de revue étrangère")
    reviewed = value.get("reviewed_refs")
    need(isinstance(reviewed, dict) and all(reviewed.get(k) == v for k, v in inspected_refs.items()),
         "Relay références réellement relues différentes")
    if packet.get("review") is not None:
        need(packet["review"] in reviewed.values(), "Relay revue indépendante non liée à décision")
