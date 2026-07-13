import type { DemoTurn, Scenario } from "./types";

const riskTiers = new Set(["low", "medium", "high", "critical"]);
const speakers = new Set(["doctor", "patient"]);
const languages = new Set(["vi", "en"]);

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function hasText(record: Record<string, unknown>, key: string): boolean {
  return typeof record[key] === "string" && record[key].trim().length > 0;
}

function assertTurn(value: unknown, scenarioId: string): asserts value is DemoTurn {
  if (!isRecord(value)) {
    throw new Error(`Scenario ${scenarioId} contains an invalid turn.`);
  }

  if (
    !hasText(value, "id") ||
    !hasText(value, "vi") ||
    !hasText(value, "en") ||
    !speakers.has(String(value.speaker)) ||
    !languages.has(String(value.sourceLanguage)) ||
    !riskTiers.has(String(value.riskTier)) ||
    !Array.isArray(value.riskSpans)
  ) {
    throw new Error(`Scenario ${scenarioId} contains an incomplete turn.`);
  }

  for (const span of value.riskSpans) {
    if (
      !isRecord(span) ||
      !hasText(span, "kind") ||
      !hasText(span, "vi") ||
      !hasText(span, "en")
    ) {
      throw new Error(`Scenario ${scenarioId} contains an invalid risk span.`);
    }
  }

  if (value.readback !== undefined) {
    if (!isRecord(value.readback) || !Array.isArray(value.readback.entities)) {
      throw new Error(`Scenario ${scenarioId} contains an invalid read-back.`);
    }
    for (const entity of value.readback.entities) {
      if (
        !isRecord(entity) ||
        !hasText(entity, "kind") ||
        !hasText(entity, "sourceText") ||
        !hasText(entity, "translatedText")
      ) {
        throw new Error(`Scenario ${scenarioId} contains an invalid entity.`);
      }
    }
  }

  if (
    (value.riskTier === "high" || value.riskTier === "critical") &&
    value.readback === undefined &&
    value.escalation !== true
  ) {
    throw new Error(
      `Scenario ${scenarioId} contains an ungated high-risk turn.`,
    );
  }
}

export function assertScenario(value: unknown): asserts value is Scenario {
  if (!isRecord(value) || !hasText(value, "id")) {
    throw new Error("Scenario must have an id.");
  }
  const scenarioId = String(value.id);
  for (const key of ["title", "summary"]) {
    const localized = value[key];
    if (
      !isRecord(localized) ||
      !hasText(localized, "vi") ||
      !hasText(localized, "en")
    ) {
      throw new Error(`Scenario ${scenarioId} has invalid ${key} copy.`);
    }
  }
  if (!Array.isArray(value.turns) || value.turns.length < 1) {
    throw new Error(`Scenario ${scenarioId} must contain turns.`);
  }
  value.turns.forEach((turn) => assertTurn(turn, scenarioId));
}
