#!/usr/bin/env python3
"""Dépôt de propositions DA/UX de THÉRÈSE : un sommaire, une page « socle commun » à trancher
d'abord, puis une page par écran. Méthode issue de la passe COCO du 05/09 : comparaison avant /
après à l'échelle 1:1 par bascule (côte à côte en option), largeur, taille de texte, thème,
contraste élevé et mouvement réduit choisis explicitement, décision datée par écran avec la
direction retenue et une réserve. Tout est local à la prévisualisation, sans réseau."""
import json, os, html, datetime
D = os.path.dirname(os.path.abspath(__file__))
ECRANS = json.load(open(f"{D}/ecrans.json"))
DIRS = [("1", "Continuité", "papier, encre, serif éditorial sur quelques grands titres, couture rare ; encres de THÉRÈSE conservées"),
        ("2", "Application affinée", "la DA validée en mai poussée au bout : Jakarta et Inter, pilule cyan, quatre domaines, deux rythmes (lecture et densité)"),
        ("3", "Deux mondes", "ce que dit THÉRÈSE sur navy avec lueur, l'humain et les vues d'administration sur la surface claire")]
LARGEURS = [("1280", "800"), ("1024", "700"), ("800", "600")]
JOUR = "5 septembre 2026"
CSS = """
:root{--papier:#FAFAF7;--encre:#0F172A;--encre2:#475569;--filet:#E2E4E9;--navy:#0B1226;--lueur:#E6EDF7;--bleu:#2451FF;--cyan:#0891B2}
*{box-sizing:border-box}html{color-scheme:light}body{margin:0;background:var(--papier);color:var(--encre);font:15px/1.55 Inter,system-ui,-apple-system,"Segoe UI",sans-serif}
a{color:var(--bleu)}header{display:flex;align-items:center;gap:16px;padding:14px 24px;border-bottom:1px solid var(--filet);background:#fff;position:sticky;top:0;z-index:2}
header h1{font:400 22px/1.1 "Instrument Serif",Georgia,serif;margin:0;letter-spacing:-.012em}header .fil{color:var(--encre2);font-size:13px}
.couture{height:4px;background:linear-gradient(90deg,#2451FF 0%,#22D3EE 22%,#10B981 42%,#F59E0B 62%,#E11D8D 82%,#8B5CF6 100%)}
main{max-width:1560px;margin:0 auto;padding:20px 24px 60px}
nav.ecrans{display:flex;gap:8px;flex-wrap:wrap;margin:0 0 18px}nav.ecrans a{font-size:13px;text-decoration:none;color:var(--encre);border:1px solid var(--filet);border-radius:999px;padding:6px 12px;background:#fff}
nav.ecrans a[aria-current=page]{background:var(--encre);color:#fff;border-color:var(--encre)}
.texte{font-size:14px;max-width:900px}.texte p{margin:0 0 8px}.texte strong{color:var(--encre)}
.controles{display:flex;gap:10px;align-items:center;flex-wrap:wrap;padding:10px 12px;background:#fff;border:1px solid var(--filet);border-radius:14px;margin-bottom:12px}
.groupe{display:inline-flex;gap:2px;align-items:center;padding:3px;border:1px solid var(--filet);border-radius:999px;background:#fff}
.groupe span{font-size:12px;color:var(--encre2);padding:0 8px 0 6px}
.groupe button{font:600 13px/1 Inter,sans-serif;border:0;background:transparent;color:var(--encre);border-radius:999px;padding:8px 12px;cursor:pointer}
.groupe button[aria-pressed=true]{background:var(--encre);color:#fff}
button:focus-visible{outline:3px solid var(--cyan);outline-offset:2px}
.scene{background:#fff;border:1px solid var(--filet);border-radius:14px;overflow:auto;padding:12px}
.cadres{display:flex;gap:12px;justify-content:center;align-items:flex-start;min-width:min-content}
.cadre{position:relative;flex:none;border:1px solid var(--filet);border-radius:8px;overflow:hidden;background:#fff;box-shadow:0 10px 30px -18px rgba(15,23,42,.35)}
.cadre img{display:block;width:100%;height:auto}.cadre iframe{display:block;border:0;width:100%;height:100%}
.cadre .etiquette{position:absolute;right:8px;bottom:8px;font:600 11px/1 Inter;letter-spacing:.06em;text-transform:uppercase;background:rgba(15,23,42,.85);color:#fff;padding:5px 8px;border-radius:999px;pointer-events:none}
.cadre .absent{position:absolute;inset:0;display:grid;place-items:center;background:repeating-linear-gradient(45deg,#fff 0 12px,#F3F4F6 12px 24px);color:var(--encre2);font-size:14px}
.legende{display:flex;justify-content:space-between;gap:12px;font-size:12px;color:var(--encre2);padding:8px 4px 0;flex-wrap:wrap}
.deux{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-top:16px}@media(max-width:1000px){.deux{grid-template-columns:1fr}}
.bloc{background:#fff;border:1px solid var(--filet);border-radius:14px;padding:14px 16px}
.bloc h2{font:600 13px/1 Inter,sans-serif;letter-spacing:.06em;text-transform:uppercase;color:var(--encre2);margin:0 0 10px}
.decision{display:flex;gap:8px;align-items:center;flex-wrap:wrap}
.decision button{font:600 13px/1 Inter,sans-serif;border:1px solid var(--filet);background:#fff;color:var(--encre);border-radius:999px;padding:9px 14px;cursor:pointer}
.decision button[aria-pressed=true]{background:var(--encre);color:#fff;border-color:var(--encre)}
.decision .note{flex:1;min-width:220px;font:14px Inter,sans-serif;padding:8px 10px;border:1px solid var(--filet);border-radius:8px}
.decision .horodatage{width:100%;font-size:12px;color:var(--encre2)}
.liste{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:16px;margin-top:16px}
.carte{display:block;text-decoration:none;color:inherit;background:#fff;border:1px solid var(--filet);border-radius:14px;overflow:hidden}
.carte img{width:100%;height:170px;object-fit:cover;object-position:top;display:block;border-bottom:1px solid var(--filet)}.carte div{padding:12px 14px}.carte b{display:block;font-size:15px;margin-bottom:4px}.carte span{font-size:12px;color:var(--encre2)}
.carte.socle{border-color:var(--encre)}.carte.socle div{background:var(--encre);color:#fff}.carte.socle span{color:#CBD5E1}
.recap{margin-top:24px}.recap textarea{width:100%;min-height:140px;font:13px/1.5 "IBM Plex Mono",ui-monospace,monospace;border:1px solid var(--filet);border-radius:8px;padding:10px}
.pill{display:inline-block;font:600 11px/1 Inter;letter-spacing:.05em;text-transform:uppercase;padding:4px 8px;border-radius:999px;background:#EEF2FF;color:#1E3A8A;margin-right:6px}
"""
JS = r"""
const P=document.body.dataset;const ecran=P.ecran;const etats=JSON.parse(P.etats||'{}');const captures=JSON.parse(P.captures||'[]');
const L=k=>localStorage.getItem('therese-da-'+k);const S=(k,v)=>localStorage.setItem('therese-da-'+k,v);
let st={vue:L('vue')||'apres',d:L('d')||'2',theme:L('theme')||'clair',largeur:L('largeur')||'1280',taille:L('taille')||'16',contraste:L('contraste')||'0',mouvement:L('mouvement')||'0',etat:'normal',capture:0};
const H={ '1280':800,'1024':700,'800':600 };
function urlMaquette(){const u=new URLSearchParams({d:st.d,theme:st.theme,taille:st.taille});if(st.contraste==='1')u.set('contraste','1');if(st.mouvement==='1')u.set('mouvement','reduit');if(st.etat!=='normal')u.set('etat',st.etat);return 'maquettes/'+ecran+'.html?'+u;}
function cadreAvant(){const c=captures[st.capture]||captures[0];return c?`<div class="cadre" style="width:${st.largeur}px"><span class="etiquette">Avant · 0.66 · capture</span><img src="captures/${c}.jpg" alt="Capture ${c} de THÉRÈSE 0.66"></div>`:'';}
function cadreApres(){const abs=P.maquette==='1'?'':'<div class="absent">Maquette en cours de fabrication</div>';return `<div class="cadre" style="width:${st.largeur}px;height:${H[st.largeur]}px"><span class="etiquette">Après · direction ${st.d} · ${st.theme}</span><iframe title="Maquette ${ecran}" src="${urlMaquette()}"></iframe>${abs}</div>`;}
function rendre(){if(!ecran)return;const s=document.getElementById('cadres');
 s.innerHTML=st.vue==='avant'?cadreAvant():st.vue==='apres'?cadreApres():cadreAvant()+cadreApres();
 document.querySelectorAll('[data-k]').forEach(b=>b.setAttribute('aria-pressed',String(st[b.dataset.k])===b.dataset.v));
 const leg=document.getElementById('legende');leg.innerHTML=`<span>${st.vue==='avant'?'Capture réelle de la 0.66 (fenêtre ≈1181 px, réduite en JPEG 1300 px) : '+(captures[st.capture]||'').replace(/^\d+[a-z]?-/,'').replace(/-/g,' '):'Maquette HTML à l\'échelle 1:1, '+st.largeur+'×'+H[st.largeur]+' px, direction '+st.d+', thème '+st.theme+', texte '+st.taille+' px'+(st.contraste==='1'?', contraste élevé':'')+(st.mouvement==='1'?', mouvement réduit':'')+', état « '+(etats[st.etat]||st.etat)+' »'}</span><span>Référence : THÉRÈSE 0.66.1, commit b4ffddbe, ${document.body.dataset.jour}</span>`;}
document.querySelectorAll('[data-k]').forEach(b=>b.addEventListener('click',()=>{const k=b.dataset.k,v=b.dataset.v;if(k==='capture'){st.capture=(st.capture+1)%Math.max(captures.length,1);}else{st[k]=v;if(['vue','d','theme','largeur','taille','contraste','mouvement'].includes(k))S(k,v);}rendre();}));
function cle(){return 'therese-da-decision-'+ecran;}
function chargerDecision(){const v=JSON.parse(localStorage.getItem(cle())||'{}');document.querySelectorAll('.decision [data-choix]').forEach(b=>b.setAttribute('aria-pressed',b.dataset.choix===v.choix));const n=document.querySelector('.decision .note');if(n)n.value=v.note||'';const h=document.querySelector('.decision .horodatage');if(h)h.textContent=v.quand?`Décision « ${v.choix} » enregistrée le ${v.quand}, direction ${v.direction}, thème ${v.theme}.`:'Aucune décision enregistrée pour cet écran.';}
document.querySelectorAll('.decision [data-choix]').forEach(b=>b.addEventListener('click',()=>{const v=JSON.parse(localStorage.getItem(cle())||'{}');v.choix=b.dataset.choix;v.direction=st.d;v.theme=st.theme;v.quand=new Date().toLocaleString('fr-FR');v.version='0.66.1';localStorage.setItem(cle(),JSON.stringify(v));chargerDecision();}));
const note=document.querySelector('.decision .note');if(note)note.addEventListener('input',()=>{const v=JSON.parse(localStorage.getItem(cle())||'{}');v.note=note.value;localStorage.setItem(cle(),JSON.stringify(v));});
if(ecran){rendre();chargerDecision();}
const recap=document.getElementById('recap');if(recap){const l=[];for(const k of Object.keys(localStorage)){if(k.startsWith('therese-da-decision-')){const v=JSON.parse(localStorage.getItem(k));l.push(`${k.replace('therese-da-decision-','')} : ${v.choix||'?'} · direction ${v.direction||'?'} · ${v.theme||''} · ${v.quand||''}${v.note?' · '+v.note:''}`);}}
 recap.value=l.length?l.sort().join('\n'):'Aucune décision enregistrée dans ce navigateur.';document.getElementById('copier')?.addEventListener('click',()=>navigator.clipboard.writeText(recap.value));}
"""
def page(titre, corps, attrs=""):
    return f"""<!doctype html><html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{html.escape(titre)} · THÉRÈSE, propositions DA</title><style>{CSS}</style></head>
<body data-jour="{JOUR}" {attrs}><header><h1>THÉRÈSE, propositions DA et UX</h1><span class="fil">{JOUR} · 0.66.1 · {html.escape(titre)}</span></header><div class="couture"></div><main>{corps}</main><script>{JS}</script></body></html>"""
def nav(courant):
    items = [("index.html","Sommaire"),("socle.html","Socle commun")] + [(f"{e['id']}.html", e["titre"]) for e in ECRANS]
    return '<nav class="ecrans">' + "".join(f'<a href="{h}"{" aria-current=\"page\"" if h==courant else ""}>{html.escape(t)}</a>' for h,t in items) + "</nav>"
def controles(e, socle=False):
    g = lambda label, k, opts: f'<div class="groupe"><span>{label}</span>' + "".join(f'<button type="button" data-k="{k}" data-v="{v}" aria-pressed="false">{html.escape(t)}</button>' for v,t in opts) + '</div>'
    parts = []
    if not socle: parts.append(g("Vue","vue",[("avant","Avant"),("apres","Après"),("cote","Côte à côte")]))
    parts.append(g("Direction","d",[(k, f"{k} {n}") for k,n,_ in DIRS]))
    parts.append(g("Thème","theme",[("clair","Clair"),("sombre","Sombre")]))
    parts.append(g("Largeur","largeur",[(w, f"{w}×{h}") for w,h in LARGEURS]))
    parts.append(g("Texte","taille",[("14","14"),("16","16"),("18","18")]))
    parts.append(g("Accessibilité","contraste",[("1","Contraste élevé")]) .replace('aria-pressed="false">Contraste élevé','aria-pressed="false">Contraste élevé'))
    parts.append(g("","mouvement",[("1","Mouvement réduit")]))
    if e and e.get("etats"): parts.append(g("État","etat",list(e["etats"].items())))
    if e and not socle: parts.append('<div class="groupe"><span>Capture</span><button type="button" data-k="capture" data-v="suivante">Suivante</button></div>')
    return '<div class="controles">' + "".join(parts) + '</div>'
# toggles contraste / mouvement : valeur 1 <-> 0
JS = JS.replace("st[k]=v;", "st[k]=(k==='contraste'||k==='mouvement')?(st[k]==='1'?'0':'1'):v;")
# Sommaire
cartes = '<a class="carte socle" href="socle.html"><img src="recette/socle-d2-clair.png" alt="" onerror="this.style.display=\'none\'"><div><b>0 · Socle commun, à trancher d\'abord</b><span>Polices, couleurs, boutons, rail, tiroir, étiquettes : une direction pour toute l\'application, puis les écrans.</span></div></a>'
cartes += "".join(f'<a class="carte" href="{e["id"]}.html"><img src="captures/{e["captures"][0]}.jpg" alt=""><div><b>{html.escape(e["titre"])}</b><span>{html.escape(e["reussir"])}</span></div></a>' for e in ECRANS)
intro = f"""<div class="texte"><p><strong>Comment lire.</strong> D'abord la page <a href="socle.html">socle commun</a> : elle montre les polices, les couleurs, les boutons et les étiquettes dans les trois directions ; c'est là que se choisit une direction pour toute l'application. Ensuite, une page par écran : « Avant » montre la capture réelle de la 0.66, « Après » une maquette HTML qui réagit à l'échelle 1:1 (thème, largeur, taille du texte, contraste élevé, mouvement réduit, états). Tu décides par écran : oui, non, plus tard, avec une note. Le récapitulatif en bas se copie en un clic.</p>
<p><strong>Les trois directions.</strong> {' '.join(f'<span class="pill">{k}</span>{html.escape(n)} : {html.escape(t)}.' for k,n,t in DIRS)}</p>
<p><strong>Ce qui ne bouge pas.</strong> Les encres de THÉRÈSE (4,5:1 sur leurs fonds), les deux rayons, Jakarta en tête des titres, les tests de charte du dépôt. Ce qui est déjà décidé côté UX (plan du 27/08, propositions acceptées) est rappelé sous chaque écran et n'est pas à rejuger. Coût indicatif d'intégration (estimation COCO du 05/09, hors PDF) : direction 2, 10 à 18 jours ; direction 1, 18 à 30 ; direction 3, 20 à 35.</p></div>"""
recap = '<div class="bloc recap"><h2>Mes décisions (ce navigateur)</h2><textarea id="recap" readonly></textarea><p><button id="copier" class="decision" style="font:600 13px Inter;border:1px solid var(--filet);border-radius:999px;padding:9px 14px;background:#fff;cursor:pointer">Copier le récapitulatif</button></p></div>'
open(f"{D}/index.html","w").write(page("Sommaire", nav("index.html") + intro + f'<div class="liste">{cartes}</div>' + recap))
# Socle
socle_corps = nav("socle.html") + controles({"etats":None}, socle=True) + '<div class="scene"><div class="cadres" id="cadres"></div><div class="legende" id="legende"></div></div>' + """
<div class="deux"><div class="bloc"><h2>Ce que cette page tranche</h2><div class="texte"><p>Une seule direction pour les polices, les couleurs de fond et d'encre, les boutons, le rail, les étiquettes et le tiroir. Les écrans en héritent ; ils ne rejugent pas ces choix. Dans chaque direction, le thème sombre « Signature » et le contraste élevé sont au même niveau que le clair.</p><p><strong>Direction 2</strong> est le socle recommandé par la passe COCO (le plus solide, le moins coûteux). <strong>Direction 1</strong> ajoute le registre du site (papier, serif, couture) sans toucher aux encres. <strong>Direction 3</strong> réserve le navy à ce que dit THÉRÈSE.</p></div></div>
<div class="bloc"><h2>Ta décision sur le socle</h2><div class="decision"><button type="button" data-choix="oui">Oui</button><button type="button" data-choix="non">Non</button><button type="button" data-choix="plus tard">Plus tard</button><input class="note" type="text" placeholder="Une réserve, si tu veux (mémorisée dans ce navigateur)"><span class="horodatage"></span></div></div></div>"""
open(f"{D}/socle.html","w").write(page("Socle commun", socle_corps, 'data-ecran="socle" data-etats="{}" data-captures="[]" data-maquette="%s"' % ("1" if os.path.exists(f"{D}/maquettes/socle.html") else "0")))
# Écrans
for i,e in enumerate(ECRANS):
    exists = os.path.exists(f"{D}/maquettes/{e['id']}.html")
    prev = ECRANS[i-1]["id"]+".html" if i else "socle.html"; nxt = ECRANS[i+1]["id"]+".html" if i+1<len(ECRANS) else "index.html"
    corps = nav(f"{e['id']}.html") + controles(e) + '<div class="scene"><div class="cadres" id="cadres"></div><div class="legende" id="legende"></div></div>' + f"""
<div class="deux">
 <div class="bloc"><h2>Ce que l'écran doit réussir</h2><div class="texte"><p>{html.escape(e['reussir'])}</p><p><strong>Critères de recette.</strong> {html.escape(e['criteres'])}</p><p><strong>Déjà décidé côté UX, pas à rejuger.</strong> {html.escape(e['ux_decide'])}</p></div></div>
 <div class="bloc"><h2>Ta décision pour cet écran</h2><div class="decision"><button type="button" data-choix="oui">Oui</button><button type="button" data-choix="non">Non</button><button type="button" data-choix="plus tard">Plus tard</button><input class="note" type="text" placeholder="Une réserve, si tu veux (mémorisée dans ce navigateur)"><span class="horodatage"></span></div><p class="texte" style="margin-top:10px;font-size:12px;color:var(--encre2)">« Plus tard » conserve l'existant. La décision enregistre l'écran, la direction et le thème affichés, la version et l'heure.</p></div>
</div>
<p style="display:flex;justify-content:space-between;margin-top:18px"><a href="{prev}">Précédent</a><a href="{nxt}">Suivant</a></p>"""
    attrs = f'data-ecran="{e["id"]}" data-etats="{html.escape(json.dumps(e.get("etats",{}),ensure_ascii=False), quote=True)}" data-captures="{html.escape(json.dumps(e["captures"]), quote=True)}" data-maquette="{"1" if exists else "0"}"'
    open(f"{D}/{e['id']}.html","w").write(page(e["titre"], corps, attrs))
print("généré :", len(ECRANS)+2, "pages ;", sum(os.path.exists(f"{D}/maquettes/{e['id']}.html") for e in ECRANS), "maquettes présentes")
