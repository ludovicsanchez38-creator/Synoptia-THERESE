"""Diagnostics d'exception bornés : données seulement, jamais autorité RPC."""
from __future__ import annotations

import json
from typing import Any

SCHEMA = "c17-rpc-exception-diagnostic-v1"
MAX_NODES = 8
MAX_MESSAGE_BYTES = 1024
MAX_JSON_BYTES = 16 * 1024
MAX_TYPE_BYTES = 128
MAX_MODULE_BYTES = 256
_KEYS = {"schema", "diagnostic_only", "nodes", "cycle_detected",
         "depth_truncated", "budget_truncated", "serializer_failed"}
_NODE_KEYS = {"index", "relation", "type", "module", "message",
              "message_truncated", "suppress_context"}


def _encoded(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, ensure_ascii=False,
                       allow_nan=False) + "\n").encode("utf-8")


def _clip(value: str, limit: int) -> tuple[str, bool]:
    # Encode only a bounded prefix. Invalid surrogate code points become '?'.
    raw = value[:limit + 1].encode("utf-8", errors="replace")
    return raw[:limit].decode("utf-8", errors="ignore"), (
        len(value) > limit + 1 or len(raw) > limit)


def _message(error: BaseException) -> tuple[str, bool]:
    try:
        value = str(error)
    except BaseException:
        value = "<exception message unavailable>"
    return _clip(value, MAX_MESSAGE_BYTES)


def _metadata(error: BaseException) -> tuple[str, str]:
    try:
        cls = type(error)
        return _clip(cls.__name__, MAX_TYPE_BYTES)[0], _clip(cls.__module__, MAX_MODULE_BYTES)[0]
    except BaseException:
        return "UnknownException", "unknown"


def _blank() -> dict[str, Any]:
    return {"schema": SCHEMA, "diagnostic_only": True, "nodes": [],
            "cycle_detected": False, "depth_truncated": False,
            "budget_truncated": False, "serializer_failed": False}


def exception_diagnostic(error: BaseException) -> dict[str, Any]:
    """Outer -> explicit cause, otherwise unsuppressed context; no traceback."""
    result = _blank()
    try:
        if not isinstance(error, BaseException):
            raise TypeError("exception required")
        seen: set[int] = set()
        current: BaseException | None = error
        relation = "outer"
        while current is not None:
            if id(current) in seen:
                result["cycle_detected"] = True
                break
            if len(result["nodes"]) == MAX_NODES:
                result["depth_truncated"] = True
                break
            name, module = _metadata(current)
            message, shortened = _message(current)
            suppressed = bool(current.__suppress_context__)
            node = {"index": len(result["nodes"]), "relation": relation,
                    "type": name, "module": module, "message": message,
                    "message_truncated": shortened,
                    "suppress_context": suppressed}
            result["nodes"].append(node)
            if len(_encoded(result)) > MAX_JSON_BYTES:
                result["nodes"].pop()
                result["budget_truncated"] = True
                break
            seen.add(id(current))
            if current.__cause__ is not None:
                current, relation = current.__cause__, "cause"
            elif not suppressed and current.__context__ is not None:
                current, relation = current.__context__, "context"
            else:
                current = None
        if len(_encoded(result)) > MAX_JSON_BYTES:
            raise ValueError("diagnostic serialization bound")
        return result
    except BaseException:
        # Observability must not interrupt refusal, cleanup or ACK gating.
        fallback = _blank()
        fallback["serializer_failed"] = True
        return fallback


def validated_exception_diagnostic(value: Any) -> dict[str, Any] | None:
    """Copy bounded diagnostic data, or ignore it. No lifecycle validation."""
    try:
        if not isinstance(value, dict) or set(value) != _KEYS:
            return None
        if value["schema"] != SCHEMA or value["diagnostic_only"] is not True:
            return None
        if any(type(value[k]) is not bool for k in (
                "cycle_detected", "depth_truncated", "budget_truncated", "serializer_failed")):
            return None
        nodes = value["nodes"]
        if not isinstance(nodes, list) or len(nodes) > MAX_NODES:
            return None
        for index, node in enumerate(nodes):
            if not isinstance(node, dict) or set(node) != _NODE_KEYS:
                return None
            if type(node["index"]) is not int or node["index"] != index:
                return None
            if node["relation"] not in ({"outer"} if index == 0 else {"cause", "context"}):
                return None
            for key, limit in (("type", MAX_TYPE_BYTES), ("module", MAX_MODULE_BYTES),
                               ("message", MAX_MESSAGE_BYTES)):
                if not isinstance(node[key], str) or len(node[key].encode("utf-8")) > limit:
                    return None
            if any(type(node[k]) is not bool for k in ("message_truncated", "suppress_context")):
                return None
        raw = _encoded(value)
        if len(raw) > MAX_JSON_BYTES:
            return None
        return json.loads(raw)
    except BaseException:
        return None


def exception_fields(error: BaseException) -> dict[str, Any]:
    diagnostic = exception_diagnostic(error)
    nodes = diagnostic["nodes"]
    return {"type": nodes[0]["type"] if nodes else "UnknownException",
            "reason": nodes[0]["message"] if nodes else "<exception diagnostic unavailable>",
            "diagnostic": diagnostic}


def exception_record_text(record: Any) -> str:
    """Bounded ACK-error display; never recreate a remote exception class."""
    result: dict[str, Any] = {}
    try:
        if isinstance(record, dict):
            for key in ("id", "phase", "type", "reason"):
                if isinstance(record.get(key), str):
                    limit = MAX_MESSAGE_BYTES if key == "reason" else MAX_TYPE_BYTES
                    result[key] = _clip(record[key], limit)[0]
            diagnostic = validated_exception_diagnostic(record.get("diagnostic"))
            if diagnostic is not None:
                result["diagnostic"] = diagnostic
        elif record is None:
            result["reason"] = "None"
        else:
            result["reason"] = _clip(str(record), MAX_MESSAGE_BYTES)[0]
        while len(_encoded(result)) > MAX_JSON_BYTES and result.get("diagnostic", {}).get("nodes"):
            result["diagnostic"]["nodes"].pop()
            result["diagnostic"]["budget_truncated"] = True
        if len(_encoded(result)) > MAX_JSON_BYTES:
            result.pop("diagnostic", None)
        return _encoded(result).decode("utf-8").rstrip("\n")
    except BaseException:
        return '{"reason": "<exception display unavailable>"}'
