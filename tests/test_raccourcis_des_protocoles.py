"""Un raccourci dispatché par un protocole doit exister, et sur la bonne touche modificatrice.

B-074 (02/09/2026). Les protocoles de personas déclenchent des raccourcis en
dispatchant un `KeyboardEvent` depuis `javascript_tool`. Deux écarts les
rendaient incapables d'échouer utilement sur le poste macOS de référence :

1. Le modificateur était écrit `ctrlKey: true` en dur, alors que
   `useKeyboardShortcuts.ts` lit `event.metaKey` dès que `navigator.platform`
   contient « MAC ». Le gestionnaire sortait donc avant toute action, et le
   contrôle qui suivait constatait un écran inchangé sans jamais nommer la
   cause.
2. Trois étapes visaient Ctrl+1, Ctrl+2 et Ctrl+3, que le hook ne traite sur
   AUCUNE plateforme : le protocole exigeait une fonctionnalité absente.

Ce test lit les deux sources — les `.md` de `tests/protocols/` et le hook — et
refuse qu'elles divergent à nouveau. Les protocoles de `server/` sont exclus :
ils visent THÉRÈSE Server, un autre dépôt.
"""

from __future__ import annotations

import re
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
PROTOCOLES = RACINE / "tests" / "protocols"
HOOK = RACINE / "src" / "frontend" / "src" / "hooks" / "useKeyboardShortcuts.ts"

# Chaque appel `new KeyboardEvent('keydown', { ... })` avec son objet d'options.
DISPATCH = re.compile(r"new KeyboardEvent\(\s*'keydown'\s*,\s*\{(?P<options>[^}]*)\}")
TOUCHE = re.compile(r"key:\s*'(?P<touche>[^']*)'")
# Le hook énumère ses touches par comparaison littérale : `key === 'k'` sur la
# forme minuscule, `event.key === ','` sur la forme brute. Les deux comptent.
BRANCHE_HOOK = re.compile(r"\bkey\s*===\s*'(?P<touche>[^']*)'")
# Seule touche que le hook traite AVANT le contrôle du modificateur (:51-54).
SANS_MODIFICATEUR = {"escape"}


def _fichiers_de_protocole() -> list[Path]:
    return sorted(
        chemin
        for chemin in PROTOCOLES.rglob("*.md")
        if "server" not in chemin.relative_to(PROTOCOLES).parts
    )


def _dispatches() -> list[tuple[Path, int, str, str]]:
    """(fichier, numéro de ligne, options du KeyboardEvent, ligne entière)."""
    releves: list[tuple[Path, int, str, str]] = []
    for chemin in _fichiers_de_protocole():
        for numero, ligne in enumerate(chemin.read_text(encoding="utf-8").splitlines(), 1):
            for trouve in DISPATCH.finditer(ligne):
                releves.append((chemin, numero, trouve.group("options"), ligne))
    return releves


def _touches_du_hook() -> set[str]:
    source = HOOK.read_text(encoding="utf-8")
    return {trouve.group("touche").lower() for trouve in BRANCHE_HOOK.finditer(source)}


def test_le_hook_reste_lisible_par_ce_test():
    """Garde-fou : sans branche lue, les deux tests suivants passeraient à vide."""
    assert HOOK.exists(), f"Hook introuvable : {HOOK}"
    touches = _touches_du_hook()
    assert len(touches) >= 8, f"Lecture du hook suspecte : {sorted(touches)}"
    assert {"k", "n", "m", "escape"} <= touches, sorted(touches)


def test_les_protocoles_dispatchent_un_modificateur_dependant_de_la_plateforme():
    """`ctrlKey` en dur ne déclenche rien sur macOS : le hook y lit `metaKey`."""
    releves = _dispatches()
    assert releves, "Aucun KeyboardEvent trouvé : le motif ne lit plus les protocoles."

    fautifs = []
    for chemin, numero, options, ligne in releves:
        trouve = TOUCHE.search(options)
        assert trouve, f"{chemin.relative_to(RACINE)}:{numero} : KeyboardEvent sans `key:`"
        if trouve.group("touche").lower() in SANS_MODIFICATEUR:
            # Escape est traité ligne 51, avant `if (!modKey) return`.
            continue
        en_dur = re.search(r"\b(ctrlKey|metaKey)\s*:", options)
        nomme_la_plateforme = "navigator.platform" in ligne
        nomme_les_deux = "'metaKey'" in ligne and "'ctrlKey'" in ligne
        if en_dur or not (nomme_la_plateforme and nomme_les_deux):
            fautifs.append(
                f"{chemin.relative_to(RACINE)}:{numero} -> options={options.strip()!r}"
            )

    assert not fautifs, (
        "Modificateur figé dans le protocole. Sur macOS le hook lit "
        "`event.metaKey` (useKeyboardShortcuts.ts:40) : un `ctrlKey: true` en "
        "dur sort ligne 57 sans rien déclencher.\n" + "\n".join(fautifs)
    )


def test_toute_touche_dispatchee_a_un_gestionnaire_dans_le_hook():
    """Un protocole ne peut pas exiger un raccourci que le code n'implémente pas."""
    touches_du_hook = _touches_du_hook()
    orphelines = []
    for chemin, numero, options, _ligne in _dispatches():
        trouve = TOUCHE.search(options)
        assert trouve, f"{chemin.relative_to(RACINE)}:{numero} : KeyboardEvent sans `key:`"
        touche = trouve.group("touche").lower()
        if touche not in touches_du_hook:
            orphelines.append(f"{chemin.relative_to(RACINE)}:{numero} -> key={touche!r}")

    assert not orphelines, (
        "Raccourci dispatché sans gestionnaire dans useKeyboardShortcuts.ts : "
        "l'étape ne peut pas échouer pour la bonne raison.\n"
        + "\n".join(orphelines)
    )
