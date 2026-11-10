// A minimal stand-in for the browser DOM, enough to verify how nodes are built.
class FakeText {
  constructor(text) { this.nodeType = 3; this.text = String(text); }
  get textContent() { return this.text; }
}

class FakeElement {
  constructor(tag, namespace) { this.nodeType = 1; this.tag = tag.toLowerCase(); this.namespace = namespace; this.children = []; this.attrs = {}; this.listeners = {}; this.style = { setProperty() {} }; }
  setAttribute(key, value) { this.attrs[key] = String(value); }
  appendChild(child) { this.children.push(child); return child; }
  removeChild(child) { this.children.splice(this.children.indexOf(child), 1); return child; }
  addEventListener(type, fn) { this.listeners[type] = fn; }
  get firstChild() { return this.children[0] || null; }
  get textContent() { return this.children.map((c) => c.textContent).join(""); }
  set textContent(value) { this.children = [new FakeText(value)]; }
  findAll(predicate) {
    const out = [];
    for (const c of this.children) if (c.nodeType === 1) { if (predicate(c)) out.push(c); out.push(...c.findAll(predicate)); }
    return out;
  }
}

export function fakeDocument() {
  globalThis.document = {
    createElement: (tag) => new FakeElement(tag),
    createElementNS: (ns, tag) => new FakeElement(tag, ns),
    createTextNode: (text) => new FakeText(text),
  };
}
