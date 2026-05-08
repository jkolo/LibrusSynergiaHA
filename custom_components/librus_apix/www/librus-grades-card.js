/**
 * @license
 * Copyright 2019 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const N = globalThis, q = N.ShadowRoot && (N.ShadyCSS === void 0 || N.ShadyCSS.nativeShadow) && "adoptedStyleSheets" in Document.prototype && "replace" in CSSStyleSheet.prototype, V = Symbol(), F = /* @__PURE__ */ new WeakMap();
let dt = class {
  constructor(t, e, s) {
    if (this._$cssResult$ = !0, s !== V) throw Error("CSSResult is not constructable. Use `unsafeCSS` or `css` instead.");
    this.cssText = t, this.t = e;
  }
  get styleSheet() {
    let t = this.o;
    const e = this.t;
    if (q && t === void 0) {
      const s = e !== void 0 && e.length === 1;
      s && (t = F.get(e)), t === void 0 && ((this.o = t = new CSSStyleSheet()).replaceSync(this.cssText), s && F.set(e, t));
    }
    return t;
  }
  toString() {
    return this.cssText;
  }
};
const $t = (i) => new dt(typeof i == "string" ? i : i + "", void 0, V), _t = (i, ...t) => {
  const e = i.length === 1 ? i[0] : t.reduce((s, r, o) => s + ((n) => {
    if (n._$cssResult$ === !0) return n.cssText;
    if (typeof n == "number") return n;
    throw Error("Value passed to 'css' function must be a 'css' function result: " + n + ". Use 'unsafeCSS' to pass non-literal values, but take care to ensure page security.");
  })(r) + i[o + 1], i[0]);
  return new dt(e, i, V);
}, yt = (i, t) => {
  if (q) i.adoptedStyleSheets = t.map((e) => e instanceof CSSStyleSheet ? e : e.styleSheet);
  else for (const e of t) {
    const s = document.createElement("style"), r = N.litNonce;
    r !== void 0 && s.setAttribute("nonce", r), s.textContent = e.cssText, i.appendChild(s);
  }
}, J = q ? (i) => i : (i) => i instanceof CSSStyleSheet ? ((t) => {
  let e = "";
  for (const s of t.cssRules) e += s.cssText;
  return $t(e);
})(i) : i;
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const { is: mt, defineProperty: vt, getOwnPropertyDescriptor: bt, getOwnPropertyNames: wt, getOwnPropertySymbols: At, getPrototypeOf: xt } = Object, _ = globalThis, X = _.trustedTypes, Et = X ? X.emptyScript : "", L = _.reactiveElementPolyfillSupport, C = (i, t) => i, H = { toAttribute(i, t) {
  switch (t) {
    case Boolean:
      i = i ? Et : null;
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
} }, G = (i, t) => !mt(i, t), Y = { attribute: !0, type: String, converter: H, reflect: !1, useDefault: !1, hasChanged: G };
Symbol.metadata ?? (Symbol.metadata = Symbol("metadata")), _.litPropertyMetadata ?? (_.litPropertyMetadata = /* @__PURE__ */ new WeakMap());
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
      r !== void 0 && vt(this.prototype, t, r);
    }
  }
  static getPropertyDescriptor(t, e, s) {
    const { get: r, set: o } = bt(this.prototype, t) ?? { get() {
      return this[e];
    }, set(n) {
      this[e] = n;
    } };
    return { get: r, set(n) {
      const l = r == null ? void 0 : r.call(this);
      o == null || o.call(this, n), this.requestUpdate(t, l, s);
    }, configurable: !0, enumerable: !0 };
  }
  static getPropertyOptions(t) {
    return this.elementProperties.get(t) ?? Y;
  }
  static _$Ei() {
    if (this.hasOwnProperty(C("elementProperties"))) return;
    const t = xt(this);
    t.finalize(), t.l !== void 0 && (this.l = [...t.l]), this.elementProperties = new Map(t.elementProperties);
  }
  static finalize() {
    if (this.hasOwnProperty(C("finalized"))) return;
    if (this.finalized = !0, this._$Ei(), this.hasOwnProperty(C("properties"))) {
      const e = this.properties, s = [...wt(e), ...At(e)];
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
      for (const r of s) e.unshift(J(r));
    } else t !== void 0 && e.push(J(t));
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
    return yt(t, this.constructor.elementStyles), t;
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
      const n = (((o = s.converter) == null ? void 0 : o.toAttribute) !== void 0 ? s.converter : H).toAttribute(e, s.type);
      this._$Em = t, n == null ? this.removeAttribute(r) : this.setAttribute(r, n), this._$Em = null;
    }
  }
  _$AK(t, e) {
    var o, n;
    const s = this.constructor, r = s._$Eh.get(t);
    if (r !== void 0 && this._$Em !== r) {
      const l = s.getPropertyOptions(r), a = typeof l.converter == "function" ? { fromAttribute: l.converter } : ((o = l.converter) == null ? void 0 : o.fromAttribute) !== void 0 ? l.converter : H;
      this._$Em = r;
      const h = a.fromAttribute(e, l.type);
      this[r] = h ?? ((n = this._$Ej) == null ? void 0 : n.get(r)) ?? h, this._$Em = null;
    }
  }
  requestUpdate(t, e, s, r = !1, o) {
    var n;
    if (t !== void 0) {
      const l = this.constructor;
      if (r === !1 && (o = this[t]), s ?? (s = l.getPropertyOptions(t)), !((s.hasChanged ?? G)(o, e) || s.useDefault && s.reflect && o === ((n = this._$Ej) == null ? void 0 : n.get(t)) && !this.hasAttribute(l._$Eu(t, s)))) return;
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
        const { wrapped: l } = n, a = this[o];
        l !== !0 || this._$AL.has(o) || a === void 0 || this.C(o, void 0, n, a);
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
A.elementStyles = [], A.shadowRootOptions = { mode: "open" }, A[C("elementProperties")] = /* @__PURE__ */ new Map(), A[C("finalized")] = /* @__PURE__ */ new Map(), L == null || L({ ReactiveElement: A }), (_.reactiveElementVersions ?? (_.reactiveElementVersions = [])).push("2.1.2");
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const P = globalThis, Q = (i) => i, D = P.trustedTypes, tt = D ? D.createPolicy("lit-html", { createHTML: (i) => i }) : void 0, ht = "$lit$", $ = `lit$${Math.random().toFixed(9).slice(2)}$`, pt = "?" + $, St = `<${pt}>`, b = document, k = () => b.createComment(""), U = (i) => i === null || typeof i != "object" && typeof i != "function", K = Array.isArray, Ct = (i) => K(i) || typeof (i == null ? void 0 : i[Symbol.iterator]) == "function", I = `[ 	
\f\r]`, S = /<(?:(!--|\/[^a-zA-Z])|(\/?[a-zA-Z][^>\s]*)|(\/?$))/g, et = /-->/g, st = />/g, y = RegExp(`>|${I}(?:([^\\s"'>=/]+)(${I}*=${I}*(?:[^ 	
\f\r"'\`<>=]|("|')|))|$)`, "g"), it = /'/g, rt = /"/g, ut = /^(?:script|style|textarea|title)$/i, Pt = (i) => (t, ...e) => ({ _$litType$: i, strings: t, values: e }), u = Pt(1), x = Symbol.for("lit-noChange"), c = Symbol.for("lit-nothing"), ot = /* @__PURE__ */ new WeakMap(), m = b.createTreeWalker(b, 129);
function gt(i, t) {
  if (!K(i) || !i.hasOwnProperty("raw")) throw Error("invalid template strings array");
  return tt !== void 0 ? tt.createHTML(t) : t;
}
const Ot = (i, t) => {
  const e = i.length - 1, s = [];
  let r, o = t === 2 ? "<svg>" : t === 3 ? "<math>" : "", n = S;
  for (let l = 0; l < e; l++) {
    const a = i[l];
    let h, p, d = -1, g = 0;
    for (; g < a.length && (n.lastIndex = g, p = n.exec(a), p !== null); ) g = n.lastIndex, n === S ? p[1] === "!--" ? n = et : p[1] !== void 0 ? n = st : p[2] !== void 0 ? (ut.test(p[2]) && (r = RegExp("</" + p[2], "g")), n = y) : p[3] !== void 0 && (n = y) : n === y ? p[0] === ">" ? (n = r ?? S, d = -1) : p[1] === void 0 ? d = -2 : (d = n.lastIndex - p[2].length, h = p[1], n = p[3] === void 0 ? y : p[3] === '"' ? rt : it) : n === rt || n === it ? n = y : n === et || n === st ? n = S : (n = y, r = void 0);
    const f = n === y && i[l + 1].startsWith("/>") ? " " : "";
    o += n === S ? a + St : d >= 0 ? (s.push(h), a.slice(0, d) + ht + a.slice(d) + $ + f) : a + $ + (d === -2 ? l : f);
  }
  return [gt(i, o + (i[e] || "<?>") + (t === 2 ? "</svg>" : t === 3 ? "</math>" : "")), s];
};
class z {
  constructor({ strings: t, _$litType$: e }, s) {
    let r;
    this.parts = [];
    let o = 0, n = 0;
    const l = t.length - 1, a = this.parts, [h, p] = Ot(t, e);
    if (this.el = z.createElement(h, s), m.currentNode = this.el.content, e === 2 || e === 3) {
      const d = this.el.content.firstChild;
      d.replaceWith(...d.childNodes);
    }
    for (; (r = m.nextNode()) !== null && a.length < l; ) {
      if (r.nodeType === 1) {
        if (r.hasAttributes()) for (const d of r.getAttributeNames()) if (d.endsWith(ht)) {
          const g = p[n++], f = r.getAttribute(d).split($), R = /([.?@])?(.*)/.exec(g);
          a.push({ type: 1, index: o, name: R[2], strings: f, ctor: R[1] === "." ? Ut : R[1] === "?" ? zt : R[1] === "@" ? Tt : j }), r.removeAttribute(d);
        } else d.startsWith($) && (a.push({ type: 6, index: o }), r.removeAttribute(d));
        if (ut.test(r.tagName)) {
          const d = r.textContent.split($), g = d.length - 1;
          if (g > 0) {
            r.textContent = D ? D.emptyScript : "";
            for (let f = 0; f < g; f++) r.append(d[f], k()), m.nextNode(), a.push({ type: 2, index: ++o });
            r.append(d[g], k());
          }
        }
      } else if (r.nodeType === 8) if (r.data === pt) a.push({ type: 2, index: o });
      else {
        let d = -1;
        for (; (d = r.data.indexOf($, d + 1)) !== -1; ) a.push({ type: 7, index: o }), d += $.length - 1;
      }
      o++;
    }
  }
  static createElement(t, e) {
    const s = b.createElement("template");
    return s.innerHTML = t, s;
  }
}
function E(i, t, e = i, s) {
  var n, l;
  if (t === x) return t;
  let r = s !== void 0 ? (n = e._$Co) == null ? void 0 : n[s] : e._$Cl;
  const o = U(t) ? void 0 : t._$litDirective$;
  return (r == null ? void 0 : r.constructor) !== o && ((l = r == null ? void 0 : r._$AO) == null || l.call(r, !1), o === void 0 ? r = void 0 : (r = new o(i), r._$AT(i, e, s)), s !== void 0 ? (e._$Co ?? (e._$Co = []))[s] = r : e._$Cl = r), r !== void 0 && (t = E(i, r._$AS(i, t.values), r, s)), t;
}
class kt {
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
    const { el: { content: e }, parts: s } = this._$AD, r = ((t == null ? void 0 : t.creationScope) ?? b).importNode(e, !0);
    m.currentNode = r;
    let o = m.nextNode(), n = 0, l = 0, a = s[0];
    for (; a !== void 0; ) {
      if (n === a.index) {
        let h;
        a.type === 2 ? h = new T(o, o.nextSibling, this, t) : a.type === 1 ? h = new a.ctor(o, a.name, a.strings, this, t) : a.type === 6 && (h = new Mt(o, this, t)), this._$AV.push(h), a = s[++l];
      }
      n !== (a == null ? void 0 : a.index) && (o = m.nextNode(), n++);
    }
    return m.currentNode = b, r;
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
    t = E(this, t, e), U(t) ? t === c || t == null || t === "" ? (this._$AH !== c && this._$AR(), this._$AH = c) : t !== this._$AH && t !== x && this._(t) : t._$litType$ !== void 0 ? this.$(t) : t.nodeType !== void 0 ? this.T(t) : Ct(t) ? this.k(t) : this._(t);
  }
  O(t) {
    return this._$AA.parentNode.insertBefore(t, this._$AB);
  }
  T(t) {
    this._$AH !== t && (this._$AR(), this._$AH = this.O(t));
  }
  _(t) {
    this._$AH !== c && U(this._$AH) ? this._$AA.nextSibling.data = t : this.T(b.createTextNode(t)), this._$AH = t;
  }
  $(t) {
    var o;
    const { values: e, _$litType$: s } = t, r = typeof s == "number" ? this._$AC(t) : (s.el === void 0 && (s.el = z.createElement(gt(s.h, s.h[0]), this.options)), s);
    if (((o = this._$AH) == null ? void 0 : o._$AD) === r) this._$AH.p(e);
    else {
      const n = new kt(r, this), l = n.u(this.options);
      n.p(e), this.T(l), this._$AH = n;
    }
  }
  _$AC(t) {
    let e = ot.get(t.strings);
    return e === void 0 && ot.set(t.strings, e = new z(t)), e;
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
      const r = Q(t).nextSibling;
      Q(t).remove(), t = r;
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
    if (o === void 0) t = E(this, t, e, 0), n = !U(t) || t !== this._$AH && t !== x, n && (this._$AH = t);
    else {
      const l = t;
      let a, h;
      for (t = o[0], a = 0; a < o.length - 1; a++) h = E(this, l[s + a], e, a), h === x && (h = this._$AH[a]), n || (n = !U(h) || h !== this._$AH[a]), h === c ? t = c : t !== c && (t += (h ?? "") + o[a + 1]), this._$AH[a] = h;
    }
    n && !r && this.j(t);
  }
  j(t) {
    t === c ? this.element.removeAttribute(this.name) : this.element.setAttribute(this.name, t ?? "");
  }
}
class Ut extends j {
  constructor() {
    super(...arguments), this.type = 3;
  }
  j(t) {
    this.element[this.name] = t === c ? void 0 : t;
  }
}
class zt extends j {
  constructor() {
    super(...arguments), this.type = 4;
  }
  j(t) {
    this.element.toggleAttribute(this.name, !!t && t !== c);
  }
}
class Tt extends j {
  constructor(t, e, s, r, o) {
    super(t, e, s, r, o), this.type = 5;
  }
  _$AI(t, e = this) {
    if ((t = E(this, t, e, 0) ?? c) === x) return;
    const s = this._$AH, r = t === c && s !== c || t.capture !== s.capture || t.once !== s.once || t.passive !== s.passive, o = t !== c && (s === c || r);
    r && this.element.removeEventListener(this.name, this, s), o && this.element.addEventListener(this.name, this, t), this._$AH = t;
  }
  handleEvent(t) {
    var e;
    typeof this._$AH == "function" ? this._$AH.call(((e = this.options) == null ? void 0 : e.host) ?? this.element, t) : this._$AH.handleEvent(t);
  }
}
class Mt {
  constructor(t, e, s) {
    this.element = t, this.type = 6, this._$AN = void 0, this._$AM = e, this.options = s;
  }
  get _$AU() {
    return this._$AM._$AU;
  }
  _$AI(t) {
    E(this, t);
  }
}
const B = P.litHtmlPolyfillSupport;
B == null || B(z, T), (P.litHtmlVersions ?? (P.litHtmlVersions = [])).push("3.3.2");
const Rt = (i, t, e) => {
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
class O extends A {
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
    return x;
  }
}
var ct;
O._$litElement$ = !0, O.finalized = !0, (ct = v.litElementHydrateSupport) == null || ct.call(v, { LitElement: O });
const W = v.litElementPolyfillSupport;
W == null || W({ LitElement: O });
(v.litElementVersions ?? (v.litElementVersions = [])).push("4.2.2");
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const Nt = (i) => (t, e) => {
  e !== void 0 ? e.addInitializer(() => {
    customElements.define(i, t);
  }) : customElements.define(i, t);
};
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const Ht = { attribute: !0, type: String, converter: H, reflect: !1, hasChanged: G }, Dt = (i = Ht, t, e) => {
  const { kind: s, metadata: r } = e;
  let o = globalThis.litPropertyMetadata.get(r);
  if (o === void 0 && globalThis.litPropertyMetadata.set(r, o = /* @__PURE__ */ new Map()), s === "setter" && ((i = Object.create(i)).wrapped = !0), o.set(e.name, i), s === "accessor") {
    const { name: n } = e;
    return { set(l) {
      const a = t.get.call(this);
      t.set.call(this, l), this.requestUpdate(n, a, i, !0, l);
    }, init(l) {
      return l !== void 0 && this.C(n, void 0, i, l), l;
    } };
  }
  if (s === "setter") {
    const { name: n } = e;
    return function(l) {
      const a = this[n];
      t.call(this, l), this.requestUpdate(n, a, i, !0, l);
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
function Z(i) {
  return ft({ ...i, state: !0, attribute: !1 });
}
var jt = Object.defineProperty, Lt = Object.getOwnPropertyDescriptor, M = (i, t, e, s) => {
  for (var r = s > 1 ? void 0 : s ? Lt(t, e) : t, o = i.length - 1, n; o >= 0; o--)
    (n = i[o]) && (r = (s ? n(t, e, r) : n(r)) || r);
  return s && r && jt(t, e, r), r;
};
function nt(i) {
  if (/^\d{2}\.\d{2}\.\d{4}$/.test(i)) {
    const [t, e, s] = i.split(".");
    return (/* @__PURE__ */ new Date(`${s}-${e}-${t}`)).getTime();
  }
  return new Date(i).getTime();
}
function at(i) {
  if (/^\d{2}\.\d{2}\.\d{4}$/.test(i)) return i;
  if (/^\d{4}-\d{2}-\d{2}$/.test(i)) {
    const [t, e, s] = i.split("-");
    return `${s}.${e}.${t}`;
  }
  return i;
}
function lt(i) {
  const t = i.toLowerCase();
  return t.includes("sprawdzian") || t.includes("test") ? { label: "SPRAWDZ", cssClass: "type-test" } : t.includes("kartkówka") || t.includes("kartkowka") ? { label: "KARTK", cssClass: "type-quiz" } : t.includes("praca klasow") || t.includes("praca kontrolna") ? { label: "PR.KL", cssClass: "type-classwork" } : t.includes("praca domow") ? { label: "PR.DOM", cssClass: "type-homework" } : t.includes("wypracowanie") ? { label: "WYPRAC", cssClass: "type-essay" } : { label: t.slice(0, 5).toUpperCase() || "INNE", cssClass: "type-other" };
}
let w = class extends O {
  constructor() {
    super(...arguments), this._selectedGrade = null, this._dlgOpen = !1;
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
    const e = (this._config.only_recent ? i.filter((r) => r.is_recent) : i).sort((r, o) => nt(r.date) - nt(o.date));
    return (this._config.sort_order ?? "desc") === "desc" ? e.reverse() : e;
  }
  _openDialog(i) {
    this._selectedGrade = i, this._dlgOpen = !0;
  }
  _closeDialog() {
    this._dlgOpen = !1, this._selectedGrade = null;
  }
  _renderRow(i) {
    const { label: t, cssClass: e } = lt(i.category), s = [
      i.teacher,
      i.weight != null ? `waga ${i.weight}` : ""
    ].filter(Boolean).join(" · ");
    return u`
      <div
        class="grade-row ${i.is_recent ? "recent" : ""}"
        data-tooltip="${s || c}"
        role="button"
        tabindex="0"
        @click="${() => this._openDialog(i)}"
        @keydown="${(r) => r.key === "Enter" && this._openDialog(i)}"
      >
        <span class="grade-badge ${e}">${t}</span>
        <span class="grade-subject">${i.subject}</span>
        <span class="grade-value">${i.grade}</span>
        <span class="grade-date">${at(i.date)}</span>
      </div>
    `;
  }
  _renderDialog() {
    const i = this._selectedGrade;
    return u`
      <ha-dialog
        .open=${this._dlgOpen}
        .heading=${(i == null ? void 0 : i.subject) ?? ""}
        @closed=${() => this._closeDialog()}
      >
        ${i ? u`
          <div class="dlg-category-row">${i.category}${i.category && i.date ? " · " : ""}${at(i.date)}</div>
          <div class="dlg-grade-large ${lt(i.category).cssClass}">${i.grade}</div>
          <div class="dlg-details">
            ${i.teacher ? u`<div class="dlg-detail-row"><span class="dlg-detail-label">Nauczyciel</span><span>${i.teacher}</span></div>` : c}
            ${i.weight != null ? u`<div class="dlg-detail-row"><span class="dlg-detail-label">Waga</span><span>${i.weight}</span></div>` : c}
            <div class="dlg-detail-row"><span class="dlg-detail-label">Liczy do średniej</span><span>${i.counts ? "Tak" : "Nie"}</span></div>
            ${i.title ? u`<div class="dlg-detail-row dlg-detail-row--block"><span class="dlg-detail-label">Temat</span><span class="dlg-detail-text">${i.title}</span></div>` : c}
            ${i.description ? u`<div class="dlg-detail-row"><span class="dlg-detail-label">Poprawa</span><span>${i.description}</span></div>` : c}
          </div>
        ` : c}
      </ha-dialog>
    `;
  }
  render() {
    if (!this._config) return c;
    const i = this._grades, t = this._config.title ?? "Oceny", e = i.filter((r) => r.is_recent).length, s = this._config.height ?? 400;
    return u`
      <ha-card style="--card-h:${s}px">
        <div class="card-header">
          <span class="card-title">${t}</span>
          <span class="card-count">${i.length}${e > 0 ? u` <span class="new-badge">${e} nowe</span>` : c}</span>
        </div>
        <div class="grade-list">
          ${i.length === 0 ? u`<div class="empty">Brak ocen</div>` : i.map((r) => this._renderRow(r))}
        </div>
      </ha-card>
      ${this._renderDialog()}
    `;
  }
};
w.styles = _t`
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

    /* Zawartość ha-dialog (default slot = nasz shadow DOM) */
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
  ft({ attribute: !1 })
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
  Nt("librus-grades-card")
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
