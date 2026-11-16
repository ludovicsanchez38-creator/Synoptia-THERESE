// Les réglages et le sélecteur du chat écrivent la même configuration.
// La file survit à la fermeture des réglages et reste utilisable après refus.
let enregistrement: Promise<void> = Promise.resolve();

export function ordonnerEnregistrementLLM<T>(operation: () => Promise<T>): Promise<T> {
  const suivant = enregistrement.then(operation);
  enregistrement = suivant.then(() => undefined, () => undefined);
  return suivant;
}
