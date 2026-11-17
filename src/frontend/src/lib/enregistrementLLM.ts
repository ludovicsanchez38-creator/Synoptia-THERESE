// Les réglages et le sélecteur du chat écrivent la même configuration.
// La file survit à la fermeture des réglages et reste utilisable après refus.
let enregistrement: Promise<void> = Promise.resolve();
let derniereIntention = 0;

// Réserver l'ordre au geste, avant toute lecture préparatoire asynchrone.
export function nouvelleIntentionLLM(): number {
  return ++derniereIntention;
}

export function intentionLLMCourante(intention: number): boolean {
  return intention === derniereIntention;
}

export function ordonnerEnregistrementLLM<T>(operation: () => Promise<T>): Promise<T> {
  const suivant = enregistrement.then(operation);
  enregistrement = suivant.then(() => undefined, () => undefined);
  return suivant;
}
