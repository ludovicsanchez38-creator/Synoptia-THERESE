"""Sanitizer HTML pour signatures email et contenus utilisateur."""

import nh3

ALLOWED_TAGS = {
    "p", "br", "a", "img", "strong", "em", "b", "i", "u", "span", "div",
    "table", "tr", "td", "th", "thead", "tbody",
    "ul", "ol", "li", "h1", "h2", "h3", "h4", "blockquote", "hr",
}
# Pas d'attribut `style` : nh3 ne filtre pas le CSS inline, ce qui laisserait
# passer background-image:url(http://...) (exfiltration réseau au rendu, contraire
# à la promesse « 100 % local ») et position:fixed (overlay). On ne garde que des
# attributs de présentation HTML inoffensifs, alignés sur la politique déjà
# appliquée aux emails reçus (sanitizeEmailHtml côté frontend, qui interdit style).
ALLOWED_ATTRIBUTES: dict[str, set[str]] = {
    "a": {"href", "title", "target"},
    "img": {"src", "alt", "width", "height"},
    "td": {"colspan", "rowspan"},
    "th": {"colspan", "rowspan"},
    "table": {"border", "cellpadding", "cellspacing"},
}


def sanitize_html(html: str) -> str:
    """Nettoie le HTML en ne gardant que les tags/attributs autorisés."""
    return nh3.clean(
        html,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        # rel=noopener noreferrer sur les liens (anti tab-nabbing / fuite referrer)
        link_rel="noopener noreferrer",
    )
