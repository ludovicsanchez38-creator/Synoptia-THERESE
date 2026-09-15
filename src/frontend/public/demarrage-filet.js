// B-805 (cycle 9) : le splash est un calque plein écran en -webkit-app-region: drag.
// Si le bundle ne monte jamais (erreur de chargement), il n'offrait aucune issue.
// Ce script tourne hors du bundle : après trente secondes sans montage de React
// (main.tsx pose window.__thereseMonte), il le dit et propose de relancer.
(function () {
  window.setTimeout(function () {
    if (window.__thereseMonte) return;
    var splash = document.getElementById('therese-splash');
    if (!splash) return;
    var statut = splash.querySelector('.therese-status');
    if (statut) statut.textContent = 'Le démarrage prend plus de temps que prévu.';
    var bouton = document.createElement('button');
    bouton.type = 'button';
    bouton.textContent = 'Relancer THÉRÈSE';
    bouton.setAttribute('style', 'margin-top:16px;min-height:36px;padding:0 16px;border:1px solid currentColor;border-radius:8px;background:transparent;color:inherit;font:inherit;cursor:pointer;-webkit-app-region:no-drag;');
    bouton.addEventListener('click', function () { window.location.reload(); });
    splash.appendChild(bouton);
  }, 30000);
})();
