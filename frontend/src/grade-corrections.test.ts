import { describe, it, expect } from "vitest";
import {
  collapseCorrections,
  correctionLabel,
  correctionNote,
  findReplaced,
  supersededLabel,
  supersededNote,
} from "./grade-corrections.js";
import type { HassGrade, HassGradeRef } from "./types.js";

function grade(
  value: string,
  date: string,
  extra: Partial<HassGrade> = {},
): HassGrade {
  return {
    subject: "matematyka",
    grade: value,
    value: null,
    counts: false,
    weight: 0,
    date,
    category: "kartkówka",
    description: "",
    title: "",
    comment: "",
    teacher: "",
    is_recent: false,
    ...extra,
  };
}

const ref = (g: string, date: string | null, category = "kartkówka"): HassGradeRef => ({
  grade: g,
  category,
  date,
});

/** A replaced grade and the grade that corrected it, linked the way the integration does. */
function pair(from: string, fromDate: string, to: string, toDate: string) {
  const original = grade(from, fromDate, { corrected_by: ref(to, toDate) });
  const correction = grade(to, toDate, {
    description: `${from} (kartkówka)`,
    correction_of: ref(from, fromDate),
  });
  return { original, correction };
}

describe("findReplaced", () => {
  it("returns the grade a correction replaces", () => {
    const { original, correction } = pair("1", "2026-09-17", "6", "2026-09-28");
    expect(findReplaced(correction, [original, correction])).toBe(original);
  });

  it("returns undefined when the integration could not identify the original", () => {
    const orphan = grade("6", "2026-09-28", { correction_of: ref("1", null) });
    expect(findReplaced(orphan, [grade("1", "2026-09-17"), orphan])).toBeUndefined();
  });

  it("returns undefined for an ordinary grade", () => {
    const plain = grade("4", "2026-09-28");
    expect(findReplaced(plain, [plain])).toBeUndefined();
  });
});

describe("collapseCorrections", () => {
  it("passes ordinary grades through unchanged", () => {
    const a = grade("5", "2026-09-10");
    const b = grade("3", "2026-09-12");
    expect(collapseCorrections([a, b])).toEqual([
      { grade: a, replaced: [] },
      { grade: b, replaced: [] },
    ]);
  });

  it("folds a replaced grade into its correction", () => {
    const first = grade("bz", "2026-09-10", { category: "zadanie" });
    const { original, correction } = pair("1", "2026-09-17", "6", "2026-09-28");

    const entries = collapseCorrections([first, original, correction]);

    expect(entries).toEqual([
      { grade: first, replaced: [] },
      { grade: correction, replaced: [original] },
    ]);
  });

  it("folds a whole chain of corrections, oldest first", () => {
    const one = grade("1", "2026-09-10", { corrected_by: ref("3", "2026-09-17") });
    const three = grade("3", "2026-09-17", {
      description: "1 (kartkówka)",
      correction_of: ref("1", "2026-09-10"),
      corrected_by: ref("5", "2026-09-24"),
    });
    const five = grade("5", "2026-09-24", {
      description: "3 (kartkówka)",
      correction_of: ref("3", "2026-09-17"),
    });

    expect(collapseCorrections([one, three, five])).toEqual([
      { grade: five, replaced: [one, three] },
    ]);
  });

  it("keeps an unidentified correction as an entry of its own", () => {
    const one = grade("1", "2026-09-10");
    const orphan = grade("4", "2026-09-28", { correction_of: ref("1", null) });

    expect(collapseCorrections([one, orphan])).toEqual([
      { grade: one, replaced: [] },
      { grade: orphan, replaced: [] },
    ]);
  });

  it("never drops a grade when the links form a loop", () => {
    const a = grade("1", "2026-09-10", {
      description: "1 (kartkówka)",
      correction_of: ref("1", "2026-09-10"),
      corrected_by: ref("1", "2026-09-10"),
    });
    const b = grade("1", "2026-09-10", {
      description: "1 (kartkówka)",
      correction_of: ref("1", "2026-09-10"),
      corrected_by: ref("1", "2026-09-10"),
    });

    const entries = collapseCorrections([a, b]);
    const shown = entries.flatMap(e => [e.grade, ...e.replaced]);

    expect(shown).toHaveLength(2);
    expect(shown).toContain(a);
    expect(shown).toContain(b);
  });
});

describe("notes", () => {
  it("describes a correction with the replaced grade, category and date", () => {
    const g = grade("6", "2026-09-28", { correction_of: ref("1", "2026-09-17") });
    expect(correctionNote(g)).toBe("poprawa oceny 1 (kartkówka) z 17.09.2026");
  });

  it("omits the date when the original is unknown", () => {
    const g = grade("6", "2026-09-28", { correction_of: ref("1", null) });
    expect(correctionNote(g)).toBe("poprawa oceny 1 (kartkówka)");
  });

  it("falls back to a bare label when nothing could be parsed", () => {
    const g = grade("6", "2026-09-28", {
      correction_of: { grade: null, category: null, date: null },
    });
    expect(correctionNote(g)).toBe("poprawa oceny");
  });

  it("returns nothing for an ordinary grade", () => {
    expect(correctionNote(grade("4", "2026-09-28"))).toBeNull();
  });

  it("describes a replaced grade with its correction", () => {
    const g = grade("1", "2026-09-17", { corrected_by: ref("6", "2026-09-28") });
    expect(supersededNote(g)).toBe("poprawiona oceną 6 z 28.09.2026");
  });

  it("returns nothing for a grade that was not replaced", () => {
    expect(supersededNote(grade("4", "2026-09-28"))).toBeNull();
  });
});

describe("short labels (list rows)", () => {
  it("names the date of the replaced grade", () => {
    const g = grade("6", "2026-09-28", { correction_of: ref("1", "2026-09-17") });
    expect(correctionLabel(g)).toBe("poprawa z 17.09");
  });

  it("is just 'poprawa' when the original is unknown", () => {
    const g = grade("6", "2026-09-28", { correction_of: ref("1", null) });
    expect(correctionLabel(g)).toBe("poprawa");
  });

  it("is empty for an ordinary grade", () => {
    expect(correctionLabel(grade("4", "2026-09-28"))).toBeNull();
    expect(supersededLabel(grade("4", "2026-09-28"))).toBeNull();
  });

  it("names the grade that replaced a corrected one", () => {
    const g = grade("1", "2026-09-17", { corrected_by: ref("6", "2026-09-28") });
    expect(supersededLabel(g)).toBe("poprawiona na 6");
  });
});
