RUNTIME_SOURCE = r"""
const __jseasy = (() => {
  let nodeId = 1;
  const timers = [];
  const mutationObservers = [];

  function escapeHtml(value) {
    return String(value)
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;");
  }

  function escapeAttr(value) {
    return escapeHtml(value).replaceAll('"', "&quot;");
  }

  class Node {
    constructor(type) {
      this.__id = nodeId++;
      this.nodeType = type;
      this.parentNode = null;
      this.childNodes = [];
      this.__listeners = {};
    }

    appendChild(node) {
      if (node.parentNode) node.parentNode.removeChild(node);
      node.parentNode = this;
      this.childNodes.push(node);
      notifyMutation(this, { type: "childList", target: this, addedNodes: [node], removedNodes: [] });
      return node;
    }

    removeChild(node) {
      const index = this.childNodes.indexOf(node);
      if (index === -1) throw new Error("Node is not a child");
      this.childNodes.splice(index, 1);
      node.parentNode = null;
      notifyMutation(this, { type: "childList", target: this, addedNodes: [], removedNodes: [node] });
      return node;
    }

    insertBefore(node, before) {
      if (before == null) return this.appendChild(node);
      const index = this.childNodes.indexOf(before);
      if (index === -1) throw new Error("Reference node is not a child");
      if (node.parentNode) node.parentNode.removeChild(node);
      node.parentNode = this;
      this.childNodes.splice(index, 0, node);
      notifyMutation(this, { type: "childList", target: this, addedNodes: [node], removedNodes: [] });
      return node;
    }

    remove() {
      if (this.parentNode) this.parentNode.removeChild(this);
    }

    get textContent() {
      return this.childNodes.map((child) => child.textContent).join("");
    }

    set textContent(value) {
      this.childNodes = [];
      if (value !== "") this.appendChild(new Text(String(value)));
      notifyMutation(this, { type: "characterData", target: this });
    }

    addEventListener(type, callback) {
      this.__listeners[type] ||= [];
      this.__listeners[type].push(callback);
    }

    removeEventListener(type, callback) {
      this.__listeners[type] = (this.__listeners[type] || []).filter((item) => item !== callback);
    }

    dispatchEvent(event) {
      event.target ||= this;
      event.currentTarget = this;
      event.eventPhase = 2;
      for (const callback of this.__listeners[event.type] || []) {
        try {
          callback.call(this, event);
        } catch (error) {
          console.error(error && error.stack ? error.stack : String(error));
        }
      }
      if (event.bubbles && this.parentNode) this.parentNode.dispatchEvent(event);
      return !event.defaultPrevented;
    }
  }

  class Text extends Node {
    constructor(data) {
      super(3);
      this.data = String(data);
    }

    get textContent() {
      return this.data;
    }

    set textContent(value) {
      this.data = String(value);
      notifyMutation(this, { type: "characterData", target: this });
    }

    get outerHTML() {
      return escapeHtml(this.data);
    }
  }

  class CSSStyleDeclaration {
    constructor(owner = null) {
      this.__owner = owner;
      this.__values = {};
    }

    setProperty(name, value) {
      this.__values[String(name).trim().toLowerCase()] = String(value).trim();
      this.__syncOwner();
    }

    getPropertyValue(name) {
      return this.__values[String(name).trim().toLowerCase()] || "";
    }

    removeProperty(name) {
      name = String(name).trim().toLowerCase();
      const old = this.__values[name] || "";
      delete this.__values[name];
      this.__syncOwner();
      return old;
    }

    get cssText() {
      return Object.entries(this.__values).map(([key, value]) => `${key}: ${value};`).join(" ");
    }

    set cssText(value) {
      this.__values = parseDeclarations(value);
      this.__syncOwner();
    }

    __syncOwner() {
      if (this.__owner && this.cssText) this.__owner.attributes.style = this.cssText;
      if (this.__owner && !this.cssText) delete this.__owner.attributes.style;
    }
  }

  class CSSRule {
    constructor(cssText) {
      this.cssText = String(cssText).trim();
    }
  }

  class CSSStyleRule extends CSSRule {
    constructor(selectorText, declarations) {
      super(`${selectorText} { ${declarations} }`);
      this.type = 1;
      this.selectorText = selectorText.trim();
      this.style = new CSSStyleDeclaration();
      this.style.cssText = declarations;
    }
  }

  class CSSStyleSheet {
    constructor({ href = "", text = "" } = {}) {
      this.href = href || null;
      this.ownerNode = null;
      this.cssRules = parseCssRules(text);
      this.rules = this.cssRules;
    }

    insertRule(rule, index = this.cssRules.length) {
      const parsed = parseCssRules(rule);
      if (parsed.length === 0) throw new Error("Invalid CSS rule");
      this.cssRules.splice(index, 0, parsed[0]);
      return index;
    }

    deleteRule(index) {
      this.cssRules.splice(index, 1);
    }
  }

  class Element extends Node {
    constructor(tagName) {
      super(1);
      this.tagName = String(tagName).toUpperCase();
      this.localName = String(tagName).toLowerCase();
      this.attributes = {};
      this.style = new CSSStyleDeclaration(this);
      this.shadowRoot = null;
    }

    get id() {
      return this.getAttribute("id") || "";
    }

    set id(value) {
      this.setAttribute("id", value);
    }

    get className() {
      return this.getAttribute("class") || "";
    }

    set className(value) {
      this.setAttribute("class", value);
    }

    get name() {
      return this.getAttribute("name") || "";
    }

    set name(value) {
      this.setAttribute("name", value);
    }

    get value() {
      return this.getAttribute("value") || "";
    }

    set value(value) {
      this.setAttribute("value", value);
    }

    get classList() {
      const element = this;
      return {
        contains(name) {
          return element.className.split(/\s+/).filter(Boolean).includes(name);
        },
        add(...names) {
          const values = new Set(element.className.split(/\s+/).filter(Boolean));
          names.forEach((name) => values.add(name));
          element.className = Array.from(values).join(" ");
        },
        remove(...names) {
          const remove = new Set(names);
          element.className = element.className
            .split(/\s+/)
            .filter((name) => name && !remove.has(name))
            .join(" ");
        },
      };
    }

    getAttribute(name) {
      name = String(name).toLowerCase();
      return Object.prototype.hasOwnProperty.call(this.attributes, name)
        ? this.attributes[name]
        : null;
    }

    setAttribute(name, value) {
      name = String(name).toLowerCase();
      const oldValue = this.attributes[name] ?? null;
      this.attributes[name] = String(value);
      if (name === "style") this.style.cssText = String(value);
      notifyMutation(this, { type: "attributes", target: this, attributeName: name, oldValue });
    }

    hasAttribute(name) {
      return Object.prototype.hasOwnProperty.call(this.attributes, String(name).toLowerCase());
    }

    removeAttribute(name) {
      name = String(name).toLowerCase();
      const oldValue = this.attributes[name] ?? null;
      delete this.attributes[name];
      if (name === "style") this.style.cssText = "";
      notifyMutation(this, { type: "attributes", target: this, attributeName: name, oldValue });
    }

    querySelector(selector) {
      return querySelectorAll(this, selector)[0] || null;
    }

    querySelectorAll(selector) {
      return querySelectorAll(this, selector);
    }

    matches(selector) {
      return matchesSimple(this, selector);
    }

    closest(selector) {
      let node = this;
      while (node) {
        if (node.nodeType === 1 && node.matches(selector)) return node;
        node = node.parentNode;
      }
      return null;
    }

    attachShadow(_init = {}) {
      this.shadowRoot = new ShadowRoot(this);
      return this.shadowRoot;
    }

    getBoundingClientRect() {
      const width = parseCssPixel(this.style.getPropertyValue("width")) || 0;
      const height = parseCssPixel(this.style.getPropertyValue("height")) || 0;
      return { x: 0, y: 0, top: 0, left: 0, right: width, bottom: height, width, height };
    }

    get offsetWidth() {
      return this.getBoundingClientRect().width;
    }

    get offsetHeight() {
      return this.getBoundingClientRect().height;
    }

    get clientWidth() {
      return this.offsetWidth;
    }

    get clientHeight() {
      return this.offsetHeight;
    }

    get children() {
      return this.childNodes.filter((node) => node.nodeType === 1);
    }

    get innerHTML() {
      return this.childNodes.map(serialize).join("");
    }

    set innerHTML(html) {
      this.childNodes = parseFragment(String(html));
      this.childNodes.forEach((child) => {
        child.parentNode = this;
      });
    }

    get outerHTML() {
      return serialize(this);
    }

    get innerText() {
      return this.textContent;
    }

    set innerText(value) {
      this.textContent = value;
    }

    append(...nodes) {
      nodes.forEach((node) => this.appendChild(typeof node === "string" ? new Text(node) : node));
    }

    click() {
      this.dispatchEvent(new Event("click", { bubbles: true }));
    }
  }

  class Document extends Node {
    constructor() {
      super(9);
      this.readyState = "loading";
      this.hidden = false;
      this.visibilityState = "visible";
      this.styleSheets = [];
      this.cookie = "";
    }

    createElement(tagName) {
      return new Element(tagName);
    }

    createTextNode(data) {
      return new Text(data);
    }

    createDocumentFragment() {
      return new DocumentFragment();
    }

    write(html) {
      const nodes = parseFragment(String(html));
      const target = this.body || this;
      nodes.forEach((node) => target.appendChild(node));
    }

    get documentElement() {
      return this.childNodes.find((node) => node.nodeType === 1 && node.localName === "html")
        || this.childNodes.find((node) => node.nodeType === 1)
        || null;
    }

    get body() {
      return this.querySelector("body");
    }

    get head() {
      return this.querySelector("head");
    }

    get scripts() {
      return this.querySelectorAll("script");
    }

    get title() {
      const title = this.querySelector("title");
      return title ? title.textContent : "";
    }

    getElementById(id) {
      return walk(this).find((node) => node.nodeType === 1 && node.id === String(id)) || null;
    }

    querySelector(selector) {
      return querySelectorAll(this, selector)[0] || null;
    }

    querySelectorAll(selector) {
      return querySelectorAll(this, selector);
    }
  }

  class DocumentFragment extends Node {
    constructor() {
      super(11);
    }

    get innerHTML() {
      return this.childNodes.map(serialize).join("");
    }

    set innerHTML(html) {
      this.childNodes = parseFragment(String(html));
      this.childNodes.forEach((child) => {
        child.parentNode = this;
      });
    }

    querySelector(selector) {
      return querySelectorAll(this, selector)[0] || null;
    }

    querySelectorAll(selector) {
      return querySelectorAll(this, selector);
    }
  }

  class ShadowRoot extends DocumentFragment {
    constructor(host) {
      super();
      this.host = host;
      this.mode = "open";
    }
  }

  class FormData {
    constructor(form = null) {
      this.__entries = [];
      if (form) {
        for (const node of walk(form)) {
          if (node.nodeType === 1 && node.name) this.append(node.name, node.value);
        }
      }
    }

    append(name, value) {
      this.__entries.push([String(name), String(value)]);
    }

    get(name) {
      name = String(name);
      const found = this.__entries.find(([key]) => key === name);
      return found ? found[1] : null;
    }

    getAll(name) {
      name = String(name);
      return this.__entries.filter(([key]) => key === name).map(([, value]) => value);
    }

    has(name) {
      name = String(name);
      return this.__entries.some(([key]) => key === name);
    }

    delete(name) {
      name = String(name);
      this.__entries = this.__entries.filter(([key]) => key !== name);
    }

    set(name, value) {
      this.delete(name);
      this.append(name, value);
    }

    entries() {
      return this.__entries[Symbol.iterator]();
    }

    [Symbol.iterator]() {
      return this.entries();
    }
  }

  class Storage {
    constructor() {
      this.__items = {};
    }

    get length() {
      return Object.keys(this.__items).length;
    }

    key(index) {
      return Object.keys(this.__items)[index] || null;
    }

    getItem(key) {
      key = String(key);
      return Object.prototype.hasOwnProperty.call(this.__items, key) ? this.__items[key] : null;
    }

    setItem(key, value) {
      this.__items[String(key)] = String(value);
    }

    removeItem(key) {
      delete this.__items[String(key)];
    }

    clear() {
      this.__items = {};
    }
  }

  class Headers {
    constructor(init = {}) {
      this.__items = {};
      if (Array.isArray(init)) init.forEach(([key, value]) => this.append(key, value));
      else if (init instanceof Headers) init.forEach((value, key) => this.append(key, value));
      else Object.entries(init || {}).forEach(([key, value]) => this.append(key, value));
    }

    append(key, value) {
      key = String(key).toLowerCase();
      this.__items[key] = this.__items[key] ? `${this.__items[key]}, ${value}` : String(value);
    }

    set(key, value) {
      this.__items[String(key).toLowerCase()] = String(value);
    }

    get(key) {
      return this.__items[String(key).toLowerCase()] || null;
    }

    has(key) {
      return Object.prototype.hasOwnProperty.call(this.__items, String(key).toLowerCase());
    }

    delete(key) {
      delete this.__items[String(key).toLowerCase()];
    }

    forEach(callback) {
      for (const [key, value] of Object.entries(this.__items)) callback(value, key, this);
    }

    entries() {
      return Object.entries(this.__items)[Symbol.iterator]();
    }

    [Symbol.iterator]() {
      return this.entries();
    }
  }

  class Response {
    constructor(body = "", init = {}) {
      this.status = init.status || 200;
      this.statusText = init.statusText || "";
      this.headers = new Headers(init.headers || {});
      this.url = init.url || "";
      this.ok = this.status >= 200 && this.status < 300;
      this.__body = String(body ?? "");
    }

    text() {
      return Promise.resolve(this.__body);
    }

    json() {
      return Promise.resolve(JSON.parse(this.__body));
    }

    clone() {
      return new Response(this.__body, {
        status: this.status,
        statusText: this.statusText,
        headers: this.headers,
        url: this.url,
      });
    }
  }

  class Request {
    constructor(input, init = {}) {
      if (input instanceof Request) {
        this.url = input.url;
        this.method = input.method;
        this.headers = new Headers(input.headers);
        this.body = input.body;
      } else {
        this.url = String(input);
        this.method = "GET";
        this.headers = new Headers();
        this.body = null;
      }
      if (init.method) this.method = String(init.method).toUpperCase();
      if (init.headers) this.headers = new Headers(init.headers);
      if (init.body != null) this.body = String(init.body);
    }
  }

  class MutationObserver {
    constructor(callback) {
      this.callback = callback;
      this.records = [];
      this.targets = [];
      mutationObservers.push(this);
    }

    observe(target, options = {}) {
      this.targets.push({ target, options });
    }

    disconnect() {
      this.targets = [];
      this.records = [];
    }

    takeRecords() {
      const records = this.records;
      this.records = [];
      return records;
    }
  }

  function notifyMutation(target, record) {
    for (const observer of mutationObservers) {
      for (const watched of observer.targets) {
        const interested = watched.target === target || (watched.options.subtree && isDescendantOf(target, watched.target));
        if (!interested) continue;
        if (record.type === "attributes" && !watched.options.attributes) continue;
        if (record.type === "childList" && !watched.options.childList) continue;
        if (record.type === "characterData" && !watched.options.characterData) continue;
        observer.records.push(record);
        setTimeout(() => observer.callback(observer.takeRecords(), observer), 0);
      }
    }
  }

  function isDescendantOf(node, ancestor) {
    let current = node;
    while (current) {
      if (current === ancestor) return true;
      current = current.parentNode;
    }
    return false;
  }

  function evaluateMediaQuery(query, environment) {
    const minWidth = query.match(/\(\s*min-width\s*:\s*(\d+)px\s*\)/);
    if (minWidth && environment.width < Number(minWidth[1])) return false;
    const maxWidth = query.match(/\(\s*max-width\s*:\s*(\d+)px\s*\)/);
    if (maxWidth && environment.width > Number(maxWidth[1])) return false;
    const minHeight = query.match(/\(\s*min-height\s*:\s*(\d+)px\s*\)/);
    if (minHeight && environment.height < Number(minHeight[1])) return false;
    const maxHeight = query.match(/\(\s*max-height\s*:\s*(\d+)px\s*\)/);
    if (maxHeight && environment.height > Number(maxHeight[1])) return false;
    return true;
  }

  function walk(root) {
    const out = [];
    function visit(node) {
      for (const child of node.childNodes || []) {
        out.push(child);
        visit(child);
      }
    }
    visit(root);
    return out;
  }

  function parseDeclarations(text) {
    const values = {};
    for (const declaration of String(text).split(";")) {
      const index = declaration.indexOf(":");
      if (index === -1) continue;
      const key = declaration.slice(0, index).trim().toLowerCase();
      const value = declaration.slice(index + 1).trim();
      if (key) values[key] = value;
    }
    return values;
  }

  function parseCssPixel(value) {
    const match = String(value || "").trim().match(/^(-?\d+(?:\.\d+)?)px$/);
    return match ? Number(match[1]) : 0;
  }

  function parseCssRules(css) {
    const rules = [];
    const withoutComments = String(css).replace(/\/\*[\s\S]*?\*\//g, "");
    const pattern = /([^{}@][^{}]*)\{([^{}]*)\}/g;
    let match;
    while ((match = pattern.exec(withoutComments))) {
      rules.push(new CSSStyleRule(match[1], match[2]));
    }
    return rules;
  }

  function computeStyle(element) {
    const style = new CSSStyleDeclaration();
    for (const sheet of document.styleSheets || []) {
      for (const rule of sheet.cssRules || []) {
        if (rule.selectorText && elementMatchesSelector(element, rule.selectorText)) {
          for (const [key, value] of Object.entries(rule.style.__values)) style.setProperty(key, value);
        }
      }
    }
    for (const [key, value] of Object.entries(element.style.__values)) style.setProperty(key, value);
    return style;
  }

  function elementMatchesSelector(element, selectorText) {
    return selectorText
      .split(",")
      .map((selector) => selector.trim())
      .filter(Boolean)
      .some((selector) => matchesSimple(element, selector));
  }

  function matchesSimple(node, selector) {
    if (!node || node.nodeType !== 1) return false;
    const nth = selector.match(/^(.*):nth-child\((\d+)\)$/);
    if (nth) {
      const base = nth[1] || "*";
      const siblings = node.parentNode ? node.parentNode.childNodes.filter((child) => child.nodeType === 1) : [];
      if (siblings.indexOf(node) !== Number(nth[2]) - 1) return false;
      selector = base;
    }
    if (selector === "*") return true;
    if (selector.startsWith("#")) return node.id === selector.slice(1);
    if (selector.startsWith(".")) return node.classList.contains(selector.slice(1));
    const attr = selector.match(/^\[([^=\]]+)(?:=["']?([^"'\]]+)["']?)?\]$/);
    if (attr) {
      const value = node.getAttribute(attr[1]);
      return attr[2] == null ? value != null : value === attr[2];
    }
    const tagClass = selector.match(/^([a-zA-Z0-9_-]+)\.([a-zA-Z0-9_-]+)$/);
    if (tagClass) return node.localName === tagClass[1].toLowerCase() && node.classList.contains(tagClass[2]);
    return node.localName === selector.toLowerCase();
  }

  function querySelectorAll(root, selector) {
    const parts = String(selector).trim().replace(/\s*>\s*/g, " > ").split(/\s+/).filter(Boolean);
    if (parts.length === 0) return [];
    let candidates = walk(root).filter((node) => matchesSimple(node, parts[0]));
    for (let index = 1; index < parts.length; index += 1) {
      const part = parts[index];
      if (part === ">") {
        const childSelector = parts[index + 1];
        candidates = candidates.flatMap((candidate) =>
          candidate.children.filter((node) => matchesSimple(node, childSelector))
        );
        index += 1;
        continue;
      }
      const next = [];
      for (const candidate of candidates) {
        next.push(...walk(candidate).filter((node) => matchesSimple(node, part)));
      }
      candidates = next;
    }
    return candidates;
  }

  function serialize(node) {
    if (node.nodeType === 3) return node.outerHTML;
    if (node.nodeType === 9) return node.childNodes.map(serialize).join("");
    const attrs = Object.entries(node.attributes)
      .map(([key, value]) => ` ${key}="${escapeAttr(value)}"`)
      .join("");
    return `<${node.localName}${attrs}>${node.childNodes.map(serialize).join("")}</${node.localName}>`;
  }

  function parseFragment(html) {
    const root = new Element("jseasy-fragment");
    const stack = [root];
    const tokens = String(html).match(/<[^>]+>|[^<]+/g) || [];
    for (const token of tokens) {
      if (token.startsWith("</")) {
        if (stack.length > 1) stack.pop();
        continue;
      }
      if (token.startsWith("<")) {
        const open = token.match(/^<\s*([a-zA-Z0-9-]+)([^>]*)>/);
        if (!open) continue;
        const element = new Element(open[1]);
        const attrs = open[2].matchAll(/([^\s=]+)(?:=(?:"([^"]*)"|'([^']*)'|([^\s"'>/]+)))?/g);
        for (const attr of attrs) element.setAttribute(attr[1], attr[2] || attr[3] || attr[4] || "");
        stack[stack.length - 1].appendChild(element);
        if (!token.endsWith("/>")) stack.push(element);
      } else {
        stack[stack.length - 1].appendChild(new Text(token));
      }
    }
    return root.childNodes;
  }

  function fromJson(data) {
    if (data.type === "document") {
      const doc = new Document();
      (data.childNodes || []).forEach((child) => doc.appendChild(fromJson(child)));
      return doc;
    }
    if (data.type === "text") return new Text(data.data || "");
    const element = new Element(data.tagName);
    for (const [key, value] of Object.entries(data.attributes || {})) {
      element.setAttribute(key, value);
    }
    (data.childNodes || []).forEach((child) => element.appendChild(fromJson(child)));
    return element;
  }

  function installGlobals(document, environment) {
    globalThis.document = document;
    globalThis.window = globalThis;
    globalThis.self = globalThis;
    globalThis.globalThis = globalThis;
    globalThis.Node = Node;
    globalThis.Element = Element;
    globalThis.Document = Document;
    globalThis.Text = Text;
    globalThis.DocumentFragment = DocumentFragment;
    globalThis.ShadowRoot = ShadowRoot;
    globalThis.FormData = FormData;
    globalThis.Storage = Storage;
    globalThis.Headers = Headers;
    globalThis.Request = Request;
    globalThis.Response = Response;
    globalThis.MutationObserver = MutationObserver;
    globalThis.CSSStyleDeclaration = CSSStyleDeclaration;
    globalThis.CSSRule = CSSRule;
    globalThis.CSSStyleRule = CSSStyleRule;
    globalThis.CSSStyleSheet = CSSStyleSheet;
    globalThis.navigator = {
      userAgent: environment.userAgent,
      webdriver: false,
      language: "en-US",
      languages: ["en-US", "en"],
      cookieEnabled: true,
      onLine: true,
      sendBeacon: (url, data = null) => {
        try {
          __py_fetch(String(url), JSON.stringify({ method: "POST", body: data == null ? null : String(data), headers: {} }));
          return true;
        } catch (_error) {
          return false;
        }
      },
    };
    globalThis.location = {
      href: environment.url,
      origin: environment.origin,
      protocol: environment.protocol,
      host: environment.host,
      pathname: environment.pathname,
      assign(url) {
        this.href = String(url);
      },
      replace(url) {
        this.href = String(url);
      },
      reload() {},
    };
    globalThis.history = {
      length: 1,
      state: null,
      pushState(state, _title, url = null) {
        this.state = state;
        this.length += 1;
        if (url != null) location.href = String(url);
      },
      replaceState(state, _title, url = null) {
        this.state = state;
        if (url != null) location.href = String(url);
      },
      back() {},
      forward() {},
      go() {},
    };
    globalThis.localStorage = new Storage();
    globalThis.sessionStorage = new Storage();
    globalThis.innerWidth = environment.width;
    globalThis.innerHeight = environment.height;
    globalThis.devicePixelRatio = environment.devicePixelRatio;
    globalThis.screen = {
      width: environment.width,
      height: environment.height,
      availWidth: environment.width,
      availHeight: environment.height,
    };
    globalThis.matchMedia = (query) => ({
      media: String(query),
      matches: evaluateMediaQuery(String(query), environment),
      onchange: null,
      addEventListener() {},
      removeEventListener() {},
      addListener() {},
      removeListener() {},
      dispatchEvent: () => true,
    });
    globalThis.performance = {
      now: () => Date.now(),
      timeOrigin: Date.now(),
      mark() {},
      measure() {},
      getEntriesByType: () => [],
      getEntriesByName: () => [],
    };
    globalThis.atob = (value) => __py_atob(String(value));
    globalThis.btoa = (value) => __py_btoa(String(value));
    globalThis.console = {
      log: (...args) => __py_console("log", args.map(String).join(" ")),
      warn: (...args) => __py_console("warn", args.map(String).join(" ")),
      error: (...args) => __py_console("error", args.map(String).join(" ")),
    };
    globalThis.setTimeout = (callback, delay = 0, ...args) => {
      timers.push(() => callback(...args));
      return timers.length;
    };
    globalThis.clearTimeout = () => {};
    globalThis.setInterval = globalThis.setTimeout;
    globalThis.clearInterval = () => {};
    globalThis.requestAnimationFrame = (callback) => setTimeout(() => callback(Date.now()), 16);
    globalThis.cancelAnimationFrame = () => {};
    const windowTarget = new Node(0);
    globalThis.addEventListener = windowTarget.addEventListener.bind(windowTarget);
    globalThis.removeEventListener = windowTarget.removeEventListener.bind(windowTarget);
    globalThis.dispatchEvent = windowTarget.dispatchEvent.bind(windowTarget);
    globalThis.Event = class Event {
      constructor(type, options = {}) {
        this.type = type;
        this.bubbles = Boolean(options.bubbles);
        this.cancelable = Boolean(options.cancelable);
        this.defaultPrevented = false;
        this.isTrusted = false;
        this.timeStamp = Date.now();
      }

      preventDefault() {
        if (this.cancelable) this.defaultPrevented = true;
      }
    };
    globalThis.CustomEvent = class CustomEvent extends Event {
      constructor(type, options = {}) {
        super(type, options);
        this.detail = options.detail ?? null;
      }
    };
    globalThis.MouseEvent = class MouseEvent extends Event {
      constructor(type, options = {}) {
        super(type, options);
        this.clientX = options.clientX || 0;
        this.clientY = options.clientY || 0;
        this.button = options.button || 0;
        this.buttons = options.buttons || 0;
      }
    };
    globalThis.KeyboardEvent = class KeyboardEvent extends Event {
      constructor(type, options = {}) {
        super(type, options);
        this.key = options.key || "";
        this.code = options.code || "";
        this.ctrlKey = Boolean(options.ctrlKey);
        this.shiftKey = Boolean(options.shiftKey);
        this.altKey = Boolean(options.altKey);
        this.metaKey = Boolean(options.metaKey);
      }
    };
    globalThis.WebSocket = class WebSocket extends Node {
      constructor(url) {
        super(0);
        this.url = String(url);
        this.readyState = WebSocket.CLOSED;
        throw new Error("WebSocket transport is not implemented in jseasy");
      }
    };
    globalThis.WebSocket.CONNECTING = 0;
    globalThis.WebSocket.OPEN = 1;
    globalThis.WebSocket.CLOSING = 2;
    globalThis.WebSocket.CLOSED = 3;
    globalThis.getComputedStyle = (element) => computeStyle(element);
    globalThis.fetch = (input, options = {}) => {
      const request = input instanceof Request ? new Request(input, options) : new Request(input, options);
      const raw = __py_fetch(
        request.url,
        JSON.stringify({
          method: request.method,
          body: request.body == null ? null : String(request.body),
          headers: Object.fromEntries(request.headers.entries()),
        })
      );
      const payload = JSON.parse(raw);
      return Promise.resolve(new Response(payload.text, {
        status: payload.status,
        headers: payload.headers,
        url: payload.url,
      }));
    };
    globalThis.XMLHttpRequest = class XMLHttpRequest extends Node {
      constructor() {
        super(0);
        this.UNSENT = 0;
        this.OPENED = 1;
        this.HEADERS_RECEIVED = 2;
        this.LOADING = 3;
        this.DONE = 4;
        this.readyState = this.UNSENT;
        this.status = 0;
        this.statusText = "";
        this.responseText = "";
        this.response = "";
        this.responseURL = "";
        this.responseType = "";
        this.onreadystatechange = null;
        this.onload = null;
        this.onerror = null;
        this.__method = "GET";
        this.__url = "";
        this.__async = true;
        this.__headers = {};
        this.__responseHeaders = {};
      }

      open(method, url, async = true) {
        this.__method = String(method || "GET").toUpperCase();
        this.__url = String(url);
        this.__async = async !== false;
        this.__setReadyState(this.OPENED);
      }

      setRequestHeader(name, value) {
        this.__headers[String(name)] = String(value);
      }

      getResponseHeader(name) {
        return this.__responseHeaders[String(name).toLowerCase()] || null;
      }

      getAllResponseHeaders() {
        return Object.entries(this.__responseHeaders).map(([key, value]) => `${key}: ${value}`).join("\r\n");
      }

      send(body = null) {
        const run = () => {
          try {
            const raw = __py_fetch(this.__url, JSON.stringify({
              method: this.__method,
              body: body == null ? null : String(body),
              headers: this.__headers,
            }));
            const payload = JSON.parse(raw);
            this.status = payload.status;
            this.responseURL = payload.url;
            this.__responseHeaders = {};
            for (const [key, value] of Object.entries(payload.headers || {})) {
              this.__responseHeaders[key.toLowerCase()] = value;
            }
            this.__setReadyState(this.HEADERS_RECEIVED);
            this.__setReadyState(this.LOADING);
            this.responseText = payload.text;
            this.response = this.responseType === "json" ? JSON.parse(payload.text) : payload.text;
            this.__setReadyState(this.DONE);
            if (this.onload) this.onload(new Event("load"));
            this.dispatchEvent(new Event("load"));
          } catch (error) {
            if (this.onerror) this.onerror(new Event("error"));
            this.dispatchEvent(new Event("error"));
          }
        };
        if (this.__async) setTimeout(run, 0);
        else run();
      }

      __setReadyState(state) {
        this.readyState = state;
        if (this.onreadystatechange) this.onreadystatechange(new Event("readystatechange"));
        this.dispatchEvent(new Event("readystatechange"));
      }
    };
  }

  function installStyleSheets(stylesheets) {
    document.styleSheets = stylesheets.map((sheet) => new CSSStyleSheet(sheet));
  }

  function drainTimers() {
    let count = 0;
    while (timers.length && count < 1000) {
      const timer = timers.shift();
      try {
        timer();
      } catch (error) {
        console.error(error && error.stack ? error.stack : String(error));
      }
      count += 1;
    }
    return count;
  }

  return { fromJson, installGlobals, installStyleSheets, serialize, drainTimers };
})();
"""
