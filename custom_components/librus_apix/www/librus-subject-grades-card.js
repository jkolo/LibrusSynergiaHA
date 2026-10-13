/**
 * @license
 * Copyright 2019 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const R = globalThis, G = R.ShadowRoot && (R.ShadyCSS === void 0 || R.ShadyCSS.nativeShadow) && "adoptedStyleSheets" in Document.prototype && "replace" in CSSStyleSheet.prototype, K = Symbol(), Q = /* @__PURE__ */ new WeakMap();
let he = class {
  constructor(e, t, i) {
    if (this._$cssResult$ = !0, i !== K) throw Error("CSSResult is not constructable. Use `unsafeCSS` or `css` instead.");
    this.cssText = e, this.t = t;
  }
  get styleSheet() {
    let e = this.o;
    const t = this.t;
    if (G && e === void 0) {
      const i = t !== void 0 && t.length === 1;
      i && (e = Q.get(t)), e === void 0 && ((this.o = e = new CSSStyleSheet()).replaceSync(this.cssText), i && Q.set(t, e));
    }
    return e;
  }
  toString() {
    return this.cssText;
  }
};
const _e = (s) => new he(typeof s == "string" ? s : s + "", void 0, K), ye = (s, ...e) => {
  const t = s.length === 1 ? s[0] : e.reduce((i, r, n) => i + ((o) => {
    if (o._$cssResult$ === !0) return o.cssText;
    if (typeof o == "number") return o;
    throw Error("Value passed to 'css' function must be a 'css' function result: " + o + ". Use 'unsafeCSS' to pass non-literal values, but take care to ensure page security.");
  })(r) + s[n + 1], s[0]);
  return new he(t, s, K);
}, me = (s, e) => {
  if (G) s.adoptedStyleSheets = e.map((t) => t instanceof CSSStyleSheet ? t : t.styleSheet);
  else for (const t of e) {
    const i = document.createElement("style"), r = R.litNonce;
    r !== void 0 && i.setAttribute("nonce", r), i.textContent = t.cssText, s.appendChild(i);
  }
}, X = G ? (s) => s : (s) => s instanceof CSSStyleSheet ? ((e) => {
  let t = "";
  for (const i of e.cssRules) t += i.cssText;
  return _e(t);
})(s) : s;
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const { is: ve, defineProperty: be, getOwnPropertyDescriptor: we, getOwnPropertyNames: Ae, getOwnPropertySymbols: xe, getPrototypeOf: Ee } = Object, _ = globalThis, Y = _.trustedTypes, Ce = Y ? Y.emptyScript : "", B = _.reactiveElementPolyfillSupport, S = (s, e) => s, j = { toAttribute(s, e) {
  switch (e) {
    case Boolean:
      s = s ? Ce : null;
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
} }, F = (s, e) => !ve(s, e), ee = { attribute: !0, type: String, converter: j, reflect: !1, useDefault: !1, hasChanged: F };
Symbol.metadata ?? (Symbol.metadata = Symbol("metadata")), _.litPropertyMetadata ?? (_.litPropertyMetadata = /* @__PURE__ */ new WeakMap());
let A = class extends HTMLElement {
  static addInitializer(e) {
    this._$Ei(), (this.l ?? (this.l = [])).push(e);
  }
  static get observedAttributes() {
    return this.finalize(), this._$Eh && [...this._$Eh.keys()];
  }
  static createProperty(e, t = ee) {
    if (t.state && (t.attribute = !1), this._$Ei(), this.prototype.hasOwnProperty(e) && ((t = Object.create(t)).wrapped = !0), this.elementProperties.set(e, t), !t.noAccessor) {
      const i = Symbol(), r = this.getPropertyDescriptor(e, i, t);
      r !== void 0 && be(this.prototype, e, r);
    }
  }
  static getPropertyDescriptor(e, t, i) {
    const { get: r, set: n } = we(this.prototype, e) ?? { get() {
      return this[t];
    }, set(o) {
      this[t] = o;
    } };
    return { get: r, set(o) {
      const l = r == null ? void 0 : r.call(this);
      n == null || n.call(this, o), this.requestUpdate(e, l, i);
    }, configurable: !0, enumerable: !0 };
  }
  static getPropertyOptions(e) {
    return this.elementProperties.get(e) ?? ee;
  }
  static _$Ei() {
    if (this.hasOwnProperty(S("elementProperties"))) return;
    const e = Ee(this);
    e.finalize(), e.l !== void 0 && (this.l = [...e.l]), this.elementProperties = new Map(e.elementProperties);
  }
  static finalize() {
    if (this.hasOwnProperty(S("finalized"))) return;
    if (this.finalized = !0, this._$Ei(), this.hasOwnProperty(S("properties"))) {
      const t = this.properties, i = [...Ae(t), ...xe(t)];
      for (const r of i) this.createProperty(r, t[r]);
    }
    const e = this[Symbol.metadata];
    if (e !== null) {
      const t = litPropertyMetadata.get(e);
      if (t !== void 0) for (const [i, r] of t) this.elementProperties.set(i, r);
    }
    this._$Eh = /* @__PURE__ */ new Map();
    for (const [t, i] of this.elementProperties) {
      const r = this._$Eu(t, i);
      r !== void 0 && this._$Eh.set(r, t);
    }
    this.elementStyles = this.finalizeStyles(this.styles);
  }
  static finalizeStyles(e) {
    const t = [];
    if (Array.isArray(e)) {
      const i = new Set(e.flat(1 / 0).reverse());
      for (const r of i) t.unshift(X(r));
    } else e !== void 0 && t.push(X(e));
    return t;
  }
  static _$Eu(e, t) {
    const i = t.attribute;
    return i === !1 ? void 0 : typeof i == "string" ? i : typeof e == "string" ? e.toLowerCase() : void 0;
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
    for (const i of t.keys()) this.hasOwnProperty(i) && (e.set(i, this[i]), delete this[i]);
    e.size > 0 && (this._$Ep = e);
  }
  createRenderRoot() {
    const e = this.shadowRoot ?? this.attachShadow(this.constructor.shadowRootOptions);
    return me(e, this.constructor.elementStyles), e;
  }
  connectedCallback() {
    var e;
    this.renderRoot ?? (this.renderRoot = this.createRenderRoot()), this.enableUpdating(!0), (e = this._$EO) == null || e.forEach((t) => {
      var i;
      return (i = t.hostConnected) == null ? void 0 : i.call(t);
    });
  }
  enableUpdating(e) {
  }
  disconnectedCallback() {
    var e;
    (e = this._$EO) == null || e.forEach((t) => {
      var i;
      return (i = t.hostDisconnected) == null ? void 0 : i.call(t);
    });
  }
  attributeChangedCallback(e, t, i) {
    this._$AK(e, i);
  }
  _$ET(e, t) {
    var n;
    const i = this.constructor.elementProperties.get(e), r = this.constructor._$Eu(e, i);
    if (r !== void 0 && i.reflect === !0) {
      const o = (((n = i.converter) == null ? void 0 : n.toAttribute) !== void 0 ? i.converter : j).toAttribute(t, i.type);
      this._$Em = e, o == null ? this.removeAttribute(r) : this.setAttribute(r, o), this._$Em = null;
    }
  }
  _$AK(e, t) {
    var n, o;
    const i = this.constructor, r = i._$Eh.get(e);
    if (r !== void 0 && this._$Em !== r) {
      const l = i.getPropertyOptions(r), a = typeof l.converter == "function" ? { fromAttribute: l.converter } : ((n = l.converter) == null ? void 0 : n.fromAttribute) !== void 0 ? l.converter : j;
      this._$Em = r;
      const h = a.fromAttribute(t, l.type);
      this[r] = h ?? ((o = this._$Ej) == null ? void 0 : o.get(r)) ?? h, this._$Em = null;
    }
  }
  requestUpdate(e, t, i, r = !1, n) {
    var o;
    if (e !== void 0) {
      const l = this.constructor;
      if (r === !1 && (n = this[e]), i ?? (i = l.getPropertyOptions(e)), !((i.hasChanged ?? F)(n, t) || i.useDefault && i.reflect && n === ((o = this._$Ej) == null ? void 0 : o.get(e)) && !this.hasAttribute(l._$Eu(e, i)))) return;
      this.C(e, t, i);
    }
    this.isUpdatePending === !1 && (this._$ES = this._$EP());
  }
  C(e, t, { useDefault: i, reflect: r, wrapped: n }, o) {
    i && !(this._$Ej ?? (this._$Ej = /* @__PURE__ */ new Map())).has(e) && (this._$Ej.set(e, o ?? t ?? this[e]), n !== !0 || o !== void 0) || (this._$AL.has(e) || (this.hasUpdated || i || (t = void 0), this._$AL.set(e, t)), r === !0 && this._$Em !== e && (this._$Eq ?? (this._$Eq = /* @__PURE__ */ new Set())).add(e));
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
    var i;
    if (!this.isUpdatePending) return;
    if (!this.hasUpdated) {
      if (this.renderRoot ?? (this.renderRoot = this.createRenderRoot()), this._$Ep) {
        for (const [n, o] of this._$Ep) this[n] = o;
        this._$Ep = void 0;
      }
      const r = this.constructor.elementProperties;
      if (r.size > 0) for (const [n, o] of r) {
        const { wrapped: l } = o, a = this[n];
        l !== !0 || this._$AL.has(n) || a === void 0 || this.C(n, void 0, o, a);
      }
    }
    let e = !1;
    const t = this._$AL;
    try {
      e = this.shouldUpdate(t), e ? (this.willUpdate(t), (i = this._$EO) == null || i.forEach((r) => {
        var n;
        return (n = r.hostUpdate) == null ? void 0 : n.call(r);
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
    (t = this._$EO) == null || t.forEach((i) => {
      var r;
      return (r = i.hostUpdated) == null ? void 0 : r.call(i);
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
A.elementStyles = [], A.shadowRootOptions = { mode: "open" }, A[S("elementProperties")] = /* @__PURE__ */ new Map(), A[S("finalized")] = /* @__PURE__ */ new Map(), B == null || B({ ReactiveElement: A }), (_.reactiveElementVersions ?? (_.reactiveElementVersions = [])).push("2.1.2");
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const P = globalThis, te = (s) => s, D = P.trustedTypes, se = D ? D.createPolicy("lit-html", { createHTML: (s) => s }) : void 0, pe = "$lit$", $ = `lit$${Math.random().toFixed(9).slice(2)}$`, ue = "?" + $, Se = `<${ue}>`, b = document, U = () => b.createComment(""), z = (s) => s === null || typeof s != "object" && typeof s != "function", Z = Array.isArray, Pe = (s) => Z(s) || typeof (s == null ? void 0 : s[Symbol.iterator]) == "function", I = `[ 	
\f\r]`, C = /<(?:(!--|\/[^a-zA-Z])|(\/?[a-zA-Z][^>\s]*)|(\/?$))/g, ie = /-->/g, re = />/g, y = RegExp(`>|${I}(?:([^\\s"'>=/]+)(${I}*=${I}*(?:[^ 	
\f\r"'\`<>=]|("|')|))|$)`, "g"), ne = /'/g, oe = /"/g, fe = /^(?:script|style|textarea|title)$/i, ke = (s) => (e, ...t) => ({ _$litType$: s, strings: e, values: t }), p = ke(1), x = Symbol.for("lit-noChange"), c = Symbol.for("lit-nothing"), ae = /* @__PURE__ */ new WeakMap(), m = b.createTreeWalker(b, 129);
function ge(s, e) {
  if (!Z(s) || !s.hasOwnProperty("raw")) throw Error("invalid template strings array");
  return se !== void 0 ? se.createHTML(e) : e;
}
const Oe = (s, e) => {
  const t = s.length - 1, i = [];
  let r, n = e === 2 ? "<svg>" : e === 3 ? "<math>" : "", o = C;
  for (let l = 0; l < t; l++) {
    const a = s[l];
    let h, u, d = -1, f = 0;
    for (; f < a.length && (o.lastIndex = f, u = o.exec(a), u !== null); ) f = o.lastIndex, o === C ? u[1] === "!--" ? o = ie : u[1] !== void 0 ? o = re : u[2] !== void 0 ? (fe.test(u[2]) && (r = RegExp("</" + u[2], "g")), o = y) : u[3] !== void 0 && (o = y) : o === y ? u[0] === ">" ? (o = r ?? C, d = -1) : u[1] === void 0 ? d = -2 : (d = o.lastIndex - u[2].length, h = u[1], o = u[3] === void 0 ? y : u[3] === '"' ? oe : ne) : o === oe || o === ne ? o = y : o === ie || o === re ? o = C : (o = y, r = void 0);
    const g = o === y && s[l + 1].startsWith("/>") ? " " : "";
    n += o === C ? a + Se : d >= 0 ? (i.push(h), a.slice(0, d) + pe + a.slice(d) + $ + g) : a + $ + (d === -2 ? l : g);
  }
  return [ge(s, n + (s[t] || "<?>") + (e === 2 ? "</svg>" : e === 3 ? "</math>" : "")), i];
};
class T {
  constructor({ strings: e, _$litType$: t }, i) {
    let r;
    this.parts = [];
    let n = 0, o = 0;
    const l = e.length - 1, a = this.parts, [h, u] = Oe(e, t);
    if (this.el = T.createElement(h, i), m.currentNode = this.el.content, t === 2 || t === 3) {
      const d = this.el.content.firstChild;
      d.replaceWith(...d.childNodes);
    }
    for (; (r = m.nextNode()) !== null && a.length < l; ) {
      if (r.nodeType === 1) {
        if (r.hasAttributes()) for (const d of r.getAttributeNames()) if (d.endsWith(pe)) {
          const f = u[o++], g = r.getAttribute(d).split($), H = /([.?@])?(.*)/.exec(f);
          a.push({ type: 1, index: n, name: H[2], strings: g, ctor: H[1] === "." ? ze : H[1] === "?" ? Te : H[1] === "@" ? Me : L }), r.removeAttribute(d);
        } else d.startsWith($) && (a.push({ type: 6, index: n }), r.removeAttribute(d));
        if (fe.test(r.tagName)) {
          const d = r.textContent.split($), f = d.length - 1;
          if (f > 0) {
            r.textContent = D ? D.emptyScript : "";
            for (let g = 0; g < f; g++) r.append(d[g], U()), m.nextNode(), a.push({ type: 2, index: ++n });
            r.append(d[f], U());
          }
        }
      } else if (r.nodeType === 8) if (r.data === ue) a.push({ type: 2, index: n });
      else {
        let d = -1;
        for (; (d = r.data.indexOf($, d + 1)) !== -1; ) a.push({ type: 7, index: n }), d += $.length - 1;
      }
      n++;
    }
  }
  static createElement(e, t) {
    const i = b.createElement("template");
    return i.innerHTML = e, i;
  }
}
function E(s, e, t = s, i) {
  var o, l;
  if (e === x) return e;
  let r = i !== void 0 ? (o = t._$Co) == null ? void 0 : o[i] : t._$Cl;
  const n = z(e) ? void 0 : e._$litDirective$;
  return (r == null ? void 0 : r.constructor) !== n && ((l = r == null ? void 0 : r._$AO) == null || l.call(r, !1), n === void 0 ? r = void 0 : (r = new n(s), r._$AT(s, t, i)), i !== void 0 ? (t._$Co ?? (t._$Co = []))[i] = r : t._$Cl = r), r !== void 0 && (e = E(s, r._$AS(s, e.values), r, i)), e;
}
class Ue {
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
    const { el: { content: t }, parts: i } = this._$AD, r = ((e == null ? void 0 : e.creationScope) ?? b).importNode(t, !0);
    m.currentNode = r;
    let n = m.nextNode(), o = 0, l = 0, a = i[0];
    for (; a !== void 0; ) {
      if (o === a.index) {
        let h;
        a.type === 2 ? h = new M(n, n.nextSibling, this, e) : a.type === 1 ? h = new a.ctor(n, a.name, a.strings, this, e) : a.type === 6 && (h = new Ne(n, this, e)), this._$AV.push(h), a = i[++l];
      }
      o !== (a == null ? void 0 : a.index) && (n = m.nextNode(), o++);
    }
    return m.currentNode = b, r;
  }
  p(e) {
    let t = 0;
    for (const i of this._$AV) i !== void 0 && (i.strings !== void 0 ? (i._$AI(e, i, t), t += i.strings.length - 2) : i._$AI(e[t])), t++;
  }
}
class M {
  get _$AU() {
    var e;
    return ((e = this._$AM) == null ? void 0 : e._$AU) ?? this._$Cv;
  }
  constructor(e, t, i, r) {
    this.type = 2, this._$AH = c, this._$AN = void 0, this._$AA = e, this._$AB = t, this._$AM = i, this.options = r, this._$Cv = (r == null ? void 0 : r.isConnected) ?? !0;
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
    e = E(this, e, t), z(e) ? e === c || e == null || e === "" ? (this._$AH !== c && this._$AR(), this._$AH = c) : e !== this._$AH && e !== x && this._(e) : e._$litType$ !== void 0 ? this.$(e) : e.nodeType !== void 0 ? this.T(e) : Pe(e) ? this.k(e) : this._(e);
  }
  O(e) {
    return this._$AA.parentNode.insertBefore(e, this._$AB);
  }
  T(e) {
    this._$AH !== e && (this._$AR(), this._$AH = this.O(e));
  }
  _(e) {
    this._$AH !== c && z(this._$AH) ? this._$AA.nextSibling.data = e : this.T(b.createTextNode(e)), this._$AH = e;
  }
  $(e) {
    var n;
    const { values: t, _$litType$: i } = e, r = typeof i == "number" ? this._$AC(e) : (i.el === void 0 && (i.el = T.createElement(ge(i.h, i.h[0]), this.options)), i);
    if (((n = this._$AH) == null ? void 0 : n._$AD) === r) this._$AH.p(t);
    else {
      const o = new Ue(r, this), l = o.u(this.options);
      o.p(t), this.T(l), this._$AH = o;
    }
  }
  _$AC(e) {
    let t = ae.get(e.strings);
    return t === void 0 && ae.set(e.strings, t = new T(e)), t;
  }
  k(e) {
    Z(this._$AH) || (this._$AH = [], this._$AR());
    const t = this._$AH;
    let i, r = 0;
    for (const n of e) r === t.length ? t.push(i = new M(this.O(U()), this.O(U()), this, this.options)) : i = t[r], i._$AI(n), r++;
    r < t.length && (this._$AR(i && i._$AB.nextSibling, r), t.length = r);
  }
  _$AR(e = this._$AA.nextSibling, t) {
    var i;
    for ((i = this._$AP) == null ? void 0 : i.call(this, !1, !0, t); e !== this._$AB; ) {
      const r = te(e).nextSibling;
      te(e).remove(), e = r;
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
  constructor(e, t, i, r, n) {
    this.type = 1, this._$AH = c, this._$AN = void 0, this.element = e, this.name = t, this._$AM = r, this.options = n, i.length > 2 || i[0] !== "" || i[1] !== "" ? (this._$AH = Array(i.length - 1).fill(new String()), this.strings = i) : this._$AH = c;
  }
  _$AI(e, t = this, i, r) {
    const n = this.strings;
    let o = !1;
    if (n === void 0) e = E(this, e, t, 0), o = !z(e) || e !== this._$AH && e !== x, o && (this._$AH = e);
    else {
      const l = e;
      let a, h;
      for (e = n[0], a = 0; a < n.length - 1; a++) h = E(this, l[i + a], t, a), h === x && (h = this._$AH[a]), o || (o = !z(h) || h !== this._$AH[a]), h === c ? e = c : e !== c && (e += (h ?? "") + n[a + 1]), this._$AH[a] = h;
    }
    o && !r && this.j(e);
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
class Te extends L {
  constructor() {
    super(...arguments), this.type = 4;
  }
  j(e) {
    this.element.toggleAttribute(this.name, !!e && e !== c);
  }
}
class Me extends L {
  constructor(e, t, i, r, n) {
    super(e, t, i, r, n), this.type = 5;
  }
  _$AI(e, t = this) {
    if ((e = E(this, e, t, 0) ?? c) === x) return;
    const i = this._$AH, r = e === c && i !== c || e.capture !== i.capture || e.once !== i.once || e.passive !== i.passive, n = e !== c && (i === c || r);
    r && this.element.removeEventListener(this.name, this, i), n && this.element.addEventListener(this.name, this, e), this._$AH = e;
  }
  handleEvent(e) {
    var t;
    typeof this._$AH == "function" ? this._$AH.call(((t = this.options) == null ? void 0 : t.host) ?? this.element, e) : this._$AH.handleEvent(e);
  }
}
class Ne {
  constructor(e, t, i) {
    this.element = e, this.type = 6, this._$AN = void 0, this._$AM = t, this.options = i;
  }
  get _$AU() {
    return this._$AM._$AU;
  }
  _$AI(e) {
    E(this, e);
  }
}
const q = P.litHtmlPolyfillSupport;
q == null || q(T, M), (P.litHtmlVersions ?? (P.litHtmlVersions = [])).push("3.3.2");
const He = (s, e, t) => {
  const i = (t == null ? void 0 : t.renderBefore) ?? e;
  let r = i._$litPart$;
  if (r === void 0) {
    const n = (t == null ? void 0 : t.renderBefore) ?? null;
    i._$litPart$ = r = new M(e.insertBefore(U(), n), n, void 0, t ?? {});
  }
  return r._$AI(s), r;
};
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const v = globalThis;
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
    this.hasUpdated || (this.renderOptions.isConnected = this.isConnected), super.update(e), this._$Do = He(t, this.renderRoot, this.renderOptions);
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
    return x;
  }
}
var de;
k._$litElement$ = !0, k.finalized = !0, (de = v.litElementHydrateSupport) == null || de.call(v, { LitElement: k });
const W = v.litElementPolyfillSupport;
W == null || W({ LitElement: k });
(v.litElementVersions ?? (v.litElementVersions = [])).push("4.2.2");
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const Re = (s) => (e, t) => {
  t !== void 0 ? t.addInitializer(() => {
    customElements.define(s, e);
  }) : customElements.define(s, e);
};
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const je = { attribute: !0, type: String, converter: j, reflect: !1, hasChanged: F }, De = (s = je, e, t) => {
  const { kind: i, metadata: r } = t;
  let n = globalThis.litPropertyMetadata.get(r);
  if (n === void 0 && globalThis.litPropertyMetadata.set(r, n = /* @__PURE__ */ new Map()), i === "setter" && ((s = Object.create(s)).wrapped = !0), n.set(t.name, s), i === "accessor") {
    const { name: o } = t;
    return { set(l) {
      const a = e.get.call(this);
      e.set.call(this, l), this.requestUpdate(o, a, s, !0, l);
    }, init(l) {
      return l !== void 0 && this.C(o, void 0, s, l), l;
    } };
  }
  if (i === "setter") {
    const { name: o } = t;
    return function(l) {
      const a = this[o];
      e.call(this, l), this.requestUpdate(o, a, s, !0, l);
    };
  }
  throw Error("Unsupported decorator location: " + i);
};
function $e(s) {
  return (e, t) => typeof t == "object" ? De(s, e, t) : ((i, r, n) => {
    const o = r.hasOwnProperty(n);
    return r.constructor.createProperty(n, i), o ? Object.getOwnPropertyDescriptor(r, n) : void 0;
  })(s, e, t);
}
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
function J(s) {
  return $e({ ...s, state: !0, attribute: !1 });
}
function le(s) {
  if (/^\d{2}\.\d{2}\.\d{4}$/.test(s)) {
    const [e, t, i] = s.split(".");
    return (/* @__PURE__ */ new Date(`${i}-${t}-${e}`)).getTime();
  }
  return new Date(s).getTime();
}
function O(s) {
  if (/^\d{2}\.\d{2}\.\d{4}$/.test(s)) return s;
  if (/^\d{4}-\d{2}-\d{2}$/.test(s)) {
    const [e, t, i] = s.split("-");
    return `${i}.${t}.${e}`;
  }
  return s;
}
function Le(s, e) {
  const t = s.correction_of;
  if (t != null && t.date)
    return e.find(
      (i) => {
        var r, n;
        return i !== s && i.date === t.date && i.grade === t.grade && ((r = i.corrected_by) == null ? void 0 : r.date) === s.date && ((n = i.corrected_by) == null ? void 0 : n.grade) === s.grade;
      }
    );
}
function Be(s, e, t) {
  const i = /* @__PURE__ */ new Set();
  for (let r = s; r && !i.has(r); r = t.get(r)) {
    if (r === e) return !0;
    i.add(r);
  }
  return !1;
}
function Ie(s) {
  const e = /* @__PURE__ */ new Map(), t = /* @__PURE__ */ new Set();
  for (const i of s) {
    const r = Le(i, s);
    !r || t.has(r) || Be(r, i, e) || (e.set(i, r), t.add(r));
  }
  return s.filter((i) => !t.has(i)).map((i) => {
    const r = [];
    for (let n = e.get(i); n; n = e.get(n))
      r.unshift(n);
    return { grade: i, replaced: r };
  });
}
function V(s) {
  const e = s.correction_of;
  if (!e) return null;
  const t = [e.grade, e.category ? `(${e.category})` : null].filter(Boolean).join(" "), i = e.date ? ` z ${O(e.date)}` : "";
  return `poprawa oceny${t ? ` ${t}` : ""}${i}`;
}
function qe(s) {
  const e = s.corrected_by;
  if (!e) return null;
  const t = e.date ? ` z ${O(e.date)}` : "";
  return `poprawiona oceną${e.grade ? ` ${e.grade}` : ""}${t}`;
}
var We = Object.defineProperty, Ve = Object.getOwnPropertyDescriptor, N = (s, e, t, i) => {
  for (var r = i > 1 ? void 0 : i ? Ve(e, t) : e, n = s.length - 1, o; n >= 0; n--)
    (o = s[n]) && (r = (i ? o(e, t, r) : o(r)) || r);
  return i && r && We(e, t, r), r;
};
function ce(s) {
  const e = s.toLowerCase();
  return e.includes("sprawdzian") || e.includes("test") ? { cssClass: "type-test" } : e.includes("kartkówka") || e.includes("kartkowka") ? { cssClass: "type-quiz" } : e.includes("praca klasow") || e.includes("praca kontrolna") ? { cssClass: "type-classwork" } : e.includes("praca domow") ? { cssClass: "type-homework" } : e.includes("wypracowanie") ? { cssClass: "type-essay" } : { cssClass: "type-other" };
}
let w = class extends k {
  constructor() {
    super(...arguments), this._selectedGrade = null, this._dlgOpen = !1;
  }
  static getStubConfig() {
    return { type: "librus-subject-grades-card", entity: "" };
  }
  setConfig(s) {
    if (!s.entity) throw new Error("entity jest wymagany");
    this._config = s;
  }
  getCardSize() {
    return 2;
  }
  get _grades() {
    var t;
    if (!this.hass || !this._config) return [];
    const s = this.hass.states[this._config.entity], e = (t = s == null ? void 0 : s.attributes) == null ? void 0 : t.grade_details;
    return e ? [...e].sort(
      (i, r) => le(i.date) - le(r.date)
    ) : [];
  }
  _openDialog(s) {
    this._selectedGrade = s, this._dlgOpen = !0;
  }
  _closeDialog() {
    this._dlgOpen = !1, this._selectedGrade = null;
  }
  _describeRef(s) {
    return [[s.grade, s.category ? `(${s.category})` : ""].filter(Boolean).join(" ") || "—", s.date ? O(s.date) : ""].filter(Boolean).join(" · ");
  }
  _renderChip(s) {
    const e = V(s) ?? qe(s), t = `${s.category}${s.date ? " · " + O(s.date) : ""}${e ? " — " + e : ""}`;
    return p`<span
      class="grade-chip ${ce(s.category).cssClass} ${s.is_recent ? "recent" : ""} ${s.corrected_by ? "superseded" : ""}"
      role="button"
      tabindex="0"
      title="${t}"
      @click="${() => this._openDialog(s)}"
      @keydown="${(i) => i.key === "Enter" && this._openDialog(s)}"
    >${s.grade}</span>`;
  }
  /** A grade, preceded by what it replaced: `1 → 6` (or `1 → 3 → 5` for a chain). */
  _renderEntry(s) {
    var r;
    const { grade: e, replaced: t } = s, i = t.length === 0 ? (r = e.correction_of) == null ? void 0 : r.grade : null;
    return t.length === 0 && !i ? this._renderChip(e) : p`<span class="chain" aria-label="${V(e) ?? ""}">
      ${t.map(
      (n) => p`${this._renderChip(n)}<span class="arrow" aria-hidden="true">→</span>`
    )}
      ${i ? p`<span class="grade-from" title="${V(e) ?? ""}">${i}</span><span class="arrow" aria-hidden="true">→</span>` : c}
      ${this._renderChip(e)}
    </span>`;
  }
  _renderDialog() {
    var e;
    const s = this._selectedGrade;
    return p`
      <ha-dialog .open=${this._dlgOpen} @closed=${() => this._closeDialog()}>
        ${s ? p`
              <div class="dlg-title">${s.subject || s.category}</div>
              <div class="dlg-category-row">
                ${s.category}${s.category && s.date ? " · " : ""}${O(s.date)}
              </div>
              <div class="dlg-grade-large ${ce(s.category).cssClass}">
                ${(e = s.correction_of) != null && e.grade ? p`<span class="dlg-from">${s.correction_of.grade}</span><span class="dlg-arrow" aria-hidden="true">→</span>` : c}
                <span class="${s.corrected_by ? "grade-struck" : ""}">${s.grade}</span>
              </div>
              <div class="dlg-details">
                ${s.teacher ? p`<div class="dlg-detail-row">
                      <span class="dlg-detail-label">Nauczyciel</span>
                      <span>${s.teacher}</span>
                    </div>` : c}
                ${s.weight != null ? p`<div class="dlg-detail-row">
                      <span class="dlg-detail-label">Waga</span>
                      <span>${s.weight}</span>
                    </div>` : c}
                ${s.counts != null ? p`<div class="dlg-detail-row">
                      <span class="dlg-detail-label">Liczy do średniej</span>
                      <span>${s.counts ? "Tak" : "Nie"}</span>
                    </div>` : c}
                ${s.title ? p`<div class="dlg-detail-row dlg-detail-row--block">
                      <span class="dlg-detail-label">Temat</span>
                      <span class="dlg-detail-text">${s.title}</span>
                    </div>` : c}
                ${s.correction_of ? p`<div class="dlg-detail-row">
                      <span class="dlg-detail-label">Poprawa oceny</span>
                      <span>${this._describeRef(s.correction_of)}</span>
                    </div>` : c}
                ${s.corrected_by ? p`<div class="dlg-detail-row">
                      <span class="dlg-detail-label">Poprawiona oceną</span>
                      <span>${this._describeRef(s.corrected_by)}</span>
                    </div>` : c}
                ${!s.correction_of && s.description ? p`<div class="dlg-detail-row">
                      <span class="dlg-detail-label">Poprawa</span>
                      <span>${s.description}</span>
                    </div>` : c}
                ${s.comment ? p`<div class="dlg-detail-row dlg-detail-row--block">
                      <span class="dlg-detail-label">Komentarz</span>
                      <span class="dlg-detail-text">${s.comment}</span>
                    </div>` : c}
              </div>
            ` : c}
      </ha-dialog>
    `;
  }
  render() {
    var r, n;
    if (!this._config) return c;
    const s = this._grades, e = (r = this.hass) == null ? void 0 : r.states[this._config.entity], t = this._config.title ?? ((n = e == null ? void 0 : e.attributes) == null ? void 0 : n.subject) ?? this._config.entity, i = s.filter((o) => o.is_recent).length;
    return p`
      <ha-card>
        <div class="card-header">
          <span class="card-title">${t}</span>
          ${i > 0 ? p`<span class="new-badge">${i} nowe</span>` : c}
        </div>
        <div class="grades-line">
          ${s.length === 0 ? p`<span class="empty">Brak ocen</span>` : Ie(s).map(
      (o, l) => p`
                  ${l > 0 ? p`<span class="sep">,</span>` : c}
                  ${this._renderEntry(o)}
                `
    )}
        </div>
      </ha-card>
      ${this._renderDialog()}
    `;
  }
};
w.styles = ye`
    :host { display: block; }

    ha-card {
      padding: 0;
    }

    .card-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 12px 16px 6px;
    }
    .card-title {
      font-size: 1em;
      font-weight: 500;
      color: var(--primary-text-color);
    }
    .new-badge {
      background: var(--primary-color);
      color: var(--text-primary-color, #fff);
      border-radius: 10px;
      padding: 1px 7px;
      font-size: 0.78em;
    }

    .grades-line {
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      gap: 2px;
      padding: 6px 16px 14px;
    }

    .sep {
      color: var(--secondary-text-color);
      font-size: 0.9em;
      line-height: 1;
      user-select: none;
    }

    .grade-chip {
      display: inline-block;
      padding: 3px 8px;
      border-radius: 12px;
      font-size: 0.9em;
      font-weight: 600;
      color: #fff;
      background: var(--chip-bg, var(--secondary-text-color, #888));
      cursor: pointer;
      transition: filter 0.12s;
      line-height: 1.3;
      outline: none;
    }
    .grade-chip:hover { filter: brightness(1.15); }
    .grade-chip:focus-visible {
      outline: 2px solid var(--primary-color);
      outline-offset: 2px;
    }
    .grade-chip.recent {
      box-shadow: 0 0 0 2px var(--primary-color);
    }
    .grade-chip.superseded {
      opacity: 0.55;
      text-decoration: line-through;
    }

    .chain {
      display: inline-flex;
      align-items: center;
      gap: 3px;
      padding: 1px 6px 1px 3px;
      border: 1px dashed var(--divider-color, #bbb);
      border-radius: 14px;
    }
    .arrow {
      color: var(--secondary-text-color);
      font-size: 0.9em;
      line-height: 1;
      user-select: none;
    }
    .grade-from {
      padding: 3px 4px;
      font-size: 0.9em;
      font-weight: 600;
      color: var(--secondary-text-color);
      text-decoration: line-through;
    }
    .grade-struck { text-decoration: line-through; }

    .type-test      { --chip-bg: var(--error-color, #f44336); }
    .type-quiz      { --chip-bg: #ff9800; }
    .type-classwork { --chip-bg: var(--info-color, #2196f3); }
    .type-homework  { --chip-bg: #4caf50; }
    .type-essay     { --chip-bg: #9c27b0; }
    .type-other     { --chip-bg: var(--secondary-text-color, #888); }

    .empty {
      font-size: 0.85em;
      color: var(--secondary-text-color);
    }

    /* Popup */
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
      background: var(--chip-bg, var(--secondary-text-color, #888));
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
    .dlg-detail-row--block { align-items: flex-start; }
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
  $e({ attribute: !1 })
], w.prototype, "hass", 2);
N([
  J()
], w.prototype, "_config", 2);
N([
  J()
], w.prototype, "_selectedGrade", 2);
N([
  J()
], w.prototype, "_dlgOpen", 2);
w = N([
  Re("librus-subject-grades-card")
], w);
window.customCards ?? (window.customCards = []);
window.customCards.push({
  type: "librus-subject-grades-card",
  name: "Librus — Oceny przedmiotu",
  description: "Kompaktowa karta z ocenami jednego przedmiotu: kolorowe chipy po przecinku, popup ze szczegółami po kliknięciu."
});
export {
  w as LibrusSubjectGradesCard
};
