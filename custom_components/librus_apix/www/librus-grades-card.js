/**
 * @license
 * Copyright 2019 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const H = globalThis, G = H.ShadowRoot && (H.ShadyCSS === void 0 || H.ShadyCSS.nativeShadow) && "adoptedStyleSheets" in Document.prototype && "replace" in CSSStyleSheet.prototype, V = Symbol(), J = /* @__PURE__ */ new WeakMap();
let de = class {
  constructor(e, t, r) {
    if (this._$cssResult$ = !0, r !== V) throw Error("CSSResult is not constructable. Use `unsafeCSS` or `css` instead.");
    this.cssText = e, this.t = t;
  }
  get styleSheet() {
    let e = this.o;
    const t = this.t;
    if (G && e === void 0) {
      const r = t !== void 0 && t.length === 1;
      r && (e = J.get(t)), e === void 0 && ((this.o = e = new CSSStyleSheet()).replaceSync(this.cssText), r && J.set(t, e));
    }
    return e;
  }
  toString() {
    return this.cssText;
  }
};
const $e = (s) => new de(typeof s == "string" ? s : s + "", void 0, V), _e = (s, ...e) => {
  const t = s.length === 1 ? s[0] : e.reduce((r, i, o) => r + ((n) => {
    if (n._$cssResult$ === !0) return n.cssText;
    if (typeof n == "number") return n;
    throw Error("Value passed to 'css' function must be a 'css' function result: " + n + ". Use 'unsafeCSS' to pass non-literal values, but take care to ensure page security.");
  })(i) + s[o + 1], s[0]);
  return new de(t, s, V);
}, ye = (s, e) => {
  if (G) s.adoptedStyleSheets = e.map((t) => t instanceof CSSStyleSheet ? t : t.styleSheet);
  else for (const t of e) {
    const r = document.createElement("style"), i = H.litNonce;
    i !== void 0 && r.setAttribute("nonce", i), r.textContent = t.cssText, s.appendChild(r);
  }
}, X = G ? (s) => s : (s) => s instanceof CSSStyleSheet ? ((e) => {
  let t = "";
  for (const r of e.cssRules) t += r.cssText;
  return $e(t);
})(s) : s;
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const { is: me, defineProperty: be, getOwnPropertyDescriptor: ve, getOwnPropertyNames: we, getOwnPropertySymbols: Ae, getPrototypeOf: xe } = Object, _ = globalThis, Y = _.trustedTypes, Ee = Y ? Y.emptyScript : "", I = _.reactiveElementPolyfillSupport, P = (s, e) => s, D = { toAttribute(s, e) {
  switch (e) {
    case Boolean:
      s = s ? Ee : null;
      break;
    case Object:
    case Array:
      s = s == null ? s : JSON.stringify(s);
  }
  return s;
}, fromAttribute(s, e) {
  let t = s;
  switch (e) {
    case Boolean:
      t = s !== null;
      break;
    case Number:
      t = s === null ? null : Number(s);
      break;
    case Object:
    case Array:
      try {
        t = JSON.parse(s);
      } catch {
        t = null;
      }
  }
  return t;
} }, K = (s, e) => !me(s, e), Q = { attribute: !0, type: String, converter: D, reflect: !1, useDefault: !1, hasChanged: K };
Symbol.metadata ?? (Symbol.metadata = Symbol("metadata")), _.litPropertyMetadata ?? (_.litPropertyMetadata = /* @__PURE__ */ new WeakMap());
let A = class extends HTMLElement {
  static addInitializer(e) {
    this._$Ei(), (this.l ?? (this.l = [])).push(e);
  }
  static get observedAttributes() {
    return this.finalize(), this._$Eh && [...this._$Eh.keys()];
  }
  static createProperty(e, t = Q) {
    if (t.state && (t.attribute = !1), this._$Ei(), this.prototype.hasOwnProperty(e) && ((t = Object.create(t)).wrapped = !0), this.elementProperties.set(e, t), !t.noAccessor) {
      const r = Symbol(), i = this.getPropertyDescriptor(e, r, t);
      i !== void 0 && be(this.prototype, e, i);
    }
  }
  static getPropertyDescriptor(e, t, r) {
    const { get: i, set: o } = ve(this.prototype, e) ?? { get() {
      return this[t];
    }, set(n) {
      this[t] = n;
    } };
    return { get: i, set(n) {
      const l = i == null ? void 0 : i.call(this);
      o == null || o.call(this, n), this.requestUpdate(e, l, r);
    }, configurable: !0, enumerable: !0 };
  }
  static getPropertyOptions(e) {
    return this.elementProperties.get(e) ?? Q;
  }
  static _$Ei() {
    if (this.hasOwnProperty(P("elementProperties"))) return;
    const e = xe(this);
    e.finalize(), e.l !== void 0 && (this.l = [...e.l]), this.elementProperties = new Map(e.elementProperties);
  }
  static finalize() {
    if (this.hasOwnProperty(P("finalized"))) return;
    if (this.finalized = !0, this._$Ei(), this.hasOwnProperty(P("properties"))) {
      const t = this.properties, r = [...we(t), ...Ae(t)];
      for (const i of r) this.createProperty(i, t[i]);
    }
    const e = this[Symbol.metadata];
    if (e !== null) {
      const t = litPropertyMetadata.get(e);
      if (t !== void 0) for (const [r, i] of t) this.elementProperties.set(r, i);
    }
    this._$Eh = /* @__PURE__ */ new Map();
    for (const [t, r] of this.elementProperties) {
      const i = this._$Eu(t, r);
      i !== void 0 && this._$Eh.set(i, t);
    }
    this.elementStyles = this.finalizeStyles(this.styles);
  }
  static finalizeStyles(e) {
    const t = [];
    if (Array.isArray(e)) {
      const r = new Set(e.flat(1 / 0).reverse());
      for (const i of r) t.unshift(X(i));
    } else e !== void 0 && t.push(X(e));
    return t;
  }
  static _$Eu(e, t) {
    const r = t.attribute;
    return r === !1 ? void 0 : typeof r == "string" ? r : typeof e == "string" ? e.toLowerCase() : void 0;
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
    for (const r of t.keys()) this.hasOwnProperty(r) && (e.set(r, this[r]), delete this[r]);
    e.size > 0 && (this._$Ep = e);
  }
  createRenderRoot() {
    const e = this.shadowRoot ?? this.attachShadow(this.constructor.shadowRootOptions);
    return ye(e, this.constructor.elementStyles), e;
  }
  connectedCallback() {
    var e;
    this.renderRoot ?? (this.renderRoot = this.createRenderRoot()), this.enableUpdating(!0), (e = this._$EO) == null || e.forEach((t) => {
      var r;
      return (r = t.hostConnected) == null ? void 0 : r.call(t);
    });
  }
  enableUpdating(e) {
  }
  disconnectedCallback() {
    var e;
    (e = this._$EO) == null || e.forEach((t) => {
      var r;
      return (r = t.hostDisconnected) == null ? void 0 : r.call(t);
    });
  }
  attributeChangedCallback(e, t, r) {
    this._$AK(e, r);
  }
  _$ET(e, t) {
    var o;
    const r = this.constructor.elementProperties.get(e), i = this.constructor._$Eu(e, r);
    if (i !== void 0 && r.reflect === !0) {
      const n = (((o = r.converter) == null ? void 0 : o.toAttribute) !== void 0 ? r.converter : D).toAttribute(t, r.type);
      this._$Em = e, n == null ? this.removeAttribute(i) : this.setAttribute(i, n), this._$Em = null;
    }
  }
  _$AK(e, t) {
    var o, n;
    const r = this.constructor, i = r._$Eh.get(e);
    if (i !== void 0 && this._$Em !== i) {
      const l = r.getPropertyOptions(i), a = typeof l.converter == "function" ? { fromAttribute: l.converter } : ((o = l.converter) == null ? void 0 : o.fromAttribute) !== void 0 ? l.converter : D;
      this._$Em = i;
      const d = a.fromAttribute(t, l.type);
      this[i] = d ?? ((n = this._$Ej) == null ? void 0 : n.get(i)) ?? d, this._$Em = null;
    }
  }
  requestUpdate(e, t, r, i = !1, o) {
    var n;
    if (e !== void 0) {
      const l = this.constructor;
      if (i === !1 && (o = this[e]), r ?? (r = l.getPropertyOptions(e)), !((r.hasChanged ?? K)(o, t) || r.useDefault && r.reflect && o === ((n = this._$Ej) == null ? void 0 : n.get(e)) && !this.hasAttribute(l._$Eu(e, r)))) return;
      this.C(e, t, r);
    }
    this.isUpdatePending === !1 && (this._$ES = this._$EP());
  }
  C(e, t, { useDefault: r, reflect: i, wrapped: o }, n) {
    r && !(this._$Ej ?? (this._$Ej = /* @__PURE__ */ new Map())).has(e) && (this._$Ej.set(e, n ?? t ?? this[e]), o !== !0 || n !== void 0) || (this._$AL.has(e) || (this.hasUpdated || r || (t = void 0), this._$AL.set(e, t)), i === !0 && this._$Em !== e && (this._$Eq ?? (this._$Eq = /* @__PURE__ */ new Set())).add(e));
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
    var r;
    if (!this.isUpdatePending) return;
    if (!this.hasUpdated) {
      if (this.renderRoot ?? (this.renderRoot = this.createRenderRoot()), this._$Ep) {
        for (const [o, n] of this._$Ep) this[o] = n;
        this._$Ep = void 0;
      }
      const i = this.constructor.elementProperties;
      if (i.size > 0) for (const [o, n] of i) {
        const { wrapped: l } = n, a = this[o];
        l !== !0 || this._$AL.has(o) || a === void 0 || this.C(o, void 0, n, a);
      }
    }
    let e = !1;
    const t = this._$AL;
    try {
      e = this.shouldUpdate(t), e ? (this.willUpdate(t), (r = this._$EO) == null || r.forEach((i) => {
        var o;
        return (o = i.hostUpdate) == null ? void 0 : o.call(i);
      }), this.update(t)) : this._$EM();
    } catch (i) {
      throw e = !1, this._$EM(), i;
    }
    e && this._$AE(t);
  }
  willUpdate(e) {
  }
  _$AE(e) {
    var t;
    (t = this._$EO) == null || t.forEach((r) => {
      var i;
      return (i = r.hostUpdated) == null ? void 0 : i.call(r);
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
A.elementStyles = [], A.shadowRootOptions = { mode: "open" }, A[P("elementProperties")] = /* @__PURE__ */ new Map(), A[P("finalized")] = /* @__PURE__ */ new Map(), I == null || I({ ReactiveElement: A }), (_.reactiveElementVersions ?? (_.reactiveElementVersions = [])).push("2.1.2");
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const O = globalThis, ee = (s) => s, j = O.trustedTypes, te = j ? j.createPolicy("lit-html", { createHTML: (s) => s }) : void 0, he = "$lit$", $ = `lit$${Math.random().toFixed(9).slice(2)}$`, pe = "?" + $, Se = `<${pe}>`, v = document, z = () => v.createComment(""), U = (s) => s === null || typeof s != "object" && typeof s != "function", Z = Array.isArray, Ce = (s) => Z(s) || typeof (s == null ? void 0 : s[Symbol.iterator]) == "function", B = `[ 	
\f\r]`, C = /<(?:(!--|\/[^a-zA-Z])|(\/?[a-zA-Z][^>\s]*)|(\/?$))/g, se = /-->/g, re = />/g, y = RegExp(`>|${B}(?:([^\\s"'>=/]+)(${B}*=${B}*(?:[^ 	
\f\r"'\`<>=]|("|')|))|$)`, "g"), ie = /'/g, oe = /"/g, ue = /^(?:script|style|textarea|title)$/i, Pe = (s) => (e, ...t) => ({ _$litType$: s, strings: e, values: t }), u = Pe(1), E = Symbol.for("lit-noChange"), c = Symbol.for("lit-nothing"), ne = /* @__PURE__ */ new WeakMap(), m = v.createTreeWalker(v, 129);
function ge(s, e) {
  if (!Z(s) || !s.hasOwnProperty("raw")) throw Error("invalid template strings array");
  return te !== void 0 ? te.createHTML(e) : e;
}
const Oe = (s, e) => {
  const t = s.length - 1, r = [];
  let i, o = e === 2 ? "<svg>" : e === 3 ? "<math>" : "", n = C;
  for (let l = 0; l < t; l++) {
    const a = s[l];
    let d, p, h = -1, g = 0;
    for (; g < a.length && (n.lastIndex = g, p = n.exec(a), p !== null); ) g = n.lastIndex, n === C ? p[1] === "!--" ? n = se : p[1] !== void 0 ? n = re : p[2] !== void 0 ? (ue.test(p[2]) && (i = RegExp("</" + p[2], "g")), n = y) : p[3] !== void 0 && (n = y) : n === y ? p[0] === ">" ? (n = i ?? C, h = -1) : p[1] === void 0 ? h = -2 : (h = n.lastIndex - p[2].length, d = p[1], n = p[3] === void 0 ? y : p[3] === '"' ? oe : ie) : n === oe || n === ie ? n = y : n === se || n === re ? n = C : (n = y, i = void 0);
    const f = n === y && s[l + 1].startsWith("/>") ? " " : "";
    o += n === C ? a + Se : h >= 0 ? (r.push(d), a.slice(0, h) + he + a.slice(h) + $ + f) : a + $ + (h === -2 ? l : f);
  }
  return [ge(s, o + (s[t] || "<?>") + (e === 2 ? "</svg>" : e === 3 ? "</math>" : "")), r];
};
class R {
  constructor({ strings: e, _$litType$: t }, r) {
    let i;
    this.parts = [];
    let o = 0, n = 0;
    const l = e.length - 1, a = this.parts, [d, p] = Oe(e, t);
    if (this.el = R.createElement(d, r), m.currentNode = this.el.content, t === 2 || t === 3) {
      const h = this.el.content.firstChild;
      h.replaceWith(...h.childNodes);
    }
    for (; (i = m.nextNode()) !== null && a.length < l; ) {
      if (i.nodeType === 1) {
        if (i.hasAttributes()) for (const h of i.getAttributeNames()) if (h.endsWith(he)) {
          const g = p[n++], f = i.getAttribute(h).split($), M = /([.?@])?(.*)/.exec(g);
          a.push({ type: 1, index: o, name: M[2], strings: f, ctor: M[1] === "." ? ze : M[1] === "?" ? Ue : M[1] === "@" ? Re : L }), i.removeAttribute(h);
        } else h.startsWith($) && (a.push({ type: 6, index: o }), i.removeAttribute(h));
        if (ue.test(i.tagName)) {
          const h = i.textContent.split($), g = h.length - 1;
          if (g > 0) {
            i.textContent = j ? j.emptyScript : "";
            for (let f = 0; f < g; f++) i.append(h[f], z()), m.nextNode(), a.push({ type: 2, index: ++o });
            i.append(h[g], z());
          }
        }
      } else if (i.nodeType === 8) if (i.data === pe) a.push({ type: 2, index: o });
      else {
        let h = -1;
        for (; (h = i.data.indexOf($, h + 1)) !== -1; ) a.push({ type: 7, index: o }), h += $.length - 1;
      }
      o++;
    }
  }
  static createElement(e, t) {
    const r = v.createElement("template");
    return r.innerHTML = e, r;
  }
}
function S(s, e, t = s, r) {
  var n, l;
  if (e === E) return e;
  let i = r !== void 0 ? (n = t._$Co) == null ? void 0 : n[r] : t._$Cl;
  const o = U(e) ? void 0 : e._$litDirective$;
  return (i == null ? void 0 : i.constructor) !== o && ((l = i == null ? void 0 : i._$AO) == null || l.call(i, !1), o === void 0 ? i = void 0 : (i = new o(s), i._$AT(s, t, r)), r !== void 0 ? (t._$Co ?? (t._$Co = []))[r] = i : t._$Cl = i), i !== void 0 && (e = S(s, i._$AS(s, e.values), i, r)), e;
}
class ke {
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
    const { el: { content: t }, parts: r } = this._$AD, i = ((e == null ? void 0 : e.creationScope) ?? v).importNode(t, !0);
    m.currentNode = i;
    let o = m.nextNode(), n = 0, l = 0, a = r[0];
    for (; a !== void 0; ) {
      if (n === a.index) {
        let d;
        a.type === 2 ? d = new T(o, o.nextSibling, this, e) : a.type === 1 ? d = new a.ctor(o, a.name, a.strings, this, e) : a.type === 6 && (d = new Te(o, this, e)), this._$AV.push(d), a = r[++l];
      }
      n !== (a == null ? void 0 : a.index) && (o = m.nextNode(), n++);
    }
    return m.currentNode = v, i;
  }
  p(e) {
    let t = 0;
    for (const r of this._$AV) r !== void 0 && (r.strings !== void 0 ? (r._$AI(e, r, t), t += r.strings.length - 2) : r._$AI(e[t])), t++;
  }
}
class T {
  get _$AU() {
    var e;
    return ((e = this._$AM) == null ? void 0 : e._$AU) ?? this._$Cv;
  }
  constructor(e, t, r, i) {
    this.type = 2, this._$AH = c, this._$AN = void 0, this._$AA = e, this._$AB = t, this._$AM = r, this.options = i, this._$Cv = (i == null ? void 0 : i.isConnected) ?? !0;
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
    e = S(this, e, t), U(e) ? e === c || e == null || e === "" ? (this._$AH !== c && this._$AR(), this._$AH = c) : e !== this._$AH && e !== E && this._(e) : e._$litType$ !== void 0 ? this.$(e) : e.nodeType !== void 0 ? this.T(e) : Ce(e) ? this.k(e) : this._(e);
  }
  O(e) {
    return this._$AA.parentNode.insertBefore(e, this._$AB);
  }
  T(e) {
    this._$AH !== e && (this._$AR(), this._$AH = this.O(e));
  }
  _(e) {
    this._$AH !== c && U(this._$AH) ? this._$AA.nextSibling.data = e : this.T(v.createTextNode(e)), this._$AH = e;
  }
  $(e) {
    var o;
    const { values: t, _$litType$: r } = e, i = typeof r == "number" ? this._$AC(e) : (r.el === void 0 && (r.el = R.createElement(ge(r.h, r.h[0]), this.options)), r);
    if (((o = this._$AH) == null ? void 0 : o._$AD) === i) this._$AH.p(t);
    else {
      const n = new ke(i, this), l = n.u(this.options);
      n.p(t), this.T(l), this._$AH = n;
    }
  }
  _$AC(e) {
    let t = ne.get(e.strings);
    return t === void 0 && ne.set(e.strings, t = new R(e)), t;
  }
  k(e) {
    Z(this._$AH) || (this._$AH = [], this._$AR());
    const t = this._$AH;
    let r, i = 0;
    for (const o of e) i === t.length ? t.push(r = new T(this.O(z()), this.O(z()), this, this.options)) : r = t[i], r._$AI(o), i++;
    i < t.length && (this._$AR(r && r._$AB.nextSibling, i), t.length = i);
  }
  _$AR(e = this._$AA.nextSibling, t) {
    var r;
    for ((r = this._$AP) == null ? void 0 : r.call(this, !1, !0, t); e !== this._$AB; ) {
      const i = ee(e).nextSibling;
      ee(e).remove(), e = i;
    }
  }
  setConnected(e) {
    var t;
    this._$AM === void 0 && (this._$Cv = e, (t = this._$AP) == null || t.call(this, e));
  }
}
class L {
  get tagName() {
    return this.element.tagName;
  }
  get _$AU() {
    return this._$AM._$AU;
  }
  constructor(e, t, r, i, o) {
    this.type = 1, this._$AH = c, this._$AN = void 0, this.element = e, this.name = t, this._$AM = i, this.options = o, r.length > 2 || r[0] !== "" || r[1] !== "" ? (this._$AH = Array(r.length - 1).fill(new String()), this.strings = r) : this._$AH = c;
  }
  _$AI(e, t = this, r, i) {
    const o = this.strings;
    let n = !1;
    if (o === void 0) e = S(this, e, t, 0), n = !U(e) || e !== this._$AH && e !== E, n && (this._$AH = e);
    else {
      const l = e;
      let a, d;
      for (e = o[0], a = 0; a < o.length - 1; a++) d = S(this, l[r + a], t, a), d === E && (d = this._$AH[a]), n || (n = !U(d) || d !== this._$AH[a]), d === c ? e = c : e !== c && (e += (d ?? "") + o[a + 1]), this._$AH[a] = d;
    }
    n && !i && this.j(e);
  }
  j(e) {
    e === c ? this.element.removeAttribute(this.name) : this.element.setAttribute(this.name, e ?? "");
  }
}
class ze extends L {
  constructor() {
    super(...arguments), this.type = 3;
  }
  j(e) {
    this.element[this.name] = e === c ? void 0 : e;
  }
}
class Ue extends L {
  constructor() {
    super(...arguments), this.type = 4;
  }
  j(e) {
    this.element.toggleAttribute(this.name, !!e && e !== c);
  }
}
class Re extends L {
  constructor(e, t, r, i, o) {
    super(e, t, r, i, o), this.type = 5;
  }
  _$AI(e, t = this) {
    if ((e = S(this, e, t, 0) ?? c) === E) return;
    const r = this._$AH, i = e === c && r !== c || e.capture !== r.capture || e.once !== r.once || e.passive !== r.passive, o = e !== c && (r === c || i);
    i && this.element.removeEventListener(this.name, this, r), o && this.element.addEventListener(this.name, this, e), this._$AH = e;
  }
  handleEvent(e) {
    var t;
    typeof this._$AH == "function" ? this._$AH.call(((t = this.options) == null ? void 0 : t.host) ?? this.element, e) : this._$AH.handleEvent(e);
  }
}
class Te {
  constructor(e, t, r) {
    this.element = e, this.type = 6, this._$AN = void 0, this._$AM = t, this.options = r;
  }
  get _$AU() {
    return this._$AM._$AU;
  }
  _$AI(e) {
    S(this, e);
  }
}
const W = O.litHtmlPolyfillSupport;
W == null || W(R, T), (O.litHtmlVersions ?? (O.litHtmlVersions = [])).push("3.3.2");
const Ne = (s, e, t) => {
  const r = (t == null ? void 0 : t.renderBefore) ?? e;
  let i = r._$litPart$;
  if (i === void 0) {
    const o = (t == null ? void 0 : t.renderBefore) ?? null;
    r._$litPart$ = i = new T(e.insertBefore(z(), o), o, void 0, t ?? {});
  }
  return i._$AI(s), i;
};
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const b = globalThis;
class k extends A {
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
    this.hasUpdated || (this.renderOptions.isConnected = this.isConnected), super.update(e), this._$Do = Ne(t, this.renderRoot, this.renderOptions);
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
}
var ce;
k._$litElement$ = !0, k.finalized = !0, (ce = b.litElementHydrateSupport) == null || ce.call(b, { LitElement: k });
const q = b.litElementPolyfillSupport;
q == null || q({ LitElement: k });
(b.litElementVersions ?? (b.litElementVersions = [])).push("4.2.2");
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const Me = (s) => (e, t) => {
  t !== void 0 ? t.addInitializer(() => {
    customElements.define(s, e);
  }) : customElements.define(s, e);
};
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const He = { attribute: !0, type: String, converter: D, reflect: !1, hasChanged: K }, De = (s = He, e, t) => {
  const { kind: r, metadata: i } = t;
  let o = globalThis.litPropertyMetadata.get(i);
  if (o === void 0 && globalThis.litPropertyMetadata.set(i, o = /* @__PURE__ */ new Map()), r === "setter" && ((s = Object.create(s)).wrapped = !0), o.set(t.name, s), r === "accessor") {
    const { name: n } = t;
    return { set(l) {
      const a = e.get.call(this);
      e.set.call(this, l), this.requestUpdate(n, a, s, !0, l);
    }, init(l) {
      return l !== void 0 && this.C(n, void 0, s, l), l;
    } };
  }
  if (r === "setter") {
    const { name: n } = t;
    return function(l) {
      const a = this[n];
      e.call(this, l), this.requestUpdate(n, a, s, !0, l);
    };
  }
  throw Error("Unsupported decorator location: " + r);
};
function fe(s) {
  return (e, t) => typeof t == "object" ? De(s, e, t) : ((r, i, o) => {
    const n = i.hasOwnProperty(o);
    return i.constructor.createProperty(o, r), n ? Object.getOwnPropertyDescriptor(i, o) : void 0;
  })(s, e, t);
}
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
function F(s) {
  return fe({ ...s, state: !0, attribute: !1 });
}
function je(s, e) {
  var i, o, n, l;
  const t = new Set(e.entities ?? []), r = e.entity ? (o = (i = s.entities) == null ? void 0 : i[e.entity]) == null ? void 0 : o.device_id : void 0;
  if (r)
    for (const a of Object.values(s.entities ?? {}))
      a.device_id === r && Array.isArray((l = (n = s.states[a.entity_id]) == null ? void 0 : n.attributes) == null ? void 0 : l.grade_details) && t.add(a.entity_id);
  return [...t];
}
function ae(s) {
  if (/^\d{2}\.\d{2}\.\d{4}$/.test(s)) {
    const [e, t, r] = s.split(".");
    return (/* @__PURE__ */ new Date(`${r}-${t}-${e}`)).getTime();
  }
  return new Date(s).getTime();
}
function x(s) {
  if (/^\d{2}\.\d{2}\.\d{4}$/.test(s)) return s;
  if (/^\d{4}-\d{2}-\d{2}$/.test(s)) {
    const [e, t, r] = s.split("-");
    return `${r}.${t}.${e}`;
  }
  return s;
}
function Le(s) {
  return x(s).replace(/^(\d{2}\.\d{2})\.\d{4}$/, "$1");
}
function Ie(s) {
  const e = s.correction_of;
  if (!e) return null;
  const t = [e.grade, e.category ? `(${e.category})` : null].filter(Boolean).join(" "), r = e.date ? ` z ${x(e.date)}` : "";
  return `poprawa oceny${t ? ` ${t}` : ""}${r}`;
}
function Be(s) {
  const e = s.corrected_by;
  if (!e) return null;
  const t = e.date ? ` z ${x(e.date)}` : "";
  return `poprawiona oceną${e.grade ? ` ${e.grade}` : ""}${t}`;
}
function We(s) {
  const e = s.correction_of;
  return e ? e.date ? `poprawa z ${Le(e.date)}` : "poprawa" : null;
}
function qe(s) {
  const e = s.corrected_by;
  return e ? e.grade ? `poprawiona na ${e.grade}` : "poprawiona" : null;
}
var Ge = Object.defineProperty, Ve = Object.getOwnPropertyDescriptor, N = (s, e, t, r) => {
  for (var i = r > 1 ? void 0 : r ? Ve(e, t) : e, o = s.length - 1, n; o >= 0; o--)
    (n = s[o]) && (i = (r ? n(e, t, i) : n(i)) || i);
  return r && i && Ge(e, t, i), i;
};
function le(s) {
  const e = s.toLowerCase();
  return e.includes("sprawdzian") || e.includes("test") ? { label: "SPRAWDZ", cssClass: "type-test" } : e.includes("kartkówka") || e.includes("kartkowka") ? { label: "KARTK", cssClass: "type-quiz" } : e.includes("praca klasow") || e.includes("praca kontrolna") ? { label: "PR.KL", cssClass: "type-classwork" } : e.includes("praca domow") ? { label: "PR.DOM", cssClass: "type-homework" } : e.includes("wypracowanie") ? { label: "WYPRAC", cssClass: "type-essay" } : { label: e.slice(0, 5).toUpperCase() || "INNE", cssClass: "type-other" };
}
let w = class extends k {
  constructor() {
    super(...arguments), this._selectedGrade = null, this._dlgOpen = !1;
  }
  static getStubConfig() {
    return { type: "librus-grades-card", entities: [], title: "Oceny" };
  }
  setConfig(s) {
    if (!s.entity && !Array.isArray(s.entities))
      throw new Error("wymagane entity (dowolna encja ucznia) lub entities (lista sensorów per-przedmiot)");
    this._config = s;
  }
  getCardSize() {
    return 6;
  }
  get _grades() {
    var r;
    if (!this.hass || !this._config) return [];
    const s = [];
    for (const i of je(this.hass, this._config)) {
      const o = this.hass.states[i], n = (r = o == null ? void 0 : o.attributes) == null ? void 0 : r.grade_details;
      n && s.push(...n);
    }
    const t = (this._config.only_recent ? s.filter((i) => i.is_recent) : s).sort((i, o) => ae(i.date) - ae(o.date));
    return (this._config.sort_order ?? "desc") === "desc" ? t.reverse() : t;
  }
  _openDialog(s) {
    this._selectedGrade = s, this._dlgOpen = !0;
  }
  _closeDialog() {
    this._dlgOpen = !1, this._selectedGrade = null;
  }
  _renderRow(s) {
    var d;
    const e = Ie(s), t = Be(s), r = e ?? t, i = We(s) ?? qe(s), { label: o, cssClass: n } = e ? { label: "POPRAWA", cssClass: "type-correction" } : le(s.category), l = (d = s.correction_of) == null ? void 0 : d.grade, a = [
      s.teacher,
      s.weight != null ? `waga ${s.weight}` : "",
      r ?? ""
    ].filter(Boolean).join(" · ");
    return u`
      <div
        class="grade-row ${s.is_recent ? "recent" : ""} ${t ? "superseded" : ""}"
        data-tooltip="${a || c}"
        role="button"
        tabindex="0"
        @click="${() => this._openDialog(s)}"
        @keydown="${(p) => p.key === "Enter" && this._openDialog(s)}"
      >
        <span class="grade-badge ${n}">${o}</span>
        <span class="grade-subject">
          <span class="grade-subject-name">${s.subject}</span>
          ${i ? u`<span class="grade-note">${i}</span>` : c}
        </span>
        <span
          class="grade-value"
          aria-label="${l ? `${l}, poprawiona na ${s.grade}` : s.grade}"
        >
          ${l ? u`<span class="grade-from">${l}</span><span class="grade-arrow" aria-hidden="true">→</span>` : c}
          <span class="${t ? "grade-struck" : ""}">${s.grade}</span>
        </span>
        <span class="grade-date">${x(s.date)}</span>
      </div>
    `;
  }
  _describeRef(s) {
    return [[s.grade, s.category ? `(${s.category})` : ""].filter(Boolean).join(" ") || "—", s.date ? x(s.date) : ""].filter(Boolean).join(" · ");
  }
  _renderDialog() {
    var e;
    const s = this._selectedGrade;
    return u`
      <ha-dialog
        .open=${this._dlgOpen}
        @closed=${() => this._closeDialog()}
      >
        ${s ? u`
          <div class="dlg-title">${s.subject}</div>
          <div class="dlg-category-row">${s.category}${s.category && s.date ? " · " : ""}${x(s.date)}</div>
          <div class="dlg-grade-large ${le(s.category).cssClass}">
            ${(e = s.correction_of) != null && e.grade ? u`<span class="dlg-from">${s.correction_of.grade}</span><span class="dlg-arrow" aria-hidden="true">→</span>` : c}
            <span class="${s.corrected_by ? "grade-struck" : ""}">${s.grade}</span>
          </div>
          <div class="dlg-details">
            ${s.teacher ? u`<div class="dlg-detail-row"><span class="dlg-detail-label">Nauczyciel</span><span>${s.teacher}</span></div>` : c}
            ${s.weight != null ? u`<div class="dlg-detail-row"><span class="dlg-detail-label">Waga</span><span>${s.weight}</span></div>` : c}
            ${s.counts != null ? u`<div class="dlg-detail-row"><span class="dlg-detail-label">Liczy do średniej</span><span>${s.counts ? "Tak" : "Nie"}</span></div>` : c}
            ${s.title ? u`<div class="dlg-detail-row dlg-detail-row--block"><span class="dlg-detail-label">Temat</span><span class="dlg-detail-text">${s.title}</span></div>` : c}
            ${s.correction_of ? u`<div class="dlg-detail-row"><span class="dlg-detail-label">Poprawa oceny</span><span>${this._describeRef(s.correction_of)}</span></div>` : c}
            ${s.corrected_by ? u`<div class="dlg-detail-row"><span class="dlg-detail-label">Poprawiona oceną</span><span>${this._describeRef(s.corrected_by)}</span></div>` : c}
            ${!s.correction_of && s.description ? u`<div class="dlg-detail-row"><span class="dlg-detail-label">Poprawa</span><span>${s.description}</span></div>` : c}
            ${s.comment ? u`<div class="dlg-detail-row dlg-detail-row--block"><span class="dlg-detail-label">Komentarz</span><span class="dlg-detail-text">${s.comment}</span></div>` : c}
          </div>
        ` : c}
      </ha-dialog>
    `;
  }
  render() {
    if (!this._config) return c;
    const s = this._grades, e = this._config.title ?? "Oceny", t = s.filter((i) => i.is_recent).length, r = this._config.height ?? 400;
    return u`
      <ha-card style="--card-h:${r}px">
        <div class="card-header">
          <span class="card-title">${e}</span>
          <span class="card-count">${s.length}${t > 0 ? u` <span class="new-badge">${t} nowe</span>` : c}</span>
        </div>
        <div class="grade-list">
          ${s.length === 0 ? u`<div class="empty">Brak ocen</div>` : s.map((i) => this._renderRow(i))}
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
    .grade-row:hover { background: var(--secondary-background-color); }
    .grade-row.recent { background: color-mix(in srgb, var(--primary-color) 8%, transparent); }
    .grade-row.recent:hover { background: color-mix(in srgb, var(--primary-color) 15%, transparent); }

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
    .type-correction { --badge-bg: #009688; }

    .grade-subject {
      display: flex;
      flex-direction: column;
      min-width: 0;
      font-size: 0.9em;
      color: var(--primary-text-color);
    }
    .grade-subject-name,
    .grade-note {
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
    .grade-note {
      font-size: 0.82em;
      color: var(--secondary-text-color);
    }
    .grade-value {
      font-size: 1em;
      font-weight: 600;
      color: var(--primary-text-color);
      min-width: 28px;
      text-align: right;
      white-space: nowrap;
    }
    .grade-from,
    .grade-struck {
      text-decoration: line-through;
    }
    .grade-from {
      font-weight: 400;
      color: var(--secondary-text-color);
    }
    .grade-arrow {
      margin: 0 4px;
      font-weight: 400;
      color: var(--secondary-text-color);
    }
    .grade-row.superseded { opacity: 0.65; }
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

    /* Zawartość ha-dialog (default slot = nasz shadow DOM) */
    .dlg-title {
      font-size: 1.1em;
      font-weight: 600;
      color: var(--primary-text-color);
      margin-bottom: 2px;
    }
    .dlg-category-row {
      font-size: 0.85em;
      color: var(--secondary-text-color);
      margin-bottom: 16px;
    }
    .dlg-grade-large {
      font-size: 2.8em;
      font-weight: 700;
      text-align: center;
      padding: 12px;
      border-radius: 8px;
      color: #fff;
      background: var(--badge-bg, var(--secondary-text-color, #888));
      margin-bottom: 16px;
    }
    .dlg-from {
      text-decoration: line-through;
      opacity: 0.7;
      font-weight: 400;
    }
    .dlg-arrow { margin: 0 12px; font-weight: 400; }
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
N([
  fe({ attribute: !1 })
], w.prototype, "hass", 2);
N([
  F()
], w.prototype, "_config", 2);
N([
  F()
], w.prototype, "_selectedGrade", 2);
N([
  F()
], w.prototype, "_dlgOpen", 2);
w = N([
  Me("librus-grades-card")
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
