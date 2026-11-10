import test from "node:test";
import assert from "node:assert/strict";
import { fakeDocument } from "./fake_dom.mjs";

fakeDocument();
const { h, s, mount, safeHref } = await import("../../src/dbintel/ui/static/js/dom.js");
const { sevBadge, kindBadge } = await import("../../src/dbintel/ui/static/js/components.js");

const SCRIPT = "<script>alert(1)</script>";

test("h() puts hostile strings in text nodes, never as elements", () => {
  const el = h("div", {}, SCRIPT, h("span", { text: "<img src=x onerror=alert(2)>" }));
  assert.equal(el.children[0].nodeType, 3);
  assert.equal(el.children[0].text, SCRIPT);
  assert.equal(el.children[1].textContent, "<img src=x onerror=alert(2)>");
  assert.ok(!el.findAll((c) => c.tag === "script" || c.tag === "img").length);
});

test("s() creates SVG elements with text children", () => {
  const t = s("text", { x: "1" }, SCRIPT);
  assert.equal(t.namespace, "http://www.w3.org/2000/svg");
  assert.equal(t.children[0].text, SCRIPT);
});

test("href only allows in-page or same-origin links", () => {
  assert.equal(h("a", { href: "javascript:alert(1)" }).attrs.href, "#");
  assert.equal(h("a", { href: "https://evil.example" }).attrs.href, "#");
  assert.equal(h("a", { href: "//evil.example" }).attrs.href, "#");
  assert.equal(h("a", { href: "#/run/x" }).attrs.href, "#/run/x");
  assert.equal(safeHref("/static/x.css"), "/static/x.css");
});

test("inline style properties are refused", () => {
  assert.throws(() => h("div", { style: "color: red" }));
});

test("event handler props become listeners, not attributes", () => {
  const el = h("button", { onClick: () => 1 });
  assert.ok(el.listeners.click);
  assert.equal(el.attrs.onClick, undefined);
});

test("severity badges always include a text label", () => {
  for (const [sev, label] of [["critical", "Critical"], ["high", "High"], ["medium", "Medium"], ["low", "Low"], ["informational", "Informational"]]) {
    const badge = sevBadge(sev);
    assert.ok(badge.textContent.includes(label), label);
  }
  assert.ok(kindBadge("confirmed_defect").textContent.includes("Confirmed defect"));
});

test("mount replaces children", () => {
  const root = h("div", {}, "old");
  mount(root, "new");
  assert.equal(root.textContent, "new");
});
