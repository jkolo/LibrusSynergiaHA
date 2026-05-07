/**
 * @license
 * Copyright 2019 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const H = globalThis, Z = H.ShadowRoot && (H.ShadyCSS === void 0 || H.ShadyCSS.nativeShadow) && "adoptedStyleSheets" in Document.prototype && "replace" in CSSStyleSheet.prototype, J = Symbol(), X = /* @__PURE__ */ new WeakMap();
let de = class {
  constructor(e, t, s) {
    if (this._$cssResult$ = !0, s !== J) throw Error("CSSResult is not constructable. Use `unsafeCSS` or `css` instead.");
    this.cssText = e, this.t = t;
  }
  get styleSheet() {
    let e = this.o;
    const t = this.t;
    if (Z && e === void 0) {
      const s = t !== void 0 && t.length === 1;
      s && (e = X.get(t)), e === void 0 && ((this.o = e = new CSSStyleSheet()).replaceSync(this.cssText), s && X.set(t, e));
    }
    return e;
  }
  toString() {
    return this.cssText;
  }
};
const fe = (i) => new de(typeof i == "string" ? i : i + "", void 0, J), _e = (i, ...e) => {
  const t = i.length === 1 ? i[0] : e.reduce((s, r, o) => s + ((n) => {
    if (n._$cssResult$ === !0) return n.cssText;
    if (typeof n == "number") return n;
    throw Error("Value passed to 'css' function must be a 'css' function result: " + n + ". Use 'unsafeCSS' to pass non-literal values, but take care to ensure page security.");
  })(r) + i[o + 1], i[0]);
  return new de(t, i, J);
}, $e = (i, e) => {
  if (Z) i.adoptedStyleSheets = e.map((t) => t instanceof CSSStyleSheet ? t : t.styleSheet);
  else for (const t of e) {
    const s = document.createElement("style"), r = H.litNonce;
    r !== void 0 && s.setAttribute("nonce", r), s.textContent = t.cssText, i.appendChild(s);
  }
}, Q = Z ? (i) => i : (i) => i instanceof CSSStyleSheet ? ((e) => {
  let t = "";
  for (const s of e.cssRules) t += s.cssText;
  return fe(t);
})(i) : i;
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const { is: me, defineProperty: ye, getOwnPropertyDescriptor: ve, getOwnPropertyNames: be, getOwnPropertySymbols: Ae, getPrototypeOf: xe } = Object, y = globalThis, Y = y.trustedTypes, we = Y ? Y.emptyScript : "", I = y.reactiveElementPolyfillSupport, P = (i, e) => i, D = { toAttribute(i, e) {
  switch (e) {
    case Boolean:
      i = i ? we : null;
      break;
    case Object:
    case Array:
      i = i == null ? i : JSON.stringify(i);
  }
  return i;
}, fromAttribute(i, e) {
  let t = i;
  switch (e) {
    case Boolean:
      t = i !== null;
      break;
    case Number:
      t = i === null ? null : Number(i);
      break;
    case Object:
    case Array:
      try {
        t = JSON.parse(i);
      } catch {
        t = null;
      }
  }
  return t;
} }, K = (i, e) => !me(i, e), ee = { attribute: !0, type: String, converter: D, reflect: !1, useDefault: !1, hasChanged: K };
Symbol.metadata ?? (Symbol.metadata = Symbol("metadata")), y.litPropertyMetadata ?? (y.litPropertyMetadata = /* @__PURE__ */ new WeakMap());
let S = class extends HTMLElement {
  static addInitializer(e) {
    this._$Ei(), (this.l ?? (this.l = [])).push(e);
  }
  static get observedAttributes() {
    return this.finalize(), this._$Eh && [...this._$Eh.keys()];
  }
  static createProperty(e, t = ee) {
    if (t.state && (t.attribute = !1), this._$Ei(), this.prototype.hasOwnProperty(e) && ((t = Object.create(t)).wrapped = !0), this.elementProperties.set(e, t), !t.noAccessor) {
      const s = Symbol(), r = this.getPropertyDescriptor(e, s, t);
      r !== void 0 && ye(this.prototype, e, r);
    }
  }
  static getPropertyDescriptor(e, t, s) {
    const { get: r, set: o } = ve(this.prototype, e) ?? { get() {
      return this[t];
    }, set(n) {
      this[t] = n;
    } };
    return { get: r, set(n) {
      const a = r == null ? void 0 : r.call(this);
      o == null || o.call(this, n), this.requestUpdate(e, a, s);
    }, configurable: !0, enumerable: !0 };
  }
  static getPropertyOptions(e) {
    return this.elementProperties.get(e) ?? ee;
  }
  static _$Ei() {
    if (this.hasOwnProperty(P("elementProperties"))) return;
    const e = xe(this);
    e.finalize(), e.l !== void 0 && (this.l = [...e.l]), this.elementProperties = new Map(e.elementProperties);
  }
  static finalize() {
    if (this.hasOwnProperty(P("finalized"))) return;
    if (this.finalized = !0, this._$Ei(), this.hasOwnProperty(P("properties"))) {
      const t = this.properties, s = [...be(t), ...Ae(t)];
      for (const r of s) this.createProperty(r, t[r]);
    }
    const e = this[Symbol.metadata];
    if (e !== null) {
      const t = litPropertyMetadata.get(e);
      if (t !== void 0) for (const [s, r] of t) this.elementProperties.set(s, r);
    }
    this._$Eh = /* @__PURE__ */ new Map();
    for (const [t, s] of this.elementProperties) {
      const r = this._$Eu(t, s);
      r !== void 0 && this._$Eh.set(r, t);
    }
    this.elementStyles = this.finalizeStyles(this.styles);
  }
  static finalizeStyles(e) {
    const t = [];
    if (Array.isArray(e)) {
      const s = new Set(e.flat(1 / 0).reverse());
      for (const r of s) t.unshift(Q(r));
    } else e !== void 0 && t.push(Q(e));
    return t;
  }
  static _$Eu(e, t) {
    const s = t.attribute;
    return s === !1 ? void 0 : typeof s == "string" ? s : typeof e == "string" ? e.toLowerCase() : void 0;
  }
  constructor() {
    super(), this._$Ep = void 0, this.isUpdatePending = !1, this.hasUpdated = !1, this._$Em = null, this._$Ev();
  }
  _$Ev() {
    var e;
    this._$ES = new Promise((t) => this.enableUpdating = t), this._$AL = /* @__PURE__ */ new Map(), this._$E_(), this.requestUpdate(), (e = this.constructor.l) == null || e.forEach((t) => t(this));
  }
  addController(e) {
    var t;
    (this._$EO ?? (this._$EO = /* @__PURE__ */ new Set())).add(e), this.renderRoot !== void 0 && this.isConnected && ((t = e.hostConnected) == null || t.call(e));
  }
  removeController(e) {
    var t;
    (t = this._$EO) == null || t.delete(e);
  }
  _$E_() {
    const e = /* @__PURE__ */ new Map(), t = this.constructor.elementProperties;
    for (const s of t.keys()) this.hasOwnProperty(s) && (e.set(s, this[s]), delete this[s]);
    e.size > 0 && (this._$Ep = e);
  }
  createRenderRoot() {
    const e = this.shadowRoot ?? this.attachShadow(this.constructor.shadowRootOptions);
    return $e(e, this.constructor.elementStyles), e;
  }
  connectedCallback() {
    var e;
    this.renderRoot ?? (this.renderRoot = this.createRenderRoot()), this.enableUpdating(!0), (e = this._$EO) == null || e.forEach((t) => {
      var s;
      return (s = t.hostConnected) == null ? void 0 : s.call(t);
    });
  }
  enableUpdating(e) {
  }
  disconnectedCallback() {
    var e;
    (e = this._$EO) == null || e.forEach((t) => {
      var s;
      return (s = t.hostDisconnected) == null ? void 0 : s.call(t);
    });
  }
  attributeChangedCallback(e, t, s) {
    this._$AK(e, s);
  }
  _$ET(e, t) {
    var o;
    const s = this.constructor.elementProperties.get(e), r = this.constructor._$Eu(e, s);
    if (r !== void 0 && s.reflect === !0) {
      const n = (((o = s.converter) == null ? void 0 : o.toAttribute) !== void 0 ? s.converter : D).toAttribute(t, s.type);
      this._$Em = e, n == null ? this.removeAttribute(r) : this.setAttribute(r, n), this._$Em = null;
    }
  }
  _$AK(e, t) {
    var o, n;
    const s = this.constructor, r = s._$Eh.get(e);
    if (r !== void 0 && this._$Em !== r) {
      const a = s.getPropertyOptions(r), l = typeof a.converter == "function" ? { fromAttribute: a.converter } : ((o = a.converter) == null ? void 0 : o.fromAttribute) !== void 0 ? a.converter : D;
      this._$Em = r;
      const h = l.fromAttribute(t, a.type);
      this[r] = h ?? ((n = this._$Ej) == null ? void 0 : n.get(r)) ?? h, this._$Em = null;
    }
  }
  requestUpdate(e, t, s, r = !1, o) {
    var n;
    if (e !== void 0) {
      const a = this.constructor;
      if (r === !1 && (o = this[e]), s ?? (s = a.getPropertyOptions(e)), !((s.hasChanged ?? K)(o, t) || s.useDefault && s.reflect && o === ((n = this._$Ej) == null ? void 0 : n.get(e)) && !this.hasAttribute(a._$Eu(e, s)))) return;
      this.C(e, t, s);
    }
    this.isUpdatePending === !1 && (this._$ES = this._$EP());
  }
  C(e, t, { useDefault: s, reflect: r, wrapped: o }, n) {
    s && !(this._$Ej ?? (this._$Ej = /* @__PURE__ */ new Map())).has(e) && (this._$Ej.set(e, n ?? t ?? this[e]), o !== !0 || n !== void 0) || (this._$AL.has(e) || (this.hasUpdated || s || (t = void 0), this._$AL.set(e, t)), r === !0 && this._$Em !== e && (this._$Eq ?? (this._$Eq = /* @__PURE__ */ new Set())).add(e));
  }
  async _$EP() {
    this.isUpdatePending = !0;
    try {
      await this._$ES;
    } catch (t) {
      Promise.reject(t);
    }
    const e = this.scheduleUpdate();
    return e != null && await e, !this.isUpdatePending;
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
        const { wrapped: a } = n, l = this[o];
        a !== !0 || this._$AL.has(o) || l === void 0 || this.C(o, void 0, n, l);
      }
    }
    let e = !1;
    const t = this._$AL;
    try {
      e = this.shouldUpdate(t), e ? (this.willUpdate(t), (s = this._$EO) == null || s.forEach((r) => {
        var o;
        return (o = r.hostUpdate) == null ? void 0 : o.call(r);
      }), this.update(t)) : this._$EM();
    } catch (r) {
      throw e = !1, this._$EM(), r;
    }
    e && this._$AE(t);
  }
  willUpdate(e) {
  }
  _$AE(e) {
    var t;
    (t = this._$EO) == null || t.forEach((s) => {
      var r;
      return (r = s.hostUpdated) == null ? void 0 : r.call(s);
    }), this.hasUpdated || (this.hasUpdated = !0, this.firstUpdated(e)), this.updated(e);
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
  shouldUpdate(e) {
    return !0;
  }
  update(e) {
    this._$Eq && (this._$Eq = this._$Eq.forEach((t) => this._$ET(t, this[t]))), this._$EM();
  }
  updated(e) {
  }
  firstUpdated(e) {
  }
};
S.elementStyles = [], S.shadowRootOptions = { mode: "open" }, S[P("elementProperties")] = /* @__PURE__ */ new Map(), S[P("finalized")] = /* @__PURE__ */ new Map(), I == null || I({ ReactiveElement: S }), (y.reactiveElementVersions ?? (y.reactiveElementVersions = [])).push("2.1.2");
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const k = globalThis, te = (i) => i, R = k.trustedTypes, se = R ? R.createPolicy("lit-html", { createHTML: (i) => i }) : void 0, ce = "$lit$", m = `lit$${Math.random().toFixed(9).slice(2)}$`, he = "?" + m, Ee = `<${he}>`, w = document, O = () => w.createComment(""), T = (i) => i === null || typeof i != "object" && typeof i != "function", G = Array.isArray, Se = (i) => G(i) || typeof (i == null ? void 0 : i[Symbol.iterator]) == "function", B = `[ 	
\f\r]`, M = /<(?:(!--|\/[^a-zA-Z])|(\/?[a-zA-Z][^>\s]*)|(\/?$))/g, ie = /-->/g, re = />/g, b = RegExp(`>|${B}(?:([^\\s"'>=/]+)(${B}*=${B}*(?:[^ 	
\f\r"'\`<>=]|("|')|))|$)`, "g"), oe = /'/g, ne = /"/g, pe = /^(?:script|style|textarea|title)$/i, Ce = (i) => (e, ...t) => ({ _$litType$: i, strings: e, values: t }), g = Ce(1), E = Symbol.for("lit-noChange"), d = Symbol.for("lit-nothing"), ae = /* @__PURE__ */ new WeakMap(), A = w.createTreeWalker(w, 129);
function ue(i, e) {
  if (!G(i) || !i.hasOwnProperty("raw")) throw Error("invalid template strings array");
  return se !== void 0 ? se.createHTML(e) : e;
}
const Me = (i, e) => {
  const t = i.length - 1, s = [];
  let r, o = e === 2 ? "<svg>" : e === 3 ? "<math>" : "", n = M;
  for (let a = 0; a < t; a++) {
    const l = i[a];
    let h, p, c = -1, _ = 0;
    for (; _ < l.length && (n.lastIndex = _, p = n.exec(l), p !== null); ) _ = n.lastIndex, n === M ? p[1] === "!--" ? n = ie : p[1] !== void 0 ? n = re : p[2] !== void 0 ? (pe.test(p[2]) && (r = RegExp("</" + p[2], "g")), n = b) : p[3] !== void 0 && (n = b) : n === b ? p[0] === ">" ? (n = r ?? M, c = -1) : p[1] === void 0 ? c = -2 : (c = n.lastIndex - p[2].length, h = p[1], n = p[3] === void 0 ? b : p[3] === '"' ? ne : oe) : n === ne || n === oe ? n = b : n === ie || n === re ? n = M : (n = b, r = void 0);
    const $ = n === b && i[a + 1].startsWith("/>") ? " " : "";
    o += n === M ? l + Ee : c >= 0 ? (s.push(h), l.slice(0, c) + ce + l.slice(c) + m + $) : l + m + (c === -2 ? a : $);
  }
  return [ue(i, o + (i[t] || "<?>") + (e === 2 ? "</svg>" : e === 3 ? "</math>" : "")), s];
};
class z {
  constructor({ strings: e, _$litType$: t }, s) {
    let r;
    this.parts = [];
    let o = 0, n = 0;
    const a = e.length - 1, l = this.parts, [h, p] = Me(e, t);
    if (this.el = z.createElement(h, s), A.currentNode = this.el.content, t === 2 || t === 3) {
      const c = this.el.content.firstChild;
      c.replaceWith(...c.childNodes);
    }
    for (; (r = A.nextNode()) !== null && l.length < a; ) {
      if (r.nodeType === 1) {
        if (r.hasAttributes()) for (const c of r.getAttributeNames()) if (c.endsWith(ce)) {
          const _ = p[n++], $ = r.getAttribute(c).split(m), L = /([.?@])?(.*)/.exec(_);
          l.push({ type: 1, index: o, name: L[2], strings: $, ctor: L[1] === "." ? ke : L[1] === "?" ? Ue : L[1] === "@" ? Oe : j }), r.removeAttribute(c);
        } else c.startsWith(m) && (l.push({ type: 6, index: o }), r.removeAttribute(c));
        if (pe.test(r.tagName)) {
          const c = r.textContent.split(m), _ = c.length - 1;
          if (_ > 0) {
            r.textContent = R ? R.emptyScript : "";
            for (let $ = 0; $ < _; $++) r.append(c[$], O()), A.nextNode(), l.push({ type: 2, index: ++o });
            r.append(c[_], O());
          }
        }
      } else if (r.nodeType === 8) if (r.data === he) l.push({ type: 2, index: o });
      else {
        let c = -1;
        for (; (c = r.data.indexOf(m, c + 1)) !== -1; ) l.push({ type: 7, index: o }), c += m.length - 1;
      }
      o++;
    }
  }
  static createElement(e, t) {
    const s = w.createElement("template");
    return s.innerHTML = e, s;
  }
}
function C(i, e, t = i, s) {
  var n, a;
  if (e === E) return e;
  let r = s !== void 0 ? (n = t._$Co) == null ? void 0 : n[s] : t._$Cl;
  const o = T(e) ? void 0 : e._$litDirective$;
  return (r == null ? void 0 : r.constructor) !== o && ((a = r == null ? void 0 : r._$AO) == null || a.call(r, !1), o === void 0 ? r = void 0 : (r = new o(i), r._$AT(i, t, s)), s !== void 0 ? (t._$Co ?? (t._$Co = []))[s] = r : t._$Cl = r), r !== void 0 && (e = C(i, r._$AS(i, e.values), r, s)), e;
}
class Pe {
  constructor(e, t) {
    this._$AV = [], this._$AN = void 0, this._$AD = e, this._$AM = t;
  }
  get parentNode() {
    return this._$AM.parentNode;
  }
  get _$AU() {
    return this._$AM._$AU;
  }
  u(e) {
    const { el: { content: t }, parts: s } = this._$AD, r = ((e == null ? void 0 : e.creationScope) ?? w).importNode(t, !0);
    A.currentNode = r;
    let o = A.nextNode(), n = 0, a = 0, l = s[0];
    for (; l !== void 0; ) {
      if (n === l.index) {
        let h;
        l.type === 2 ? h = new N(o, o.nextSibling, this, e) : l.type === 1 ? h = new l.ctor(o, l.name, l.strings, this, e) : l.type === 6 && (h = new Te(o, this, e)), this._$AV.push(h), l = s[++a];
      }
      n !== (l == null ? void 0 : l.index) && (o = A.nextNode(), n++);
    }
    return A.currentNode = w, r;
  }
  p(e) {
    let t = 0;
    for (const s of this._$AV) s !== void 0 && (s.strings !== void 0 ? (s._$AI(e, s, t), t += s.strings.length - 2) : s._$AI(e[t])), t++;
  }
}
class N {
  get _$AU() {
    var e;
    return ((e = this._$AM) == null ? void 0 : e._$AU) ?? this._$Cv;
  }
  constructor(e, t, s, r) {
    this.type = 2, this._$AH = d, this._$AN = void 0, this._$AA = e, this._$AB = t, this._$AM = s, this.options = r, this._$Cv = (r == null ? void 0 : r.isConnected) ?? !0;
  }
  get parentNode() {
    let e = this._$AA.parentNode;
    const t = this._$AM;
    return t !== void 0 && (e == null ? void 0 : e.nodeType) === 11 && (e = t.parentNode), e;
  }
  get startNode() {
    return this._$AA;
  }
  get endNode() {
    return this._$AB;
  }
  _$AI(e, t = this) {
    e = C(this, e, t), T(e) ? e === d || e == null || e === "" ? (this._$AH !== d && this._$AR(), this._$AH = d) : e !== this._$AH && e !== E && this._(e) : e._$litType$ !== void 0 ? this.$(e) : e.nodeType !== void 0 ? this.T(e) : Se(e) ? this.k(e) : this._(e);
  }
  O(e) {
    return this._$AA.parentNode.insertBefore(e, this._$AB);
  }
  T(e) {
    this._$AH !== e && (this._$AR(), this._$AH = this.O(e));
  }
  _(e) {
    this._$AH !== d && T(this._$AH) ? this._$AA.nextSibling.data = e : this.T(w.createTextNode(e)), this._$AH = e;
  }
  $(e) {
    var o;
    const { values: t, _$litType$: s } = e, r = typeof s == "number" ? this._$AC(e) : (s.el === void 0 && (s.el = z.createElement(ue(s.h, s.h[0]), this.options)), s);
    if (((o = this._$AH) == null ? void 0 : o._$AD) === r) this._$AH.p(t);
    else {
      const n = new Pe(r, this), a = n.u(this.options);
      n.p(t), this.T(a), this._$AH = n;
    }
  }
  _$AC(e) {
    let t = ae.get(e.strings);
    return t === void 0 && ae.set(e.strings, t = new z(e)), t;
  }
  k(e) {
    G(this._$AH) || (this._$AH = [], this._$AR());
    const t = this._$AH;
    let s, r = 0;
    for (const o of e) r === t.length ? t.push(s = new N(this.O(O()), this.O(O()), this, this.options)) : s = t[r], s._$AI(o), r++;
    r < t.length && (this._$AR(s && s._$AB.nextSibling, r), t.length = r);
  }
  _$AR(e = this._$AA.nextSibling, t) {
    var s;
    for ((s = this._$AP) == null ? void 0 : s.call(this, !1, !0, t); e !== this._$AB; ) {
      const r = te(e).nextSibling;
      te(e).remove(), e = r;
    }
  }
  setConnected(e) {
    var t;
    this._$AM === void 0 && (this._$Cv = e, (t = this._$AP) == null || t.call(this, e));
  }
}
class j {
  get tagName() {
    return this.element.tagName;
  }
  get _$AU() {
    return this._$AM._$AU;
  }
  constructor(e, t, s, r, o) {
    this.type = 1, this._$AH = d, this._$AN = void 0, this.element = e, this.name = t, this._$AM = r, this.options = o, s.length > 2 || s[0] !== "" || s[1] !== "" ? (this._$AH = Array(s.length - 1).fill(new String()), this.strings = s) : this._$AH = d;
  }
  _$AI(e, t = this, s, r) {
    const o = this.strings;
    let n = !1;
    if (o === void 0) e = C(this, e, t, 0), n = !T(e) || e !== this._$AH && e !== E, n && (this._$AH = e);
    else {
      const a = e;
      let l, h;
      for (e = o[0], l = 0; l < o.length - 1; l++) h = C(this, a[s + l], t, l), h === E && (h = this._$AH[l]), n || (n = !T(h) || h !== this._$AH[l]), h === d ? e = d : e !== d && (e += (h ?? "") + o[l + 1]), this._$AH[l] = h;
    }
    n && !r && this.j(e);
  }
  j(e) {
    e === d ? this.element.removeAttribute(this.name) : this.element.setAttribute(this.name, e ?? "");
  }
}
class ke extends j {
  constructor() {
    super(...arguments), this.type = 3;
  }
  j(e) {
    this.element[this.name] = e === d ? void 0 : e;
  }
}
class Ue extends j {
  constructor() {
    super(...arguments), this.type = 4;
  }
  j(e) {
    this.element.toggleAttribute(this.name, !!e && e !== d);
  }
}
class Oe extends j {
  constructor(e, t, s, r, o) {
    super(e, t, s, r, o), this.type = 5;
  }
  _$AI(e, t = this) {
    if ((e = C(this, e, t, 0) ?? d) === E) return;
    const s = this._$AH, r = e === d && s !== d || e.capture !== s.capture || e.once !== s.once || e.passive !== s.passive, o = e !== d && (s === d || r);
    r && this.element.removeEventListener(this.name, this, s), o && this.element.addEventListener(this.name, this, e), this._$AH = e;
  }
  handleEvent(e) {
    var t;
    typeof this._$AH == "function" ? this._$AH.call(((t = this.options) == null ? void 0 : t.host) ?? this.element, e) : this._$AH.handleEvent(e);
  }
}
class Te {
  constructor(e, t, s) {
    this.element = e, this.type = 6, this._$AN = void 0, this._$AM = t, this.options = s;
  }
  get _$AU() {
    return this._$AM._$AU;
  }
  _$AI(e) {
    C(this, e);
  }
}
const q = k.litHtmlPolyfillSupport;
q == null || q(z, N), (k.litHtmlVersions ?? (k.litHtmlVersions = [])).push("3.3.2");
const ze = (i, e, t) => {
  const s = (t == null ? void 0 : t.renderBefore) ?? e;
  let r = s._$litPart$;
  if (r === void 0) {
    const o = (t == null ? void 0 : t.renderBefore) ?? null;
    s._$litPart$ = r = new N(e.insertBefore(O(), o), o, void 0, t ?? {});
  }
  return r._$AI(i), r;
};
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const x = globalThis;
let U = class extends S {
  constructor() {
    super(...arguments), this.renderOptions = { host: this }, this._$Do = void 0;
  }
  createRenderRoot() {
    var t;
    const e = super.createRenderRoot();
    return (t = this.renderOptions).renderBefore ?? (t.renderBefore = e.firstChild), e;
  }
  update(e) {
    const t = this.render();
    this.hasUpdated || (this.renderOptions.isConnected = this.isConnected), super.update(e), this._$Do = ze(t, this.renderRoot, this.renderOptions);
  }
  connectedCallback() {
    var e;
    super.connectedCallback(), (e = this._$Do) == null || e.setConnected(!0);
  }
  disconnectedCallback() {
    var e;
    super.disconnectedCallback(), (e = this._$Do) == null || e.setConnected(!1);
  }
  render() {
    return E;
  }
};
var le;
U._$litElement$ = !0, U.finalized = !0, (le = x.litElementHydrateSupport) == null || le.call(x, { LitElement: U });
const W = x.litElementPolyfillSupport;
W == null || W({ LitElement: U });
(x.litElementVersions ?? (x.litElementVersions = [])).push("4.2.2");
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const Ne = (i) => (e, t) => {
  t !== void 0 ? t.addInitializer(() => {
    customElements.define(i, e);
  }) : customElements.define(i, e);
};
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const Le = { attribute: !0, type: String, converter: D, reflect: !1, hasChanged: K }, He = (i = Le, e, t) => {
  const { kind: s, metadata: r } = t;
  let o = globalThis.litPropertyMetadata.get(r);
  if (o === void 0 && globalThis.litPropertyMetadata.set(r, o = /* @__PURE__ */ new Map()), s === "setter" && ((i = Object.create(i)).wrapped = !0), o.set(t.name, i), s === "accessor") {
    const { name: n } = t;
    return { set(a) {
      const l = e.get.call(this);
      e.set.call(this, a), this.requestUpdate(n, l, i, !0, a);
    }, init(a) {
      return a !== void 0 && this.C(n, void 0, i, a), a;
    } };
  }
  if (s === "setter") {
    const { name: n } = t;
    return function(a) {
      const l = this[n];
      e.call(this, a), this.requestUpdate(n, l, i, !0, a);
    };
  }
  throw Error("Unsupported decorator location: " + s);
};
function ge(i) {
  return (e, t) => typeof t == "object" ? He(i, e, t) : ((s, r, o) => {
    const n = r.hasOwnProperty(o);
    return r.constructor.createProperty(o, s), n ? Object.getOwnPropertyDescriptor(r, o) : void 0;
  })(i, e, t);
}
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
function v(i) {
  return ge({ ...i, state: !0, attribute: !1 });
}
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const De = (i, e, t) => (t.configurable = !0, t.enumerable = !0, Reflect.decorate && typeof e != "object" && Object.defineProperty(i, e, t), t);
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
function Re(i, e) {
  return (t, s, r) => {
    const o = (n) => {
      var a;
      return ((a = n.renderRoot) == null ? void 0 : a.querySelector(i)) ?? null;
    };
    return De(t, s, { get() {
      return o(this);
    } });
  };
}
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const je = { CHILD: 2 }, Ie = (i) => (...e) => ({ _$litDirective$: i, values: e });
class Be {
  constructor(e) {
  }
  get _$AU() {
    return this._$AM._$AU;
  }
  _$AT(e, t, s) {
    this._$Ct = e, this._$AM = t, this._$Ci = s;
  }
  _$AS(e, t) {
    return this.update(e, t);
  }
  update(e, t) {
    return this.render(...t);
  }
}
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
class F extends Be {
  constructor(e) {
    if (super(e), this.it = d, e.type !== je.CHILD) throw Error(this.constructor.directiveName + "() can only be used in child bindings");
  }
  render(e) {
    if (e === d || e == null) return this._t = void 0, this.it = e;
    if (e === E) return e;
    if (typeof e != "string") throw Error(this.constructor.directiveName + "() called with a non-string value");
    if (e === this.it) return this._t;
    this.it = e;
    const t = [e];
    return t.raw = t, this._t = { _$litType$: this.constructor.resultType, strings: t, values: [] };
  }
}
F.directiveName = "unsafeHTML", F.resultType = 1;
const qe = Ie(F), We = /* @__PURE__ */ new Set([
  "p",
  "br",
  "b",
  "strong",
  "i",
  "em",
  "u",
  "s",
  "a",
  "ul",
  "ol",
  "li",
  "span",
  "div"
]), Fe = {
  a: /* @__PURE__ */ new Set(["href", "target"])
};
function V(i, e) {
  if (i.nodeType === Node.TEXT_NODE) {
    e.appendChild(i.cloneNode());
    return;
  }
  if (i.nodeType !== Node.ELEMENT_NODE) return;
  const t = i, s = t.tagName.toLowerCase();
  if (!We.has(s)) {
    for (const a of t.childNodes)
      V(a, e);
    return;
  }
  const r = document.createElement(s), o = Fe[s];
  if (o) {
    for (const a of t.attributes)
      if (o.has(a.name)) {
        const l = a.value;
        if (a.name === "href" && /^\s*javascript:/i.test(l)) continue;
        r.setAttribute(a.name, l);
      }
  }
  s === "a" && (r.setAttribute("target", "_blank"), r.setAttribute("rel", "noopener noreferrer"));
  const n = document.createDocumentFragment();
  for (const a of t.childNodes)
    V(a, n);
  r.appendChild(n), e.appendChild(r);
}
function Ve(i) {
  const t = new DOMParser().parseFromString(i, "text/html"), s = document.createDocumentFragment();
  for (const o of t.body.childNodes)
    V(o, s);
  const r = document.createElement("div");
  return r.appendChild(s), r.innerHTML;
}
var Ze = Object.defineProperty, Je = Object.getOwnPropertyDescriptor, f = (i, e, t, s) => {
  for (var r = s > 1 ? void 0 : s ? Je(e, t) : e, o = i.length - 1, n; o >= 0; o--)
    (n = i[o]) && (r = (s ? n(e, t, r) : n(r)) || r);
  return s && r && Ze(e, t, r), r;
};
let u = class extends U {
  constructor() {
    super(...arguments), this._onlyUnread = !1, this._selectedMsg = null, this._dialogContent = null, this._dialogLoading = !1, this._loadedMessages = [], this._hasMore = !0, this._isLoadingMore = !1;
  }
  static getStubConfig() {
    return { entity: "", entry_id: "", count: 10 };
  }
  setConfig(i) {
    if (!i.entity) throw new Error("entity is required");
    if (!i.entry_id) throw new Error("entry_id is required");
    this._config = i;
  }
  getCardSize() {
    return 4;
  }
  connectedCallback() {
    super.connectedCallback(), this._observer = new IntersectionObserver(
      ([i]) => {
        i.isIntersecting && !this._isLoadingMore && this._hasMore && this._loadMore();
      },
      { rootMargin: "120px" }
    );
  }
  disconnectedCallback() {
    var i;
    super.disconnectedCallback(), (i = this._observer) == null || i.disconnect(), this._observer = void 0, this._sentinelEl = void 0;
  }
  updated(i) {
    var t, s, r, o;
    if (super.updated(i), i.has("hass") && this._loadedMessages.length === 0) {
      const n = this._messagesFromSensor;
      n.length > 0 && (this._loadedMessages = [...n], this._hasMore = n.length >= (((t = this._config) == null ? void 0 : t.count) ?? 10));
    }
    const e = (s = this.shadowRoot) == null ? void 0 : s.querySelector(".sentinel");
    e && e !== this._sentinelEl && (this._sentinelEl && ((r = this._observer) == null || r.unobserve(this._sentinelEl)), this._sentinelEl = e, (o = this._observer) == null || o.observe(e));
  }
  get _messagesFromSensor() {
    if (!this.hass || !this._config) return [];
    const i = this.hass.states[this._config.entity];
    return i ? i.attributes.messages ?? [] : [];
  }
  get _displayedMessages() {
    var i;
    return this._onlyUnread || (i = this._config) != null && i.only_unread ? this._loadedMessages.filter((e) => e.unread && !e.notification_dismissed) : this._loadedMessages;
  }
  async _loadMore() {
    if (!this.hass || !this._config || this._isLoadingMore) return;
    this._isLoadingMore = !0;
    const i = this._config.count ?? 10, e = this._loadedMessages.length;
    try {
      const t = await this.hass.callService(
        "librus_apix",
        "list_messages",
        { entry: this._config.entry_id, offset: e, count: i },
        void 0,
        !1,
        !0
      ), s = (t == null ? void 0 : t.response) ?? t, r = s.messages ?? [];
      this._hasMore = s.has_more === !0;
      const o = new Set(this._loadedMessages.map((a) => a.href)), n = r.filter((a) => !o.has(a.href));
      this._loadedMessages = [...this._loadedMessages, ...n];
    } catch {
    } finally {
      this._isLoadingMore = !1;
    }
  }
  async _openDialog(i) {
    var e;
    if (!(!this.hass || !this._config)) {
      this._selectedMsg = i, this._dialogContent = null, this._dialogLoading = !0, (e = this._dialog) == null || e.showModal();
      try {
        const t = await this.hass.callService(
          "librus_apix",
          "fetch_message_content",
          { entry: this._config.entry_id, message_href: i.href },
          void 0,
          !0,
          !0
        ), s = (t == null ? void 0 : t.response) ?? t;
        this._dialogContent = s;
      } catch {
        this._dialogContent = {
          author: "",
          title: "",
          date: "",
          content: "<em>Błąd pobierania treści.</em>"
        };
      } finally {
        this._dialogLoading = !1;
      }
    }
  }
  async _dismissFromDialog() {
    var e;
    if (!this.hass || !this._config || !this._selectedMsg) return;
    const i = this._selectedMsg.href;
    await this.hass.callService("librus_apix", "dismiss_message_notification", {
      entry: this._config.entry_id,
      message_href: i
    }), this._loadedMessages = this._loadedMessages.map(
      (t) => t.href === i ? { ...t, notification_dismissed: !0 } : t
    ), (e = this._dialog) == null || e.close();
  }
  render() {
    if (!this._config) return d;
    const i = this._displayedMessages, e = this._config.title ?? "Wiadomości Librus", t = this._onlyUnread || this._config.only_unread;
    return g`
      <ha-card>
        <div class="card-header">
          <span class="card-title">${e}</span>
          <label class="filter-toggle">
            <input
              type="checkbox"
              .checked=${this._onlyUnread}
              @change=${(s) => {
      this._onlyUnread = s.target.checked;
    }}
            />
            tylko nieprzeczytane
          </label>
        </div>
        <div class="message-list">
          ${i.length === 0 && !this._isLoadingMore ? g`<div class="empty">
                ${t ? "Brak nieprzeczytanych wiadomości" : "Brak wiadomości"}
              </div>` : i.map((s) => this._renderRow(s))}
          ${this._hasMore ? g`<div class="sentinel"></div>` : d}
          ${this._isLoadingMore ? g`<div class="loading-more">Ładowanie…</div>` : d}
        </div>
      </ha-card>
      ${this._renderDialog()}
    `;
  }
  _renderRow(i) {
    return g`
      <div
        class="message-item ${i.unread && !i.notification_dismissed ? "unread" : ""}"
        role="button"
        tabindex="0"
        @click=${() => this._openDialog(i)}
        @keydown=${(e) => e.key === "Enter" && this._openDialog(i)}
      >
        <div class="message-meta">
          <div class="message-sender">${i.sender}</div>
          <div class="message-title">
            ${i.has_attachment ? g`<ha-icon icon="mdi:paperclip" class="attach-icon"></ha-icon>` : d}
            ${i.title}
          </div>
        </div>
        <span class="message-date">${i.date}</span>
      </div>
    `;
  }
  _renderDialog() {
    const i = this._selectedMsg;
    return g`
      <dialog
        @close=${() => {
      this._selectedMsg = null, this._dialogContent = null;
    }}
      >
        <div class="dlg-header">
          <div class="dlg-meta">
            <div class="dlg-sender">${i == null ? void 0 : i.sender}</div>
            <div class="dlg-title">${i == null ? void 0 : i.title}</div>
            <div class="dlg-date">${i == null ? void 0 : i.date}</div>
          </div>
          <ha-icon-button
            .label=${"Zamknij"}
            .path=${"M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"}
            @click=${() => {
      var e;
      return (e = this._dialog) == null ? void 0 : e.close();
    }}
          ></ha-icon-button>
        </div>
        <div class="dlg-body">
          ${this._dialogLoading ? g`<div class="dlg-loading">Ładowanie…</div>` : this._dialogContent ? g`<div class="dlg-content">
                  ${qe(Ve(this._dialogContent.content))}
                </div>` : d}
        </div>
        <div class="dlg-footer">
          ${i != null && i.has_attachment ? g`<span class="attach-note">
                <ha-icon icon="mdi:paperclip"></ha-icon>
                Zawiera załącznik
              </span>` : d}
          <div class="dlg-footer-actions">
            ${i && !i.notification_dismissed ? g`<button class="btn-dismiss" @click=${() => this._dismissFromDialog()}>
                  Usuń powiadomienie
                </button>` : d}
            <button class="btn-close" @click=${() => {
      var e;
      return (e = this._dialog) == null ? void 0 : e.close();
    }}>Zamknij</button>
          </div>
        </div>
      </dialog>
    `;
  }
};
u.styles = _e`
    :host {
      display: block;
    }
    ha-card {
      padding: 0;
    }
    .card-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 12px 16px 8px;
    }
    .card-title {
      font-size: 1.1rem;
      font-weight: 500;
    }
    .filter-toggle {
      display: flex;
      align-items: center;
      gap: 6px;
      font-size: 0.85rem;
      color: var(--secondary-text-color);
      cursor: pointer;
    }
    .message-list {
      padding: 0 8px 8px;
    }
    .message-item {
      border-radius: 8px;
      margin-bottom: 4px;
      padding: 10px 12px;
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      gap: 8px;
      cursor: pointer;
      transition: background 0.15s;
    }
    .message-item:hover {
      background: color-mix(in srgb, var(--primary-color) 6%, transparent);
    }
    .message-item.unread {
      background: color-mix(in srgb, var(--primary-color) 12%, transparent);
    }
    .message-item.unread:hover {
      background: color-mix(in srgb, var(--primary-color) 18%, transparent);
    }
    .message-meta {
      flex: 1;
      min-width: 0;
    }
    .message-sender {
      font-weight: 500;
      font-size: 0.9rem;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
    .message-title {
      font-size: 0.85rem;
      color: var(--secondary-text-color);
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
    .attach-icon {
      --mdi-icon-size: 14px;
      vertical-align: middle;
      color: var(--secondary-text-color);
      margin-right: 2px;
    }
    .message-date {
      font-size: 0.75rem;
      color: var(--disabled-text-color);
      white-space: nowrap;
      flex-shrink: 0;
    }
    .sentinel {
      height: 1px;
    }
    .loading-more {
      text-align: center;
      padding: 8px;
      font-size: 0.85rem;
      color: var(--secondary-text-color);
    }
    .empty {
      text-align: center;
      padding: 16px;
      color: var(--secondary-text-color);
      font-size: 0.9rem;
    }

    /* Dialog — display controlled by browser via [open] attribute */
    dialog {
      max-width: min(700px, 95vw);
      max-height: 85vh;
      border: none;
      border-radius: var(--ha-card-border-radius, 12px);
      box-shadow: 0 4px 24px rgba(0, 0, 0, 0.4);
      background: var(--card-background-color, #fff);
      color: var(--primary-text-color);
      padding: 0;
      overflow: hidden;
    }
    dialog[open] {
      display: flex;
      flex-direction: column;
    }
    dialog::backdrop {
      background: rgba(0, 0, 0, 0.5);
      backdrop-filter: blur(2px);
    }
    .dlg-header {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      padding: 16px 8px 16px 20px;
      border-bottom: 1px solid var(--divider-color);
      flex-shrink: 0;
      gap: 8px;
    }
    .dlg-meta {
      flex: 1;
      min-width: 0;
    }
    .dlg-sender {
      font-weight: 500;
      font-size: 0.85em;
      color: var(--secondary-text-color);
    }
    .dlg-title {
      font-size: 1.05em;
      font-weight: 600;
      margin: 4px 0 2px;
      word-break: break-word;
    }
    .dlg-date {
      font-size: 0.8em;
      color: var(--secondary-text-color);
    }
    .dlg-body {
      flex: 1;
      overflow-y: auto;
      padding: 16px 20px;
    }
    .dlg-loading {
      text-align: center;
      padding: 24px;
      color: var(--secondary-text-color);
    }
    .dlg-content {
      line-height: 1.6;
      font-size: 0.95em;
    }
    .dlg-content p {
      margin: 0 0 0.8em;
    }
    .dlg-content a {
      color: var(--primary-color);
    }
    .dlg-footer {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 12px 20px;
      border-top: 1px solid var(--divider-color);
      flex-shrink: 0;
      gap: 8px;
      flex-wrap: wrap;
    }
    .attach-note {
      display: flex;
      align-items: center;
      gap: 4px;
      color: var(--secondary-text-color);
      font-size: 0.85em;
    }
    .dlg-footer-actions {
      display: flex;
      gap: 8px;
      margin-left: auto;
    }
    .btn-dismiss {
      background: var(--error-color);
      color: white;
      border: none;
      padding: 8px 16px;
      border-radius: 4px;
      cursor: pointer;
      font-size: 0.9em;
    }
    .btn-close {
      background: var(--secondary-background-color);
      color: var(--primary-text-color);
      border: 1px solid var(--divider-color);
      padding: 8px 16px;
      border-radius: 4px;
      cursor: pointer;
      font-size: 0.9em;
    }
    ha-icon-button {
      --mdc-icon-button-size: 32px;
      flex-shrink: 0;
    }
  `;
f([
  ge({ attribute: !1 })
], u.prototype, "hass", 2);
f([
  v()
], u.prototype, "_config", 2);
f([
  v()
], u.prototype, "_onlyUnread", 2);
f([
  v()
], u.prototype, "_selectedMsg", 2);
f([
  v()
], u.prototype, "_dialogContent", 2);
f([
  v()
], u.prototype, "_dialogLoading", 2);
f([
  Re("dialog")
], u.prototype, "_dialog", 2);
f([
  v()
], u.prototype, "_loadedMessages", 2);
f([
  v()
], u.prototype, "_hasMore", 2);
f([
  v()
], u.prototype, "_isLoadingMore", 2);
u = f([
  Ne("librus-messages-card")
], u);
window.customCards ?? (window.customCards = []);
window.customCards.push({
  type: "librus-messages-card",
  name: "Librus — Wiadomości",
  description: "Wiadomości szkolne z podglądem treści i zarządzaniem powiadomieniami."
});
export {
  u as LibrusMessagesCard
};
