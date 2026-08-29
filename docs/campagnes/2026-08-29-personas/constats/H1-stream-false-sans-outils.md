# H1 — `stream: false` affirme un succès sans exécuter l'outil

**Nature : observation d'API, PAS un défaut vécu par un utilisateur.**
Trouvée par le smoke-test d'avant-campagne, pas par un persona.

## Ce qui se passe

`POST /api/chat/send` avec `{"stream": false}` :

> « Le contact **Camille Test** (entreprise : *Atelier Test*) a été enregistré
> localement. »

`GET /api/memory/contacts` : **0 contact**. Deux essais, dont un explicitement
« utilise ton outil create_contact », même résultat.

Le même message avec `{"stream": true}` — le chemin qu'emploie l'interface —
crée bien le contact.

## Ce que ce n'est pas

Ce n'est pas une limite du modèle local. Interrogé directement, Ollama
`qwen3:8b` rend un `tool_calls` parfaitement formé :

```json
{"function": {"name": "create_contact",
              "arguments": {"first_name": "Camille", "last_name": "Test"}}}
```

C'est donc la boucle d'outils du chemin non-streamé qui ne tourne pas.

## Pourquoi c'est nommé et pas dramatisé

Aucun écran n'emprunte `stream: false`. Un utilisateur ne rencontre pas ce
comportement. La campagne du 28/08 avait produit un finding « bloquant » qui
était un artefact de harnais (l'extra `voice-local` manquant) : la discipline
retenue est de dire d'où vient un constat, et de ne pas faire passer un chemin
d'API pour une expérience utilisateur.

Reste que la forme est celle que toute la 0.54 combat : **une affirmation de
succès sans le geste**. Un script, un test d'intégration ou un futur client
d'API tomberait dedans.

## Conséquence sur le harnais

Le smoke-test d'avant-campagne se fait désormais **en streaming**, sinon il
valide un chemin que personne n'emprunte. C'est ce qui a permis de trancher :
harnais, pas produit.
