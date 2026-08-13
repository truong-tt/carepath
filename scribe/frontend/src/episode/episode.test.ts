import { beforeEach, describe, expect, it } from "vitest";
import {
  addDocuments,
  clearEpisode,
  loadEpisode,
  newEpisode,
  patchEpisode,
  saveEpisode,
  type EpisodeDocument,
} from "./episode";

const KEY = "carepath.episode";

function docLine(overrides: Partial<EpisodeDocument> = {}): EpisodeDocument {
  return {
    id: "d1",
    kind: "prescription",
    vi: "Amoxicillin 500 mg — Uống 1 viên, ngày 2 lần, sau ăn",
    en: "Amoxicillin 500 mg — take 1 tablet twice daily after meals",
    isMedication: true,
    source: "scripted",
    ...overrides,
  };
}

describe("care episode", () => {
  beforeEach(() => {
    sessionStorage.clear();
  });

  it("returns null when nothing has been stored", () => {
    expect(loadEpisode()).toBeNull();
  });

  it("round-trips an episode through sessionStorage", () => {
    const episode = saveEpisode(newEpisode({ location: "Hanoi", careNeed: "skin rash" }));
    expect(loadEpisode()?.id).toBe(episode.id);
    expect(loadEpisode()?.careNeed).toBe("skin rash");
  });

  it("does not persist beyond the tab: the store is sessionStorage", () => {
    saveEpisode(newEpisode());
    expect(sessionStorage.getItem(KEY)).not.toBeNull();
    expect(localStorage.getItem(KEY)).toBeNull();
  });

  // A parse error here used to be able to take out every screen that reads the
  // episode on mount. The recovery is the same as having no episode, so that is
  // what a bad value becomes.
  it("treats malformed storage as no episode instead of throwing", () => {
    sessionStorage.setItem(KEY, "{not json");
    expect(loadEpisode()).toBeNull();

    sessionStorage.setItem(KEY, JSON.stringify({ nope: true }));
    expect(loadEpisode()).toBeNull();
  });

  it("repairs missing arrays so screens can map over them", () => {
    sessionStorage.setItem(KEY, JSON.stringify({ id: "ep_x", status: "planning" }));
    const loaded = loadEpisode();
    expect(loaded?.documents).toEqual([]);
    expect(loaded?.confirmedMedications).toEqual([]);
  });

  it("creates an episode on first patch", () => {
    const patched = patchEpisode({ careNeed: "rash on both arms" });
    expect(patched.careNeed).toBe("rash on both arms");
    expect(loadEpisode()?.careNeed).toBe("rash on both arms");
  });

  it("lifts confirmed medication lines out of documents", () => {
    addDocuments([
      docLine(),
      docLine({ id: "d2", vi: "Tái khám sau 5 ngày", en: "Return after 5 days", isMedication: false }),
    ]);

    const episode = loadEpisode();
    expect(episode?.documents).toHaveLength(2);
    expect(episode?.confirmedMedications).toEqual([
      "Amoxicillin 500 mg — take 1 tablet twice daily after meals",
    ]);
  });

  it("does not duplicate a line saved twice", () => {
    addDocuments([docLine()]);
    addDocuments([docLine()]);

    const episode = loadEpisode();
    expect(episode?.documents).toHaveLength(1);
    expect(episode?.confirmedMedications).toHaveLength(1);
  });

  it("clears everything it stored", () => {
    saveEpisode(newEpisode());
    clearEpisode();
    expect(loadEpisode()).toBeNull();
    expect(sessionStorage.getItem(KEY)).toBeNull();
  });

  it("collects no identity fields", () => {
    const episode = newEpisode();
    for (const banned of ["name", "passport", "dateOfBirth", "phone", "email"]) {
      expect(episode).not.toHaveProperty(banned);
    }
  });
});
