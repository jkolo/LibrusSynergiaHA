import { describe, it, expect } from "vitest";
import { daysUntilLabel, shortWeekday, examLabel, pickExams, pickReadings, urgency } from "./schedule-view.js";
import type { HassScheduleEvent } from "./types.js";

function ev(over: Partial<HassScheduleEvent>): HassScheduleEvent {
  return {
    date: "2026-10-20", weekday: "wtorek", title: "Sprawdzian", subject: "matematyka",
    category: "", description: "", teacher: "", hour: "", lesson_number: null,
    event_type: "exam", is_exam: true, is_day_off: false, days_until: 7,
    ...over,
  };
}

describe("daysUntilLabel", () => {
  it("names today and tomorrow", () => {
    expect(daysUntilLabel(0)).toBe("dziś");
    expect(daysUntilLabel(1)).toBe("jutro");
  });
  it("counts further days", () => {
    expect(daysUntilLabel(2)).toBe("za 2 dni");
    expect(daysUntilLabel(22)).toBe("za 22 dni");
  });
});

describe("urgency", () => {
  it("grades how close the date is", () => {
    expect(urgency(0)).toBe("urgent");
    expect(urgency(1)).toBe("urgent");
    expect(urgency(3)).toBe("soon");
    expect(urgency(4)).toBe("later");
  });
});

describe("examLabel", () => {
  it("names each exam type in Polish", () => {
    expect(examLabel("exam")).toBe("Sprawdzian");
    expect(examLabel("quiz")).toBe("Kartkówka");
    expect(examLabel("class_test")).toBe("Praca klasowa");
    expect(examLabel("assessment")).toBe("Praca kontrolna");
    expect(examLabel("essay_test")).toBe("Wypracowanie");
    expect(examLabel("test")).toBe("Test");
  });
});

describe("pickExams", () => {
  it("keeps exams only, soonest first, past ones dropped", () => {
    const events = [
      ev({ date: "2026-10-25", days_until: 12 }),
      ev({ event_type: "reading", is_exam: false }),
      ev({ date: "2026-10-14", days_until: 1, event_type: "quiz" }),
      ev({ date: "2026-10-01", days_until: -12 }),
      ev({ event_type: "day_off", is_exam: false, is_day_off: true }),
    ];
    expect(pickExams(events).map(e => e.date)).toEqual(["2026-10-14", "2026-10-25"]);
  });
});

describe("pickReadings", () => {
  it("keeps readings by deadline", () => {
    const events = [
      ev({ date: "2026-11-05", event_type: "reading", is_exam: false, days_until: 23 }),
      ev({}),
      ev({ date: "2026-10-19", event_type: "reading", is_exam: false, days_until: 6 }),
    ];
    expect(pickReadings(events).map(e => e.date)).toEqual(["2026-10-19", "2026-11-05"]);
  });
});

describe("shortWeekday", () => {
  it("uses Polish abbreviations", () => {
    expect(shortWeekday("poniedziałek")).toBe("pn");
    expect(shortWeekday("wtorek")).toBe("wt");
    expect(shortWeekday("środa")).toBe("śr");
    expect(shortWeekday("czwartek")).toBe("czw");
    expect(shortWeekday("piątek")).toBe("pt");
    expect(shortWeekday("sobota")).toBe("sob");
    expect(shortWeekday("niedziela")).toBe("nd");
    expect(shortWeekday("")).toBe("");
  });
});
