it("détecte le défaut puis l’état sain", () => { expect(process.env.C17_TEST_RUNNER_DEFECT === "1" ? 2 : 1).toBe(1); });
