#!/usr/bin/env python3
"""Assemble chaque fragment (_fragments/<ecran>.html : <style>, <main>, <script>) dans la coque commune."""
import os, glob, re
R=os.path.dirname(os.path.abspath(__file__))
coque=open(f"{R}/da/_coque.html").read()
TITRES={"accueil":"Accueil, brief du jour","devis":"Devis et factures","decision":"Décision","contacts":"Contacts et pipeline","projets":"Projets et tâches","agenda":"Agenda","tiroir":"Tiroir et catalogue","parametres":"Paramètres","socle":"Socle commun"}
for f in sorted(glob.glob(f"{R}/_fragments/*.html")):
    e=os.path.basename(f)[:-5]; frag=open(f).read()
    rail=re.sub(r'aria-current="page"','',coque)
    cible={"accueil":"Accueil","devis":"Fichiers","decision":"Conversations","contacts":"Fichiers","projets":"Fichiers","agenda":"Fichiers","tiroir":"Conversations","parametres":"Paramètres"}.get(e)
    if cible: rail=rail.replace(f'<button type="button" aria-label="{cible}"', f'<button type="button" aria-current="page" aria-label="{cible}"',1)
    html=f"""<!doctype html><html lang="fr" data-d="2"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{TITRES.get(e,e)} · maquette THÉRÈSE</title>
<link rel="stylesheet" href="da/tokens.css"><link rel="stylesheet" href="da/base.css"><link rel="stylesheet" href="da/d1.css"><link rel="stylesheet" href="da/d2.css"><link rel="stylesheet" href="da/d3.css">
<script src="da/moteur.js"></script>
{frag[:frag.find('</style>')+8] if '<style' in frag else ''}</head>
<body><div class="app">
 {rail}{frag[frag.find('<main'):] if '<main' in frag else frag}
 </div>
</div>
</body></html>"""
    # le fragment contient <style>…</style> (dans head) puis <main>…</main> et <script>
    open(f"{R}/{e}.html","w").write(html); print("assemblé", e)
