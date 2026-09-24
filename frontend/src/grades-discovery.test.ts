import { describe, it, expect } from "vitest";
import { resolveGradeEntities } from "./grades-discovery.js";
import type { HomeAssistant } from "./types.js";

function makeHass(): HomeAssistant {
  const subject = (id: string) => ({ entity_id: id, state: "1", attributes: { grade_details: [] } });
  const plain = (id: string) => ({ entity_id: id, state: "5", attributes: { grade_count: 5 } });
  return {
    states: {
      "sensor.librus_ewa_grades": plain("sensor.librus_ewa_grades"),
      "sensor.librus_ewa_math": subject("sensor.librus_ewa_math"),
      "sensor.librus_ewa_jezyk_polski": subject("sensor.librus_ewa_jezyk_polski"),
      "sensor.librus_ewa_old_subject": { entity_id: "sensor.librus_ewa_old_subject", state: "unavailable", attributes: {} },
      "sensor.librus_luk_math": subject("sensor.librus_luk_math"),
    },
    entities: {
      "sensor.librus_ewa_grades": { entity_id: "sensor.librus_ewa_grades", device_id: "dev-ewa" },
      "sensor.librus_ewa_math": { entity_id: "sensor.librus_ewa_math", device_id: "dev-ewa" },
      "sensor.librus_ewa_jezyk_polski": { entity_id: "sensor.librus_ewa_jezyk_polski", device_id: "dev-ewa" },
      "sensor.librus_ewa_old_subject": { entity_id: "sensor.librus_ewa_old_subject", device_id: "dev-ewa" },
      "sensor.librus_luk_math": { entity_id: "sensor.librus_luk_math", device_id: "dev-luk" },
    },
    callService: async () => undefined,
  };
}

describe("resolveGradeEntities", () => {
  it("discovers subject sensors on the same device as the anchor entity", () => {
    const result = resolveGradeEntities(makeHass(), { type: "librus-grades-card", entity: "sensor.librus_ewa_grades" });
    expect(result.sort()).toEqual(["sensor.librus_ewa_jezyk_polski", "sensor.librus_ewa_math"]);
  });

  it("skips sensors without grade_details (aggregates, unavailable leftovers)", () => {
    const result = resolveGradeEntities(makeHass(), { type: "librus-grades-card", entity: "sensor.librus_ewa_grades" });
    expect(result).not.toContain("sensor.librus_ewa_grades");
    expect(result).not.toContain("sensor.librus_ewa_old_subject");
  });

  it("does not pick up another student's device", () => {
    const result = resolveGradeEntities(makeHass(), { type: "librus-grades-card", entity: "sensor.librus_ewa_grades" });
    expect(result).not.toContain("sensor.librus_luk_math");
  });

  it("passes an explicit entities list through unchanged", () => {
    const result = resolveGradeEntities(makeHass(), { type: "librus-grades-card", entities: ["sensor.librus_luk_math"] });
    expect(result).toEqual(["sensor.librus_luk_math"]);
  });

  it("merges explicit entities with discovered ones without duplicates", () => {
    const result = resolveGradeEntities(makeHass(), {
      type: "librus-grades-card",
      entity: "sensor.librus_ewa_grades",
      entities: ["sensor.librus_ewa_math", "sensor.librus_luk_math"],
    });
    expect(result.sort()).toEqual(["sensor.librus_ewa_jezyk_polski", "sensor.librus_ewa_math", "sensor.librus_luk_math"]);
  });

  it("returns nothing when the anchor entity has no device", () => {
    const hass = makeHass();
    delete hass.entities!["sensor.librus_ewa_grades"];
    const result = resolveGradeEntities(hass, { type: "librus-grades-card", entity: "sensor.librus_ewa_grades" });
    expect(result).toEqual([]);
  });
});
