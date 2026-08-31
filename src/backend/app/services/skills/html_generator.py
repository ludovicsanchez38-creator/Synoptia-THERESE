"""
THÉRÈSE v2 - HTML Page Generator Skill

Génère des pages web complètes (landing pages, portfolios, mini-sites).
Le LLM produit directement le HTML + CSS + JS inline.

v0.6 - Rattrapage Manus ("Build website")
"""

import logging
import re
from pathlib import Path

from app.services.skills.base import (
    BaseSkill,
    FileFormat,
    InputField,
    SkillOutputType,
    SkillParams,
    SkillResult,
)
from app.services.skills.code_executor import LivrableInexploitable

logger = logging.getLogger(__name__)


class HtmlSkill(BaseSkill):
    """
    Skill de génération de pages web HTML.

    Crée des pages web complètes (HTML + CSS + JS inline) avec le style Synoptia.
    Le LLM génère directement le code HTML, pas besoin de code-execution.
    """

    skill_id = "html-web"
    name = "Page Web"
    description = "Génère une page web complète (landing page, portfolio, mini-site)"
    output_format = FileFormat.HTML
    output_type = SkillOutputType.FILE

    def __init__(self, output_dir: Path):
        super().__init__(output_dir)

    def get_system_prompt_addition(self) -> str:
        """Instructions pour le LLM : générer du HTML complet."""
        return """
## Instructions pour génération de page web HTML

Tu dois générer une **page web HTML complète** et autonome (un seul fichier).
Le fichier doit être un document HTML valide, prêt à ouvrir dans un navigateur.

### Structure obligatoire
```html
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>[Titre pertinent]</title>
    <style>
        /* CSS intégré ici */
    </style>
</head>
<body>
    <!-- Contenu ici -->
    <script>
        /* JS optionnel ici */
    </script>
</body>
</html>
```

### Palette et couleurs
- Adapte les couleurs au sujet de la page (ex: vert pour un coach bien-être, bleu pour un consultant tech, chaud pour un restaurant)
- Si l'utilisateur ne précise pas, utilise un design moderne et élégant (fond sombre ou clair selon le contexte)
- Propose des couleurs harmonieuses avec un bon contraste

### Règles de design
1. **Responsive** : utiliser flexbox/grid, media queries pour mobile
2. **Typographie** : font-family system-ui ou Inter via Google Fonts CDN
3. **Animations** : transitions CSS douces (hover, scroll reveal avec IntersectionObserver)
4. **Sections** : hero, features/services, about, contact/CTA, footer
5. **Images** : utiliser des placeholders SVG inline ou des emojis/icones Unicode
6. **Pas de dépendances externes** sauf Google Fonts CDN (pas de Bootstrap, Tailwind CDN, jQuery)
7. **Accessibilité** : alt sur les images, contraste suffisant, structure sémantique (header, main, section, footer)

### Types de pages
- **Landing page** : hero avec CTA, 3-4 features, témoignages, pricing, footer
- **Portfolio** : galerie de projets avec filtres, section about, contact
- **Mini-site** : navigation, plusieurs sections, formulaire de contact
- **Dashboard** : cartes de statistiques, graphiques CSS, tableau de bord

### IMPORTANT
- Génère UNIQUEMENT le code HTML complet, sans commentaires d'explication avant ou après
- Le code doit être prêt à l'emploi, copier-coller dans un fichier .html
- Minimum 100 lignes de HTML pour un résultat professionnel
"""

    def get_input_schema(self) -> dict[str, InputField]:
        """Schéma d'entrée pour le formulaire frontend."""
        return {
            "prompt": InputField(
                type="textarea",
                label="Description de la page",
                placeholder="Ex: Landing page pour un coach sportif à Manosque, avec sections services, tarifs et contact",
                required=True,
                help_text="Décrivez le contenu et le style souhaité",
            ),
            "template": InputField(
                type="select",
                label="Type de page",
                options=["landing", "portfolio", "mini-site", "dashboard"],
                default="landing",
                help_text="Le type de page influence la structure générée",
            ),
        }

    async def execute(self, params: SkillParams) -> SkillResult:
        """
        Génère une page HTML à partir du contenu LLM.

        Le contenu LLM est directement du HTML. On l'extrait, le valide,
        et le sauvegarde en fichier .html.
        """
        file_id = self.generate_file_id()
        output_path = self.get_output_path(file_id, params.title)

        # Extraire le HTML du contenu LLM
        html_content = self._extract_html(params.content)

        if not html_content:
            # Revue 30/08 : wrapper un refus ou un HTML partiel dans un
            # <pre> produisait une page « réussie ». Échec franc.
            raise LivrableInexploitable(
                "le contenu produit n'est pas exploitable "
                "(HTML incomplet ou refus du modèle)"
            )

        # Sauvegarder
        output_path.write_text(html_content, encoding="utf-8")

        file_size = output_path.stat().st_size
        logger.info(f"HTML généré : {output_path.name} ({file_size} octets)")

        return SkillResult(
            file_id=file_id,
            file_path=output_path,
            file_name=output_path.name,
            file_size=file_size,
            mime_type="text/html",
            format=FileFormat.HTML,
        )

    def _extract_html(self, content: str) -> str | None:
        """Extrait le code HTML du contenu LLM (peut être dans un bloc code)."""
        # Chercher un bloc de code HTML
        code_block = re.search(
            r"```(?:html)?\s*\n(.*?)```",
            content,
            re.DOTALL,
        )
        if code_block:
            html = code_block.group(1).strip()
            if "<!DOCTYPE" in html.upper() or "<html" in html.lower():
                return html

        # Le contenu est peut-être directement du HTML
        if "<!DOCTYPE" in content.upper() or "<html" in content.lower():
            # Extraire depuis <!DOCTYPE ou <html jusqu'à </html>
            start = content.lower().find("<!doctype")
            if start == -1:
                start = content.lower().find("<html")
            end = content.lower().rfind("</html>")
            if start >= 0 and end > start:
                return content[start:end + 7]

        return None

    def _wrap_in_html(self, title: str, content: str) -> str:
        """Fallback : wrapper du contenu texte dans une page HTML minimale."""
        escaped_content = content.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        return f"""<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{
            font-family: system-ui, -apple-system, sans-serif;
            background: #1a1a2e;
            color: #e0e0e0;
            max-width: 800px;
            margin: 0 auto;
            padding: 2rem;
            line-height: 1.6;
        }}
        h1 {{
            color: #4fc3f7;
            border-bottom: 2px solid #3949ab;
            padding-bottom: 0.5rem;
        }}
        pre {{
            background: #16213e;
            padding: 1rem;
            border-radius: 8px;
            overflow-x: auto;
        }}
    </style>
</head>
<body>
    <h1>{title}</h1>
    <pre>{escaped_content}</pre>
</body>
</html>"""
