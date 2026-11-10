// Hash routes: #/run/<id>/findings?severity=high&f=<id>. Every screen state is a deep link.

export function parseHash(hash) {
  let text = String(hash || "");
  if (text.startsWith("#")) text = text.slice(1);
  const [pathPart, ...rest] = text.split("?");
  const segments = pathPart.split("/").filter(Boolean).map(decodeURIComponent);
  const query = {};
  const params = new URLSearchParams(rest.join("?"));
  params.forEach((value, key) => { query[key] = value; });
  return { segments, query };
}

export function routeHref(segments, query) {
  let hash = "#/" + segments.map((part) => encodeURIComponent(part)).join("/");
  const params = new URLSearchParams();
  for (const [key, value] of Object.entries(query || {})) {
    if (value !== undefined && value !== null && value !== "") params.set(key, value);
  }
  const text = params.toString();
  return text ? `${hash}?${text}` : hash;
}

export function navigate(segments, query, options = {}) {
  const href = routeHref(segments, query);
  if (options.replace) window.location.replace(href);
  else window.location.hash = href;
}

export function replaceQuery(segments, query) { navigate(segments, query, { replace: true }); }
