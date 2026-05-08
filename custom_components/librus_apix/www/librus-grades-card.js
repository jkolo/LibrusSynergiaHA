/**
 * @license
 * Copyright 2019 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const N = globalThis, q = N.ShadowRoot && (N.ShadyCSS === void 0 || N.ShadyCSS.nativeShadow) && "adoptedStyleSheets" in Document.prototype && "replace" in CSSStyleSheet.prototype, K = Symbol(), F = /* @__PURE__ */ new WeakMap();
let ce = class {
  constructor(e, t, s) {
    if (this._$cssResult$ = !0, s !== K) throw Error("CSSResult is not constructable. Use `unsafeCSS` or `css` instead.");
    this.cssText = e, this.t = t;
  }
  get styleSheet() {
    let e = this.o;
    const t = this.t;
    if (q && e === void 0) {
      const s = t !== void 0 && t.length === 1;
      s && (e = F.get(t)), e === void 0 && ((this.o = e = new CSSStyleSheet()).replaceSync(this.cssText), s && F.set(t, e));
    }
    return e;
  }
  toString() {
    return this.cssText;
  }
};
const $e = (i) => new ce(typeof i == "string" ? i : i + "", void 0, K), _e = (i, ...e) => {
  const t = i.length === 1 ? i[0] : e.reduce((s, r, o) => s + ((n) => {
    if (n._$cssResult$ === !0) return n.cssText;
    if (typeof n == "number") return n;
    throw Error("Value passed to 'css' function must be a 'css' function result: " + n + ". Use 'unsafeCSS' to pass non-literal values, but take care to ensure page security.");
  })(r) + i[o + 1], i[0]);
  return new ce(t, i, K);
}, ye = (i, e) => {
  if (q) i.adoptedStyleSheets = e.map((t) => t instanceof CSSStyleSheet ? t : t.styleSheet);
  else for (const t of e) {
    const s = document.createElement("style"), r = N.litNonce;
    r !== void 0 && s.setAttribute("nonce", r), s.textContent = t.cssText, i.appendChild(s);
  }
}, J = q ? (i) => i : (i) => i instanceof CSSStyleSheet ? ((e) => {
  let t = "";
  for (const s of e.cssRules) t += s.cssText;
  return $e(t);
})(i) : i;
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const { is: me, defineProperty: ve, getOwnPropertyDescriptor: be, getOwnPropertyNames: we, getOwnPropertySymbols: xe, getPrototypeOf: Ae } = Object, _ = globalThis, X = _.trustedTypes, Ee = X ? X.emptyScript : "", L = _.reactiveElementPolyfillSupport, S = (i, e) => i, H = { toAttribute(i, e) {
  switch (e) {
    case Boolean:
      i = i ? Ee : null;
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
} }, V = (i, e) => !me(i, e), Y = { attribute: !0, type: String, converter: H, reflect: !1, useDefault: !1, hasChanged: V };
Symbol.metadata ?? (Symbol.metadata = Symbol("metadata")), _.litPropertyMetadata ?? (_.litPropertyMetadata = /* @__PURE__ */ new WeakMap());
let x = class extends HTMLElement {
  static addInitializer(e) {
    this._$Ei(), (this.l ?? (this.l = [])).push(e);
  }
  static get observedAttributes() {
    return this.finalize(), this._$Eh && [...this._$Eh.keys()];
  }
  static createProperty(e, t = Y) {
    if (t.state && (t.attribute = !1), this._$Ei(), this.prototype.hasOwnProperty(e) && ((t = Object.create(t)).wrapped = !0), this.elementProperties.set(e, t), !t.noAccessor) {
      const s = Symbol(), r = this.getPropertyDescriptor(e, s, t);
      r !== void 0 && ve(this.prototype, e, r);
    }
  }
  static getPropertyDescriptor(e, t, s) {
    const { get: r, set: o } = be(this.prototype, e) ?? { get() {
      return this[t];
    }, set(n) {
      this[t] = n;
    } };
    return { get: r, set(n) {
      const l = r == null ? void 0 : r.call(this);
      o == null || o.call(this, n), this.requestUpdate(e, l, s);
    }, configurable: !0, enumerable: !0 };
  }
  static getPropertyOptions(e) {
    return this.elementProperties.get(e) ?? Y;
  }
  static _$Ei() {
    if (this.hasOwnProperty(S("elementProperties"))) return;
    const e = Ae(this);
    e.finalize(), e.l !== void 0 && (this.l = [...e.l]), this.elementProperties = new Map(e.elementProperties);
  }
  static finalize() {
    if (this.hasOwnProperty(S("finalized"))) return;
    if (this.finalized = !0, this._$Ei(), this.hasOwnProperty(S("properties"))) {
      const t = this.properties, s = [...we(t), ...xe(t)];
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
      for (const r of s) t.unshift(J(r));
    } else e !== void 0 && t.push(J(e));
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
    return ye(e, this.constructor.elementStyles), e;
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
      const n = (((o = s.converter) == null ? void 0 : o.toAttribute) !== void 0 ? s.converter : H).toAttribute(t, s.type);
      this._$Em = e, n == null ? this.removeAttribute(r) : this.setAttribute(r, n), this._$Em = null;
    }
  }
  _$AK(e, t) {
    var o, n;
    const s = this.constructor, r = s._$Eh.get(e);
    if (r !== void 0 && this._$Em !== r) {
      const l = s.getPropertyOptions(r), a = typeof l.converter == "function" ? { fromAttribute: l.converter } : ((o = l.converter) == null ? void 0 : o.fromAttribute) !== void 0 ? l.converter : H;
      this._$Em = r;
      const h = a.fromAttribute(t, l.type);
      this[r] = h ?? ((n = this._$Ej) == null ? void 0 : n.get(r)) ?? h, this._$Em = null;
    }
  }
  requestUpdate(e, t, s, r = !1, o) {
    var n;
    if (e !== void 0) {
      const l = this.constructor;
      if (r === !1 && (o = this[e]), s ?? (s = l.getPropertyOptions(e)), !((s.hasChanged ?? V)(o, t) || s.useDefault && s.reflect && o === ((n = this._$Ej) == null ? void 0 : n.get(e)) && !this.hasAttribute(l._$Eu(e, s)))) return;
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
        const { wrapped: l } = n, a = this[o];
        l !== !0 || this._$AL.has(o) || a === void 0 || this.C(o, void 0, n, a);
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
x.elementStyles = [], x.shadowRootOptions = { mode: "open" }, x[S("elementProperties")] = /* @__PURE__ */ new Map(), x[S("finalized")] = /* @__PURE__ */ new Map(), L == null || L({ ReactiveElement: x }), (_.reactiveElementVersions ?? (_.reactiveElementVersions = [])).push("2.1.2");
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const k = globalThis, Q = (i) => i, D = k.trustedTypes, ee = D ? D.createPolicy("lit-html", { createHTML: (i) => i }) : void 0, he = "$lit$", $ = `lit$${Math.random().toFixed(9).slice(2)}$`, pe = "?" + $, Ce = `<${pe}>`, b = document, O = () => b.createComment(""), U = (i) => i === null || typeof i != "object" && typeof i != "function", G = Array.isArray, Se = (i) => G(i) || typeof (i == null ? void 0 : i[Symbol.iterator]) == "function", I = `[ 	
\f\r]`, C = /<(?:(!--|\/[^a-zA-Z])|(\/?[a-zA-Z][^>\s]*)|(\/?$))/g, te = /-->/g, se = />/g, y = RegExp(`>|${I}(?:([^\\s"'>=/]+)(${I}*=${I}*(?:[^ 	
\f\r"'\`<>=]|("|')|))|$)`, "g"), ie = /'/g, re = /"/g, ue = /^(?:script|style|textarea|title)$/i, ke = (i) => (e, ...t) => ({ _$litType$: i, strings: e, values: t }), u = ke(1), A = Symbol.for("lit-noChange"), d = Symbol.for("lit-nothing"), oe = /* @__PURE__ */ new WeakMap(), m = b.createTreeWalker(b, 129);
function ge(i, e) {
  if (!G(i) || !i.hasOwnProperty("raw")) throw Error("invalid template strings array");
  return ee !== void 0 ? ee.createHTML(e) : e;
}
const Pe = (i, e) => {
  const t = i.length - 1, s = [];
  let r, o = e === 2 ? "<svg>" : e === 3 ? "<math>" : "", n = C;
  for (let l = 0; l < t; l++) {
    const a = i[l];
    let h, p, c = -1, g = 0;
    for (; g < a.length && (n.lastIndex = g, p = n.exec(a), p !== null); ) g = n.lastIndex, n === C ? p[1] === "!--" ? n = te : p[1] !== void 0 ? n = se : p[2] !== void 0 ? (ue.test(p[2]) && (r = RegExp("</" + p[2], "g")), n = y) : p[3] !== void 0 && (n = y) : n === y ? p[0] === ">" ? (n = r ?? C, c = -1) : p[1] === void 0 ? c = -2 : (c = n.lastIndex - p[2].length, h = p[1], n = p[3] === void 0 ? y : p[3] === '"' ? re : ie) : n === re || n === ie ? n = y : n === te || n === se ? n = C : (n = y, r = void 0);
    const f = n === y && i[l + 1].startsWith("/>") ? " " : "";
    o += n === C ? a + Ce : c >= 0 ? (s.push(h), a.slice(0, c) + he + a.slice(c) + $ + f) : a + $ + (c === -2 ? l : f);
  }
  return [ge(i, o + (i[t] || "<?>") + (e === 2 ? "</svg>" : e === 3 ? "</math>" : "")), s];
};
class z {
  constructor({ strings: e, _$litType$: t }, s) {
    let r;
    this.parts = [];
    let o = 0, n = 0;
    const l = e.length - 1, a = this.parts, [h, p] = Pe(e, t);
    if (this.el = z.createElement(h, s), m.currentNode = this.el.content, t === 2 || t === 3) {
      const c = this.el.content.firstChild;
      c.replaceWith(...c.childNodes);
    }
    for (; (r = m.nextNode()) !== null && a.length < l; ) {
      if (r.nodeType === 1) {
        if (r.hasAttributes()) for (const c of r.getAttributeNames()) if (c.endsWith(he)) {
          const g = p[n++], f = r.getAttribute(c).split($), R = /([.?@])?(.*)/.exec(g);
          a.push({ type: 1, index: o, name: R[2], strings: f, ctor: R[1] === "." ? Ue : R[1] === "?" ? ze : R[1] === "@" ? Te : j }), r.removeAttribute(c);
        } else c.startsWith($) && (a.push({ type: 6, index: o }), r.removeAttribute(c));
        if (ue.test(r.tagName)) {
          const c = r.textContent.split($), g = c.length - 1;
          if (g > 0) {
            r.textContent = D ? D.emptyScript : "";
            for (let f = 0; f < g; f++) r.append(c[f], O()), m.nextNode(), a.push({ type: 2, index: ++o });
            r.append(c[g], O());
          }
        }
      } else if (r.nodeType === 8) if (r.data === pe) a.push({ type: 2, index: o });
      else {
        let c = -1;
        for (; (c = r.data.indexOf($, c + 1)) !== -1; ) a.push({ type: 7, index: o }), c += $.length - 1;
      }
      o++;
    }
  }
  static createElement(e, t) {
    const s = b.createElement("template");
    return s.innerHTML = e, s;
  }
}
function E(i, e, t = i, s) {
  var n, l;
  if (e === A) return e;
  let r = s !== void 0 ? (n = t._$Co) == null ? void 0 : n[s] : t._$Cl;
  const o = U(e) ? void 0 : e._$litDirective$;
  return (r == null ? void 0 : r.constructor) !== o && ((l = r == null ? void 0 : r._$AO) == null || l.call(r, !1), o === void 0 ? r = void 0 : (r = new o(i), r._$AT(i, t, s)), s !== void 0 ? (t._$Co ?? (t._$Co = []))[s] = r : t._$Cl = r), r !== void 0 && (e = E(i, r._$AS(i, e.values), r, s)), e;
}
class Oe {
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
    const { el: { content: t }, parts: s } = this._$AD, r = ((e == null ? void 0 : e.creationScope) ?? b).importNode(t, !0);
    m.currentNode = r;
    let o = m.nextNode(), n = 0, l = 0, a = s[0];
    for (; a !== void 0; ) {
      if (n === a.index) {
        let h;
        a.type === 2 ? h = new T(o, o.nextSibling, this, e) : a.type === 1 ? h = new a.ctor(o, a.name, a.strings, this, e) : a.type === 6 && (h = new Me(o, this, e)), this._$AV.push(h), a = s[++l];
      }
      n !== (a == null ? void 0 : a.index) && (o = m.nextNode(), n++);
    }
    return m.currentNode = b, r;
  }
  p(e) {
    let t = 0;
    for (const s of this._$AV) s !== void 0 && (s.strings !== void 0 ? (s._$AI(e, s, t), t += s.strings.length - 2) : s._$AI(e[t])), t++;
  }
}
class T {
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
    e = E(this, e, t), U(e) ? e === d || e == null || e === "" ? (this._$AH !== d && this._$AR(), this._$AH = d) : e !== this._$AH && e !== A && this._(e) : e._$litType$ !== void 0 ? this.$(e) : e.nodeType !== void 0 ? this.T(e) : Se(e) ? this.k(e) : this._(e);
  }
  O(e) {
    return this._$AA.parentNode.insertBefore(e, this._$AB);
  }
  T(e) {
    this._$AH !== e && (this._$AR(), this._$AH = this.O(e));
  }
  _(e) {
    this._$AH !== d && U(this._$AH) ? this._$AA.nextSibling.data = e : this.T(b.createTextNode(e)), this._$AH = e;
  }
  $(e) {
    var o;
    const { values: t, _$litType$: s } = e, r = typeof s == "number" ? this._$AC(e) : (s.el === void 0 && (s.el = z.createElement(ge(s.h, s.h[0]), this.options)), s);
    if (((o = this._$AH) == null ? void 0 : o._$AD) === r) this._$AH.p(t);
    else {
      const n = new Oe(r, this), l = n.u(this.options);
      n.p(t), this.T(l), this._$AH = n;
    }
  }
  _$AC(e) {
    let t = oe.get(e.strings);
    return t === void 0 && oe.set(e.strings, t = new z(e)), t;
  }
  k(e) {
    G(this._$AH) || (this._$AH = [], this._$AR());
    const t = this._$AH;
    let s, r = 0;
    for (const o of e) r === t.length ? t.push(s = new T(this.O(O()), this.O(O()), this, this.options)) : s = t[r], s._$AI(o), r++;
    r < t.length && (this._$AR(s && s._$AB.nextSibling, r), t.length = r);
  }
  _$AR(e = this._$AA.nextSibling, t) {
    var s;
    for ((s = this._$AP) == null ? void 0 : s.call(this, !1, !0, t); e !== this._$AB; ) {
      const r = Q(e).nextSibling;
      Q(e).remove(), e = r;
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
    if (o === void 0) e = E(this, e, t, 0), n = !U(e) || e !== this._$AH && e !== A, n && (this._$AH = e);
    else {
      const l = e;
      let a, h;
      for (e = o[0], a = 0; a < o.length - 1; a++) h = E(this, l[s + a], t, a), h === A && (h = this._$AH[a]), n || (n = !U(h) || h !== this._$AH[a]), h === d ? e = d : e !== d && (e += (h ?? "") + o[a + 1]), this._$AH[a] = h;
    }
    n && !r && this.j(e);
  }
  j(e) {
    e === d ? this.element.removeAttribute(this.name) : this.element.setAttribute(this.name, e ?? "");
  }
}
class Ue extends j {
  constructor() {
    super(...arguments), this.type = 3;
  }
  j(e) {
    this.element[this.name] = e === d ? void 0 : e;
  }
}
class ze extends j {
  constructor() {
    super(...arguments), this.type = 4;
  }
  j(e) {
    this.element.toggleAttribute(this.name, !!e && e !== d);
  }
}
class Te extends j {
  constructor(e, t, s, r, o) {
    super(e, t, s, r, o), this.type = 5;
  }
  _$AI(e, t = this) {
    if ((e = E(this, e, t, 0) ?? d) === A) return;
    const s = this._$AH, r = e === d && s !== d || e.capture !== s.capture || e.once !== s.once || e.passive !== s.passive, o = e !== d && (s === d || r);
    r && this.element.removeEventListener(this.name, this, s), o && this.element.addEventListener(this.name, this, e), this._$AH = e;
  }
  handleEvent(e) {
    var t;
    typeof this._$AH == "function" ? this._$AH.call(((t = this.options) == null ? void 0 : t.host) ?? this.element, e) : this._$AH.handleEvent(e);
  }
}
class Me {
  constructor(e, t, s) {
    this.element = e, this.type = 6, this._$AN = void 0, this._$AM = t, this.options = s;
  }
  get _$AU() {
    return this._$AM._$AU;
  }
  _$AI(e) {
    E(this, e);
  }
}
const B = k.litHtmlPolyfillSupport;
B == null || B(z, T), (k.litHtmlVersions ?? (k.litHtmlVersions = [])).push("3.3.2");
const Re = (i, e, t) => {
  const s = (t == null ? void 0 : t.renderBefore) ?? e;
  let r = s._$litPart$;
  if (r === void 0) {
    const o = (t == null ? void 0 : t.renderBefore) ?? null;
    s._$litPart$ = r = new T(e.insertBefore(O(), o), o, void 0, t ?? {});
  }
  return r._$AI(i), r;
};
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const v = globalThis;
class P extends x {
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
    this.hasUpdated || (this.renderOptions.isConnected = this.isConnected), super.update(e), this._$Do = Re(t, this.renderRoot, this.renderOptions);
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
    return A;
  }
}
var de;
P._$litElement$ = !0, P.finalized = !0, (de = v.litElementHydrateSupport) == null || de.call(v, { LitElement: P });
const W = v.litElementPolyfillSupport;
W == null || W({ LitElement: P });
(v.litElementVersions ?? (v.litElementVersions = [])).push("4.2.2");
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
const He = { attribute: !0, type: String, converter: H, reflect: !1, hasChanged: V }, De = (i = He, e, t) => {
  const { kind: s, metadata: r } = t;
  let o = globalThis.litPropertyMetadata.get(r);
  if (o === void 0 && globalThis.litPropertyMetadata.set(r, o = /* @__PURE__ */ new Map()), s === "setter" && ((i = Object.create(i)).wrapped = !0), o.set(t.name, i), s === "accessor") {
    const { name: n } = t;
    return { set(l) {
      const a = e.get.call(this);
      e.set.call(this, l), this.requestUpdate(n, a, i, !0, l);
    }, init(l) {
      return l !== void 0 && this.C(n, void 0, i, l), l;
    } };
  }
  if (s === "setter") {
    const { name: n } = t;
    return function(l) {
      const a = this[n];
      e.call(this, l), this.requestUpdate(n, a, i, !0, l);
    };
  }
  throw Error("Unsupported decorator location: " + s);
};
function fe(i) {
  return (e, t) => typeof t == "object" ? De(i, e, t) : ((s, r, o) => {
    const n = r.hasOwnProperty(o);
    return r.constructor.createProperty(o, s), n ? Object.getOwnPropertyDescriptor(r, o) : void 0;
  })(i, e, t);
}
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
function Z(i) {
  return fe({ ...i, state: !0, attribute: !1 });
}
var je = Object.defineProperty, Le = Object.getOwnPropertyDescriptor, M = (i, e, t, s) => {
  for (var r = s > 1 ? void 0 : s ? Le(e, t) : e, o = i.length - 1, n; o >= 0; o--)
    (n = i[o]) && (r = (s ? n(e, t, r) : n(r)) || r);
  return s && r && je(e, t, r), r;
};
function ne(i) {
  if (/^\d{2}\.\d{2}\.\d{4}$/.test(i)) {
    const [e, t, s] = i.split(".");
    return (/* @__PURE__ */ new Date(`${s}-${t}-${e}`)).getTime();
  }
  return new Date(i).getTime();
}
function ae(i) {
  if (/^\d{2}\.\d{2}\.\d{4}$/.test(i)) return i;
  if (/^\d{4}-\d{2}-\d{2}$/.test(i)) {
    const [e, t, s] = i.split("-");
    return `${s}.${t}.${e}`;
  }
  return i;
}
function le(i) {
  const e = i.toLowerCase();
  return e.includes("sprawdzian") || e.includes("test") ? { label: "SPRAWDZ", cssClass: "type-test" } : e.includes("kartkówka") || e.includes("kartkowka") ? { label: "KARTK", cssClass: "type-quiz" } : e.includes("praca klasow") || e.includes("praca kontrolna") ? { label: "PR.KL", cssClass: "type-classwork" } : e.includes("praca domow") ? { label: "PR.DOM", cssClass: "type-homework" } : e.includes("wypracowanie") ? { label: "WYPRAC", cssClass: "type-essay" } : { label: e.slice(0, 5).toUpperCase() || "INNE", cssClass: "type-other" };
}
let w = class extends P {
  constructor() {
    super(...arguments), this._selectedGrade = null, this._dlgOpen = !1, this._onKeydown = (i) => {
      i.key === "Escape" && this._dlgOpen && (i.stopPropagation(), this._closeDialog());
    };
  }
  connectedCallback() {
    super.connectedCallback(), window.addEventListener("keydown", this._onKeydown);
  }
  disconnectedCallback() {
    super.disconnectedCallback(), window.removeEventListener("keydown", this._onKeydown);
  }
  static getStubConfig() {
    return { type: "librus-grades-card", entities: [], title: "Oceny" };
  }
  setConfig(i) {
    if (!i.entities || !Array.isArray(i.entities))
      throw new Error("entities (lista sensorów per-przedmiot) jest wymagana");
    this._config = i;
  }
  getCardSize() {
    return 6;
  }
  get _grades() {
    var s;
    if (!this.hass || !this._config) return [];
    const i = [];
    for (const r of this._config.entities) {
      const o = this.hass.states[r], n = (s = o == null ? void 0 : o.attributes) == null ? void 0 : s.grade_details;
      n && i.push(...n);
    }
    const t = (this._config.only_recent ? i.filter((r) => r.is_recent) : i).sort((r, o) => ne(r.date) - ne(o.date));
    return (this._config.sort_order ?? "desc") === "desc" ? t.reverse() : t;
  }
  _openDialog(i) {
    this._selectedGrade = i, this._dlgOpen = !0;
  }
  _closeDialog() {
    this._dlgOpen = !1, this._selectedGrade = null;
  }
  _renderRow(i) {
    const { label: e, cssClass: t } = le(i.category), s = [
      i.teacher,
      i.weight != null ? `waga ${i.weight}` : ""
    ].filter(Boolean).join(" · ");
    return u`
      <div
        class="grade-row ${i.is_recent ? "recent" : ""}"
        data-tooltip="${s || d}"
        role="button"
        tabindex="0"
        @click="${() => this._openDialog(i)}"
        @keydown="${(r) => r.key === "Enter" && this._openDialog(i)}"
      >
        <span class="grade-badge ${t}">${e}</span>
        <span class="grade-subject">${i.subject}</span>
        <span class="grade-value">${i.grade}</span>
        <span class="grade-date">${ae(i.date)}</span>
      </div>
    `;
  }
  _renderDialog() {
    const i = this._selectedGrade;
    return u`
      <div
        class="dlg-overlay${this._dlgOpen ? " dlg-overlay--open" : ""}"
        @click="${(e) => {
      e.target === e.currentTarget && this._closeDialog();
    }}"
        aria-hidden="${String(!this._dlgOpen)}"
      >
        <div class="dlg-panel" role="dialog" aria-modal="true">
          ${i ? u`
            <div class="dlg-header">
              <div class="dlg-meta">
                <div class="dlg-subject">${i.subject}</div>
                <div class="dlg-category">${i.category || "—"}${i.category && i.date ? " · " : ""}${ae(i.date)}</div>
              </div>
              <ha-icon-button
                .label=${"Zamknij"}
                .path=${"M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"}
                @click="${() => this._closeDialog()}"
              ></ha-icon-button>
            </div>
            <div class="dlg-body">
              <div class="dlg-grade-large ${le(i.category).cssClass}">${i.grade}</div>
              <div class="dlg-details">
                ${i.teacher ? u`<div class="dlg-detail-row"><span class="dlg-detail-label">Nauczyciel</span><span>${i.teacher}</span></div>` : d}
                ${i.weight != null ? u`<div class="dlg-detail-row"><span class="dlg-detail-label">Waga</span><span>${i.weight}</span></div>` : d}
                <div class="dlg-detail-row"><span class="dlg-detail-label">Liczy do średniej</span><span>${i.counts ? "Tak" : "Nie"}</span></div>
                ${i.title ? u`<div class="dlg-detail-row dlg-detail-row--block"><span class="dlg-detail-label">Temat</span><span class="dlg-detail-text">${i.title}</span></div>` : d}
                ${i.description ? u`<div class="dlg-detail-row"><span class="dlg-detail-label">Poprawa</span><span>${i.description}</span></div>` : d}
              </div>
            </div>
          ` : d}
        </div>
      </div>
    `;
  }
  render() {
    if (!this._config) return d;
    const i = this._grades, e = this._config.title ?? "Oceny", t = i.filter((r) => r.is_recent).length, s = this._config.height ?? 400;
    return u`
      <ha-card style="--card-h:${s}px">
        <div class="card-header">
          <span class="card-title">${e}</span>
          <span class="card-count">${i.length}${t > 0 ? u` <span class="new-badge">${t} nowe</span>` : d}</span>
        </div>
        <div class="grade-list">
          ${i.length === 0 ? u`<div class="empty">Brak ocen</div>` : i.map((r) => this._renderRow(r))}
        </div>
      </ha-card>
      ${this._renderDialog()}
    `;
  }
};
w.styles = _e`
    :host { display: block; }

    ha-card {
      padding: 0;
      overflow: hidden;
      height: var(--card-h, 400px);
      display: flex;
      flex-direction: column;
    }

    .card-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 12px 16px 8px;
      flex-shrink: 0;
    }
    .card-title {
      font-size: 1.1em;
      font-weight: 500;
      color: var(--primary-text-color);
    }
    .card-count {
      font-size: 0.85em;
      color: var(--secondary-text-color);
      display: flex;
      align-items: center;
      gap: 6px;
    }
    .new-badge {
      background: var(--primary-color);
      color: var(--text-primary-color, #fff);
      border-radius: 10px;
      padding: 1px 7px;
      font-size: 0.8em;
    }

    .grade-list {
      flex: 1;
      overflow-y: auto;
      min-height: 0;
    }

    .grade-row {
      display: grid;
      grid-template-columns: 68px 1fr auto auto;
      align-items: center;
      gap: 8px;
      padding: 8px 16px;
      border-bottom: 1px solid var(--divider-color);
      cursor: pointer;
      position: relative;
      transition: background 0.15s;
    }
    .grade-row:hover {
      background: var(--secondary-background-color);
    }
    .grade-row.recent {
      background: color-mix(in srgb, var(--primary-color) 8%, transparent);
    }
    .grade-row.recent:hover {
      background: color-mix(in srgb, var(--primary-color) 15%, transparent);
    }

    /* CSS tooltip */
    .grade-row[data-tooltip]:not([data-tooltip=""]):hover::after {
      content: attr(data-tooltip);
      position: absolute;
      bottom: calc(100% + 4px);
      left: 50%;
      transform: translateX(-50%);
      background: var(--card-background-color, #fff);
      border: 1px solid var(--divider-color);
      border-radius: 4px;
      padding: 4px 8px;
      font-size: 0.75em;
      white-space: nowrap;
      z-index: 10;
      pointer-events: none;
      box-shadow: 0 2px 6px rgba(0, 0, 0, 0.15);
      color: var(--primary-text-color);
    }

    .grade-badge {
      display: inline-block;
      background: var(--badge-bg, #888);
      color: #fff;
      font-size: 0.65em;
      font-weight: 600;
      letter-spacing: 0.04em;
      padding: 2px 5px;
      border-radius: 3px;
      text-align: center;
      min-width: 52px;
    }
    .type-test      { --badge-bg: var(--error-color, #f44336); }
    .type-quiz      { --badge-bg: #ff9800; }
    .type-classwork { --badge-bg: var(--info-color, #2196f3); }
    .type-homework  { --badge-bg: #4caf50; }
    .type-essay     { --badge-bg: #9c27b0; }
    .type-other     { --badge-bg: var(--secondary-text-color, #888); }

    .grade-subject {
      font-size: 0.9em;
      color: var(--primary-text-color);
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
    .grade-value {
      font-size: 1em;
      font-weight: 600;
      color: var(--primary-text-color);
      min-width: 28px;
      text-align: right;
    }
    .grade-date {
      font-size: 0.78em;
      color: var(--secondary-text-color);
      white-space: nowrap;
      min-width: 72px;
      text-align: right;
    }

    .empty {
      padding: 24px 16px;
      text-align: center;
      color: var(--secondary-text-color);
      font-size: 0.9em;
    }

    /* Overlay — position:fixed nie blokuje scroll body (w odróżnieniu od showModal) */
    .dlg-overlay {
      display: none;
      position: fixed;
      inset: 0;
      z-index: 9999;
      background: rgba(0, 0, 0, 0.45);
      backdrop-filter: blur(2px);
      align-items: center;
      justify-content: center;
    }
    .dlg-overlay--open {
      display: flex;
    }

    .dlg-panel {
      max-width: min(480px, 95vw);
      max-height: 80vh;
      overflow: hidden;
      display: flex;
      flex-direction: column;
      border-radius: var(--ha-card-border-radius, 12px);
      box-shadow: var(--ha-card-box-shadow, 0 4px 16px rgba(0, 0, 0, 0.4));
      background: var(--card-background-color, #fff);
      color: var(--primary-text-color);
    }

    .dlg-header {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      padding: 16px 8px 12px 20px;
      border-bottom: 1px solid var(--divider-color);
      flex-shrink: 0;
    }
    .dlg-subject {
      font-size: 1.1em;
      font-weight: 600;
    }
    .dlg-category {
      font-size: 0.82em;
      color: var(--secondary-text-color);
      margin-top: 2px;
    }

    .dlg-body {
      flex: 1;
      overflow-y: auto;
      padding: 20px;
      display: flex;
      flex-direction: column;
      gap: 16px;
    }
    .dlg-grade-large {
      font-size: 2.8em;
      font-weight: 700;
      text-align: center;
      padding: 12px;
      border-radius: 8px;
      color: #fff;
      background: var(--badge-bg, var(--secondary-text-color, #888));
      flex-shrink: 0;
    }

    .dlg-details {
      display: flex;
      flex-direction: column;
      gap: 8px;
    }
    .dlg-detail-row {
      display: flex;
      justify-content: space-between;
      align-items: baseline;
      gap: 12px;
      font-size: 0.9em;
    }
    .dlg-detail-row--block {
      align-items: flex-start;
    }
    .dlg-detail-label {
      color: var(--secondary-text-color);
      white-space: nowrap;
      flex-shrink: 0;
    }
    .dlg-detail-text {
      text-align: right;
      word-break: break-word;
      white-space: pre-wrap;
      flex-shrink: 1;
    }
  `;
M([
  fe({ attribute: !1 })
], w.prototype, "hass", 2);
M([
  Z()
], w.prototype, "_config", 2);
M([
  Z()
], w.prototype, "_selectedGrade", 2);
M([
  Z()
], w.prototype, "_dlgOpen", 2);
w = M([
  Ne("librus-grades-card")
], w);
window.customCards ?? (window.customCards = []);
window.customCards.push({
  type: "librus-grades-card",
  name: "Librus — Oceny",
  description: "Chronologiczna lista ocen z kolorowym badgem typu, tooltipem i popupem ze szczegółami."
});
export {
  w as LibrusGradesCard
};
