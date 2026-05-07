/**
 * @license
 * Copyright 2019 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const L = globalThis, K = L.ShadowRoot && (L.ShadyCSS === void 0 || L.ShadyCSS.nativeShadow) && "adoptedStyleSheets" in Document.prototype && "replace" in CSSStyleSheet.prototype, J = Symbol(), Y = /* @__PURE__ */ new WeakMap();
let dt = class {
  constructor(t, e, i) {
    if (this._$cssResult$ = !0, i !== J) throw Error("CSSResult is not constructable. Use `unsafeCSS` or `css` instead.");
    this.cssText = t, this.t = e;
  }
  get styleSheet() {
    let t = this.o;
    const e = this.t;
    if (K && t === void 0) {
      const i = e !== void 0 && e.length === 1;
      i && (t = Y.get(e)), t === void 0 && ((this.o = t = new CSSStyleSheet()).replaceSync(this.cssText), i && Y.set(e, t));
    }
    return t;
  }
  toString() {
    return this.cssText;
  }
};
const mt = (s) => new dt(typeof s == "string" ? s : s + "", void 0, J), $t = (s, ...t) => {
  const e = s.length === 1 ? s[0] : t.reduce((i, r, o) => i + ((n) => {
    if (n._$cssResult$ === !0) return n.cssText;
    if (typeof n == "number") return n;
    throw Error("Value passed to 'css' function must be a 'css' function result: " + n + ". Use 'unsafeCSS' to pass non-literal values, but take care to ensure page security.");
  })(r) + s[o + 1], s[0]);
  return new dt(e, s, J);
}, vt = (s, t) => {
  if (K) s.adoptedStyleSheets = t.map((e) => e instanceof CSSStyleSheet ? e : e.styleSheet);
  else for (const e of t) {
    const i = document.createElement("style"), r = L.litNonce;
    r !== void 0 && i.setAttribute("nonce", r), i.textContent = e.cssText, s.appendChild(i);
  }
}, tt = K ? (s) => s : (s) => s instanceof CSSStyleSheet ? ((t) => {
  let e = "";
  for (const i of t.cssRules) e += i.cssText;
  return mt(e);
})(s) : s;
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const { is: yt, defineProperty: bt, getOwnPropertyDescriptor: At, getOwnPropertyNames: xt, getOwnPropertySymbols: wt, getPrototypeOf: Et } = Object, v = globalThis, et = v.trustedTypes, St = et ? et.emptyScript : "", B = v.reactiveElementPolyfillSupport, O = (s, t) => s, j = { toAttribute(s, t) {
  switch (t) {
    case Boolean:
      s = s ? St : null;
      break;
    case Object:
    case Array:
      s = s == null ? s : JSON.stringify(s);
  }
  return s;
}, fromAttribute(s, t) {
  let e = s;
  switch (t) {
    case Boolean:
      e = s !== null;
      break;
    case Number:
      e = s === null ? null : Number(s);
      break;
    case Object:
    case Array:
      try {
        e = JSON.parse(s);
      } catch {
        e = null;
      }
  }
  return e;
} }, X = (s, t) => !yt(s, t), st = { attribute: !0, type: String, converter: j, reflect: !1, useDefault: !1, hasChanged: X };
Symbol.metadata ?? (Symbol.metadata = Symbol("metadata")), v.litPropertyMetadata ?? (v.litPropertyMetadata = /* @__PURE__ */ new WeakMap());
let C = class extends HTMLElement {
  static addInitializer(t) {
    this._$Ei(), (this.l ?? (this.l = [])).push(t);
  }
  static get observedAttributes() {
    return this.finalize(), this._$Eh && [...this._$Eh.keys()];
  }
  static createProperty(t, e = st) {
    if (e.state && (e.attribute = !1), this._$Ei(), this.prototype.hasOwnProperty(t) && ((e = Object.create(e)).wrapped = !0), this.elementProperties.set(t, e), !e.noAccessor) {
      const i = Symbol(), r = this.getPropertyDescriptor(t, i, e);
      r !== void 0 && bt(this.prototype, t, r);
    }
  }
  static getPropertyDescriptor(t, e, i) {
    const { get: r, set: o } = At(this.prototype, t) ?? { get() {
      return this[e];
    }, set(n) {
      this[e] = n;
    } };
    return { get: r, set(n) {
      const a = r == null ? void 0 : r.call(this);
      o == null || o.call(this, n), this.requestUpdate(t, a, i);
    }, configurable: !0, enumerable: !0 };
  }
  static getPropertyOptions(t) {
    return this.elementProperties.get(t) ?? st;
  }
  static _$Ei() {
    if (this.hasOwnProperty(O("elementProperties"))) return;
    const t = Et(this);
    t.finalize(), t.l !== void 0 && (this.l = [...t.l]), this.elementProperties = new Map(t.elementProperties);
  }
  static finalize() {
    if (this.hasOwnProperty(O("finalized"))) return;
    if (this.finalized = !0, this._$Ei(), this.hasOwnProperty(O("properties"))) {
      const e = this.properties, i = [...xt(e), ...wt(e)];
      for (const r of i) this.createProperty(r, e[r]);
    }
    const t = this[Symbol.metadata];
    if (t !== null) {
      const e = litPropertyMetadata.get(t);
      if (e !== void 0) for (const [i, r] of e) this.elementProperties.set(i, r);
    }
    this._$Eh = /* @__PURE__ */ new Map();
    for (const [e, i] of this.elementProperties) {
      const r = this._$Eu(e, i);
      r !== void 0 && this._$Eh.set(r, e);
    }
    this.elementStyles = this.finalizeStyles(this.styles);
  }
  static finalizeStyles(t) {
    const e = [];
    if (Array.isArray(t)) {
      const i = new Set(t.flat(1 / 0).reverse());
      for (const r of i) e.unshift(tt(r));
    } else t !== void 0 && e.push(tt(t));
    return e;
  }
  static _$Eu(t, e) {
    const i = e.attribute;
    return i === !1 ? void 0 : typeof i == "string" ? i : typeof t == "string" ? t.toLowerCase() : void 0;
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
    for (const i of e.keys()) this.hasOwnProperty(i) && (t.set(i, this[i]), delete this[i]);
    t.size > 0 && (this._$Ep = t);
  }
  createRenderRoot() {
    const t = this.shadowRoot ?? this.attachShadow(this.constructor.shadowRootOptions);
    return vt(t, this.constructor.elementStyles), t;
  }
  connectedCallback() {
    var t;
    this.renderRoot ?? (this.renderRoot = this.createRenderRoot()), this.enableUpdating(!0), (t = this._$EO) == null || t.forEach((e) => {
      var i;
      return (i = e.hostConnected) == null ? void 0 : i.call(e);
    });
  }
  enableUpdating(t) {
  }
  disconnectedCallback() {
    var t;
    (t = this._$EO) == null || t.forEach((e) => {
      var i;
      return (i = e.hostDisconnected) == null ? void 0 : i.call(e);
    });
  }
  attributeChangedCallback(t, e, i) {
    this._$AK(t, i);
  }
  _$ET(t, e) {
    var o;
    const i = this.constructor.elementProperties.get(t), r = this.constructor._$Eu(t, i);
    if (r !== void 0 && i.reflect === !0) {
      const n = (((o = i.converter) == null ? void 0 : o.toAttribute) !== void 0 ? i.converter : j).toAttribute(e, i.type);
      this._$Em = t, n == null ? this.removeAttribute(r) : this.setAttribute(r, n), this._$Em = null;
    }
  }
  _$AK(t, e) {
    var o, n;
    const i = this.constructor, r = i._$Eh.get(t);
    if (r !== void 0 && this._$Em !== r) {
      const a = i.getPropertyOptions(r), l = typeof a.converter == "function" ? { fromAttribute: a.converter } : ((o = a.converter) == null ? void 0 : o.fromAttribute) !== void 0 ? a.converter : j;
      this._$Em = r;
      const h = l.fromAttribute(e, a.type);
      this[r] = h ?? ((n = this._$Ej) == null ? void 0 : n.get(r)) ?? h, this._$Em = null;
    }
  }
  requestUpdate(t, e, i, r = !1, o) {
    var n;
    if (t !== void 0) {
      const a = this.constructor;
      if (r === !1 && (o = this[t]), i ?? (i = a.getPropertyOptions(t)), !((i.hasChanged ?? X)(o, e) || i.useDefault && i.reflect && o === ((n = this._$Ej) == null ? void 0 : n.get(t)) && !this.hasAttribute(a._$Eu(t, i)))) return;
      this.C(t, e, i);
    }
    this.isUpdatePending === !1 && (this._$ES = this._$EP());
  }
  C(t, e, { useDefault: i, reflect: r, wrapped: o }, n) {
    i && !(this._$Ej ?? (this._$Ej = /* @__PURE__ */ new Map())).has(t) && (this._$Ej.set(t, n ?? e ?? this[t]), o !== !0 || n !== void 0) || (this._$AL.has(t) || (this.hasUpdated || i || (e = void 0), this._$AL.set(t, e)), r === !0 && this._$Em !== t && (this._$Eq ?? (this._$Eq = /* @__PURE__ */ new Set())).add(t));
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
    var i;
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
      t = this.shouldUpdate(e), t ? (this.willUpdate(e), (i = this._$EO) == null || i.forEach((r) => {
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
    (e = this._$EO) == null || e.forEach((i) => {
      var r;
      return (r = i.hostUpdated) == null ? void 0 : r.call(i);
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
C.elementStyles = [], C.shadowRootOptions = { mode: "open" }, C[O("elementProperties")] = /* @__PURE__ */ new Map(), C[O("finalized")] = /* @__PURE__ */ new Map(), B == null || B({ ReactiveElement: C }), (v.reactiveElementVersions ?? (v.reactiveElementVersions = [])).push("2.1.2");
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const z = globalThis, it = (s) => s, I = z.trustedTypes, rt = I ? I.createPolicy("lit-html", { createHTML: (s) => s }) : void 0, pt = "$lit$", $ = `lit$${Math.random().toFixed(9).slice(2)}$`, ut = "?" + $, Ct = `<${ut}>`, w = document, T = () => w.createComment(""), U = (s) => s === null || typeof s != "object" && typeof s != "function", Q = Array.isArray, Mt = (s) => Q(s) || typeof (s == null ? void 0 : s[Symbol.iterator]) == "function", F = `[ 	
\f\r]`, k = /<(?:(!--|\/[^a-zA-Z])|(\/?[a-zA-Z][^>\s]*)|(\/?$))/g, ot = /-->/g, nt = />/g, b = RegExp(`>|${F}(?:([^\\s"'>=/]+)(${F}*=${F}*(?:[^ 	
\f\r"'\`<>=]|("|')|))|$)`, "g"), at = /'/g, lt = /"/g, ft = /^(?:script|style|textarea|title)$/i, kt = (s) => (t, ...e) => ({ _$litType$: s, strings: t, values: e }), f = kt(1), E = Symbol.for("lit-noChange"), c = Symbol.for("lit-nothing"), ct = /* @__PURE__ */ new WeakMap(), A = w.createTreeWalker(w, 129);
function gt(s, t) {
  if (!Q(s) || !s.hasOwnProperty("raw")) throw Error("invalid template strings array");
  return rt !== void 0 ? rt.createHTML(t) : t;
}
const Ot = (s, t) => {
  const e = s.length - 1, i = [];
  let r, o = t === 2 ? "<svg>" : t === 3 ? "<math>" : "", n = k;
  for (let a = 0; a < e; a++) {
    const l = s[a];
    let h, p, d = -1, _ = 0;
    for (; _ < l.length && (n.lastIndex = _, p = n.exec(l), p !== null); ) _ = n.lastIndex, n === k ? p[1] === "!--" ? n = ot : p[1] !== void 0 ? n = nt : p[2] !== void 0 ? (ft.test(p[2]) && (r = RegExp("</" + p[2], "g")), n = b) : p[3] !== void 0 && (n = b) : n === b ? p[0] === ">" ? (n = r ?? k, d = -1) : p[1] === void 0 ? d = -2 : (d = n.lastIndex - p[2].length, h = p[1], n = p[3] === void 0 ? b : p[3] === '"' ? lt : at) : n === lt || n === at ? n = b : n === ot || n === nt ? n = k : (n = b, r = void 0);
    const m = n === b && s[a + 1].startsWith("/>") ? " " : "";
    o += n === k ? l + Ct : d >= 0 ? (i.push(h), l.slice(0, d) + pt + l.slice(d) + $ + m) : l + $ + (d === -2 ? a : m);
  }
  return [gt(s, o + (s[e] || "<?>") + (t === 2 ? "</svg>" : t === 3 ? "</math>" : "")), i];
};
class H {
  constructor({ strings: t, _$litType$: e }, i) {
    let r;
    this.parts = [];
    let o = 0, n = 0;
    const a = t.length - 1, l = this.parts, [h, p] = Ot(t, e);
    if (this.el = H.createElement(h, i), A.currentNode = this.el.content, e === 2 || e === 3) {
      const d = this.el.content.firstChild;
      d.replaceWith(...d.childNodes);
    }
    for (; (r = A.nextNode()) !== null && l.length < a; ) {
      if (r.nodeType === 1) {
        if (r.hasAttributes()) for (const d of r.getAttributeNames()) if (d.endsWith(pt)) {
          const _ = p[n++], m = r.getAttribute(d).split($), R = /([.?@])?(.*)/.exec(_);
          l.push({ type: 1, index: o, name: R[2], strings: m, ctor: R[1] === "." ? Pt : R[1] === "?" ? Tt : R[1] === "@" ? Ut : W }), r.removeAttribute(d);
        } else d.startsWith($) && (l.push({ type: 6, index: o }), r.removeAttribute(d));
        if (ft.test(r.tagName)) {
          const d = r.textContent.split($), _ = d.length - 1;
          if (_ > 0) {
            r.textContent = I ? I.emptyScript : "";
            for (let m = 0; m < _; m++) r.append(d[m], T()), A.nextNode(), l.push({ type: 2, index: ++o });
            r.append(d[_], T());
          }
        }
      } else if (r.nodeType === 8) if (r.data === ut) l.push({ type: 2, index: o });
      else {
        let d = -1;
        for (; (d = r.data.indexOf($, d + 1)) !== -1; ) l.push({ type: 7, index: o }), d += $.length - 1;
      }
      o++;
    }
  }
  static createElement(t, e) {
    const i = w.createElement("template");
    return i.innerHTML = t, i;
  }
}
function M(s, t, e = s, i) {
  var n, a;
  if (t === E) return t;
  let r = i !== void 0 ? (n = e._$Co) == null ? void 0 : n[i] : e._$Cl;
  const o = U(t) ? void 0 : t._$litDirective$;
  return (r == null ? void 0 : r.constructor) !== o && ((a = r == null ? void 0 : r._$AO) == null || a.call(r, !1), o === void 0 ? r = void 0 : (r = new o(s), r._$AT(s, e, i)), i !== void 0 ? (e._$Co ?? (e._$Co = []))[i] = r : e._$Cl = r), r !== void 0 && (t = M(s, r._$AS(s, t.values), r, i)), t;
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
    const { el: { content: e }, parts: i } = this._$AD, r = ((t == null ? void 0 : t.creationScope) ?? w).importNode(e, !0);
    A.currentNode = r;
    let o = A.nextNode(), n = 0, a = 0, l = i[0];
    for (; l !== void 0; ) {
      if (n === l.index) {
        let h;
        l.type === 2 ? h = new N(o, o.nextSibling, this, t) : l.type === 1 ? h = new l.ctor(o, l.name, l.strings, this, t) : l.type === 6 && (h = new Ht(o, this, t)), this._$AV.push(h), l = i[++a];
      }
      n !== (l == null ? void 0 : l.index) && (o = A.nextNode(), n++);
    }
    return A.currentNode = w, r;
  }
  p(t) {
    let e = 0;
    for (const i of this._$AV) i !== void 0 && (i.strings !== void 0 ? (i._$AI(t, i, e), e += i.strings.length - 2) : i._$AI(t[e])), e++;
  }
}
class N {
  get _$AU() {
    var t;
    return ((t = this._$AM) == null ? void 0 : t._$AU) ?? this._$Cv;
  }
  constructor(t, e, i, r) {
    this.type = 2, this._$AH = c, this._$AN = void 0, this._$AA = t, this._$AB = e, this._$AM = i, this.options = r, this._$Cv = (r == null ? void 0 : r.isConnected) ?? !0;
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
    t = M(this, t, e), U(t) ? t === c || t == null || t === "" ? (this._$AH !== c && this._$AR(), this._$AH = c) : t !== this._$AH && t !== E && this._(t) : t._$litType$ !== void 0 ? this.$(t) : t.nodeType !== void 0 ? this.T(t) : Mt(t) ? this.k(t) : this._(t);
  }
  O(t) {
    return this._$AA.parentNode.insertBefore(t, this._$AB);
  }
  T(t) {
    this._$AH !== t && (this._$AR(), this._$AH = this.O(t));
  }
  _(t) {
    this._$AH !== c && U(this._$AH) ? this._$AA.nextSibling.data = t : this.T(w.createTextNode(t)), this._$AH = t;
  }
  $(t) {
    var o;
    const { values: e, _$litType$: i } = t, r = typeof i == "number" ? this._$AC(t) : (i.el === void 0 && (i.el = H.createElement(gt(i.h, i.h[0]), this.options)), i);
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
    let i, r = 0;
    for (const o of t) r === e.length ? e.push(i = new N(this.O(T()), this.O(T()), this, this.options)) : i = e[r], i._$AI(o), r++;
    r < e.length && (this._$AR(i && i._$AB.nextSibling, r), e.length = r);
  }
  _$AR(t = this._$AA.nextSibling, e) {
    var i;
    for ((i = this._$AP) == null ? void 0 : i.call(this, !1, !0, e); t !== this._$AB; ) {
      const r = it(t).nextSibling;
      it(t).remove(), t = r;
    }
  }
  setConnected(t) {
    var e;
    this._$AM === void 0 && (this._$Cv = t, (e = this._$AP) == null || e.call(this, t));
  }
}
class W {
  get tagName() {
    return this.element.tagName;
  }
  get _$AU() {
    return this._$AM._$AU;
  }
  constructor(t, e, i, r, o) {
    this.type = 1, this._$AH = c, this._$AN = void 0, this.element = t, this.name = e, this._$AM = r, this.options = o, i.length > 2 || i[0] !== "" || i[1] !== "" ? (this._$AH = Array(i.length - 1).fill(new String()), this.strings = i) : this._$AH = c;
  }
  _$AI(t, e = this, i, r) {
    const o = this.strings;
    let n = !1;
    if (o === void 0) t = M(this, t, e, 0), n = !U(t) || t !== this._$AH && t !== E, n && (this._$AH = t);
    else {
      const a = t;
      let l, h;
      for (t = o[0], l = 0; l < o.length - 1; l++) h = M(this, a[i + l], e, l), h === E && (h = this._$AH[l]), n || (n = !U(h) || h !== this._$AH[l]), h === c ? t = c : t !== c && (t += (h ?? "") + o[l + 1]), this._$AH[l] = h;
    }
    n && !r && this.j(t);
  }
  j(t) {
    t === c ? this.element.removeAttribute(this.name) : this.element.setAttribute(this.name, t ?? "");
  }
}
class Pt extends W {
  constructor() {
    super(...arguments), this.type = 3;
  }
  j(t) {
    this.element[this.name] = t === c ? void 0 : t;
  }
}
class Tt extends W {
  constructor() {
    super(...arguments), this.type = 4;
  }
  j(t) {
    this.element.toggleAttribute(this.name, !!t && t !== c);
  }
}
class Ut extends W {
  constructor(t, e, i, r, o) {
    super(t, e, i, r, o), this.type = 5;
  }
  _$AI(t, e = this) {
    if ((t = M(this, t, e, 0) ?? c) === E) return;
    const i = this._$AH, r = t === c && i !== c || t.capture !== i.capture || t.once !== i.once || t.passive !== i.passive, o = t !== c && (i === c || r);
    r && this.element.removeEventListener(this.name, this, i), o && this.element.addEventListener(this.name, this, t), this._$AH = t;
  }
  handleEvent(t) {
    var e;
    typeof this._$AH == "function" ? this._$AH.call(((e = this.options) == null ? void 0 : e.host) ?? this.element, t) : this._$AH.handleEvent(t);
  }
}
class Ht {
  constructor(t, e, i) {
    this.element = t, this.type = 6, this._$AN = void 0, this._$AM = e, this.options = i;
  }
  get _$AU() {
    return this._$AM._$AU;
  }
  _$AI(t) {
    M(this, t);
  }
}
const q = z.litHtmlPolyfillSupport;
q == null || q(H, N), (z.litHtmlVersions ?? (z.litHtmlVersions = [])).push("3.3.2");
const Nt = (s, t, e) => {
  const i = (e == null ? void 0 : e.renderBefore) ?? t;
  let r = i._$litPart$;
  if (r === void 0) {
    const o = (e == null ? void 0 : e.renderBefore) ?? null;
    i._$litPart$ = r = new N(t.insertBefore(T(), o), o, void 0, e ?? {});
  }
  return r._$AI(s), r;
};
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const x = globalThis;
let P = class extends C {
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
    this.hasUpdated || (this.renderOptions.isConnected = this.isConnected), super.update(t), this._$Do = Nt(e, this.renderRoot, this.renderOptions);
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
var ht;
P._$litElement$ = !0, P.finalized = !0, (ht = x.litElementHydrateSupport) == null || ht.call(x, { LitElement: P });
const V = x.litElementPolyfillSupport;
V == null || V({ LitElement: P });
(x.litElementVersions ?? (x.litElementVersions = [])).push("4.2.2");
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const Rt = (s) => (t, e) => {
  e !== void 0 ? e.addInitializer(() => {
    customElements.define(s, t);
  }) : customElements.define(s, t);
};
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const Dt = { attribute: !0, type: String, converter: j, reflect: !1, hasChanged: X }, Lt = (s = Dt, t, e) => {
  const { kind: i, metadata: r } = e;
  let o = globalThis.litPropertyMetadata.get(r);
  if (o === void 0 && globalThis.litPropertyMetadata.set(r, o = /* @__PURE__ */ new Map()), i === "setter" && ((s = Object.create(s)).wrapped = !0), o.set(e.name, s), i === "accessor") {
    const { name: n } = e;
    return { set(a) {
      const l = t.get.call(this);
      t.set.call(this, a), this.requestUpdate(n, l, s, !0, a);
    }, init(a) {
      return a !== void 0 && this.C(n, void 0, s, a), a;
    } };
  }
  if (i === "setter") {
    const { name: n } = e;
    return function(a) {
      const l = this[n];
      t.call(this, a), this.requestUpdate(n, l, s, !0, a);
    };
  }
  throw Error("Unsupported decorator location: " + i);
};
function _t(s) {
  return (t, e) => typeof e == "object" ? Lt(s, t, e) : ((i, r, o) => {
    const n = r.hasOwnProperty(o);
    return r.constructor.createProperty(o, i), n ? Object.getOwnPropertyDescriptor(r, o) : void 0;
  })(s, t, e);
}
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
function y(s) {
  return _t({ ...s, state: !0, attribute: !1 });
}
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const jt = (s, t, e) => (e.configurable = !0, e.enumerable = !0, Reflect.decorate && typeof t != "object" && Object.defineProperty(s, t, e), e);
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
function It(s, t) {
  return (e, i, r) => {
    const o = (n) => {
      var a;
      return ((a = n.renderRoot) == null ? void 0 : a.querySelector(s)) ?? null;
    };
    return jt(e, i, { get() {
      return o(this);
    } });
  };
}
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const Wt = { CHILD: 2 }, Bt = (s) => (...t) => ({ _$litDirective$: s, values: t });
class Ft {
  constructor(t) {
  }
  get _$AU() {
    return this._$AM._$AU;
  }
  _$AT(t, e, i) {
    this._$Ct = t, this._$AM = e, this._$Ci = i;
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
class Z extends Ft {
  constructor(t) {
    if (super(t), this.it = c, t.type !== Wt.CHILD) throw Error(this.constructor.directiveName + "() can only be used in child bindings");
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
const qt = Bt(Z), Vt = /* @__PURE__ */ new Set([
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
function G(s, t) {
  if (s.nodeType === Node.TEXT_NODE) {
    t.appendChild(s.cloneNode());
    return;
  }
  if (s.nodeType !== Node.ELEMENT_NODE) return;
  const e = s, i = e.tagName.toLowerCase();
  if (!Vt.has(i)) {
    for (const a of e.childNodes)
      G(a, t);
    return;
  }
  const r = document.createElement(i), o = Zt[i];
  if (o) {
    for (const a of e.attributes)
      if (o.has(a.name)) {
        const l = a.value;
        if (a.name === "href" && /^\s*javascript:/i.test(l)) continue;
        r.setAttribute(a.name, l);
      }
  }
  i === "a" && (r.setAttribute("target", "_blank"), r.setAttribute("rel", "noopener noreferrer"));
  const n = document.createDocumentFragment();
  for (const a of e.childNodes)
    G(a, n);
  r.appendChild(n), t.appendChild(r);
}
function Gt(s) {
  const e = new DOMParser().parseFromString(s, "text/html"), i = document.createDocumentFragment();
  for (const o of e.body.childNodes)
    G(o, i);
  const r = document.createElement("div");
  return r.appendChild(i), r.innerHTML;
}
var Kt = Object.defineProperty, Jt = Object.getOwnPropertyDescriptor, g = (s, t, e, i) => {
  for (var r = i > 1 ? void 0 : i ? Jt(t, e) : t, o = s.length - 1, n; o >= 0; o--)
    (n = s[o]) && (r = (i ? n(t, e, r) : n(r)) || r);
  return i && r && Kt(t, e, r), r;
};
const S = 52, D = 4;
let u = class extends P {
  constructor() {
    super(...arguments), this._onlyUnread = !1, this._allMessages = [], this._totalCount = 0, this._scrollTop = 0, this._fetchingOffsets = /* @__PURE__ */ new Set(), this._selectedMsg = null, this._dialogContent = null, this._dialogLoading = !1;
  }
  static getStubConfig() {
    return { entity: "", entry_id: "", count: 10 };
  }
  setConfig(s) {
    if (!s.entity) throw new Error("entity is required");
    if (!s.entry_id) throw new Error("entry_id is required");
    this._config = s;
  }
  getCardSize() {
    return 4;
  }
  firstUpdated() {
    this._fetchAt(0);
  }
  updated(s) {
    super.updated(s), s.has("_onlyUnread") && this._onlyUnread && this._totalCount > 0 && this._fetchAll();
  }
  get _listHeight() {
    var s;
    return (((s = this._config) == null ? void 0 : s.count) ?? 10) * S;
  }
  get _visibleRows() {
    return Math.ceil(this._listHeight / S);
  }
  get _filterActive() {
    var s;
    return this._onlyUnread || !!((s = this._config) != null && s.only_unread);
  }
  // ---------------------------------------------------------------------------
  // Data loading
  // ---------------------------------------------------------------------------
  async _fetchAt(s) {
    if (this._fetchingOffsets.has(s) || !this.hass || !this._config || this._totalCount > 0 && s >= this._totalCount) return;
    this._fetchingOffsets.add(s);
    const t = this._config.count ?? 10;
    try {
      const e = await this.hass.callService(
        "librus_apix",
        "list_messages",
        { entry: this._config.entry_id, offset: s, count: t },
        void 0,
        !1,
        !0
      ), i = (e == null ? void 0 : e.response) ?? e, r = i.messages ?? [], o = i.total_count ?? r.length + s;
      if (o !== this._totalCount || this._allMessages.length !== o) {
        const a = new Array(o).fill(null);
        this._allMessages.forEach((l, h) => {
          l && (a[h] = l);
        }), this._allMessages = a, this._totalCount = o, this._filterActive && this._fetchAll();
      }
      const n = [...this._allMessages];
      r.forEach((a, l) => {
        s + l < n.length && (n[s + l] = a);
      }), this._allMessages = n;
    } finally {
      this._fetchingOffsets.delete(s);
    }
  }
  _fetchAll() {
    if (!this._config) return;
    const s = this._config.count ?? 10;
    for (let t = 0; t < this._totalCount; t += s) {
      if (this._fetchingOffsets.has(t)) continue;
      const e = Math.min(t + s, this._totalCount);
      this._allMessages.slice(t, e).some((r) => r === null) && this._fetchAt(t);
    }
  }
  _ensureLoaded(s, t) {
    var o;
    const e = ((o = this._config) == null ? void 0 : o.count) ?? 10, i = Math.floor(s / e), r = Math.floor(Math.max(0, t - 1) / e);
    for (let n = i; n <= r; n++) {
      const a = n * e;
      if (a >= this._totalCount) break;
      if (this._fetchingOffsets.has(a)) continue;
      const l = Math.min(a + e, this._totalCount);
      this._allMessages.slice(a, l).some((p) => p === null) && this._fetchAt(a);
    }
  }
  _onScroll(s) {
    const t = s.target.scrollTop;
    this._scrollRaf && cancelAnimationFrame(this._scrollRaf), this._scrollRaf = requestAnimationFrame(() => {
      this._scrollTop = t;
      const e = Math.max(0, Math.floor(t / S) - D), i = Math.min(
        this._totalCount,
        e + this._visibleRows + D * 2
      );
      this._ensureLoaded(e, i);
    });
  }
  // ---------------------------------------------------------------------------
  // Dialog
  // ---------------------------------------------------------------------------
  async _openDialog(s) {
    var t;
    if (!(!this.hass || !this._config)) {
      this._selectedMsg = s, this._dialogContent = null, this._dialogLoading = !0, (t = this._dialog) == null || t.showModal();
      try {
        const e = await this.hass.callService(
          "librus_apix",
          "fetch_message_content",
          { entry: this._config.entry_id, message_href: s.href },
          void 0,
          !0,
          !0
        ), i = (e == null ? void 0 : e.response) ?? e;
        this._dialogContent = i;
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
    var t;
    if (!this.hass || !this._config || !this._selectedMsg) return;
    const s = this._selectedMsg.href;
    await this.hass.callService("librus_apix", "dismiss_message_notification", {
      entry: this._config.entry_id,
      message_href: s
    }), this._allMessages = this._allMessages.map(
      (e) => (e == null ? void 0 : e.href) === s ? { ...e, notification_dismissed: !0 } : e
    ), (t = this._dialog) == null || t.close();
  }
  // ---------------------------------------------------------------------------
  // Render
  // ---------------------------------------------------------------------------
  render() {
    return this._config ? this._filterActive ? this._renderFiltered() : this._renderVirtual() : c;
  }
  _renderHeader() {
    var t;
    const s = ((t = this._config) == null ? void 0 : t.title) ?? "Wiadomości Librus";
    return f`
      <div class="card-header">
        <span class="card-title">${s}</span>
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
    const s = Math.max(0, Math.floor(this._scrollTop / S) - D), t = Math.min(
      this._totalCount,
      s + this._visibleRows + D * 2
    ), e = s * S, i = this._totalCount * S;
    return f`
      <ha-card>
        ${this._renderHeader()}
        <div
          class="message-list"
          style="height: ${this._listHeight}px"
          @scroll=${this._onScroll}
        >
          <div class="virtual-spacer" style="height: ${i}px">
            <div class="virtual-window" style="top: ${e}px">
              ${Array.from({ length: t - s }, (r, o) => {
      const n = this._allMessages[s + o];
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
    const s = this._allMessages.filter(
      (t) => t !== null && t.unread && !t.notification_dismissed
    );
    return f`
      <ha-card>
        ${this._renderHeader()}
        <div class="message-list" style="height: ${this._listHeight}px">
          ${s.length === 0 ? f`<div class="empty">Brak nieprzeczytanych wiadomości</div>` : s.map((t) => this._renderRow(t))}
        </div>
      </ha-card>
      ${this._renderDialog()}
    `;
  }
  _renderRow(s) {
    return f`
      <div
        class="message-item ${s.unread && !s.notification_dismissed ? "unread" : ""}"
        role="button"
        tabindex="0"
        @click=${() => this._openDialog(s)}
        @keydown=${(t) => t.key === "Enter" && this._openDialog(s)}
      >
        <div class="message-meta">
          <div class="message-sender">${s.sender}</div>
          <div class="message-title">
            ${s.has_attachment ? f`<ha-icon icon="mdi:paperclip" class="attach-icon"></ha-icon>` : c}
            ${s.title}
          </div>
        </div>
        <span class="message-date">${s.date}</span>
      </div>
    `;
  }
  _renderSkeleton() {
    return f`
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
    const s = this._selectedMsg;
    return f`
      <dialog
        @close=${() => {
      this._selectedMsg = null, this._dialogContent = null;
    }}
      >
        <div class="dlg-header">
          <div class="dlg-meta">
            <div class="dlg-sender">${s == null ? void 0 : s.sender}</div>
            <div class="dlg-title">${s == null ? void 0 : s.title}</div>
            <div class="dlg-date">${s == null ? void 0 : s.date}</div>
          </div>
          <ha-icon-button
            .label=${"Zamknij"}
            .path=${"M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"}
            @click=${() => {
      var t;
      return (t = this._dialog) == null ? void 0 : t.close();
    }}
          ></ha-icon-button>
        </div>
        <div class="dlg-body">
          ${this._dialogLoading ? f`<div class="dlg-loading">Ładowanie…</div>` : this._dialogContent ? f`<div class="dlg-content">
                  ${qt(Gt(this._dialogContent.content))}
                </div>` : c}
        </div>
        <div class="dlg-footer">
          ${s != null && s.has_attachment ? f`<span class="attach-note">
                <ha-icon icon="mdi:paperclip"></ha-icon>
                Zawiera załącznik
              </span>` : c}
          <div class="dlg-footer-actions">
            ${s && !s.notification_dismissed ? f`<button class="btn-dismiss" @click=${() => this._dismissFromDialog()}>
                  Usuń powiadomienie
                </button>` : c}
            <button class="btn-close" @click=${() => {
      var t;
      return (t = this._dialog) == null ? void 0 : t.close();
    }}>
              Zamknij
            </button>
          </div>
        </div>
      </dialog>
    `;
  }
};
u.styles = $t`
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
    .attach-note {
      display: flex;
      align-items: center;
      gap: 4px;
      color: var(--secondary-text-color);
      font-size: 0.85em;
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
    ha-icon-button {
      --mdc-icon-button-size: 32px;
      flex-shrink: 0;
    }
  `;
g([
  _t({ attribute: !1 })
], u.prototype, "hass", 2);
g([
  y()
], u.prototype, "_config", 2);
g([
  y()
], u.prototype, "_onlyUnread", 2);
g([
  y()
], u.prototype, "_allMessages", 2);
g([
  y()
], u.prototype, "_totalCount", 2);
g([
  y()
], u.prototype, "_scrollTop", 2);
g([
  y()
], u.prototype, "_selectedMsg", 2);
g([
  y()
], u.prototype, "_dialogContent", 2);
g([
  y()
], u.prototype, "_dialogLoading", 2);
g([
  It("dialog")
], u.prototype, "_dialog", 2);
u = g([
  Rt("librus-messages-card")
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
