#!/usr/bin/env python3
"""Contrôle des contrastes des paires déclarées par les maquettes, sur les jetons réels et les
redéfinitions des directions. Sortie : recette/contrastes.md. Seuils : 4,5:1 texte courant,
3:1 grands titres et repères d'interface, 7:1 en contraste élevé."""
import re, os
R = os.path.dirname(os.path.abspath(__file__))
def hexrgb(h):
    h = h.strip().lstrip('#'); return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))
def lum(rgb):
    def c(v):
        v /= 255; return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
    r, g, b = rgb; return 0.2126 * c(r) + 0.7152 * c(g) + 0.0722 * c(b)
def ratio(a, b):
    la, lb = sorted((lum(a), lum(b)), reverse=True); return (la + 0.05) / (lb + 0.05)
def compose(top, alpha, base):
    return tuple(round(t * alpha + b * (1 - alpha)) for t, b in zip(top, base))
def jetons(css, selector_regex):
    m = re.search(selector_regex, css, flags=re.M); 
    if not m: return {}
    j = css.find('{', m.end() - 1); depth = 0; k = j
    while k < len(css):
        if css[k] == '{': depth += 1
        elif css[k] == '}':
            depth -= 1
            if depth == 0: break
        k += 1
    return dict(re.findall(r'--([a-z0-9-]+):\s*(#[0-9A-Fa-f]{6})', css[j+1:k]))
tok = open(f"{R}/maquettes/da/tokens.css").read()
d1 = open(f"{R}/maquettes/da/d1.css").read(); d3 = open(f"{R}/maquettes/da/d3.css").read()
themes = {"clair": jetons(tok, r'^:root\s*\{'), "sombre": jetons(tok, r'^\[data-theme="dark"\]\s*\{'), "contraste élevé": jetons(tok, r'^\[data-high-contrast="true"\]\s*\{')}
themes["sombre"] = {**themes["clair"], **themes["sombre"]}; themes["contraste élevé"] = {**themes["clair"], **themes["contraste élevé"]}
themes["direction 1 (papier)"] = {**themes["clair"], **jetons(d1, r'^\[data-d="1"\]:not\(\[data-theme="dark"\]\)\s*\{')}
themes["direction 3 (navy)"] = {**themes["clair"], **dict(re.findall(r'--([a-z0-9-]+):(#[0-9A-Fa-f]{6})', d3))}
PAIRES = [("color-text", "color-bg", 4.5, "texte courant sur le fond"), ("color-text", "color-surface", 4.5, "texte sur surface"),
          ("color-text-muted", "color-bg", 4.5, "métadonnées sur le fond"), ("color-text-muted", "color-surface", 4.5, "métadonnées sur surface"),
          ("color-accent", "color-bg", 4.5, "accent encre (liens) sur le fond"), ("color-accent", "color-accent-tint", 4.5, "accent encre sur sa teinte"),
          ("color-accent-ink", "color-accent-fill", 4.5, "encre du bouton principal"), ("color-ring", "color-bg", 3.0, "anneau de focus sur le fond"),
          ("color-error", "color-surface", 4.5, "erreur sur surface"), ("color-warning", "color-surface", 4.5, "avertissement sur surface"), ("color-success", "color-surface", 4.5, "succès sur surface"), ("color-info", "color-surface", 4.5, "info sur surface"),
          ("color-domaine-agenda", "color-domaine-agenda-tint", 4.5, "agenda sur sa teinte"), ("color-domaine-taches", "color-domaine-taches-tint", 4.5, "tâches sur sa teinte"),
          ("color-domaine-factures", "color-domaine-factures-tint", 4.5, "factures sur sa teinte"), ("color-domaine-prospects", "color-domaine-prospects-tint", 4.5, "prospects sur sa teinte"),
          ("color-error-ink", "color-error-fill", 4.5, "encre sur remplissage erreur"), ("color-success-ink", "color-success-fill", 4.5, "encre sur remplissage succès")]
lignes = ["# Contrastes des maquettes (calcul WCAG, sRGB, teintes opaques ou composées à 30 % sur le fond)", "", f"Généré par contrastes.py. Seuils : 4,5:1 texte, 3:1 anneau de focus, 7:1 en contraste élevé.", ""]
echecs = 0
for nom, t in themes.items():
    lignes += [f"## {nom}", "", "| Paire | Couleurs | Ratio | Seuil | Verdict |", "|---|---|---:|---:|---|"]
    for enc, fond, seuil, libelle in PAIRES:
        if enc not in t or fond not in t: lignes.append(f"| {libelle} | jeton absent ({enc} / {fond}) | | | à vérifier |"); continue
        s = 7.0 if nom == "contraste élevé" and seuil == 4.5 else seuil
        r = ratio(hexrgb(t[enc]), hexrgb(t[fond]))
        ok = r >= s; echecs += (not ok)
        lignes.append(f"| {libelle} | {t[enc]} sur {t[fond]} | {r:.2f}:1 | {s:.1f} | {'passe' if ok else '**échec**'} |")
    # étiquettes sémantiques composées à 12-14 % sur surface
    for enc, alpha, libelle in [("color-error", .12, "étiquette erreur (12 %)"), ("color-warning", .14, "étiquette attention (14 %)"), ("color-success", .12, "étiquette succès (12 %)"), ("color-info", .12, "étiquette info (12 %)")]:
        if enc in t and "color-surface" in t:
            # en contraste élevé les étiquettes abandonnent la teinte (base.css) : encre sur surface
            fond = hexrgb(t["color-surface"]) if nom == "contraste élevé" else compose(hexrgb(t[enc]), alpha, hexrgb(t["color-surface"])); r = ratio(hexrgb(t[enc]), fond); s = 7.0 if nom == "contraste élevé" else 4.5
            ok = r >= s; echecs += (not ok)
            lignes.append(f"| {libelle} | {t[enc]} sur teinte composée | {r:.2f}:1 | {s:.1f} | {'passe' if ok else '**échec**'} |")
    lignes.append("")
lignes.append(f"**Total : {echecs} échec(s).**")
os.makedirs(f"{R}/recette", exist_ok=True); open(f"{R}/recette/contrastes.md", "w").write("\n".join(lignes))
print("échecs :", echecs); print("\n".join(l for l in lignes if "échec**" in l or l.startswith("## ")))
