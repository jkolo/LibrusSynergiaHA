/**
 * @license
 * Copyright 2019 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const D = globalThis, K = D.ShadowRoot && (D.ShadyCSS === void 0 || D.ShadyCSS.nativeShadow) && "adoptedStyleSheets" in Document.prototype && "replace" in CSSStyleSheet.prototype, J = Symbol(), Y = /* @__PURE__ */ new WeakMap();
let ht = class {
  constructor(t, e, s) {
    if (this._$cssResult$ = !0, s !== J) throw Error("CSSResult is not constructable. Use `unsafeCSS` or `css` instead.");
    this.cssText = t, this.t = e;
  }
  get styleSheet() {
    let t = this.o;
    const e = this.t;
    if (K && t === void 0) {
      const s = e !== void 0 && e.length === 1;
      s && (t = Y.get(e)), t === void 0 && ((this.o = t = new CSSStyleSheet()).replaceSync(this.cssText), s && Y.set(e, t));
    }
    return t;
  }
  toString() {
    return this.cssText;
  }
};
const mt = (i) => new ht(typeof i == "string" ? i : i + "", void 0, J), vt = (i, ...t) => {
  const e = i.length === 1 ? i[0] : t.reduce((s, r, o) => s + ((n) => {
    if (n._$cssResult$ === !0) return n.cssText;
    if (typeof n == "number") return n;
    throw Error("Value passed to 'css' function must be a 'css' function result: " + n + ". Use 'unsafeCSS' to pass non-literal values, but take care to ensure page security.");
  })(r) + i[o + 1], i[0]);
  return new ht(e, i, J);
}, $t = (i, t) => {
  if (K) i.adoptedStyleSheets = t.map((e) => e instanceof CSSStyleSheet ? e : e.styleSheet);
  else for (const e of t) {
    const s = document.createElement("style"), r = D.litNonce;
    r !== void 0 && s.setAttribute("nonce", r), s.textContent = e.cssText, i.appendChild(s);
  }
}, tt = K ? (i) => i : (i) => i instanceof CSSStyleSheet ? ((t) => {
  let e = "";
  for (const s of t.cssRules) e += s.cssText;
  return mt(e);
})(i) : i;
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const { is: yt, defineProperty: bt, getOwnPropertyDescriptor: wt, getOwnPropertyNames: xt, getOwnPropertySymbols: At, getPrototypeOf: Et } = Object, y = globalThis, et = y.trustedTypes, Ct = et ? et.emptyScript : "", I = y.reactiveElementPolyfillSupport, M = (i, t) => i, j = { toAttribute(i, t) {
  switch (t) {
    case Boolean:
      i = i ? Ct : null;
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
} }, X = (i, t) => !yt(i, t), it = { attribute: !0, type: String, converter: j, reflect: !1, useDefault: !1, hasChanged: X };
Symbol.metadata ?? (Symbol.metadata = Symbol("metadata")), y.litPropertyMetadata ?? (y.litPropertyMetadata = /* @__PURE__ */ new WeakMap());
let S = class extends HTMLElement {
  static addInitializer(t) {
    this._$Ei(), (this.l ?? (this.l = [])).push(t);
  }
  static get observedAttributes() {
    return this.finalize(), this._$Eh && [...this._$Eh.keys()];
  }
  static createProperty(t, e = it) {
    if (e.state && (e.attribute = !1), this._$Ei(), this.prototype.hasOwnProperty(t) && ((e = Object.create(e)).wrapped = !0), this.elementProperties.set(t, e), !e.noAccessor) {
      const s = Symbol(), r = this.getPropertyDescriptor(t, s, e);
      r !== void 0 && bt(this.prototype, t, r);
    }
  }
  static getPropertyDescriptor(t, e, s) {
    const { get: r, set: o } = wt(this.prototype, t) ?? { get() {
      return this[e];
    }, set(n) {
      this[e] = n;
    } };
    return { get: r, set(n) {
      const a = r == null ? void 0 : r.call(this);
      o == null || o.call(this, n), this.requestUpdate(t, a, s);
    }, configurable: !0, enumerable: !0 };
  }
  static getPropertyOptions(t) {
    return this.elementProperties.get(t) ?? it;
  }
  static _$Ei() {
    if (this.hasOwnProperty(M("elementProperties"))) return;
    const t = Et(this);
    t.finalize(), t.l !== void 0 && (this.l = [...t.l]), this.elementProperties = new Map(t.elementProperties);
  }
  static finalize() {
    if (this.hasOwnProperty(M("finalized"))) return;
    if (this.finalized = !0, this._$Ei(), this.hasOwnProperty(M("properties"))) {
      const e = this.properties, s = [...xt(e), ...At(e)];
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
      for (const r of s) e.unshift(tt(r));
    } else t !== void 0 && e.push(tt(t));
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
    return $t(t, this.constructor.elementStyles), t;
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
      const n = (((o = s.converter) == null ? void 0 : o.toAttribute) !== void 0 ? s.converter : j).toAttribute(e, s.type);
      this._$Em = t, n == null ? this.removeAttribute(r) : this.setAttribute(r, n), this._$Em = null;
    }
  }
  _$AK(t, e) {
    var o, n;
    const s = this.constructor, r = s._$Eh.get(t);
    if (r !== void 0 && this._$Em !== r) {
      const a = s.getPropertyOptions(r), l = typeof a.converter == "function" ? { fromAttribute: a.converter } : ((o = a.converter) == null ? void 0 : o.fromAttribute) !== void 0 ? a.converter : j;
      this._$Em = r;
      const d = l.fromAttribute(e, a.type);
      this[r] = d ?? ((n = this._$Ej) == null ? void 0 : n.get(r)) ?? d, this._$Em = null;
    }
  }
  requestUpdate(t, e, s, r = !1, o) {
    var n;
    if (t !== void 0) {
      const a = this.constructor;
      if (r === !1 && (o = this[t]), s ?? (s = a.getPropertyOptions(t)), !((s.hasChanged ?? X)(o, e) || s.useDefault && s.reflect && o === ((n = this._$Ej) == null ? void 0 : n.get(t)) && !this.hasAttribute(a._$Eu(t, s)))) return;
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
        const { wrapped: a } = n, l = this[o];
        a !== !0 || this._$AL.has(o) || l === void 0 || this.C(o, void 0, n, l);
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
S.elementStyles = [], S.shadowRootOptions = { mode: "open" }, S[M("elementProperties")] = /* @__PURE__ */ new Map(), S[M("finalized")] = /* @__PURE__ */ new Map(), I == null || I({ ReactiveElement: S }), (y.reactiveElementVersions ?? (y.reactiveElementVersions = [])).push("2.1.2");
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const z = globalThis, st = (i) => i, B = z.trustedTypes, rt = B ? B.createPolicy("lit-html", { createHTML: (i) => i }) : void 0, pt = "$lit$", $ = `lit$${Math.random().toFixed(9).slice(2)}$`, ut = "?" + $, St = `<${ut}>`, A = document, T = () => A.createComment(""), P = (i) => i === null || typeof i != "object" && typeof i != "function", Q = Array.isArray, kt = (i) => Q(i) || typeof (i == null ? void 0 : i[Symbol.iterator]) == "function", W = `[ 	
\f\r]`, U = /<(?:(!--|\/[^a-zA-Z])|(\/?[a-zA-Z][^>\s]*)|(\/?$))/g, ot = /-->/g, nt = />/g, b = RegExp(`>|${W}(?:([^\\s"'>=/]+)(${W}*=${W}*(?:[^ 	
\f\r"'\`<>=]|("|')|))|$)`, "g"), at = /'/g, lt = /"/g, gt = /^(?:script|style|textarea|title)$/i, Ut = (i) => (t, ...e) => ({ _$litType$: i, strings: t, values: e }), u = Ut(1), E = Symbol.for("lit-noChange"), c = Symbol.for("lit-nothing"), ct = /* @__PURE__ */ new WeakMap(), w = A.createTreeWalker(A, 129);
function _t(i, t) {
  if (!Q(i) || !i.hasOwnProperty("raw")) throw Error("invalid template strings array");
  return rt !== void 0 ? rt.createHTML(t) : t;
}
const Mt = (i, t) => {
  const e = i.length - 1, s = [];
  let r, o = t === 2 ? "<svg>" : t === 3 ? "<math>" : "", n = U;
  for (let a = 0; a < e; a++) {
    const l = i[a];
    let d, p, h = -1, m = 0;
    for (; m < l.length && (n.lastIndex = m, p = n.exec(l), p !== null); ) m = n.lastIndex, n === U ? p[1] === "!--" ? n = ot : p[1] !== void 0 ? n = nt : p[2] !== void 0 ? (gt.test(p[2]) && (r = RegExp("</" + p[2], "g")), n = b) : p[3] !== void 0 && (n = b) : n === b ? p[0] === ">" ? (n = r ?? U, h = -1) : p[1] === void 0 ? h = -2 : (h = n.lastIndex - p[2].length, d = p[1], n = p[3] === void 0 ? b : p[3] === '"' ? lt : at) : n === lt || n === at ? n = b : n === ot || n === nt ? n = U : (n = b, r = void 0);
    const v = n === b && i[a + 1].startsWith("/>") ? " " : "";
    o += n === U ? l + St : h >= 0 ? (s.push(d), l.slice(0, h) + pt + l.slice(h) + $ + v) : l + $ + (h === -2 ? a : v);
  }
  return [_t(i, o + (i[e] || "<?>") + (t === 2 ? "</svg>" : t === 3 ? "</math>" : "")), s];
};
class H {
  constructor({ strings: t, _$litType$: e }, s) {
    let r;
    this.parts = [];
    let o = 0, n = 0;
    const a = t.length - 1, l = this.parts, [d, p] = Mt(t, e);
    if (this.el = H.createElement(d, s), w.currentNode = this.el.content, e === 2 || e === 3) {
      const h = this.el.content.firstChild;
      h.replaceWith(...h.childNodes);
    }
    for (; (r = w.nextNode()) !== null && l.length < a; ) {
      if (r.nodeType === 1) {
        if (r.hasAttributes()) for (const h of r.getAttributeNames()) if (h.endsWith(pt)) {
          const m = p[n++], v = r.getAttribute(h).split($), L = /([.?@])?(.*)/.exec(m);
          l.push({ type: 1, index: o, name: L[2], strings: v, ctor: L[1] === "." ? Ot : L[1] === "?" ? Tt : L[1] === "@" ? Pt : F }), r.removeAttribute(h);
        } else h.startsWith($) && (l.push({ type: 6, index: o }), r.removeAttribute(h));
        if (gt.test(r.tagName)) {
          const h = r.textContent.split($), m = h.length - 1;
          if (m > 0) {
            r.textContent = B ? B.emptyScript : "";
            for (let v = 0; v < m; v++) r.append(h[v], T()), w.nextNode(), l.push({ type: 2, index: ++o });
            r.append(h[m], T());
          }
        }
      } else if (r.nodeType === 8) if (r.data === ut) l.push({ type: 2, index: o });
      else {
        let h = -1;
        for (; (h = r.data.indexOf($, h + 1)) !== -1; ) l.push({ type: 7, index: o }), h += $.length - 1;
      }
      o++;
    }
  }
  static createElement(t, e) {
    const s = A.createElement("template");
    return s.innerHTML = t, s;
  }
}
function k(i, t, e = i, s) {
  var n, a;
  if (t === E) return t;
  let r = s !== void 0 ? (n = e._$Co) == null ? void 0 : n[s] : e._$Cl;
  const o = P(t) ? void 0 : t._$litDirective$;
  return (r == null ? void 0 : r.constructor) !== o && ((a = r == null ? void 0 : r._$AO) == null || a.call(r, !1), o === void 0 ? r = void 0 : (r = new o(i), r._$AT(i, e, s)), s !== void 0 ? (e._$Co ?? (e._$Co = []))[s] = r : e._$Cl = r), r !== void 0 && (t = k(i, r._$AS(i, t.values), r, s)), t;
}
class zt {
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
    const { el: { content: e }, parts: s } = this._$AD, r = ((t == null ? void 0 : t.creationScope) ?? A).importNode(e, !0);
    w.currentNode = r;
    let o = w.nextNode(), n = 0, a = 0, l = s[0];
    for (; l !== void 0; ) {
      if (n === l.index) {
        let d;
        l.type === 2 ? d = new R(o, o.nextSibling, this, t) : l.type === 1 ? d = new l.ctor(o, l.name, l.strings, this, t) : l.type === 6 && (d = new Ht(o, this, t)), this._$AV.push(d), l = s[++a];
      }
      n !== (l == null ? void 0 : l.index) && (o = w.nextNode(), n++);
    }
    return w.currentNode = A, r;
  }
  p(t) {
    let e = 0;
    for (const s of this._$AV) s !== void 0 && (s.strings !== void 0 ? (s._$AI(t, s, e), e += s.strings.length - 2) : s._$AI(t[e])), e++;
  }
}
class R {
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
    t = k(this, t, e), P(t) ? t === c || t == null || t === "" ? (this._$AH !== c && this._$AR(), this._$AH = c) : t !== this._$AH && t !== E && this._(t) : t._$litType$ !== void 0 ? this.$(t) : t.nodeType !== void 0 ? this.T(t) : kt(t) ? this.k(t) : this._(t);
  }
  O(t) {
    return this._$AA.parentNode.insertBefore(t, this._$AB);
  }
  T(t) {
    this._$AH !== t && (this._$AR(), this._$AH = this.O(t));
  }
  _(t) {
    this._$AH !== c && P(this._$AH) ? this._$AA.nextSibling.data = t : this.T(A.createTextNode(t)), this._$AH = t;
  }
  $(t) {
    var o;
    const { values: e, _$litType$: s } = t, r = typeof s == "number" ? this._$AC(t) : (s.el === void 0 && (s.el = H.createElement(_t(s.h, s.h[0]), this.options)), s);
    if (((o = this._$AH) == null ? void 0 : o._$AD) === r) this._$AH.p(e);
    else {
      const n = new zt(r, this), a = n.u(this.options);
      n.p(e), this.T(a), this._$AH = n;
    }
  }
  _$AC(t) {
    let e = ct.get(t.strings);
    return e === void 0 && ct.set(t.strings, e = new H(t)), e;
  }
  k(t) {
    Q(this._$AH) || (this._$AH = [], this._$AR());
    const e = this._$AH;
    let s, r = 0;
    for (const o of t) r === e.length ? e.push(s = new R(this.O(T()), this.O(T()), this, this.options)) : s = e[r], s._$AI(o), r++;
    r < e.length && (this._$AR(s && s._$AB.nextSibling, r), e.length = r);
  }
  _$AR(t = this._$AA.nextSibling, e) {
    var s;
    for ((s = this._$AP) == null ? void 0 : s.call(this, !1, !0, e); t !== this._$AB; ) {
      const r = st(t).nextSibling;
      st(t).remove(), t = r;
    }
  }
  setConnected(t) {
    var e;
    this._$AM === void 0 && (this._$Cv = t, (e = this._$AP) == null || e.call(this, t));
  }
}
class F {
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
    if (o === void 0) t = k(this, t, e, 0), n = !P(t) || t !== this._$AH && t !== E, n && (this._$AH = t);
    else {
      const a = t;
      let l, d;
      for (t = o[0], l = 0; l < o.length - 1; l++) d = k(this, a[s + l], e, l), d === E && (d = this._$AH[l]), n || (n = !P(d) || d !== this._$AH[l]), d === c ? t = c : t !== c && (t += (d ?? "") + o[l + 1]), this._$AH[l] = d;
    }
    n && !r && this.j(t);
  }
  j(t) {
    t === c ? this.element.removeAttribute(this.name) : this.element.setAttribute(this.name, t ?? "");
  }
}
class Ot extends F {
  constructor() {
    super(...arguments), this.type = 3;
  }
  j(t) {
    this.element[this.name] = t === c ? void 0 : t;
  }
}
class Tt extends F {
  constructor() {
    super(...arguments), this.type = 4;
  }
  j(t) {
    this.element.toggleAttribute(this.name, !!t && t !== c);
  }
}
class Pt extends F {
  constructor(t, e, s, r, o) {
    super(t, e, s, r, o), this.type = 5;
  }
  _$AI(t, e = this) {
    if ((t = k(this, t, e, 0) ?? c) === E) return;
    const s = this._$AH, r = t === c && s !== c || t.capture !== s.capture || t.once !== s.once || t.passive !== s.passive, o = t !== c && (s === c || r);
    r && this.element.removeEventListener(this.name, this, s), o && this.element.addEventListener(this.name, this, t), this._$AH = t;
  }
  handleEvent(t) {
    var e;
    typeof this._$AH == "function" ? this._$AH.call(((e = this.options) == null ? void 0 : e.host) ?? this.element, t) : this._$AH.handleEvent(t);
  }
}
class Ht {
  constructor(t, e, s) {
    this.element = t, this.type = 6, this._$AN = void 0, this._$AM = e, this.options = s;
  }
  get _$AU() {
    return this._$AM._$AU;
  }
  _$AI(t) {
    k(this, t);
  }
}
const q = z.litHtmlPolyfillSupport;
q == null || q(H, R), (z.litHtmlVersions ?? (z.litHtmlVersions = [])).push("3.3.2");
const Rt = (i, t, e) => {
  const s = (e == null ? void 0 : e.renderBefore) ?? t;
  let r = s._$litPart$;
  if (r === void 0) {
    const o = (e == null ? void 0 : e.renderBefore) ?? null;
    s._$litPart$ = r = new R(t.insertBefore(T(), o), o, void 0, e ?? {});
  }
  return r._$AI(i), r;
};
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const x = globalThis;
let O = class extends S {
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
    this.hasUpdated || (this.renderOptions.isConnected = this.isConnected), super.update(t), this._$Do = Rt(e, this.renderRoot, this.renderOptions);
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
    return E;
  }
};
var dt;
O._$litElement$ = !0, O.finalized = !0, (dt = x.litElementHydrateSupport) == null || dt.call(x, { LitElement: O });
const V = x.litElementPolyfillSupport;
V == null || V({ LitElement: O });
(x.litElementVersions ?? (x.litElementVersions = [])).push("4.2.2");
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const Lt = (i) => (t, e) => {
  e !== void 0 ? e.addInitializer(() => {
    customElements.define(i, t);
  }) : customElements.define(i, t);
};
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const Nt = { attribute: !0, type: String, converter: j, reflect: !1, hasChanged: X }, Dt = (i = Nt, t, e) => {
  const { kind: s, metadata: r } = e;
  let o = globalThis.litPropertyMetadata.get(r);
  if (o === void 0 && globalThis.litPropertyMetadata.set(r, o = /* @__PURE__ */ new Map()), s === "setter" && ((i = Object.create(i)).wrapped = !0), o.set(e.name, i), s === "accessor") {
    const { name: n } = e;
    return { set(a) {
      const l = t.get.call(this);
      t.set.call(this, a), this.requestUpdate(n, l, i, !0, a);
    }, init(a) {
      return a !== void 0 && this.C(n, void 0, i, a), a;
    } };
  }
  if (s === "setter") {
    const { name: n } = e;
    return function(a) {
      const l = this[n];
      t.call(this, a), this.requestUpdate(n, l, i, !0, a);
    };
  }
  throw Error("Unsupported decorator location: " + s);
};
function ft(i) {
  return (t, e) => typeof e == "object" ? Dt(i, t, e) : ((s, r, o) => {
    const n = r.hasOwnProperty(o);
    return r.constructor.createProperty(o, s), n ? Object.getOwnPropertyDescriptor(r, o) : void 0;
  })(i, t, e);
}
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
function f(i) {
  return ft({ ...i, state: !0, attribute: !1 });
}
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const jt = (i, t, e) => (e.configurable = !0, e.enumerable = !0, Reflect.decorate && typeof t != "object" && Object.defineProperty(i, t, e), e);
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
function Bt(i, t) {
  return (e, s, r) => {
    const o = (n) => {
      var a;
      return ((a = n.renderRoot) == null ? void 0 : a.querySelector(i)) ?? null;
    };
    return jt(e, s, { get() {
      return o(this);
    } });
  };
}
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const Ft = { CHILD: 2 }, It = (i) => (...t) => ({ _$litDirective$: i, values: t });
class Wt {
  constructor(t) {
  }
  get _$AU() {
    return this._$AM._$AU;
  }
  _$AT(t, e, s) {
    this._$Ct = t, this._$AM = e, this._$Ci = s;
  }
  _$AS(t, e) {
    return this.update(t, e);
  }
  update(t, e) {
    return this.render(...e);
  }
}
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
class Z extends Wt {
  constructor(t) {
    if (super(t), this.it = c, t.type !== Ft.CHILD) throw Error(this.constructor.directiveName + "() can only be used in child bindings");
  }
  render(t) {
    if (t === c || t == null) return this._t = void 0, this.it = t;
    if (t === E) return t;
    if (typeof t != "string") throw Error(this.constructor.directiveName + "() called with a non-string value");
    if (t === this.it) return this._t;
    this.it = t;
    const e = [t];
    return e.raw = e, this._t = { _$litType$: this.constructor.resultType, strings: e, values: [] };
  }
}
Z.directiveName = "unsafeHTML", Z.resultType = 1;
const qt = It(Z), Vt = /* @__PURE__ */ new Set([
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
]), Zt = {
  a: /* @__PURE__ */ new Set(["href", "target"])
};
function G(i, t) {
  if (i.nodeType === Node.TEXT_NODE) {
    t.appendChild(i.cloneNode());
    return;
  }
  if (i.nodeType !== Node.ELEMENT_NODE) return;
  const e = i, s = e.tagName.toLowerCase();
  if (!Vt.has(s)) {
    for (const a of e.childNodes)
      G(a, t);
    return;
  }
  const r = document.createElement(s), o = Zt[s];
  if (o) {
    for (const a of e.attributes)
      if (o.has(a.name)) {
        const l = a.value;
        if (a.name === "href" && /^\s*javascript:/i.test(l)) continue;
        r.setAttribute(a.name, l);
      }
  }
  s === "a" && (r.setAttribute("target", "_blank"), r.setAttribute("rel", "noopener noreferrer"));
  const n = document.createDocumentFragment();
  for (const a of e.childNodes)
    G(a, n);
  r.appendChild(n), t.appendChild(r);
}
function Gt(i) {
  const e = new DOMParser().parseFromString(i, "text/html"), s = document.createDocumentFragment();
  for (const o of e.body.childNodes)
    G(o, s);
  const r = document.createElement("div");
  return r.appendChild(s), r.innerHTML;
}
var Kt = Object.defineProperty, Jt = Object.getOwnPropertyDescriptor, _ = (i, t, e, s) => {
  for (var r = s > 1 ? void 0 : s ? Jt(t, e) : t, o = i.length - 1, n; o >= 0; o--)
    (n = i[o]) && (r = (s ? n(t, e, r) : n(r)) || r);
  return s && r && Kt(t, e, r), r;
};
const C = 52, N = 4;
let g = class extends O {
  constructor() {
    super(...arguments), this._onlyUnread = !1, this._allMessages = [], this._totalCount = 0, this._scrollTop = 0, this._fetchingOffsets = /* @__PURE__ */ new Set(), this._selectedMsg = null, this._dialogContent = null, this._dialogLoading = !1, this._previewBlobUrl = null, this._previewContentType = null, this._previewFilename = null, this._previewLoadingUrl = null;
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
  firstUpdated() {
    this._fetchAt(0);
  }
  updated(i) {
    super.updated(i), i.has("_onlyUnread") && this._onlyUnread && this._totalCount > 0 && this._fetchAll();
  }
  get _listHeight() {
    var i;
    return (((i = this._config) == null ? void 0 : i.count) ?? 10) * C;
  }
  get _visibleRows() {
    return Math.ceil(this._listHeight / C);
  }
  get _filterActive() {
    var i;
    return this._onlyUnread || !!((i = this._config) != null && i.only_unread);
  }
  // ---------------------------------------------------------------------------
  // Data loading
  // ---------------------------------------------------------------------------
  async _fetchAt(i) {
    if (this._fetchingOffsets.has(i) || !this.hass || !this._config || this._totalCount > 0 && i >= this._totalCount) return;
    this._fetchingOffsets.add(i);
    const t = this._config.count ?? 10;
    try {
      const e = await this.hass.callService(
        "librus_apix",
        "list_messages",
        { entry: this._config.entry_id, offset: i, count: t },
        void 0,
        !1,
        !0
      ), s = (e == null ? void 0 : e.response) ?? e, r = s.messages ?? [], o = s.total_count ?? r.length + i;
      if (o !== this._totalCount || this._allMessages.length !== o) {
        const a = new Array(o).fill(null);
        this._allMessages.forEach((l, d) => {
          l && (a[d] = l);
        }), this._allMessages = a, this._totalCount = o, this._filterActive && this._fetchAll();
      }
      const n = [...this._allMessages];
      r.forEach((a, l) => {
        i + l < n.length && (n[i + l] = a);
      }), this._allMessages = n;
    } finally {
      this._fetchingOffsets.delete(i);
    }
  }
  _fetchAll() {
    if (!this._config) return;
    const i = this._config.count ?? 10;
    for (let t = 0; t < this._totalCount; t += i) {
      if (this._fetchingOffsets.has(t)) continue;
      const e = Math.min(t + i, this._totalCount);
      this._allMessages.slice(t, e).some((r) => r === null) && this._fetchAt(t);
    }
  }
  _ensureLoaded(i, t) {
    var o;
    const e = ((o = this._config) == null ? void 0 : o.count) ?? 10, s = Math.floor(i / e), r = Math.floor(Math.max(0, t - 1) / e);
    for (let n = s; n <= r; n++) {
      const a = n * e;
      if (a >= this._totalCount) break;
      if (this._fetchingOffsets.has(a)) continue;
      const l = Math.min(a + e, this._totalCount);
      this._allMessages.slice(a, l).some((p) => p === null) && this._fetchAt(a);
    }
  }
  _onScroll(i) {
    const t = i.target.scrollTop;
    this._scrollRaf && cancelAnimationFrame(this._scrollRaf), this._scrollRaf = requestAnimationFrame(() => {
      this._scrollTop = t;
      const e = Math.max(0, Math.floor(t / C) - N), s = Math.min(
        this._totalCount,
        e + this._visibleRows + N * 2
      );
      this._ensureLoaded(e, s);
    });
  }
  // ---------------------------------------------------------------------------
  // Dialog
  // ---------------------------------------------------------------------------
  async _openDialog(i) {
    var t;
    if (!(!this.hass || !this._config)) {
      this._selectedMsg = i, this._dialogContent = null, this._dialogLoading = !0, (t = this._dialog) == null || t.showModal();
      try {
        const e = await this.hass.callService(
          "librus_apix",
          "fetch_message_content",
          { entry: this._config.entry_id, message_href: i.href },
          void 0,
          !0,
          !0
        ), s = (e == null ? void 0 : e.response) ?? e;
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
    if (!this.hass || !this._config || !this._selectedMsg) return;
    const i = this._selectedMsg.href;
    await this.hass.callService("librus_apix", "dismiss_message_notification", {
      entry: this._config.entry_id,
      message_href: i
    });
    const t = { ...this._selectedMsg, notification_dismissed: !0 };
    this._allMessages = this._allMessages.map(
      (e) => (e == null ? void 0 : e.href) === i ? t : e
    ), this._selectedMsg = t;
  }
  async _restoreFromDialog() {
    if (!this.hass || !this._config || !this._selectedMsg) return;
    const i = this._selectedMsg.href;
    await this.hass.callService("librus_apix", "restore_message_notification", {
      entry: this._config.entry_id,
      message_href: i
    });
    const t = { ...this._selectedMsg, notification_dismissed: !1 };
    this._allMessages = this._allMessages.map(
      (e) => (e == null ? void 0 : e.href) === i ? t : e
    ), this._selectedMsg = t;
  }
  _isBrowserPreviewable(i) {
    return i === "application/pdf" || i.startsWith("image/") || i.startsWith("video/") || i.startsWith("audio/");
  }
  async _downloadAttachment(i, t) {
    if (!(!this.hass || !this._config)) {
      this._previewBlobUrl && (URL.revokeObjectURL(this._previewBlobUrl), this._previewBlobUrl = null, this._previewContentType = null, this._previewFilename = null), this._previewLoadingUrl = t;
      try {
        const e = await this.hass.callService(
          "librus_apix",
          "download_attachment",
          { entry: this._config.entry_id, attachment_url: t },
          void 0,
          !0,
          !0
        ), s = (e == null ? void 0 : e.response) ?? e, r = atob(s.data), o = new Uint8Array(r.length);
        for (let l = 0; l < r.length; l++) o[l] = r.charCodeAt(l);
        const n = new Blob([o], { type: s.content_type }), a = URL.createObjectURL(n);
        if (this._isBrowserPreviewable(s.content_type))
          this._previewBlobUrl = a, this._previewContentType = s.content_type, this._previewFilename = s.filename || i;
        else {
          const l = document.createElement("a");
          l.href = a, l.download = s.filename || i, l.click(), URL.revokeObjectURL(a);
        }
      } catch {
      } finally {
        this._previewLoadingUrl = null;
      }
    }
  }
  // ---------------------------------------------------------------------------
  // Render
  // ---------------------------------------------------------------------------
  render() {
    return this._config ? this._filterActive ? this._renderFiltered() : this._renderVirtual() : c;
  }
  _renderHeader() {
    var t;
    const i = ((t = this._config) == null ? void 0 : t.title) ?? "Wiadomości Librus";
    return u`
      <div class="card-header">
        <span class="card-title">${i}</span>
        <label class="filter-toggle">
          <input
            type="checkbox"
            .checked=${this._onlyUnread}
            @change=${(e) => {
      this._onlyUnread = e.target.checked;
    }}
          />
          tylko nieprzeczytane
        </label>
      </div>
    `;
  }
  // Tryb wirtualny — pełny virtual scroll dla niezafiltrowanej listy
  _renderVirtual() {
    const i = Math.max(0, Math.floor(this._scrollTop / C) - N), t = Math.min(
      this._totalCount,
      i + this._visibleRows + N * 2
    ), e = i * C, s = this._totalCount * C;
    return u`
      <ha-card>
        ${this._renderHeader()}
        <div
          class="message-list"
          style="height: ${this._listHeight}px"
          @scroll=${this._onScroll}
        >
          <div class="virtual-spacer" style="height: ${s}px">
            <div class="virtual-window" style="top: ${e}px">
              ${Array.from({ length: t - i }, (r, o) => {
      const n = this._allMessages[i + o];
      return n ? this._renderRow(n) : this._renderSkeleton();
    })}
            </div>
          </div>
        </div>
      </ha-card>
      ${this._renderDialog()}
    `;
  }
  // Tryb filtrowany — flat lista, eager-loaded
  _renderFiltered() {
    const i = this._allMessages.filter(
      (t) => t !== null && t.unread && !t.notification_dismissed
    );
    return u`
      <ha-card>
        ${this._renderHeader()}
        <div class="message-list" style="height: ${this._listHeight}px">
          ${i.length === 0 ? u`<div class="empty">Brak nieprzeczytanych wiadomości</div>` : i.map((t) => this._renderRow(t))}
        </div>
      </ha-card>
      ${this._renderDialog()}
    `;
  }
  _renderRow(i) {
    return u`
      <div
        class="message-item ${i.unread && !i.notification_dismissed ? "unread" : ""}"
        role="button"
        tabindex="0"
        @click=${() => this._openDialog(i)}
        @keydown=${(t) => t.key === "Enter" && this._openDialog(i)}
      >
        <div class="message-meta">
          <div class="message-sender">${i.sender}</div>
          <div class="message-title">
            ${i.has_attachment ? u`<ha-icon icon="mdi:paperclip" class="attach-icon"></ha-icon>` : c}
            ${i.title}
          </div>
        </div>
        <span class="message-date">${i.date}</span>
      </div>
    `;
  }
  _renderSkeleton() {
    return u`
      <div class="message-item skeleton">
        <div class="message-meta">
          <div class="skel sender"></div>
          <div class="skel title"></div>
        </div>
        <div class="skel date"></div>
      </div>
    `;
  }
  _renderDialog() {
    var t, e;
    const i = this._selectedMsg;
    return u`
      <dialog
        @close=${() => {
      this._selectedMsg = null, this._dialogContent = null, this._previewBlobUrl && (URL.revokeObjectURL(this._previewBlobUrl), this._previewBlobUrl = null, this._previewContentType = null, this._previewFilename = null);
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
      var s;
      return (s = this._dialog) == null ? void 0 : s.close();
    }}
          ></ha-icon-button>
        </div>
        <div class="dlg-body">
          ${this._dialogLoading ? u`<div class="dlg-loading">Ładowanie…</div>` : this._dialogContent ? u`<div class="dlg-content">
                  ${qt(Gt(this._dialogContent.content))}
                </div>` : c}
        </div>
        ${(e = (t = this._dialogContent) == null ? void 0 : t.attachments) != null && e.length ? u`<div class="dlg-attachments">
              <div class="dlg-attachments-header">
                <ha-icon icon="mdi:paperclip"></ha-icon>
                Załączniki
              </div>
              ${this._dialogContent.attachments.map(
      (s) => u`
                  <button
                    class="btn-attachment ${this._previewLoadingUrl === s.url ? "loading" : ""}"
                    ?disabled=${this._previewLoadingUrl !== null}
                    @click=${() => this._downloadAttachment(s.name, s.url)}
                  >
                    <ha-icon icon="${this._previewLoadingUrl === s.url ? "mdi:loading" : "mdi:download"}"></ha-icon>
                    ${s.name}
                  </button>
                `
    )}
            </div>` : c}
        ${this._previewBlobUrl && this._previewContentType ? u`<div class="dlg-preview">
              ${this._previewContentType === "application/pdf" ? u`<iframe
                    src="${this._previewBlobUrl}"
                    class="preview-iframe"
                    title="${this._previewFilename ?? ""}"
                  ></iframe>` : this._previewContentType.startsWith("image/") ? u`<img
                      src="${this._previewBlobUrl}"
                      class="preview-img"
                      alt="${this._previewFilename ?? ""}"
                    />` : this._previewContentType.startsWith("video/") ? u`<video
                        src="${this._previewBlobUrl}"
                        class="preview-video"
                        controls
                      ></video>` : u`<audio
                        src="${this._previewBlobUrl}"
                        class="preview-audio"
                        controls
                      ></audio>`}
              <a
                href="${this._previewBlobUrl}"
                download="${this._previewFilename ?? "plik"}"
                class="btn-download-preview"
              >
                <ha-icon icon="mdi:download"></ha-icon>
                Pobierz
              </a>
            </div>` : c}
        <div class="dlg-footer">
          <div class="dlg-footer-actions">
            ${i ? u`<button
                  class="${i.notification_dismissed ? "btn-restore" : "btn-dismiss"}"
                  @click=${i.notification_dismissed ? () => this._restoreFromDialog() : () => this._dismissFromDialog()}
                >
                  ${i.notification_dismissed ? "Przywróć powiadomienie" : "Oznacz jako przeczytane"}
                </button>` : c}
            <button class="btn-close" @click=${() => {
      var s;
      return (s = this._dialog) == null ? void 0 : s.close();
    }}>
              Zamknij
            </button>
          </div>
        </div>
      </dialog>
    `;
  }
};
g.styles = vt`
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

    /* Lista — stała wysokość, wewnętrzny scroll */
    .message-list {
      overflow-y: auto;
      overflow-x: hidden;
      scrollbar-width: thin;
      scrollbar-color: var(--scrollbar-thumb-color, var(--divider-color)) transparent;
    }

    /* Wirtualna przestrzeń — wysokość = total_count * ROW_HEIGHT, scroll tu */
    .virtual-spacer {
      position: relative;
    }

    /* Okno renderowanych wierszy — absolutnie pozycjonowane wewnątrz spacera */
    .virtual-window {
      position: absolute;
      left: 0;
      right: 0;
    }

    /* KLUCZOWE: każdy wiersz ma ściśle 52px — musi zgadzać się z ROW_HEIGHT w TS */
    .message-item {
      height: 52px;
      box-sizing: border-box;
      padding: 0 12px;
      display: flex;
      align-items: center;
      gap: 8px;
      cursor: pointer;
      border-radius: 6px;
      transition: background 0.12s;
      overflow: hidden;
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
      display: flex;
      flex-direction: column;
      justify-content: center;
      gap: 2px;
    }
    .message-sender {
      font-weight: 500;
      font-size: 0.88rem;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
      line-height: 1.2;
    }
    .message-title {
      font-size: 0.82rem;
      color: var(--secondary-text-color);
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
      line-height: 1.2;
    }
    .attach-icon {
      --mdi-icon-size: 13px;
      vertical-align: middle;
      color: var(--secondary-text-color);
      margin-right: 2px;
    }
    .message-date {
      font-size: 0.72rem;
      color: var(--disabled-text-color);
      white-space: nowrap;
      flex-shrink: 0;
    }

    /* Szkielet dla niezaładowanych wierszy */
    .message-item.skeleton {
      cursor: default;
      pointer-events: none;
    }
    .skel {
      border-radius: 4px;
      background: linear-gradient(
        90deg,
        color-mix(in srgb, var(--primary-text-color) 6%, transparent) 0%,
        color-mix(in srgb, var(--primary-text-color) 12%, transparent) 50%,
        color-mix(in srgb, var(--primary-text-color) 6%, transparent) 100%
      );
      background-size: 200% 100%;
      animation: shimmer 1.4s infinite;
    }
    @keyframes shimmer {
      0% { background-position: 200% 0; }
      100% { background-position: -200% 0; }
    }
    .skel.sender { width: 55%; height: 11px; margin-bottom: 4px; }
    .skel.title  { width: 38%; height: 10px; }
    .skel.date   { width: 60px; height: 9px; }

    .empty {
      text-align: center;
      padding: 16px;
      color: var(--secondary-text-color);
      font-size: 0.9rem;
    }

    /* Dialog */
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
    .dlg-meta { flex: 1; min-width: 0; }
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
    .dlg-date { font-size: 0.8em; color: var(--secondary-text-color); }
    .dlg-body { flex: 1; overflow-y: auto; padding: 16px 20px; }
    .dlg-loading { text-align: center; padding: 24px; color: var(--secondary-text-color); }
    .dlg-content { line-height: 1.6; font-size: 0.95em; }
    .dlg-content p { margin: 0 0 0.8em; }
    .dlg-content a { color: var(--primary-color); }
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
    .dlg-attachments {
      padding: 10px 20px;
      border-top: 1px solid var(--divider-color);
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
      align-items: center;
      flex-shrink: 0;
    }
    .dlg-attachments-header {
      display: flex;
      align-items: center;
      gap: 4px;
      font-size: 0.82em;
      color: var(--secondary-text-color);
      font-weight: 500;
      width: 100%;
    }
    .btn-attachment {
      display: flex;
      align-items: center;
      gap: 4px;
      background: color-mix(in srgb, var(--primary-color) 10%, transparent);
      color: var(--primary-color);
      border: 1px solid color-mix(in srgb, var(--primary-color) 30%, transparent);
      padding: 5px 10px;
      border-radius: 4px;
      cursor: pointer;
      font-size: 0.85em;
      max-width: 100%;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
    .btn-attachment:hover {
      background: color-mix(in srgb, var(--primary-color) 18%, transparent);
    }
    .btn-attachment:disabled { opacity: 0.6; cursor: default; }
    .btn-attachment.loading ha-icon { animation: spin 1s linear infinite; }
    @keyframes spin { to { transform: rotate(360deg); } }

    /* Podgląd inline załącznika */
    .dlg-preview {
      border-top: 1px solid var(--divider-color);
      padding: 12px 20px;
      display: flex;
      flex-direction: column;
      gap: 8px;
      flex-shrink: 0;
      max-height: 55vh;
    }
    .preview-iframe {
      width: 100%;
      flex: 1;
      min-height: 300px;
      border: none;
      border-radius: 4px;
      background: var(--secondary-background-color);
    }
    .preview-img {
      max-width: 100%;
      max-height: 45vh;
      object-fit: contain;
      border-radius: 4px;
      display: block;
      margin: 0 auto;
    }
    .preview-video, .preview-audio {
      width: 100%;
      border-radius: 4px;
    }
    .btn-download-preview {
      display: inline-flex;
      align-items: center;
      gap: 4px;
      padding: 6px 14px;
      background: var(--primary-color);
      color: var(--text-primary-color, white);
      border-radius: 4px;
      text-decoration: none;
      font-size: 0.85em;
      align-self: flex-end;
    }
    .dlg-footer-actions { display: flex; gap: 8px; margin-left: auto; }
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
    .btn-restore {
      background: var(--secondary-background-color);
      color: var(--secondary-text-color);
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
_([
  ft({ attribute: !1 })
], g.prototype, "hass", 2);
_([
  f()
], g.prototype, "_config", 2);
_([
  f()
], g.prototype, "_onlyUnread", 2);
_([
  f()
], g.prototype, "_allMessages", 2);
_([
  f()
], g.prototype, "_totalCount", 2);
_([
  f()
], g.prototype, "_scrollTop", 2);
_([
  f()
], g.prototype, "_selectedMsg", 2);
_([
  f()
], g.prototype, "_dialogContent", 2);
_([
  f()
], g.prototype, "_dialogLoading", 2);
_([
  Bt("dialog")
], g.prototype, "_dialog", 2);
_([
  f()
], g.prototype, "_previewBlobUrl", 2);
_([
  f()
], g.prototype, "_previewContentType", 2);
_([
  f()
], g.prototype, "_previewFilename", 2);
_([
  f()
], g.prototype, "_previewLoadingUrl", 2);
g = _([
  Lt("librus-messages-card")
], g);
window.customCards ?? (window.customCards = []);
window.customCards.push({
  type: "librus-messages-card",
  name: "Librus — Wiadomości",
  description: "Wiadomości szkolne z podglądem treści i zarządzaniem powiadomieniami."
});
export {
  g as LibrusMessagesCard
};
