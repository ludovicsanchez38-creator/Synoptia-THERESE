/**
 * Registre des textes de l'onboarding (lot C, 0.48).
 *
 * Extrait des chaînes inline de SecurityStep et LLMStep pour que le test
 * de lexique (src/lib/lexique.test.ts) porte sur un registre exporté.
 * Lexique : docs/RULES-DESIGN.md — jamais de LLM/provider/MCP/Qdrant à
 * l'écran standard.
 */

export interface RisqueOnboarding {
  id: 'cloud' | 'connecteurs' | 'fichiers' | 'web' | 'voix';
  title: string;
  description: string;
  severity: 'high' | 'medium' | 'low';
}

export const TEXTES_ONBOARDING = {
  choixServiceIA: {
    titre: 'Choisis ton service d’IA',
    sousTitre: 'Configure le modèle d’IA à utiliser',
  },
  risques: [
    {
      id: 'cloud',
      title: 'Services d’IA cloud',
      description:
        'Tes messages sont envoyés aux serveurs des services d’IA (Anthropic, OpenAI, Gemini...). Ne partage jamais de données sensibles (mots de passe, secrets, données clients).',
      severity: 'high',
    },
    {
      id: 'connecteurs',
      title: 'Connecteurs',
      description:
        'Les connecteurs peuvent exécuter des commandes, lire et écrire des fichiers sur ta machine. Active uniquement les services de confiance.',
      severity: 'high',
    },
    {
      id: 'fichiers',
      title: 'Accès fichiers',
      description:
        'THÉRÈSE peut lire tes fichiers locaux pour le contexte. Les fichiers indexés sont stockés localement, sur ta machine.',
      severity: 'medium',
    },
    {
      id: 'web',
      title: 'Recherche Web',
      description:
        'Les recherches sont envoyées à DuckDuckGo ou Google (selon le moteur choisi). Tes requêtes peuvent être tracées.',
      severity: 'low',
    },
    {
      id: 'voix',
      title: 'Transcription vocale',
      description:
        'L’audio est envoyé à Groq pour transcription. Ne dicte pas d’informations confidentielles.',
      severity: 'medium',
    },
  ] as const satisfies readonly RisqueOnboarding[],
} as const;
