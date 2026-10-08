"""Contrôle textuel et S-expressions uniquement. Ne compile ni n'exécute SBPL."""
from __future__ import annotations

import difflib
import hashlib
import json
from pathlib import Path

BASE_SHA256 = "19808ee2cac3169e9fb8c71c24385bcbb97f924c5ed785f4651817ecaa179b0c"
BASE_BYTES = 2067
ADDITION = (
    "; ROOT10 diagnostic_only : refus ciblés, causalité non prouvée, profil non admis.\n"
    '(allow mach-lookup (global-name "com.apple.CARenderServer"))\n'
    '(allow iokit-open-user-client (iokit-user-client-class "IOSurfaceRootUserClient"))\n'
    '(allow iokit-open-user-client (iokit-user-client-class "AGXDeviceUserClient"))\n'
)


def parse_sbpl(text: str) -> list:
    """Petit lecteur fermé pour les formes utilisées ici, pas un validateur Apple."""
    tokens = []
    position = 0
    while position < len(text):
        char = text[position]
        if char.isspace():
            position += 1
        elif char == ";":
            end = text.find("\n", position)
            position = len(text) if end < 0 else end + 1
        elif char in "()":
            tokens.append(char)
            position += 1
        elif char == '"':
            start = position
            position += 1
            while position < len(text):
                if text[position] == "\\":
                    position += 2
                elif text[position] == '"':
                    position += 1
                    break
                else:
                    position += 1
            else:
                raise ValueError("chaîne non terminée")
            tokens.append(("string", json.loads(text[start:position])))
        else:
            start = position
            while position < len(text) and not text[position].isspace() and text[position] not in "();\"":
                position += 1
            if start == position:
                raise ValueError("token inattendu")
            tokens.append(text[start:position])
    roots = []
    stack = []
    for token in tokens:
        if token == "(":
            form = []
            (stack[-1] if stack else roots).append(form)
            stack.append(form)
        elif token == ")":
            if not stack:
                raise ValueError("fermeture sans ouverture")
            stack.pop()
        else:
            if not stack:
                raise ValueError("atome hors forme")
            stack[-1].append(token)
    if stack:
        raise ValueError("forme non terminée")
    return roots


def validate_candidate(base: bytes, candidate: bytes) -> dict:
    if len(base) != BASE_BYTES or hashlib.sha256(base).hexdigest() != BASE_SHA256:
        raise ValueError("préimage non exacte")
    if candidate != base + ADDITION.encode("utf-8"):
        raise ValueError("delta autre que les trois règles littérales autorisées")
    old_forms = parse_sbpl(base.decode("utf-8"))
    new_forms = parse_sbpl(candidate.decode("utf-8"))
    added = parse_sbpl(ADDITION)
    if len(added) != 3 or new_forms != old_forms + added:
        raise ValueError("delta S-expressions divergent")
    return {
        "base_sha256": BASE_SHA256,
        "base_bytes": BASE_BYTES,
        "candidate_sha256": hashlib.sha256(candidate).hexdigest(),
        "candidate_bytes": len(candidate),
        "added_rules": 3,
        "original_prefix_byte_exact": True,
        "original_forms_preserved": True,
        "static_only": True,
        "compiled_or_executed_profile": False,
        "causal_claim": False,
        "admitted": False,
        "FULL": False,
    }


def expected_diff(base: str, candidate: str, *, inverse: bool = False) -> str:
    if inverse:
        base, candidate = candidate, base
        before, after = "chrome.sb", "preimage-chrome.sb"
    else:
        before, after = "preimage-chrome.sb", "chrome.sb"
    return "".join(difflib.unified_diff(base.splitlines(True), candidate.splitlines(True),
                                      fromfile=before, tofile=after))


if __name__ == "__main__":
    here = Path(__file__).resolve().parent
    print(json.dumps(validate_candidate((here / "preimage-chrome.sb").read_bytes(),
                                        (here / "chrome.sb").read_bytes()), indent=2))
