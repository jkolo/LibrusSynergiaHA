import { describe, it, expect } from "vitest";
import { formatDate, formatShortDate } from "./grade-format.js";

describe("grade date formatting", () => {
  it("renders ISO dates the Polish way", () => {
    expect(formatDate("2026-09-17")).toBe("17.09.2026");
  });

  it("leaves Polish dates alone", () => {
    expect(formatDate("17.09.2026")).toBe("17.09.2026");
  });

  it("shortens to day and month", () => {
    expect(formatShortDate("2026-09-17")).toBe("17.09");
    expect(formatShortDate("17.09.2026")).toBe("17.09");
  });

  it("returns unrecognised text unchanged", () => {
    expect(formatShortDate("wczoraj")).toBe("wczoraj");
  });
});
