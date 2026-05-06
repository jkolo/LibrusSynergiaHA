const ALLOWED_TAGS = new Set([
  "p", "br", "b", "strong", "i", "em", "u", "s",
  "a", "ul", "ol", "li", "span", "div",
]);

const ALLOWED_ATTRS: Record<string, Set<string>> = {
  a: new Set(["href", "target"]),
};

function sanitizeNode(node: Node, out: DocumentFragment): void {
  if (node.nodeType === Node.TEXT_NODE) {
    out.appendChild(node.cloneNode());
    return;
  }
  if (node.nodeType !== Node.ELEMENT_NODE) return;

  const el = node as Element;
  const tag = el.tagName.toLowerCase();

  if (!ALLOWED_TAGS.has(tag)) {
    // Strip element but keep children
    for (const child of el.childNodes) {
      sanitizeNode(child, out);
    }
    return;
  }

  const clean = document.createElement(tag);
  const allowedAttrs = ALLOWED_ATTRS[tag];
  if (allowedAttrs) {
    for (const attr of el.attributes) {
      if (allowedAttrs.has(attr.name)) {
        const value = attr.value;
        // Block javascript: URLs
        if (attr.name === "href" && /^\s*javascript:/i.test(value)) continue;
        clean.setAttribute(attr.name, value);
      }
    }
  }
  // Force links to open in new tab safely
  if (tag === "a") {
    clean.setAttribute("target", "_blank");
    clean.setAttribute("rel", "noopener noreferrer");
  }

  const childFrag = document.createDocumentFragment();
  for (const child of el.childNodes) {
    sanitizeNode(child, childFrag);
  }
  clean.appendChild(childFrag);
  out.appendChild(clean);
}

export function sanitizeHtml(html: string): string {
  const parser = new DOMParser();
  const doc = parser.parseFromString(html, "text/html");
  const frag = document.createDocumentFragment();
  for (const child of doc.body.childNodes) {
    sanitizeNode(child, frag);
  }
  const wrapper = document.createElement("div");
  wrapper.appendChild(frag);
  return wrapper.innerHTML;
}
