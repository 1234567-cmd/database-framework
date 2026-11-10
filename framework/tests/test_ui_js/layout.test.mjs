import test from "node:test";
import assert from "node:assert/strict";
import { edgePath, layoutGraph, nodeHeight, shownColumns } from "../../src/dbintel/ui/static/js/layout.js";
import { parseHash, routeHref } from "../../src/dbintel/ui/static/js/router.js";

function graph(size) {
  const nodes = Array.from({ length: size }, (_, i) => ({ name: `t${i}`, columns: [{ name: "id", pk: true, fk: false }], external: false }));
  const edges = [];
  for (let i = 1; i < size; i += 1) edges.push({ source: `t${i}`, target: `t${(i - 1) >> 1}` });
  return { nodes, edges };
}

test("layout places every node with no overlap", () => {
  const { nodes, edges } = graph(60);
  const { boxes } = layoutGraph(nodes, edges, "t0");
  assert.equal(boxes.size, 60);
  const list = [...boxes.values()];
  for (let i = 0; i < list.length; i += 1) {
    for (let j = i + 1; j < list.length; j += 1) {
      const a = list[i]; const b = list[j];
      const overlap = a.x < b.x + b.width && b.x < a.x + a.width && a.y < b.y + b.height && b.y < a.y + a.height;
      assert.ok(!overlap, `${i} overlaps ${j}`);
    }
  }
});

test("layout is deterministic and the focus sits in the first column", () => {
  const { nodes, edges } = graph(20);
  const first = layoutGraph(nodes, edges, "t5");
  const second = layoutGraph(nodes, edges, "t5");
  assert.deepEqual([...first.boxes.entries()], [...second.boxes.entries()]);
  const minX = Math.min(...[...first.boxes.values()].map((b) => b.x));
  assert.equal(first.boxes.get("t5").x, minX);
});

test("layout handles disconnected tables and missing edge targets", () => {
  const nodes = [{ name: "a", columns: [] }, { name: "b", columns: [] }];
  const { boxes } = layoutGraph(nodes, [{ source: "a", target: "missing" }], null);
  assert.equal(boxes.size, 2);
});

test("tables without links share a compact grid", () => {
  const nodes = Array.from({ length: 16 }, (_, i) => ({ name: `solo${i}`, columns: [] }));
  const { boxes, width } = layoutGraph(nodes, [], null);
  assert.equal(new Set([...boxes.values()].map((b) => b.x)).size, 4);
  assert.ok(width < 16 * 240);
});

test("key columns are shown first and the rest are counted", () => {
  const columns = Array.from({ length: 15 }, (_, i) => ({ name: `c${i}`, pk: i === 12, fk: i === 13, state: i === 14 ? "added" : null }));
  const { shown, hidden } = shownColumns({ columns }, 5);
  assert.equal(shown.length, 5);
  assert.equal(hidden, 10);
  assert.ok(shown.some((c) => c.name === "c12") && shown.some((c) => c.name === "c14"));
});

test("external nodes are short", () => {
  assert.ok(nodeHeight({ external: true, columns: [] }) < nodeHeight({ columns: Array(9).fill({}) }));
});

test("edge paths work forward, backward, and for self references", () => {
  const a = { x: 0, y: 0, width: 240, height: 50 };
  const b = { x: 400, y: 0, width: 240, height: 50 };
  assert.match(edgePath(a, b), /^M240/);
  assert.match(edgePath(b, a), /^M400/);
  assert.match(edgePath(a, a), /^M240/);
});

test("routes round-trip table names with reserved characters", () => {
  const href = routeHref(["run", "20250101-000000-abcdef", "tables", "public/a b"], { q: "x y", f: "F-1", empty: "" });
  const route = parseHash(href);
  assert.deepEqual(route.segments, ["run", "20250101-000000-abcdef", "tables", "public/a b"]);
  assert.deepEqual(route.query, { q: "x y", f: "F-1" });
});

test("routes without a query or with an empty hash parse", () => {
  assert.deepEqual(parseHash("").segments, []);
  assert.deepEqual(parseHash("#/import"), { segments: ["import"], query: {} });
});
