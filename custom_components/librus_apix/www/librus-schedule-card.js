/**
 * @license
 * Copyright 2019 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const H = globalThis, W = H.ShadowRoot && (H.ShadyCSS === void 0 || H.ShadyCSS.nativeShadow) && "adoptedStyleSheets" in Document.prototype && "replace" in CSSStyleSheet.prototype, q = Symbol(), J = /* @__PURE__ */ new WeakMap();
let ot = class {
  constructor(t, e, s) {
    if (this._$cssResult$ = !0, s !== q) throw Error("CSSResult is not constructable. Use `unsafeCSS` or `css` instead.");
    this.cssText = t, this.t = e;
  }
  get styleSheet() {
    let t = this.o;
    const e = this.t;
    if (W && t === void 0) {
      const s = e !== void 0 && e.length === 1;
      s && (t = J.get(e)), t === void 0 && ((this.o = t = new CSSStyleSheet()).replaceSync(this.cssText), s && J.set(e, t));
    }
    return t;
  }
  toString() {
    return this.cssText;
  }
};
const ut = (i) => new ot(typeof i == "string" ? i : i + "", void 0, q), $t = (i, ...t) => {
  const e = i.length === 1 ? i[0] : t.reduce((s, r, o) => s + ((n) => {
    if (n._$cssResult$ === !0) return n.cssText;
    if (typeof n == "number") return n;
    throw Error("Value passed to 'css' function must be a 'css' function result: " + n + ". Use 'unsafeCSS' to pass non-literal values, but take care to ensure page security.");
  })(r) + i[o + 1], i[0]);
  return new ot(e, i, q);
}, ft = (i, t) => {
  if (W) i.adoptedStyleSheets = t.map((e) => e instanceof CSSStyleSheet ? e : e.styleSheet);
  else for (const e of t) {
    const s = document.createElement("style"), r = H.litNonce;
    r !== void 0 && s.setAttribute("nonce", r), s.textContent = e.cssText, i.appendChild(s);
  }
}, F = W ? (i) => i : (i) => i instanceof CSSStyleSheet ? ((t) => {
  let e = "";
  for (const s of t.cssRules) e += s.cssText;
  return ut(e);
})(i) : i;
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const { is: _t, defineProperty: gt, getOwnPropertyDescriptor: yt, getOwnPropertyNames: mt, getOwnPropertySymbols: vt, getPrototypeOf: wt } = Object, g = globalThis, X = g.trustedTypes, At = X ? X.emptyScript : "", D = g.reactiveElementPolyfillSupport, S = (i, t) => i, R = { toAttribute(i, t) {
  switch (t) {
    case Boolean:
      i = i ? At : null;
      break;
    case Object:
    case Array:
      i = i == null ? i : JSON.stringify(i);
  }
  return i;
}, fromAttribute(i, t) {
  let e = i;
  switch (t) {
    case Boolean:
      e = i !== null;
      break;
    case Number:
      e = i === null ? null : Number(i);
      break;
    case Object:
    case Array:
      try {
        e = JSON.parse(i);
      } catch {
        e = null;
      }
  }
  return e;
} }, V = (i, t) => !_t(i, t), Y = { attribute: !0, type: String, converter: R, reflect: !1, useDefault: !1, hasChanged: V };
Symbol.metadata ?? (Symbol.metadata = Symbol("metadata")), g.litPropertyMetadata ?? (g.litPropertyMetadata = /* @__PURE__ */ new WeakMap());
let A = class extends HTMLElement {
  static addInitializer(t) {
    this._$Ei(), (this.l ?? (this.l = [])).push(t);
  }
  static get observedAttributes() {
    return this.finalize(), this._$Eh && [...this._$Eh.keys()];
  }
  static createProperty(t, e = Y) {
    if (e.state && (e.attribute = !1), this._$Ei(), this.prototype.hasOwnProperty(t) && ((e = Object.create(e)).wrapped = !0), this.elementProperties.set(t, e), !e.noAccessor) {
      const s = Symbol(), r = this.getPropertyDescriptor(t, s, e);
      r !== void 0 && gt(this.prototype, t, r);
    }
  }
  static getPropertyDescriptor(t, e, s) {
    const { get: r, set: o } = yt(this.prototype, t) ?? { get() {
      return this[e];
    }, set(n) {
      this[e] = n;
    } };
    return { get: r, set(n) {
      const h = r == null ? void 0 : r.call(this);
      o == null || o.call(this, n), this.requestUpdate(t, h, s);
    }, configurable: !0, enumerable: !0 };
  }
  static getPropertyOptions(t) {
    return this.elementProperties.get(t) ?? Y;
  }
  static _$Ei() {
    if (this.hasOwnProperty(S("elementProperties"))) return;
    const t = wt(this);
    t.finalize(), t.l !== void 0 && (this.l = [...t.l]), this.elementProperties = new Map(t.elementProperties);
  }
  static finalize() {
    if (this.hasOwnProperty(S("finalized"))) return;
    if (this.finalized = !0, this._$Ei(), this.hasOwnProperty(S("properties"))) {
      const e = this.properties, s = [...mt(e), ...vt(e)];
      for (const r of s) this.createProperty(r, e[r]);
    }
    const t = this[Symbol.metadata];
    if (t !== null) {
      const e = litPropertyMetadata.get(t);
      if (e !== void 0) for (const [s, r] of e) this.elementProperties.set(s, r);
    }
    this._$Eh = /* @__PURE__ */ new Map();
    for (const [e, s] of this.elementProperties) {
      const r = this._$Eu(e, s);
      r !== void 0 && this._$Eh.set(r, e);
    }
    this.elementStyles = this.finalizeStyles(this.styles);
  }
  static finalizeStyles(t) {
    const e = [];
    if (Array.isArray(t)) {
      const s = new Set(t.flat(1 / 0).reverse());
      for (const r of s) e.unshift(F(r));
    } else t !== void 0 && e.push(F(t));
    return e;
  }
  static _$Eu(t, e) {
    const s = e.attribute;
    return s === !1 ? void 0 : typeof s == "string" ? s : typeof t == "string" ? t.toLowerCase() : void 0;
  }
  constructor() {
    super(), this._$Ep = void 0, this.isUpdatePending = !1, this.hasUpdated = !1, this._$Em = null, this._$Ev();
  }
  _$Ev() {
    var t;
    this._$ES = new Promise((e) => this.enableUpdating = e), this._$AL = /* @__PURE__ */ new Map(), this._$E_(), this.requestUpdate(), (t = this.constructor.l) == null || t.forEach((e) => e(this));
  }
  addController(t) {
    var e;
    (this._$EO ?? (this._$EO = /* @__PURE__ */ new Set())).add(t), this.renderRoot !== void 0 && this.isConnected && ((e = t.hostConnected) == null || e.call(t));
  }
  removeController(t) {
    var e;
    (e = this._$EO) == null || e.delete(t);
  }
  _$E_() {
    const t = /* @__PURE__ */ new Map(), e = this.constructor.elementProperties;
    for (const s of e.keys()) this.hasOwnProperty(s) && (t.set(s, this[s]), delete this[s]);
    t.size > 0 && (this._$Ep = t);
  }
  createRenderRoot() {
    const t = this.shadowRoot ?? this.attachShadow(this.constructor.shadowRootOptions);
    return ft(t, this.constructor.elementStyles), t;
  }
  connectedCallback() {
    var t;
    this.renderRoot ?? (this.renderRoot = this.createRenderRoot()), this.enableUpdating(!0), (t = this._$EO) == null || t.forEach((e) => {
      var s;
      return (s = e.hostConnected) == null ? void 0 : s.call(e);
    });
  }
  enableUpdating(t) {
  }
  disconnectedCallback() {
    var t;
    (t = this._$EO) == null || t.forEach((e) => {
      var s;
      return (s = e.hostDisconnected) == null ? void 0 : s.call(e);
    });
  }
  attributeChangedCallback(t, e, s) {
    this._$AK(t, s);
  }
  _$ET(t, e) {
    var o;
    const s = this.constructor.elementProperties.get(t), r = this.constructor._$Eu(t, s);
    if (r !== void 0 && s.reflect === !0) {
      const n = (((o = s.converter) == null ? void 0 : o.toAttribute) !== void 0 ? s.converter : R).toAttribute(e, s.type);
      this._$Em = t, n == null ? this.removeAttribute(r) : this.setAttribute(r, n), this._$Em = null;
    }
  }
  _$AK(t, e) {
    var o, n;
    const s = this.constructor, r = s._$Eh.get(t);
    if (r !== void 0 && this._$Em !== r) {
      const h = s.getPropertyOptions(r), a = typeof h.converter == "function" ? { fromAttribute: h.converter } : ((o = h.converter) == null ? void 0 : o.fromAttribute) !== void 0 ? h.converter : R;
      this._$Em = r;
      const d = a.fromAttribute(e, h.type);
      this[r] = d ?? ((n = this._$Ej) == null ? void 0 : n.get(r)) ?? d, this._$Em = null;
    }
  }
  requestUpdate(t, e, s, r = !1, o) {
    var n;
    if (t !== void 0) {
      const h = this.constructor;
      if (r === !1 && (o = this[t]), s ?? (s = h.getPropertyOptions(t)), !((s.hasChanged ?? V)(o, e) || s.useDefault && s.reflect && o === ((n = this._$Ej) == null ? void 0 : n.get(t)) && !this.hasAttribute(h._$Eu(t, s)))) return;
      this.C(t, e, s);
    }
    this.isUpdatePending === !1 && (this._$ES = this._$EP());
  }
  C(t, e, { useDefault: s, reflect: r, wrapped: o }, n) {
    s && !(this._$Ej ?? (this._$Ej = /* @__PURE__ */ new Map())).has(t) && (this._$Ej.set(t, n ?? e ?? this[t]), o !== !0 || n !== void 0) || (this._$AL.has(t) || (this.hasUpdated || s || (e = void 0), this._$AL.set(t, e)), r === !0 && this._$Em !== t && (this._$Eq ?? (this._$Eq = /* @__PURE__ */ new Set())).add(t));
  }
  async _$EP() {
    this.isUpdatePending = !0;
    try {
      await this._$ES;
    } catch (e) {
      Promise.reject(e);
    }
    const t = this.scheduleUpdate();
    return t != null && await t, !this.isUpdatePending;
  }
  scheduleUpdate() {
    return this.performUpdate();
  }
  performUpdate() {
    var s;
    if (!this.isUpdatePending) return;
    if (!this.hasUpdated) {
      if (this.renderRoot ?? (this.renderRoot = this.createRenderRoot()), this._$Ep) {
        for (const [o, n] of this._$Ep) this[o] = n;
        this._$Ep = void 0;
      }
      const r = this.constructor.elementProperties;
      if (r.size > 0) for (const [o, n] of r) {
        const { wrapped: h } = n, a = this[o];
        h !== !0 || this._$AL.has(o) || a === void 0 || this.C(o, void 0, n, a);
      }
    }
    let t = !1;
    const e = this._$AL;
    try {
      t = this.shouldUpdate(e), t ? (this.willUpdate(e), (s = this._$EO) == null || s.forEach((r) => {
        var o;
        return (o = r.hostUpdate) == null ? void 0 : o.call(r);
      }), this.update(e)) : this._$EM();
    } catch (r) {
      throw t = !1, this._$EM(), r;
    }
    t && this._$AE(e);
  }
  willUpdate(t) {
  }
  _$AE(t) {
    var e;
    (e = this._$EO) == null || e.forEach((s) => {
      var r;
      return (r = s.hostUpdated) == null ? void 0 : r.call(s);
    }), this.hasUpdated || (this.hasUpdated = !0, this.firstUpdated(t)), this.updated(t);
  }
  _$EM() {
    this._$AL = /* @__PURE__ */ new Map(), this.isUpdatePending = !1;
  }
  get updateComplete() {
    return this.getUpdateComplete();
  }
  getUpdateComplete() {
    return this._$ES;
  }
  shouldUpdate(t) {
    return !0;
  }
  update(t) {
    this._$Eq && (this._$Eq = this._$Eq.forEach((e) => this._$ET(e, this[e]))), this._$EM();
  }
  updated(t) {
  }
  firstUpdated(t) {
  }
};
A.elementStyles = [], A.shadowRootOptions = { mode: "open" }, A[S("elementProperties")] = /* @__PURE__ */ new Map(), A[S("finalized")] = /* @__PURE__ */ new Map(), D == null || D({ ReactiveElement: A }), (g.reactiveElementVersions ?? (g.reactiveElementVersions = [])).push("2.1.2");
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const C = globalThis, G = (i) => i, N = C.trustedTypes, Q = N ? N.createPolicy("lit-html", { createHTML: (i) => i }) : void 0, at = "$lit$", _ = `lit$${Math.random().toFixed(9).slice(2)}$`, ht = "?" + _, bt = `<${ht}>`, w = document, k = () => w.createComment(""), z = (i) => i === null || typeof i != "object" && typeof i != "function", K = Array.isArray, xt = (i) => K(i) || typeof (i == null ? void 0 : i[Symbol.iterator]) == "function", L = `[ 	
\f\r]`, E = /<(?:(!--|\/[^a-zA-Z])|(\/?[a-zA-Z][^>\s]*)|(\/?$))/g, tt = /-->/g, et = />/g, y = RegExp(`>|${L}(?:([^\\s"'>=/]+)(${L}*=${L}*(?:[^ 	
\f\r"'\`<>=]|("|')|))|$)`, "g"), st = /'/g, it = /"/g, lt = /^(?:script|style|textarea|title)$/i, Et = (i) => (t, ...e) => ({ _$litType$: i, strings: t, values: e }), u = Et(1), b = Symbol.for("lit-noChange"), c = Symbol.for("lit-nothing"), rt = /* @__PURE__ */ new WeakMap(), m = w.createTreeWalker(w, 129);
function ct(i, t) {
  if (!K(i) || !i.hasOwnProperty("raw")) throw Error("invalid template strings array");
  return Q !== void 0 ? Q.createHTML(t) : t;
}
const St = (i, t) => {
  const e = i.length - 1, s = [];
  let r, o = t === 2 ? "<svg>" : t === 3 ? "<math>" : "", n = E;
  for (let h = 0; h < e; h++) {
    const a = i[h];
    let d, p, l = -1, $ = 0;
    for (; $ < a.length && (n.lastIndex = $, p = n.exec(a), p !== null); ) $ = n.lastIndex, n === E ? p[1] === "!--" ? n = tt : p[1] !== void 0 ? n = et : p[2] !== void 0 ? (lt.test(p[2]) && (r = RegExp("</" + p[2], "g")), n = y) : p[3] !== void 0 && (n = y) : n === y ? p[0] === ">" ? (n = r ?? E, l = -1) : p[1] === void 0 ? l = -2 : (l = n.lastIndex - p[2].length, d = p[1], n = p[3] === void 0 ? y : p[3] === '"' ? it : st) : n === it || n === st ? n = y : n === tt || n === et ? n = E : (n = y, r = void 0);
    const f = n === y && i[h + 1].startsWith("/>") ? " " : "";
    o += n === E ? a + bt : l >= 0 ? (s.push(d), a.slice(0, l) + at + a.slice(l) + _ + f) : a + _ + (l === -2 ? h : f);
  }
  return [ct(i, o + (i[e] || "<?>") + (t === 2 ? "</svg>" : t === 3 ? "</math>" : "")), s];
};
class O {
  constructor({ strings: t, _$litType$: e }, s) {
    let r;
    this.parts = [];
    let o = 0, n = 0;
    const h = t.length - 1, a = this.parts, [d, p] = St(t, e);
    if (this.el = O.createElement(d, s), m.currentNode = this.el.content, e === 2 || e === 3) {
      const l = this.el.content.firstChild;
      l.replaceWith(...l.childNodes);
    }
    for (; (r = m.nextNode()) !== null && a.length < h; ) {
      if (r.nodeType === 1) {
        if (r.hasAttributes()) for (const l of r.getAttributeNames()) if (l.endsWith(at)) {
          const $ = p[n++], f = r.getAttribute(l).split(_), M = /([.?@])?(.*)/.exec($);
          a.push({ type: 1, index: o, name: M[2], strings: f, ctor: M[1] === "." ? Pt : M[1] === "?" ? kt : M[1] === "@" ? zt : j }), r.removeAttribute(l);
        } else l.startsWith(_) && (a.push({ type: 6, index: o }), r.removeAttribute(l));
        if (lt.test(r.tagName)) {
          const l = r.textContent.split(_), $ = l.length - 1;
          if ($ > 0) {
            r.textContent = N ? N.emptyScript : "";
            for (let f = 0; f < $; f++) r.append(l[f], k()), m.nextNode(), a.push({ type: 2, index: ++o });
            r.append(l[$], k());
          }
        }
      } else if (r.nodeType === 8) if (r.data === ht) a.push({ type: 2, index: o });
      else {
        let l = -1;
        for (; (l = r.data.indexOf(_, l + 1)) !== -1; ) a.push({ type: 7, index: o }), l += _.length - 1;
      }
      o++;
    }
  }
  static createElement(t, e) {
    const s = w.createElement("template");
    return s.innerHTML = t, s;
  }
}
function x(i, t, e = i, s) {
  var n, h;
  if (t === b) return t;
  let r = s !== void 0 ? (n = e._$Co) == null ? void 0 : n[s] : e._$Cl;
  const o = z(t) ? void 0 : t._$litDirective$;
  return (r == null ? void 0 : r.constructor) !== o && ((h = r == null ? void 0 : r._$AO) == null || h.call(r, !1), o === void 0 ? r = void 0 : (r = new o(i), r._$AT(i, e, s)), s !== void 0 ? (e._$Co ?? (e._$Co = []))[s] = r : e._$Cl = r), r !== void 0 && (t = x(i, r._$AS(i, t.values), r, s)), t;
}
class Ct {
  constructor(t, e) {
    this._$AV = [], this._$AN = void 0, this._$AD = t, this._$AM = e;
  }
  get parentNode() {
    return this._$AM.parentNode;
  }
  get _$AU() {
    return this._$AM._$AU;
  }
  u(t) {
    const { el: { content: e }, parts: s } = this._$AD, r = ((t == null ? void 0 : t.creationScope) ?? w).importNode(e, !0);
    m.currentNode = r;
    let o = m.nextNode(), n = 0, h = 0, a = s[0];
    for (; a !== void 0; ) {
      if (n === a.index) {
        let d;
        a.type === 2 ? d = new T(o, o.nextSibling, this, t) : a.type === 1 ? d = new a.ctor(o, a.name, a.strings, this, t) : a.type === 6 && (d = new Ot(o, this, t)), this._$AV.push(d), a = s[++h];
      }
      n !== (a == null ? void 0 : a.index) && (o = m.nextNode(), n++);
    }
    return m.currentNode = w, r;
  }
  p(t) {
    let e = 0;
    for (const s of this._$AV) s !== void 0 && (s.strings !== void 0 ? (s._$AI(t, s, e), e += s.strings.length - 2) : s._$AI(t[e])), e++;
  }
}
class T {
  get _$AU() {
    var t;
    return ((t = this._$AM) == null ? void 0 : t._$AU) ?? this._$Cv;
  }
  constructor(t, e, s, r) {
    this.type = 2, this._$AH = c, this._$AN = void 0, this._$AA = t, this._$AB = e, this._$AM = s, this.options = r, this._$Cv = (r == null ? void 0 : r.isConnected) ?? !0;
  }
  get parentNode() {
    let t = this._$AA.parentNode;
    const e = this._$AM;
    return e !== void 0 && (t == null ? void 0 : t.nodeType) === 11 && (t = e.parentNode), t;
  }
  get startNode() {
    return this._$AA;
  }
  get endNode() {
    return this._$AB;
  }
  _$AI(t, e = this) {
    t = x(this, t, e), z(t) ? t === c || t == null || t === "" ? (this._$AH !== c && this._$AR(), this._$AH = c) : t !== this._$AH && t !== b && this._(t) : t._$litType$ !== void 0 ? this.$(t) : t.nodeType !== void 0 ? this.T(t) : xt(t) ? this.k(t) : this._(t);
  }
  O(t) {
    return this._$AA.parentNode.insertBefore(t, this._$AB);
  }
  T(t) {
    this._$AH !== t && (this._$AR(), this._$AH = this.O(t));
  }
  _(t) {
    this._$AH !== c && z(this._$AH) ? this._$AA.nextSibling.data = t : this.T(w.createTextNode(t)), this._$AH = t;
  }
  $(t) {
    var o;
    const { values: e, _$litType$: s } = t, r = typeof s == "number" ? this._$AC(t) : (s.el === void 0 && (s.el = O.createElement(ct(s.h, s.h[0]), this.options)), s);
    if (((o = this._$AH) == null ? void 0 : o._$AD) === r) this._$AH.p(e);
    else {
      const n = new Ct(r, this), h = n.u(this.options);
      n.p(e), this.T(h), this._$AH = n;
    }
  }
  _$AC(t) {
    let e = rt.get(t.strings);
    return e === void 0 && rt.set(t.strings, e = new O(t)), e;
  }
  k(t) {
    K(this._$AH) || (this._$AH = [], this._$AR());
    const e = this._$AH;
    let s, r = 0;
    for (const o of t) r === e.length ? e.push(s = new T(this.O(k()), this.O(k()), this, this.options)) : s = e[r], s._$AI(o), r++;
    r < e.length && (this._$AR(s && s._$AB.nextSibling, r), e.length = r);
  }
  _$AR(t = this._$AA.nextSibling, e) {
    var s;
    for ((s = this._$AP) == null ? void 0 : s.call(this, !1, !0, e); t !== this._$AB; ) {
      const r = G(t).nextSibling;
      G(t).remove(), t = r;
    }
  }
  setConnected(t) {
    var e;
    this._$AM === void 0 && (this._$Cv = t, (e = this._$AP) == null || e.call(this, t));
  }
}
class j {
  get tagName() {
    return this.element.tagName;
  }
  get _$AU() {
    return this._$AM._$AU;
  }
  constructor(t, e, s, r, o) {
    this.type = 1, this._$AH = c, this._$AN = void 0, this.element = t, this.name = e, this._$AM = r, this.options = o, s.length > 2 || s[0] !== "" || s[1] !== "" ? (this._$AH = Array(s.length - 1).fill(new String()), this.strings = s) : this._$AH = c;
  }
  _$AI(t, e = this, s, r) {
    const o = this.strings;
    let n = !1;
    if (o === void 0) t = x(this, t, e, 0), n = !z(t) || t !== this._$AH && t !== b, n && (this._$AH = t);
    else {
      const h = t;
      let a, d;
      for (t = o[0], a = 0; a < o.length - 1; a++) d = x(this, h[s + a], e, a), d === b && (d = this._$AH[a]), n || (n = !z(d) || d !== this._$AH[a]), d === c ? t = c : t !== c && (t += (d ?? "") + o[a + 1]), this._$AH[a] = d;
    }
    n && !r && this.j(t);
  }
  j(t) {
    t === c ? this.element.removeAttribute(this.name) : this.element.setAttribute(this.name, t ?? "");
  }
}
class Pt extends j {
  constructor() {
    super(...arguments), this.type = 3;
  }
  j(t) {
    this.element[this.name] = t === c ? void 0 : t;
  }
}
class kt extends j {
  constructor() {
    super(...arguments), this.type = 4;
  }
  j(t) {
    this.element.toggleAttribute(this.name, !!t && t !== c);
  }
}
class zt extends j {
  constructor(t, e, s, r, o) {
    super(t, e, s, r, o), this.type = 5;
  }
  _$AI(t, e = this) {
    if ((t = x(this, t, e, 0) ?? c) === b) return;
    const s = this._$AH, r = t === c && s !== c || t.capture !== s.capture || t.once !== s.once || t.passive !== s.passive, o = t !== c && (s === c || r);
    r && this.element.removeEventListener(this.name, this, s), o && this.element.addEventListener(this.name, this, t), this._$AH = t;
  }
  handleEvent(t) {
    var e;
    typeof this._$AH == "function" ? this._$AH.call(((e = this.options) == null ? void 0 : e.host) ?? this.element, t) : this._$AH.handleEvent(t);
  }
}
class Ot {
  constructor(t, e, s) {
    this.element = t, this.type = 6, this._$AN = void 0, this._$AM = e, this.options = s;
  }
  get _$AU() {
    return this._$AM._$AU;
  }
  _$AI(t) {
    x(this, t);
  }
}
const B = C.litHtmlPolyfillSupport;
B == null || B(O, T), (C.litHtmlVersions ?? (C.litHtmlVersions = [])).push("3.3.2");
const Ut = (i, t, e) => {
  const s = (e == null ? void 0 : e.renderBefore) ?? t;
  let r = s._$litPart$;
  if (r === void 0) {
    const o = (e == null ? void 0 : e.renderBefore) ?? null;
    s._$litPart$ = r = new T(t.insertBefore(k(), o), o, void 0, e ?? {});
  }
  return r._$AI(i), r;
};
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const v = globalThis;
class P extends A {
  constructor() {
    super(...arguments), this.renderOptions = { host: this }, this._$Do = void 0;
  }
  createRenderRoot() {
    var e;
    const t = super.createRenderRoot();
    return (e = this.renderOptions).renderBefore ?? (e.renderBefore = t.firstChild), t;
  }
  update(t) {
    const e = this.render();
    this.hasUpdated || (this.renderOptions.isConnected = this.isConnected), super.update(t), this._$Do = Ut(e, this.renderRoot, this.renderOptions);
  }
  connectedCallback() {
    var t;
    super.connectedCallback(), (t = this._$Do) == null || t.setConnected(!0);
  }
  disconnectedCallback() {
    var t;
    super.disconnectedCallback(), (t = this._$Do) == null || t.setConnected(!1);
  }
  render() {
    return b;
  }
}
var nt;
P._$litElement$ = !0, P.finalized = !0, (nt = v.litElementHydrateSupport) == null || nt.call(v, { LitElement: P });
const I = v.litElementPolyfillSupport;
I == null || I({ LitElement: P });
(v.litElementVersions ?? (v.litElementVersions = [])).push("4.2.2");
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const Tt = (i) => (t, e) => {
  e !== void 0 ? e.addInitializer(() => {
    customElements.define(i, t);
  }) : customElements.define(i, t);
};
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const Mt = { attribute: !0, type: String, converter: R, reflect: !1, hasChanged: V }, Ht = (i = Mt, t, e) => {
  const { kind: s, metadata: r } = e;
  let o = globalThis.litPropertyMetadata.get(r);
  if (o === void 0 && globalThis.litPropertyMetadata.set(r, o = /* @__PURE__ */ new Map()), s === "setter" && ((i = Object.create(i)).wrapped = !0), o.set(e.name, i), s === "accessor") {
    const { name: n } = e;
    return { set(h) {
      const a = t.get.call(this);
      t.set.call(this, h), this.requestUpdate(n, a, i, !0, h);
    }, init(h) {
      return h !== void 0 && this.C(n, void 0, i, h), h;
    } };
  }
  if (s === "setter") {
    const { name: n } = e;
    return function(h) {
      const a = this[n];
      t.call(this, h), this.requestUpdate(n, a, i, !0, h);
    };
  }
  throw Error("Unsupported decorator location: " + s);
};
function dt(i) {
  return (t, e) => typeof e == "object" ? Ht(i, t, e) : ((s, r, o) => {
    const n = r.hasOwnProperty(o);
    return r.constructor.createProperty(o, s), n ? Object.getOwnPropertyDescriptor(r, o) : void 0;
  })(i, t, e);
}
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
function Rt(i) {
  return dt({ ...i, state: !0, attribute: !1 });
}
function Nt(i) {
  if (/^\d{2}\.\d{2}\.\d{4}$/.test(i)) return i;
  if (/^\d{4}-\d{2}-\d{2}$/.test(i)) {
    const [t, e, s] = i.split("-");
    return `${s}.${e}.${t}`;
  }
  return i;
}
function jt(i) {
  return Nt(i).replace(/^(\d{2}\.\d{2})\.\d{4}$/, "$1");
}
const Dt = {
  exam: "Sprawdzian",
  quiz: "Kartkówka",
  class_test: "Praca klasowa",
  assessment: "Praca kontrolna",
  essay_test: "Wypracowanie",
  test: "Test"
};
function Lt(i) {
  return Dt[i] ?? "Sprawdzian";
}
function Bt(i) {
  return i <= 0 ? "dziś" : i === 1 ? "jutro" : `za ${i} dni`;
}
function It(i) {
  return i <= 1 ? "urgent" : i <= 3 ? "soon" : "later";
}
function pt(i) {
  return i.filter((t) => (t.days_until ?? 0) >= 0).sort((t, e) => t.date.localeCompare(e.date));
}
function Wt(i) {
  return pt(i.filter((t) => t.is_exam));
}
function qt(i) {
  return pt(i.filter((t) => t.event_type === "reading"));
}
const Vt = {
  poniedziałek: "pn",
  wtorek: "wt",
  środa: "śr",
  czwartek: "czw",
  piątek: "pt",
  sobota: "sob",
  niedziela: "nd"
};
function Kt(i) {
  return Vt[i] ?? i;
}
var Zt = Object.defineProperty, Jt = Object.getOwnPropertyDescriptor, Z = (i, t, e, s) => {
  for (var r = s > 1 ? void 0 : s ? Jt(t, e) : t, o = i.length - 1, n; o >= 0; o--)
    (n = i[o]) && (r = (s ? n(t, e, r) : n(r)) || r);
  return s && r && Zt(t, e, r), r;
};
let U = class extends P {
  static getStubConfig() {
    return { type: "librus-schedule-card", entity: "" };
  }
  setConfig(i) {
    if (!i.entity) throw new Error("entity jest wymagany (sensor.<uczeń>_terminarz)");
    this._config = i;
  }
  getCardSize() {
    return 4;
  }
  _renderWhen(i) {
    return u`<div class="when ${It(i.days_until)}">
      <span class="days">${Bt(i.days_until)}</span>
      <span class="date">${i.weekday ? Kt(i.weekday) + " " : ""}${jt(i.date)}</span>
    </div>`;
  }
  _renderExam(i) {
    return u`<li class="row">
      ${this._renderWhen(i)}
      <div class="what">
        <div class="headline">
          <span class="kind kind-${i.event_type}">${Lt(i.event_type)}</span>
          <span class="subject">${i.subject}</span>
        </div>
        ${i.description ? u`<div class="desc" title="${i.description}">${i.description}</div>` : c}
      </div>
    </li>`;
  }
  _renderReading(i) {
    const t = i.description || i.title;
    return u`<li class="row">
      ${this._renderWhen(i)}
      <div class="what">
        <div class="headline"><span class="subject">${i.subject || "Lektura"}</span></div>
        <div class="desc reading" title="${t}">📖 ${t}</div>
      </div>
    </li>`;
  }
  _renderSection(i, t, e, s) {
    return u`<section>
      <h3>${i}${t.length ? u` <span class="count">${t.length}</span>` : c}</h3>
      ${t.length ? u`<ul>${t.map(s)}</ul>` : u`<div class="empty">${e}</div>`}
    </section>`;
  }
  render() {
    var o, n;
    if (!this._config || !this.hass) return c;
    const i = this.hass.states[this._config.entity];
    if (!i)
      return u`<ha-card><div class="empty pad">Brak encji ${this._config.entity}</div></ha-card>`;
    const t = ((o = i.attributes) == null ? void 0 : o.events) ?? [], e = !!((n = i.attributes) != null && n.events_truncated), s = this._config.show_exams !== !1, r = this._config.show_readings !== !1;
    return u`
      <ha-card>
        <div class="card-header">${this._config.title ?? "Sprawdziany i lektury"}</div>
        ${s ? this._renderSection(
      "Sprawdziany",
      Wt(t),
      "Brak zapowiedzianych sprawdzianów",
      (h) => this._renderExam(h)
    ) : c}
        ${r ? this._renderSection(
      "Lektury",
      qt(t),
      "Brak lektur w terminarzu",
      (h) => this._renderReading(h)
    ) : c}
        ${e ? u`<div class="note">Terminarz przycięty — dalsze wpisy są w kalendarzu „Terminarz”.</div>` : c}
      </ha-card>
    `;
  }
};
U.styles = $t`
    :host { display: block; }
    ha-card { padding: 0 0 8px; }

    .card-header {
      padding: 12px 16px 4px;
      font-size: 1.1em;
      font-weight: 500;
      color: var(--primary-text-color);
    }

    section { padding: 4px 16px 0; }
    h3 {
      margin: 8px 0 4px;
      font-size: 0.8em;
      font-weight: 600;
      letter-spacing: 0.04em;
      text-transform: uppercase;
      color: var(--secondary-text-color);
    }
    .count {
      display: inline-block;
      min-width: 1.4em;
      padding: 0 5px;
      border-radius: 9px;
      background: var(--secondary-background-color, #eee);
      text-align: center;
      font-weight: 600;
    }

    ul { list-style: none; margin: 0; padding: 0; }
    .row {
      display: flex;
      gap: 12px;
      align-items: flex-start;
      padding: 7px 0;
      border-top: 1px solid var(--divider-color, #e0e0e0);
    }
    .row:first-child { border-top: none; }

    .when {
      flex: 0 0 76px;
      display: flex;
      flex-direction: column;
      align-items: center;
      padding: 3px 4px;
      border-radius: 8px;
      background: var(--when-bg);
      color: var(--when-fg);
    }
    .when .days { font-weight: 700; font-size: 0.9em; white-space: nowrap; }
    .when .date { font-size: 0.75em; opacity: 0.85; white-space: nowrap; }
    .when.urgent { --when-bg: var(--error-color, #db4437); --when-fg: #fff; }
    .when.soon   { --when-bg: var(--warning-color, #ffa600); --when-fg: #fff; }
    .when.later  {
      --when-bg: var(--secondary-background-color, #f2f2f2);
      --when-fg: var(--primary-text-color);
    }

    .what { flex: 1 1 auto; min-width: 0; }
    .headline { display: flex; gap: 6px; align-items: baseline; flex-wrap: wrap; }
    .kind { font-weight: 600; color: var(--primary-text-color); }
    .kind-quiz { color: var(--warning-color, #ffa600); }
    .subject { color: var(--primary-text-color); }
    .kind + .subject { color: var(--secondary-text-color); }
    .desc {
      font-size: 0.85em;
      color: var(--secondary-text-color);
      display: -webkit-box;
      -webkit-line-clamp: 2;
      -webkit-box-orient: vertical;
      overflow: hidden;
      word-break: break-word;
    }
    .desc.reading { color: var(--primary-text-color); }

    .empty { font-size: 0.85em; color: var(--secondary-text-color); padding: 4px 0 8px; }
    .empty.pad { padding: 16px; }
    .note {
      margin: 6px 16px 0;
      font-size: 0.75em;
      color: var(--secondary-text-color);
    }
  `;
Z([
  dt({ attribute: !1 })
], U.prototype, "hass", 2);
Z([
  Rt()
], U.prototype, "_config", 2);
U = Z([
  Tt("librus-schedule-card")
], U);
window.customCards ?? (window.customCards = []);
window.customCards.push({
  type: "librus-schedule-card",
  name: "Librus — Sprawdziany i lektury",
  description: "Nadchodzące sprawdziany i kartkówki z liczbą dni do terminu oraz lektury z terminarza."
});
export {
  U as LibrusScheduleCard
};
