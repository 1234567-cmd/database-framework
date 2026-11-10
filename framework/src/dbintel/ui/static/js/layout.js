// Layered layout for the ER view. Pure functions, so the behaviour can be tested without a browser.
export const NODE_WIDTH = 240;
export const ROW_HEIGHT = 16;
export const HEADER_HEIGHT = 26;
export const MAX_COLUMNS = 8;
const GAP_X = 90;
const GAP_Y = 30;

export function shownColumns(node, maxColumns = MAX_COLUMNS) {
  const columns = node.columns || [];
  const ranked = columns.map((c, i) => [c, (c.state ? 0 : c.pk ? 1 : c.fk ? 2 : 3), i]);
  ranked.sort((a, b) => a[1] - b[1] || a[2] - b[2]);
  const shown = ranked.slice(0, maxColumns).sort((a, b) => a[2] - b[2]).map((r) => r[0]);
  return { shown, hidden: Math.max(0, columns.length - shown.length) };
}

export function nodeHeight(node, maxColumns = MAX_COLUMNS) {
  if (node.external) return HEADER_HEIGHT + 20;
  const { shown, hidden } = shownColumns(node, maxColumns);
  return HEADER_HEIGHT + (shown.length + (hidden ? 1 : 0)) * ROW_HEIGHT + 8;
}

function neighbourMap(nodes, edges) {
  const ids = new Set(nodes.map((n) => n.name));
  const links = new Map(nodes.map((n) => [n.name, new Set()]));
  for (const e of edges) {
    if (ids.has(e.source) && ids.has(e.target) && e.source !== e.target) {
      links.get(e.source).add(e.target);
      links.get(e.target).add(e.source);
    }
  }
  return links;
}

// Columns are breadth-first distance from the focused or best-connected table; order within a column follows neighbour positions.
export function layoutGraph(nodes, edges, focus = null) {
  const links = neighbourMap(nodes, edges);
  const degree = (name) => links.get(name).size;
  const byDegree = [...nodes].sort((a, b) => degree(b.name) - degree(a.name) || a.name.localeCompare(b.name));
  const layer = new Map();
  const queueRoots = focus && links.has(focus) ? [focus, ...byDegree.map((n) => n.name).filter((n) => n !== focus)] : byDegree.map((n) => n.name);
  const isolated = [];
  let deepest = 0;
  for (const root of queueRoots) {
    if (layer.has(root)) continue;
    if (!links.get(root).size && root !== focus) { isolated.push(root); continue; }
    let frontier = [root];
    layer.set(root, 0);
    while (frontier.length) {
      const next = [];
      for (const name of frontier) {
        for (const other of [...links.get(name)].sort()) {
          if (!layer.has(other)) {
            const depth = layer.get(name) + 1;
            layer.set(other, depth);
            deepest = Math.max(deepest, depth);
            next.push(other);
          }
        }
      }
      frontier = next;
    }
  }
  // Tables with no links share a compact grid instead of each taking a column.
  const gridColumns = Math.max(deepest + 1, Math.ceil(Math.sqrt(isolated.length)));
  isolated.sort().forEach((name, i) => layer.set(name, i % gridColumns));
  const columns = [];
  for (const node of nodes) {
    const index = layer.get(node.name);
    (columns[index] = columns[index] || []).push(node.name);
  }
  const position = new Map();
  columns.forEach((col) => col.sort().forEach((name, i) => position.set(name, i)));
  for (let sweep = 0; sweep < 4; sweep += 1) {
    const reverse = sweep % 2 === 1;
    const ordered = reverse ? [...columns].reverse() : columns;
    for (const col of ordered) {
      if (!col) continue;
      const bary = (name) => {
        const peers = [...links.get(name)].filter((other) => layer.get(other) !== layer.get(name));
        if (!peers.length) return position.get(name);
        return peers.reduce((sum, peer) => sum + position.get(peer), 0) / peers.length;
      };
      col.sort((a, b) => bary(a) - bary(b) || a.localeCompare(b));
      col.forEach((name, i) => position.set(name, i));
    }
  }
  // A hub with many neighbours would make one very tall column, so long columns wrap to stay close to the screen's shape.
  const maxRows = Math.max(6, Math.ceil(Math.sqrt(nodes.length * 1.4)));
  const physical = [];
  columns.forEach((col) => {
    const names = col || [];
    for (let i = 0; i < names.length; i += maxRows) physical.push(names.slice(i, i + maxRows));
  });
  const byName = new Map(nodes.map((n) => [n.name, n]));
  const boxes = new Map();
  let maxY = 0;
  const columnHeights = physical.map((col) => col.reduce((sum, name) => sum + nodeHeight(byName.get(name)) + GAP_Y, 0));
  const tallest = Math.max(1, ...columnHeights);
  physical.forEach((col, x) => {
    let y = (tallest - columnHeights[x]) / 2;
    for (const name of col) {
      const height = nodeHeight(byName.get(name));
      boxes.set(name, { x: 24 + x * (NODE_WIDTH + GAP_X), y: 24 + y, width: NODE_WIDTH, height });
      y += height + GAP_Y;
      maxY = Math.max(maxY, 24 + y);
    }
  });
  const width = 24 + physical.length * NODE_WIDTH + Math.max(0, physical.length - 1) * GAP_X + 24;
  return { boxes, width, height: maxY + 24 };
}

export function edgePath(from, to) {
  if (from === to) {
    const x = from.x + from.width;
    const y = from.y + from.height / 2;
    return `M${x} ${y - 8} C ${x + 44} ${y - 34}, ${x + 44} ${y + 34}, ${x} ${y + 8}`;
  }
  const forward = from.x + from.width <= to.x;
  const backward = to.x + to.width <= from.x;
  const x1 = forward ? from.x + from.width : backward ? from.x : from.x + from.width / 2;
  const x2 = forward ? to.x : backward ? to.x + to.width : to.x + to.width / 2;
  const y1 = from.y + from.height / 2;
  const y2 = to.y + to.height / 2;
  const mid = (x1 + x2) / 2;
  return `M${x1} ${y1} C ${mid} ${y1}, ${mid} ${y2}, ${x2} ${y2}`;
}
