#!/usr/bin/env python3
"""Extrait les jetons réels de src/frontend/src/styles/globals.css vers maquettes/da/tokens.css.
Cherche les sélecteurs en début de ligne : un commentaire d'en-tête cite aussi [data-theme="dark"]."""
import re, os
R = os.path.dirname(os.path.abspath(__file__)); repo = os.path.abspath(f"{R}/../../..")
css = open(f"{repo}/src/frontend/src/styles/globals.css").read()
def bloc(sel_regex):
    m = re.search(sel_regex, css, flags=re.M)
    if not m: return ''
    j = css.find('{', m.end()-1); depth = 0; k = j
    while k < len(css):
        if css[k] == '{': depth += 1
        elif css[k] == '}':
            depth -= 1
            if depth == 0: break
        k += 1
    body = re.sub(r'/\*.*?\*/', '', css[j+1:k], flags=re.S)
    return '\n'.join('  ' + l.strip() for l in body.splitlines() if l.strip().startswith('--'))
clair = bloc(r'^@theme\s*\{'); sombre = bloc(r'^\[data-theme="dark"\]\s*\{'); hc = bloc(r'^\[data-high-contrast="true"\]\s*\{')
out = f"""/* Jetons réels de THÉRÈSE, extraits de src/frontend/src/styles/globals.css.
   Ne pas éditer à la main : régénérer par extract-tokens.py. Les maquettes consomment ces variables ;
   les directions n'en redéfinissent qu'un sous-ensemble déclaré. */
:root {{
{clair}
}}
[data-theme="dark"] {{
{sombre}
}}
[data-high-contrast="true"] {{
{hc}
}}
"""
open(f"{R}/maquettes/da/tokens.css", "w").write(out)
print("clair", clair.count('--'), "sombre", sombre.count('--'), "contraste élevé", hc.count('--'))
print("sombre bg :", re.search(r'--color-bg:\s*([^;]+)', sombre).group(1) if '--color-bg' in sombre else '?')
