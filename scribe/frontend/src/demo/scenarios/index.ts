import allergyData from "./allergy.json";
import chestPainData from "./chest-pain.json";
import prescriptionData from "./prescription.json";
import { assertScenario } from "../scenarioSchema";
import type { Scenario } from "../types";

const rawScenarios: unknown[] = [
  prescriptionData,
  allergyData,
  chestPainData,
];

export const scenarios: Scenario[] = rawScenarios.map((scenario) => {
  assertScenario(scenario);
  return scenario;
});

export function getScenario(id: string): Scenario {
  return scenarios.find((scenario) => scenario.id === id) ?? scenarios[0];
}
