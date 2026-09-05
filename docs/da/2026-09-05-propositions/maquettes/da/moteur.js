/* Lit ?d=1|2|3&theme=clair|sombre&taille=14|16|18&contraste=1&mouvement=reduit
   et pose les attributs que les jetons réels de THÉRÈSE attendent. */
(function () {
  const p = new URLSearchParams(location.search);
  const h = document.documentElement;
  h.dataset.d = p.get('d') || '2';
  if (p.get('theme') === 'sombre') h.dataset.theme = 'dark'; else delete h.dataset.theme;
  if (p.get('contraste') === '1') h.dataset.highContrast = 'true'; else delete h.dataset.highContrast;
  if (p.get('mouvement') === 'reduit') h.dataset.reducedMotion = 'true'; else delete h.dataset.reducedMotion;
  const t = p.get('taille'); h.style.fontSize = (t === '14' || t === '18') ? t + 'px' : '16px';
  h.style.colorScheme = h.dataset.theme === 'dark' ? 'dark' : 'light';
  window.addEventListener('message', (e) => {
    if (!e.data || e.data.type !== 'therese-da') return;
    const u = new URL(location.href); Object.entries(e.data.params || {}).forEach(([k, v]) => u.searchParams.set(k, v));
    location.replace(u.toString());
  });
})();
