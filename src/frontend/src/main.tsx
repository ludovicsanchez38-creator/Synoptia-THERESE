import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import App from './App';
// Polices embarquées : THÉRÈSE ne doit jamais se rabattre sur celle du
// système (SF Pro / Segoe UI), qui est aussi celle de Claude et de ChatGPT.
// Sous-ensemble latin uniquement, aucun appel réseau : l'application de
// bureau doit fonctionner hors ligne.
import '@fontsource/inter/latin-400.css';
import '@fontsource/inter/latin-500.css';
import '@fontsource/inter/latin-600.css';
import '@fontsource/inter/latin-700.css';
import '@fontsource/plus-jakarta-sans/latin-600.css';
import '@fontsource/plus-jakarta-sans/latin-700.css';
import '@fontsource/plus-jakarta-sans/latin-800.css';
import './styles/globals.css';

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>
);
