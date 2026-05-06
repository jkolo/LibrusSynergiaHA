import { describe, it, expect } from "vitest";
import { sanitizeHtml } from "./sanitize.js";

describe("sanitizeHtml", () => {
  it("preserves allowed tags", () => {
    const result = sanitizeHtml("<b>bold</b> and <i>italic</i>");
    expect(result).toContain("<b>bold</b>");
    expect(result).toContain("<i>italic</i>");
  });

  it("strips <script> tags and content", () => {
    const result = sanitizeHtml('<script>alert("xss")</script>hello');
    expect(result).not.toContain("<script>");
    expect(result).not.toContain("alert");
    expect(result).toContain("hello");
  });

  it("strips <img> with onerror", () => {
    const result = sanitizeHtml('<img src="x" onerror="alert(1)">');
    expect(result).not.toContain("<img");
    expect(result).not.toContain("onerror");
  });

  it("strips javascript: href from <a>", () => {
    const result = sanitizeHtml('<a href="javascript:alert(1)">click</a>');
    expect(result).not.toContain("javascript:");
  });

  it("allows safe <a href> with rel/target added", () => {
    const result = sanitizeHtml('<a href="https://librus.pl">link</a>');
    expect(result).toContain('href="https://librus.pl"');
    expect(result).toContain('rel="noopener noreferrer"');
    expect(result).toContain('target="_blank"');
  });

  it("strips <iframe>", () => {
    const result = sanitizeHtml('<iframe src="evil.html"></iframe>');
    expect(result).not.toContain("<iframe");
  });

  it("preserves text content of stripped elements", () => {
    const result = sanitizeHtml("<div>hello <span>world</span></div>");
    expect(result).toContain("hello");
    expect(result).toContain("world");
  });

  it("strips on* event attributes from allowed tags", () => {
    const result = sanitizeHtml('<b onclick="alert(1)">text</b>');
    expect(result).not.toContain("onclick");
    expect(result).toContain("<b>text</b>");
  });

  it("strips <style> tags", () => {
    const result = sanitizeHtml("<style>body{display:none}</style>text");
    expect(result).not.toContain("<style>");
    expect(result).not.toContain("display:none");
    expect(result).toContain("text");
  });

  it("handles nested allowed tags", () => {
    const result = sanitizeHtml("<ul><li><b>item</b></li></ul>");
    expect(result).toContain("<ul>");
    expect(result).toContain("<li>");
    expect(result).toContain("<b>item</b>");
  });

  it("handles empty string", () => {
    expect(sanitizeHtml("")).toBe("");
  });

  it("preserves <br> tags", () => {
    const result = sanitizeHtml("line1<br>line2");
    expect(result).toContain("<br>");
  });
});
