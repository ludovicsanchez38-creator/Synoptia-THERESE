# Story E3-05 : Injecter le contexte mémoire dans les prompts LLM

## Description

En tant que **THÉRÈSE**,
Je veux **avoir accès au contexte pertinent de la mémoire**,
Afin de **répondre de manière personnalisée et informée**.

## Contexte technique

- **Composants impactés** : Backend Python, Service LLM
- **Dépendances** : E2-02, E3-04
- **Fichiers concernés** :
  - `src/backend/therese/services/llm.py` (màj)
  - `src/backend/therese/services/context_builder.py` (nouveau)

## Critères d'acceptation

- [ ] Contexte pertinent récupéré avant chaque requête LLM
- [ ] Limite de tokens respectée (max 2000 tokens de contexte)
- [ ] Priorité : préférences > projet actif > contacts > faits récents
- [ ] Format structuré pour le LLM
- [ ] Cache du contexte pour conversations longues
- [ ] Logs des contextes injectés (debug)

## Notes techniques

### Context Builder

```python
# therese/services/context_builder.py
from dataclasses import dataclass
from .memory_search import memory_search_service
from ..models.memory import Contact, Project, Preference

MAX_CONTEXT_TOKENS = 2000
TOKENS_PER_CHAR = 0.25  # Approximation


@dataclass
class ContextItem:
    type: str
    content: str
    relevance: float


class ContextBuilder:
    def __init__(self):
        self._context_cache: dict[str, str] = {}

    async def build_context(
        self,
        user_message: str,
        conversation_id: str | None = None
    ) -> str:
        """Construit le contexte à injecter dans le prompt"""
        context_items: list[ContextItem] = []
        remaining_chars = int(MAX_CONTEXT_TOKENS / TOKENS_PER_CHAR)

        # 1. Préférences utilisateur (toujours incluses)
        preferences = await self._get_preferences()
        if preferences:
            pref_str = self._format_preferences(preferences)
            context_items.append(ContextItem("preferences", pref_str, 1.0))
            remaining_chars -= len(pref_str)

        # 2. Recherche sémantique basée sur le message
        if remaining_chars > 500:
            relevant_memories = await memory_search_service.search(
                query=user_message,
                limit=5,
                hybrid=True
            )
            for mem in relevant_memories:
                if remaining_chars > 200:
                    mem_str = f"- {mem.type}: {mem.content}"
                    context_items.append(ContextItem("memory", mem_str, mem.score))
                    remaining_chars -= len(mem_str)

        # 3. Projet actif (si détecté)
        active_project = await self._get_active_project(user_message)
        if active_project and remaining_chars > 300:
            proj_str = self._format_project(active_project)
            context_items.append(ContextItem("project", proj_str, 0.9))
            remaining_chars -= len(proj_str)

        # 4. Contacts mentionnés
        contacts = await self._get_mentioned_contacts(user_message)
        for contact in contacts[:3]:  # Max 3 contacts
            if remaining_chars > 200:
                contact_str = self._format_contact(contact)
                context_items.append(ContextItem("contact", contact_str, 0.8))
                remaining_chars -= len(contact_str)

        # Construire le contexte final
        return self._format_context(context_items)

    async def _get_preferences(self) -> list[Preference]:
        """Récupère les préférences utilisateur"""
        # TODO: Implémenter avec service preferences
        return []

    async def _get_active_project(self, message: str) -> Project | None:
        """Détecte et récupère le projet actif"""
        # Recherche de mots-clés projet dans le message
        # TODO: Implémenter détection intelligente
        return None

    async def _get_mentioned_contacts(self, message: str) -> list[Contact]:
        """Détecte les contacts mentionnés"""
        # TODO: NER sur le message pour extraire les noms
        return []

    def _format_preferences(self, preferences: list[Preference]) -> str:
        """Formate les préférences pour le prompt"""
        lines = ["## Préférences utilisateur"]
        for pref in preferences:
            lines.append(f"- {pref.key}: {pref.value}")
        return "\n".join(lines)

    def _format_project(self, project: Project) -> str:
        """Formate un projet pour le prompt"""
        return f"""## Projet actif: {project.name}
- Status: {project.status}
- Description: {project.description or 'Non renseignée'}
- Client: {project.client.full_name if project.client else 'Non renseigné'}"""

    def _format_contact(self, contact: Contact) -> str:
        """Formate un contact pour le prompt"""
        return f"""## Contact: {contact.full_name}
- Entreprise: {contact.company or 'Non renseignée'}
- Email: {contact.email or 'Non renseigné'}
- Notes: {contact.notes or 'Aucune'}"""

    def _format_context(self, items: list[ContextItem]) -> str:
        """Assemble le contexte final"""
        if not items:
            return ""

        sections = {
            "preferences": [],
            "project": [],
            "contact": [],
            "memory": []
        }

        for item in items:
            sections[item.type].append(item.content)

        output = ["# Contexte mémoire THÉRÈSE\n"]

        if sections["preferences"]:
            output.extend(sections["preferences"])
            output.append("")

        if sections["project"]:
            output.extend(sections["project"])
            output.append("")

        if sections["contact"]:
            output.append("## Contacts pertinents")
            output.extend(sections["contact"])
            output.append("")

        if sections["memory"]:
            output.append("## Informations mémorisées")
            output.extend(sections["memory"])

        return "\n".join(output)


# Singleton
context_builder = ContextBuilder()
```

### Intégration dans le service LLM

```python
# therese/services/llm.py (màj)

async def complete_with_context(
    self,
    user_message: str,
    conversation_history: list[dict],
    conversation_id: str | None = None
) -> str:
    """Complète avec contexte mémoire injecté"""
    # Construire le contexte
    context = await context_builder.build_context(
        user_message=user_message,
        conversation_id=conversation_id
    )

    # Construire le system prompt enrichi
    system_prompt = SYSTEM_PROMPT.format(user_name="Ludo")
    if context:
        system_prompt += f"\n\n{context}"

    # Log du contexte (debug)
    logger.debug(f"Context injected:\n{context}")

    # Appeler Claude
    messages = conversation_history + [{"role": "user", "content": user_message}]
    return await self.complete(messages, system=system_prompt)
```

## Estimation

- **Complexité** : S
- **Points** : 3

## Definition of Done

- [ ] Contexte injecté dans chaque requête
- [ ] Limite de tokens respectée
- [ ] Priorités respectées
- [ ] Logs de debug actifs
- [ ] Tests avec/sans contexte

---

*Sprint : 3*
*Assigné : Agent Dev Backend*
