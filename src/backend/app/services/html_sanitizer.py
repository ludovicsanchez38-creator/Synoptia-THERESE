"""Sanitizer HTML pour signatures email et contenus utilisateur."""

import nh3

ALLOWED_TAGS = {
    "p", "br", "a", "img", "strong", "em", "b", "i", "u", "span", "div",
    "table", "tr", "td", "th", "thead", "tbody",
    "ul", "ol", "li", "h1", "h2", "h3", "h4", "blockquote", "hr",
}
ALLOWED_ATTRIBUTES: dict[str, set[str]] = {
    "a": {"href", "title", "target"},
    "img": {"src", "alt", "width", "height"},
    "span": {"style"},
    "div": {"style"},
    "td": {"colspan", "rowspan", "style"},
    "th": {"colspan", "rowspan", "style"},
    "table": {"style", "border", "cellpadding", "cellspacing"},
}


def sanitize_html(html: str) -> str:
    """Nettoie le HTML en ne gardant que les tags/attributs autorisés."""
    return nh3.clean(
        html,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        link_rel=None,
    )
