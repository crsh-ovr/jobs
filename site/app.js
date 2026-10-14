// shane.jobs — reads data/jobs.json, renders + filters client-side. No build step.

const REL_LABELS = { worked: "worked", known: "know people", watchlist: "watchlist" };
const LEVEL_ORDER = ["intern", "junior", "mid", "senior", "staff", "principal", "lead", "manager", "director", "vp"];
const UMBRELLA_LABELS = {
  product_design: "Product / Design",
  engineering: "Engineering",
  gtm_revenue: "GTM / Revenue",
  support: "Support",
};
const NEW_DAYS = 7;

const state = { jobs: [], meta: null };

// Prod serves index.html at the site root with data/ as a sibling; local `http.server`
// serves it under /site/. Try both so either works.
async function loadJSON(name) {
  for (const base of ["./data/", "../data/"]) {
    try {
      const res = await fetch(base + name, { cache: "no-store" });
      if (res.ok) return await res.json();
    } catch (_) { /* try next */ }
  }
  return null;
}

function daysAgo(iso) {
  if (!iso) return Infinity;
  const then = new Date(iso + "T00:00:00Z").getTime();
  return (Date.now() - then) / 86400000;
}

function el(tag, cls, text) {
  const n = document.createElement(tag);
  if (cls) n.className = cls;
  if (text != null) n.textContent = text;
  return n;
}

// Job URLs come from third-party ATS data. Only allow http(s) so a malicious posting
// can't smuggle a javascript:/data: URL into an href (DOM-based XSS on click).
function safeUrl(url) {
  try {
    const u = new URL(url, location.href);
    return u.protocol === "https:" || u.protocol === "http:" ? u.href : "#";
  } catch (_) {
    return "#";
  }
}

function card(job) {
  const a = el("a", "job");
  a.href = safeUrl(job.url);
  a.target = "_blank";
  a.rel = "noopener noreferrer";
  if (job.company_tier === "featured") a.classList.add("featured-card");
  a.classList.add("rel-" + (job.company_relationship || "watchlist"));

  const top = el("div", "job-top");
  const left = el("div");
  left.appendChild(el("span", "job-title", job.title || "Untitled role"));
  left.appendChild(document.createTextNode(" @ "));
  left.appendChild(el("span", "company", job.company || ""));
  top.appendChild(left);
  top.appendChild(el("span", "apply", "apply →"));
  a.appendChild(top);

  const meta = el("div", "job-meta");
  if (job.level) meta.appendChild(el("span", "tag level", job.level));
  const rel = job.company_relationship || "watchlist";
  meta.appendChild(el("span", "badge-rel rel-" + rel, REL_LABELS[rel] || rel));
  (job.industries || []).forEach((i) => meta.appendChild(el("span", "tag industry", i)));
  if (job.location) meta.appendChild(el("span", "tag", job.location));
  if (job.remote) meta.appendChild(el("span", "tag remote", "remote"));
  if (daysAgo(job.first_seen) <= NEW_DAYS) meta.appendChild(el("span", "tag new", "new"));
  if (job.description_available === false) {
    meta.appendChild(el("span", "tag no-desc", "full description on company site"));
  }
  a.appendChild(meta);
  return a;
}

function uniqueSorted(values) {
  return [...new Set(values.filter(Boolean))].sort();
}

function populateFilters() {
  const umb = new Set();
  const inds = new Set();
  const levels = new Set();
  const companies = new Set();
  state.jobs.forEach((j) => {
    (j.umbrellas || []).forEach((u) => umb.add(u));
    (j.industries || []).forEach((i) => inds.add(i));
    if (j.level) levels.add(j.level);
    if (j.company) companies.add(j.company);
  });

  const umbSel = document.getElementById("f-umbrella");
  [...umb].sort().forEach((u) => {
    const o = el("option", null, UMBRELLA_LABELS[u] || u);
    o.value = u;
    umbSel.appendChild(o);
  });
  const indSel = document.getElementById("f-industry");
  uniqueSorted([...inds]).forEach((i) => {
    const o = el("option", null, i); o.value = i; indSel.appendChild(o);
  });
  const lvlSel = document.getElementById("f-level");
  LEVEL_ORDER.filter((l) => levels.has(l)).forEach((l) => {
    const o = el("option", null, l); o.value = l; lvlSel.appendChild(o);
  });
  const coSel = document.getElementById("f-company");
  uniqueSorted([...companies]).forEach((c) => {
    const o = el("option", null, c); o.value = c; coSel.appendChild(o);
  });
}

function currentFilters() {
  return {
    q: document.getElementById("q").value.trim().toLowerCase(),
    umbrella: document.getElementById("f-umbrella").value,
    industry: document.getElementById("f-industry").value,
    level: document.getElementById("f-level").value,
    rel: document.getElementById("f-rel").value,
    company: document.getElementById("f-company").value,
    remote: document.getElementById("f-remote").checked,
  };
}

function matches(job, f) {
  if (f.q && !(`${job.title} ${job.company}`.toLowerCase().includes(f.q))) return false;
  if (f.umbrella && !(job.umbrellas || []).includes(f.umbrella)) return false;
  if (f.industry && !(job.industries || []).includes(f.industry)) return false;
  if (f.level && job.level !== f.level) return false;
  if (f.rel && job.company_relationship !== f.rel) return false;
  if (f.company && job.company !== f.company) return false;
  if (f.remote && !job.remote) return false;
  return true;
}

function syncURL(f) {
  const p = new URLSearchParams();
  Object.entries(f).forEach(([k, v]) => {
    if (v && v !== false) p.set(k, v === true ? "1" : v);
  });
  const qs = p.toString();
  history.replaceState(null, "", qs ? `?${qs}` : location.pathname);
}

function restoreFromURL() {
  const p = new URLSearchParams(location.search);
  const set = (id, key) => { const v = p.get(key); if (v) document.getElementById(id).value = v; };
  set("q", "q");
  set("f-umbrella", "umbrella");
  set("f-industry", "industry");
  set("f-level", "level");
  set("f-rel", "rel");
  set("f-company", "company");
  if (p.get("remote")) document.getElementById("f-remote").checked = true;
}

function render() {
  const f = currentFilters();
  syncURL(f);
  const list = document.getElementById("job-list");
  list.innerHTML = "";
  const filtered = state.jobs.filter((j) => matches(j, f));
  filtered.forEach((j) => list.appendChild(card(j)));
  document.getElementById("empty").hidden = filtered.length > 0;
  document.getElementById("count").textContent =
    `${filtered.length} role${filtered.length === 1 ? "" : "s"} · ${new Set(filtered.map((j) => j.company)).size} companies`;
}

function renderFeatured() {
  const featured = state.jobs.filter((j) => j.company_tier === "featured");
  if (!featured.length) return;
  const sec = document.getElementById("featured");
  const list = document.getElementById("featured-list");
  featured.forEach((j) => list.appendChild(card(j)));
  sec.hidden = false;
}

function renderMeta() {
  if (!state.meta) return;
  const when = state.meta.generated_at ? new Date(state.meta.generated_at) : null;
  const ok = (state.meta.adapters || []).filter((a) => a.ok).length;
  const total = (state.meta.adapters || []).length;
  const parts = [];
  if (when) parts.push(`last updated ${when.toISOString().slice(0, 10)}`);
  if (total) parts.push(`${ok}/${total} boards ok`);
  parts.push(`${state.jobs.length} roles tracked`);
  document.getElementById("meta").textContent = parts.join(" · ");
}

async function init() {
  const data = await loadJSON("jobs.json");
  state.meta = await loadJSON("meta.json");
  if (!data || !Array.isArray(data.jobs)) {
    document.getElementById("empty").hidden = false;
    document.getElementById("empty").textContent = "could not load jobs data.";
    return;
  }
  state.jobs = data.jobs;

  populateFilters();
  restoreFromURL();
  renderFeatured();
  renderMeta();
  render();

  ["q", "f-umbrella", "f-industry", "f-level", "f-rel", "f-company", "f-remote"].forEach((id) => {
    const node = document.getElementById(id);
    node.addEventListener(id === "q" ? "input" : "change", render);
  });
  document.getElementById("reset").addEventListener("click", () => {
    ["q", "f-umbrella", "f-industry", "f-level", "f-rel", "f-company"].forEach((id) => {
      document.getElementById(id).value = "";
    });
    document.getElementById("f-remote").checked = false;
    render();
  });
}

init();
