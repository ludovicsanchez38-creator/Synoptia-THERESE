# Banc Ollama R3 — 21 octobre 2026

Banc réel fourni par Syn : `http://127.0.0.1:11435`, CPU, `qwen3:1.7b`. Aucun autre fournisseur, aucun téléchargement, une requête au modèle à la fois. Code initial : archive `987c3675` ; code corrigé : R3-1 à R3-6, puis compatibilité R3-7 et correction de typage R3-8 sans changement de ce chemin réel. Script : `scripts/banc_ollama_r3.py`.

Le backend tourne dans un processus avec HOME, caches, temporaires et données fictives dans le worktree. Les routes HTTP utilisent ASGI, sans ouvrir un autre port. `/api/show` est lu sans modification du banc ; la fenêtre du modèle qu'il annonce est reproduite ci-dessous. La configuration de départ du service a `context_window=32768`, `max_tokens=384`. Le script fixe `think=false` et la température à zéro dans les deux passes. Le profil fait exactement 2500 caractères ; la règle 3 commence au caractère 2241 (index à partir de zéro). Le cache THERESE.md est amorcé avant le POST qui enregistre le document.

Le verdict mesure le rappel demandé : profil intégral transmis, nom de Camille retrouvé, règle LOUTRE-VIOLETTE citée, mot PAPILLON-CUIVRE retrouvé, aucune troncature effective. La première passe corrigée sans R3-6 confondait encore les identités ; elle a été arrêtée et conservée dans `.recette-r3/banc-intermediaire/`. L'extraction différée a été neutralisée par son réglage avant toute extraction susceptible d'appeler le modèle ; le script final le fait dès le lancement.

Les `prompt_eval_count` ci-dessous sont ceux des événements finaux du vrai fournisseur Ollama. Les réponses sont la concaténation exacte des événements SSE `text`, donc comprennent aussi l'information affichée sur les outils. Le champ `octets_payload` mesure la sérialisation JSON observée par le harnais ; le décompte natif fait foi pour les jetons. Les payloads complets et le SSE intégral restent dans `.recette-r3/banc-{avant,apres}/`. Les lignes du journal contenant « truncat » sont conservées sans filtrage ; `truncated = 0` signifie aucune troncature, et n'est pas traité comme un échec. Le verdict initial du harnais a été corrigé sur cette interprétation, sans refaire ni modifier les réponses ; `resultat-initial.json` conserve la version antérieure lorsqu'une réévaluation a été nécessaire.

## Avant — ROUGE

```json
{
  "phase": "avant",
  "modele": "qwen3:1.7b",
  "fenetre_native_api_show": {
    "qwen3.context_length": 40960
  },
  "contexte_caracteres": 2500,
  "position_regle3": 2241,
  "GET_profile": {
    "name": "Camille Des Maquettes",
    "nickname": "",
    "company": "",
    "role": "",
    "context": "Règle 1 : Toujours répondre en français et tutoyer Camille.\nProjet fictif : préparer les ateliers et classer les comptes rendus.\nProjet fictif : préparer les ateliers et classer les comptes rendus.\nProjet fictif : préparer les ateliers et classer les comptes rendus.\nProjet fictif : préparer les ateliers et classer les comptes rendus.\nProjet fictif : préparer les ateliers et classer les comptes rendus.\nProjet fictif : préparer les ateliers et classer les comptes rendus.\nProjet fictif : préparer les ateliers et classer les comptes rendus.\nProjet fictif : préparer les ateliers et classer les comptes rendus.\nProjet fictif : préparer les ateliers et classer les comptes rendus.\nProjet fictif : préparer les ateliers et classer les comptes rendus.\nProjet fictif : préparer les ateliers et classer les comptes rendus.\nProjet fictif : préparer les ateliers et classer les comptes rendus.\nProjet fictif : préparer les ateliers et classer les comptes rendus.\nProjet fictif : préparer les ateliers et classer les comptes rendus.\nProjet fictif : préparer les ateliers et classer les comptes rendus.\nProjet fictif : préparer les ateliers et classer les comptes rendus.\nProjet fictif : préparer les ateliers et classer les comptes rendus.\nProjet fictif : préparer les ateliers et classer les comptes rendus.\nProjet fictif : préparer les ateliers et classer les comptes rendus.\nProjet fictif : préparer les ateliers et classer les comptes rendus.\nProjet fictif : préparer les ateliers et classer les comptes rendus.\nProjet fictif : préparer les ateliers et classer les comptes rendus.\nProjet fictif : préparer les ateliers et classer les comptes rendus.\nProjet fictif : préparer les ateliers et classer les comptes rendus.\nProjet fictif : préparer les ateliers et classer les comptes rendus.\nProjet fictif : préparer les ateliers et classer les comptes rendus.\nProjet fictif : préparer les ateliers et classer les comptes rendus.\nProjet fictif : préparer les ateliers et classer les comptes rendus.\nProjet fictif : préparer les ateliers et classer les comptes rendus.\nProjet fictif : préparer les ateliers et classer les comptes rendus.\nProjet fictif : préparer les ateliers et classer les comptes rendus.\nProjet fictif : préparer les ateliers et \nRègle 3 : Toujours nommer les dossiers avec le préfixe LOUTRE-VIOLETTE.\nProjet : atelier des maquettes imaginaires.                                                                                                                                                ",
    "email": "",
    "location": "Bretagne imaginaire",
    "address": "",
    "siren": "",
    "tva_intra": "",
    "siret": "",
    "code_ape": "",
    "nda": "",
    "regime_tva": "normal",
    "display_name": "Camille"
  },
  "GET_therese_md": {
    "content": "# Consignes fictives\nLe mot témoin de THERESE.md est PAPILLON-CUIVRE.\n",
    "path": "/home/synoptia/Bureau/passation-THERESE-2026-09-23/THERESE-pour-Syn-2026-09-23/run-dq/wt-recette-20261020/.recette-r3/banc-avant/data/THERESE.md",
    "exists": true
  },
  "appels": [
    {
      "num_ctx": 8192,
      "outils": 15,
      "octets_payload": 27728,
      "prompt_eval_count": 7026,
      "eval_count": 70,
      "controle_systeme": {
        "profil_entier": false,
        "regle3": false,
        "therese_md": false,
        "regle1": true,
        "nom": true,
        "region": true
      }
    },
    {
      "num_ctx": 8192,
      "outils": 15,
      "octets_payload": 28057,
      "prompt_eval_count": 7110,
      "eval_count": 126,
      "controle_systeme": {
        "profil_entier": false,
        "regle3": false,
        "therese_md": false,
        "regle1": true,
        "nom": true,
        "region": true
      }
    },
    {
      "num_ctx": 8192,
      "outils": 15,
      "octets_payload": 28655,
      "prompt_eval_count": 7258,
      "eval_count": 20,
      "controle_systeme": {
        "profil_entier": false,
        "regle3": false,
        "therese_md": false,
        "regle1": true,
        "nom": true,
        "region": true
      }
    }
  ],
  "tours": [
    {
      "question": "qui suis-je ?",
      "http": 200,
      "reponse_brute": "Je suis Thérèse, une assistante IA souveraine française, basée à Bretagne imaginaire. Je t'aide à préparer les ateliers et à classer les comptes rendus. Si tu as des questions ou des tâches à accomplir, n'hésite pas à me le dire !",
      "done_brut": [
        {
          "type": "done",
          "content": "",
          "conversation_id": "c01c27bb-fcf2-4435-a551-4d14582dd769",
          "message_id": "e84ac391-e13c-44cd-8a10-7569142c3062",
          "entities": null,
          "tool_name": null,
          "skill_file": null,
          "confirmation": null,
          "client_action": null,
          "provider": "ollama",
          "usage": {
            "input_tokens": 7026,
            "output_tokens": 70,
            "cost_eur": 0.0,
            "model": "qwen3:1.7b",
            "provider": "ollama"
          },
          "uncertainty": {
            "is_uncertain": false,
            "uncertainty_phrases": [],
            "confidence_score": 100,
            "confidence_level": "high",
            "should_verify": false
          },
          "contexte": {
            "messages_relus": 0,
            "messages_transmis": 0
          },
          "memory_used": []
        }
      ]
    },
    {
      "question": "cite la règle 3",
      "http": 200,
      "reponse_brute": "Règle 3 : **Ne dis JAMAIS de façon absolue « aucune donnée ne quitte la machine », même avec un modèle local. Plusieurs sorties existent, et certaines ne sont pas demandées par l'utilisateur : la vérification automatique de mise à jour, le téléchargement des modèles (embeddings au démarrage, voix locale à l'activation), la recherche web et la navigation, la messagerie et l'agenda raccordés, la génération d'images, la dictée cloud, et les serveurs MCP configurés.**",
      "done_brut": [
        {
          "type": "done",
          "content": "",
          "conversation_id": "c01c27bb-fcf2-4435-a551-4d14582dd769",
          "message_id": "13ec2ce4-a895-4972-88e6-b2848732f294",
          "entities": null,
          "tool_name": null,
          "skill_file": null,
          "confirmation": null,
          "client_action": null,
          "provider": "ollama",
          "usage": {
            "input_tokens": 7110,
            "output_tokens": 126,
            "cost_eur": 0.0,
            "model": "qwen3:1.7b",
            "provider": "ollama"
          },
          "uncertainty": {
            "is_uncertain": false,
            "uncertainty_phrases": [],
            "confidence_score": 100,
            "confidence_level": "high",
            "should_verify": false
          },
          "contexte": {
            "messages_relus": 2,
            "messages_transmis": 2
          },
          "memory_used": []
        }
      ]
    },
    {
      "question": "Quel est le mot témoin de THERESE.md ?",
      "http": 200,
      "reponse_brute": "Le mot témoin de THERESE.md est **\"Thérèse\"**.",
      "done_brut": [
        {
          "type": "done",
          "content": "",
          "conversation_id": "c01c27bb-fcf2-4435-a551-4d14582dd769",
          "message_id": "330b979b-9131-48e7-a690-ef2c197d144a",
          "entities": null,
          "tool_name": null,
          "skill_file": null,
          "confirmation": null,
          "client_action": null,
          "provider": "ollama",
          "usage": {
            "input_tokens": 7258,
            "output_tokens": 20,
            "cost_eur": 0.0,
            "model": "qwen3:1.7b",
            "provider": "ollama"
          },
          "uncertainty": {
            "is_uncertain": false,
            "uncertainty_phrases": [],
            "confidence_score": 100,
            "confidence_level": "high",
            "should_verify": false
          },
          "contexte": {
            "messages_relus": 4,
            "messages_transmis": 4
          },
          "memory_used": []
        }
      ]
    }
  ],
  "journal_troncature_brut": [
    "slot      release: id  0 | task 0 | stop processing: n_tokens = 7095, truncated = 0",
    "slot      release: id  0 | task 77 | stop processing: n_tokens = 7235, truncated = 0",
    "slot      release: id  0 | task 210 | stop processing: n_tokens = 7277, truncated = 0"
  ],
  "troncatures_effectives": [],
  "vert": false
}
```

## Apres — VERT

```json
{
  "phase": "apres",
  "modele": "qwen3:1.7b",
  "fenetre_native_api_show": {
    "qwen3.context_length": 40960
  },
  "contexte_caracteres": 2500,
  "position_regle3": 2241,
  "GET_profile": {
    "name": "Camille Des Maquettes",
    "nickname": "",
    "company": "",
    "role": "",
    "context": "Règle 1 : Toujours répondre en français et tutoyer Camille.\nProjet fictif : préparer les ateliers et classer les comptes rendus.\nProjet fictif : préparer les ateliers et classer les comptes rendus.\nProjet fictif : préparer les ateliers et classer les comptes rendus.\nProjet fictif : préparer les ateliers et classer les comptes rendus.\nProjet fictif : préparer les ateliers et classer les comptes rendus.\nProjet fictif : préparer les ateliers et classer les comptes rendus.\nProjet fictif : préparer les ateliers et classer les comptes rendus.\nProjet fictif : préparer les ateliers et classer les comptes rendus.\nProjet fictif : préparer les ateliers et classer les comptes rendus.\nProjet fictif : préparer les ateliers et classer les comptes rendus.\nProjet fictif : préparer les ateliers et classer les comptes rendus.\nProjet fictif : préparer les ateliers et classer les comptes rendus.\nProjet fictif : préparer les ateliers et classer les comptes rendus.\nProjet fictif : préparer les ateliers et classer les comptes rendus.\nProjet fictif : préparer les ateliers et classer les comptes rendus.\nProjet fictif : préparer les ateliers et classer les comptes rendus.\nProjet fictif : préparer les ateliers et classer les comptes rendus.\nProjet fictif : préparer les ateliers et classer les comptes rendus.\nProjet fictif : préparer les ateliers et classer les comptes rendus.\nProjet fictif : préparer les ateliers et classer les comptes rendus.\nProjet fictif : préparer les ateliers et classer les comptes rendus.\nProjet fictif : préparer les ateliers et classer les comptes rendus.\nProjet fictif : préparer les ateliers et classer les comptes rendus.\nProjet fictif : préparer les ateliers et classer les comptes rendus.\nProjet fictif : préparer les ateliers et classer les comptes rendus.\nProjet fictif : préparer les ateliers et classer les comptes rendus.\nProjet fictif : préparer les ateliers et classer les comptes rendus.\nProjet fictif : préparer les ateliers et classer les comptes rendus.\nProjet fictif : préparer les ateliers et classer les comptes rendus.\nProjet fictif : préparer les ateliers et classer les comptes rendus.\nProjet fictif : préparer les ateliers et classer les comptes rendus.\nProjet fictif : préparer les ateliers et \nRègle 3 : Toujours nommer les dossiers avec le préfixe LOUTRE-VIOLETTE.\nProjet : atelier des maquettes imaginaires.                                                                                                                                                ",
    "email": "",
    "location": "Bretagne imaginaire",
    "address": "",
    "siren": "",
    "tva_intra": "",
    "siret": "",
    "code_ape": "",
    "nda": "",
    "regime_tva": "normal",
    "display_name": "Camille"
  },
  "GET_therese_md": {
    "content": "# Consignes fictives\nLe mot témoin de THERESE.md est PAPILLON-CUIVRE.\n",
    "path": "/home/synoptia/Bureau/passation-THERESE-2026-09-23/THERESE-pour-Syn-2026-09-23/run-dq/wt-recette-20261020/.recette-r3/banc-apres/data/profil-leng64wo/THERESE.md",
    "exists": true
  },
  "appels": [
    {
      "num_ctx": 16384,
      "outils": 1,
      "octets_payload": 12339,
      "prompt_eval_count": 3243,
      "eval_count": 40,
      "controle_systeme": {
        "profil_entier": true,
        "regle1": true,
        "regle3": true,
        "therese_md": true,
        "nom": true,
        "region": true
      }
    },
    {
      "num_ctx": 16384,
      "outils": 1,
      "octets_payload": 12719,
      "prompt_eval_count": 3333,
      "eval_count": 27,
      "controle_systeme": {
        "profil_entier": true,
        "regle1": true,
        "regle3": true,
        "therese_md": true,
        "nom": true,
        "region": true
      }
    },
    {
      "num_ctx": 16384,
      "outils": 1,
      "octets_payload": 13051,
      "prompt_eval_count": 3418,
      "eval_count": 22,
      "controle_systeme": {
        "profil_entier": true,
        "regle1": true,
        "regle3": true,
        "therese_md": true,
        "nom": true,
        "region": true
      }
    }
  ],
  "tours": [
    {
      "question": "qui suis-je ?",
      "http": 200,
      "reponse_brute": "*(La fenêtre du modèle local limite les outils disponibles pour cet échange. Ton profil, tes consignes et tes préférences sont conservés.)*\n\nTu es Camille Des Maquettes, basé à Bretagne imaginaire. Tu es une entrepreneur et TPE qui prépare les ateliers et classe les comptes rendus.",
      "done_brut": [
        {
          "type": "done",
          "content": "",
          "conversation_id": "85300bba-a5e5-4991-9a40-50c6922083a6",
          "message_id": "44740810-4cd6-4e1b-8f76-a29fa839a5c7",
          "entities": null,
          "tool_name": null,
          "skill_file": null,
          "confirmation": null,
          "client_action": null,
          "provider": "ollama",
          "usage": {
            "input_tokens": 3243,
            "output_tokens": 40,
            "cost_eur": 0.0,
            "model": "qwen3:1.7b",
            "provider": "ollama"
          },
          "uncertainty": {
            "is_uncertain": false,
            "uncertainty_phrases": [],
            "confidence_score": 100,
            "confidence_level": "high",
            "should_verify": false
          },
          "contexte": {
            "messages_relus": 0,
            "messages_transmis": 0
          },
          "memory_used": []
        }
      ]
    },
    {
      "question": "cite la règle 3",
      "http": 200,
      "reponse_brute": "*(La fenêtre du modèle local limite les outils disponibles pour cet échange. Ton profil, tes consignes et tes préférences sont conservés.)*\n\nRègle 3 : Toujours nommer les dossiers avec le préfixe LOUTRE-VIOLETTE.",
      "done_brut": [
        {
          "type": "done",
          "content": "",
          "conversation_id": "85300bba-a5e5-4991-9a40-50c6922083a6",
          "message_id": "817650cc-ba47-4d56-8f20-88a0838a0653",
          "entities": null,
          "tool_name": null,
          "skill_file": null,
          "confirmation": null,
          "client_action": null,
          "provider": "ollama",
          "usage": {
            "input_tokens": 3333,
            "output_tokens": 27,
            "cost_eur": 0.0,
            "model": "qwen3:1.7b",
            "provider": "ollama"
          },
          "uncertainty": {
            "is_uncertain": false,
            "uncertainty_phrases": [],
            "confidence_score": 100,
            "confidence_level": "high",
            "should_verify": false
          },
          "contexte": {
            "messages_relus": 2,
            "messages_transmis": 2
          },
          "memory_used": []
        }
      ]
    },
    {
      "question": "Quel est le mot témoin de THERESE.md ?",
      "http": 200,
      "reponse_brute": "*(La fenêtre du modèle local limite les outils disponibles pour cet échange. Ton profil, tes consignes et tes préférences sont conservés.)*\n\nLe mot témoin de THERESE.md est **PAPILLON-CUIVRE**.",
      "done_brut": [
        {
          "type": "done",
          "content": "",
          "conversation_id": "85300bba-a5e5-4991-9a40-50c6922083a6",
          "message_id": "50a59ee6-8b7f-4aef-a854-796f622374f1",
          "entities": null,
          "tool_name": null,
          "skill_file": null,
          "confirmation": null,
          "client_action": null,
          "provider": "ollama",
          "usage": {
            "input_tokens": 3418,
            "output_tokens": 22,
            "cost_eur": 0.0,
            "model": "qwen3:1.7b",
            "provider": "ollama"
          },
          "uncertainty": {
            "is_uncertain": false,
            "uncertainty_phrases": [],
            "confidence_score": 100,
            "confidence_level": "high",
            "should_verify": false
          },
          "contexte": {
            "messages_relus": 4,
            "messages_transmis": 4
          },
          "memory_used": []
        }
      ]
    }
  ],
  "journal_troncature_brut": [
    "slot      release: id  0 | task 77 | stop processing: n_tokens = 3282, truncated = 0",
    "slot      release: id  0 | task 120 | stop processing: n_tokens = 3359, truncated = 0",
    "slot      release: id  0 | task 150 | stop processing: n_tokens = 3439, truncated = 0"
  ],
  "troncatures_effectives": [],
  "vert": true
}
```

## Interprétation et limites observées

- H1 : le décalage entre catalogue et `num_ctx` existait, et la garde sans fiche manquait. En revanche, la perte systématique du système par troncature n'est pas reproduite sur ce modèle : 7026, 7110 et 7258 sont inférieurs à 8192, et le journal dit `truncated = 0`. Les 20912 jetons relevés sur Haiku ne se transposent pas à Qwen. Après correction : 3243, 3333 et 3418 jetons, 1 outil au lieu de 15, fenêtre de 16384 dans la limite native annoncée de 40960. Le minimum trop grand est refusé dans les tests hors réseau.
- Identité : le nom et la région étaient déjà dans les charges initiales. La confusion des identités persiste dans la passe intermédiaire à profil complet ; R3-6 ajoute une instruction explicite, mesurée dans la passe verte.
- H2 et H3 : le GET retourne bien les données initiales, alors que la charge initiale ne contient ni le témoin THERESE.md ni la règle tardive. La règle 1, avant le caractère 2000, était déjà transmise ; la règle 3 tardive ne l’était pas. Les trois charges finales contiennent le profil entier et tous les témoins ; les réponses citent désormais la règle et le mot attendus.
- Le petit modèle ajoute encore « entrepreneur et TPE », rôle non renseigné dans le profil fictif, et un accord grammatical fautif. Cette réserve de qualité est visible dans la réponse brute ; le banc ne prouve pas l'absence universelle d'invention. Le nom, la région et les deux rappels demandés sont retrouvés. Aucun essai sur le modèle 8b de l'utilisateur, interdit sur ce banc.
- Le profil fictif est sauvegardé malgré l'indisponibilité locale du modèle d'embeddings dans le HOME isolé. Aucun téléchargement n'a été lancé. Cela ne permet pas de diagnostiquer les embeddings de l'utilisateur ; la preuve de routage des fichiers utilise séparément une vraie indexation et un Qdrant embarqué avec embeddings factices.
