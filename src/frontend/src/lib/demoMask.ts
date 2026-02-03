/**
 * THÉRÈSE v2 - Demo Mask Utilities
 *
 * Utilitaire pur (pas de React) pour le masquage des données en mode démo.
 * 15 personas français fictifs, hash déterministe, masquage contacts/projets/texte libre.
 */

// ============================================================
// Personas fictifs français
// ============================================================

export interface DemoPersona {
  firstName: string;
  lastName: string;
  company: string;
  sector: string;
  email: string;
}

export const DEMO_PERSONAS: DemoPersona[] = [
  { firstName: 'Camille', lastName: 'Moreau', company: 'Atelier Moreau', sector: 'Céramiste', email: 'camille@ateliermoreau.fr' },
  { firstName: 'Julien', lastName: 'Dupont', company: 'Dupont Coaching', sector: 'Coach pro', email: 'julien@dupontcoaching.fr' },
  { firstName: 'Nathalie', lastName: 'Lefebvre', company: 'NL Conseil', sector: 'Consultante RH', email: 'nathalie@nlconseil.fr' },
  { firstName: 'Antoine', lastName: 'Bernard', company: 'Bernard & Fils', sector: 'Ébéniste', email: 'antoine@bernardetfils.fr' },
  { firstName: 'Sophie', lastName: 'Martin', company: 'Fleur de Sel', sector: 'Traiteur', email: 'sophie@fleurdesel.fr' },
  { firstName: 'Thomas', lastName: 'Petit', company: 'TP Digital', sector: 'Consultant SEO', email: 'thomas@tpdigital.fr' },
  { firstName: 'Claire', lastName: 'Robert', company: 'Claire Robert Photo', sector: 'Photographe', email: 'claire@clairerobert.fr' },
  { firstName: 'Maxime', lastName: 'Dubois', company: 'Dubois Formation', sector: 'Formateur', email: 'maxime@duboisformation.fr' },
  { firstName: 'Émilie', lastName: 'Laurent', company: 'EL Architecture', sector: 'Archi intérieur', email: 'emilie@elarchitecture.fr' },
  { firstName: 'Romain', lastName: 'Garcia', company: 'Garcia Paysages', sector: 'Paysagiste', email: 'romain@garciapaysages.fr' },
  { firstName: 'Aurélie', lastName: 'Fournier', company: 'Bien-Être & Vous', sector: 'Naturopathe', email: 'aurelie@bienetreetous.fr' },
  { firstName: 'Nicolas', lastName: 'Girard', company: 'Girard Compta', sector: 'Expert-comptable', email: 'nicolas@girardcompta.fr' },
  { firstName: 'Marine', lastName: 'Leroy', company: 'ML Communication', sector: 'Consultante com', email: 'marine@mlcommunication.fr' },
  { firstName: 'Pierre', lastName: 'Morel', company: 'Morel Pâtisserie', sector: 'Pâtissier', email: 'pierre@morelpatisserie.fr' },
  { firstName: 'Isabelle', lastName: 'Roux', company: 'IR Coaching', sector: 'Coach de vie', email: 'isabelle@ircoaching.fr' },
];

// Noms de projets fictifs
const DEMO_PROJECT_NAMES = [
  'Refonte site vitrine',
  'Formation équipe',
  'Stratégie digitale',
  'Accompagnement croissance',
  'Optimisation processus',
  'Lancement nouveau produit',
  'Plan communication',
  'Audit organisationnel',
  'Transformation numérique',
  'Développement commercial',
  'Identité visuelle',
  'Coaching direction',
  'Prospection LinkedIn',
  'Automatisation workflows',
  'Bilan de compétences',
];

// ============================================================
// Hash déterministe (djb2)
// ============================================================

/**
 * Hash djb2 - déterministe, même entrée = même sortie.
 * Retourne un index entre 0 et max-1.
 */
export function hashToIndex(str: string, max: number): number {
  let hash = 5381;
  for (let i = 0; i < str.length; i++) {
    hash = ((hash << 5) + hash + str.charCodeAt(i)) & 0xffffffff;
  }
  return Math.abs(hash) % max;
}

/**
 * Génère un numéro de téléphone fictif depuis un hash.
 */
function hashToPhone(str: string): string {
  const h = hashToIndex(str + '_phone', 90000000) + 10000000;
  const digits = h.toString().padStart(8, '0');
  return `06 ${digits.slice(0, 2)} ${digits.slice(2, 4)} ${digits.slice(4, 6)} ${digits.slice(6, 8)}`;
}

// ============================================================
// Masquage contacts
// ============================================================

export interface MaskableContact {
  id: string;
  first_name?: string | null;
  last_name?: string | null;
  company?: string | null;
  email?: string | null;
  phone?: string | null;
}

/**
 * Masque un contact avec un persona fictif.
 * Retourne une copie avec les champs PII remplacés.
 */
export function maskContact<T extends MaskableContact>(contact: T): T {
  const key = `${contact.first_name || ''}${contact.last_name || ''}`.toLowerCase();
  if (!key) return contact;

  const idx = hashToIndex(key, DEMO_PERSONAS.length);
  const persona = DEMO_PERSONAS[idx];

  return {
    ...contact,
    first_name: persona.firstName,
    last_name: persona.lastName,
    company: contact.company ? persona.company : null,
    email: contact.email ? persona.email : null,
    phone: contact.phone ? hashToPhone(key) : null,
  };
}

// ============================================================
// Masquage projets
// ============================================================

export interface MaskableProject {
  id: string;
  name: string;
  contact_id?: string | null;
}

/**
 * Masque un projet avec un nom fictif.
 */
export function maskProject<T extends MaskableProject>(project: T): T {
  const idx = hashToIndex(project.name.toLowerCase(), DEMO_PROJECT_NAMES.length);

  return {
    ...project,
    name: DEMO_PROJECT_NAMES[idx],
  };
}

// ============================================================
// Construction de la Map de remplacement
// ============================================================

/**
 * Construit une Map<réel, fictif> pour le remplacement dans le texte libre.
 * Les clés sont triées par longueur DESC pour éviter les remplacements partiels.
 */
export function buildReplacementMap(
  contacts: Array<{ first_name?: string | null; last_name?: string | null; company?: string | null; email?: string | null }>,
  projects: Array<{ name?: string | null }>
): Map<string, string> {
  const map = new Map<string, string>();

  for (const contact of contacts) {
    const key = `${contact.first_name || ''}${contact.last_name || ''}`.toLowerCase();
    if (!key) continue;

    const idx = hashToIndex(key, DEMO_PERSONAS.length);
    const persona = DEMO_PERSONAS[idx];

    // Nom complet
    const fullName = `${contact.first_name || ''} ${contact.last_name || ''}`.trim();
    const fakeFullName = `${persona.firstName} ${persona.lastName}`;
    if (fullName) map.set(fullName, fakeFullName);

    // Prénom seul
    if (contact.first_name) map.set(contact.first_name, persona.firstName);

    // Nom seul (seulement si >= 3 caractères pour éviter les faux positifs)
    if (contact.last_name && contact.last_name.length >= 3) {
      map.set(contact.last_name, persona.lastName);
    }

    // Entreprise
    if (contact.company) map.set(contact.company, persona.company);

    // Email
    if (contact.email) map.set(contact.email, persona.email);
  }

  for (const project of projects) {
    if (!project.name) continue;
    const idx = hashToIndex(project.name.toLowerCase(), DEMO_PROJECT_NAMES.length);
    map.set(project.name, DEMO_PROJECT_NAMES[idx]);
  }

  return map;
}

// ============================================================
// Masquage texte libre
// ============================================================

/** Cache pour la regex compilée */
let _cachedRegex: RegExp | null = null;
let _cachedKeys: string | null = null;

/**
 * Remplace les noms réels par les noms fictifs dans un texte libre.
 * Utilise une regex compilée avec alternation + word-boundary.
 * Tri par longueur DESC pour éviter les remplacements partiels.
 */
export function maskText(text: string, replacements: Map<string, string>): string {
  if (!text || replacements.size === 0) return text;

  // Trier les clés par longueur DESC
  const keys = Array.from(replacements.keys()).sort((a, b) => b.length - a.length);

  // Construire la regex (cache si même ensemble de clés)
  const keysSignature = keys.join('|');
  if (_cachedKeys !== keysSignature) {
    const escaped = keys.map((k) => k.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'));
    _cachedRegex = new RegExp(`\\b(${escaped.join('|')})\\b`, 'gi');
    _cachedKeys = keysSignature;
  }

  if (!_cachedRegex) return text;

  // Reset lastIndex pour les regex globales
  _cachedRegex.lastIndex = 0;

  return text.replace(_cachedRegex, (match) => {
    // Chercher le remplacement en case-insensitive
    for (const [key, value] of replacements) {
      if (key.toLowerCase() === match.toLowerCase()) {
        return value;
      }
    }
    return match;
  });
}
