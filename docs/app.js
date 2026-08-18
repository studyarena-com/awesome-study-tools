const DATA_URL = "./data/tools.json";
const QUERY_KEYS = ["q", "category", "region", "ai", "access"];

const ui = {
  form: document.querySelector("#filter-form"),
  search: document.querySelector("#search"),
  category: document.querySelector("#category"),
  region: document.querySelector("#region"),
  aiRole: document.querySelector("#ai-role"),
  access: document.querySelector("#access"),
  clear: document.querySelector("#clear-filters"),
  emptyClear: document.querySelector("#empty-clear"),
  retry: document.querySelector("#retry-load"),
  list: document.querySelector("#tool-list"),
  resultCount: document.querySelector("#result-count"),
  resultsStatus: document.querySelector("#results-status"),
  loading: document.querySelector("#loading-state"),
  error: document.querySelector("#error-state"),
  empty: document.querySelector("#empty-state"),
  total: document.querySelector("#tool-total"),
  coverage: document.querySelector("#catalogue-coverage"),
};

const numberFormat = new Intl.NumberFormat(document.documentElement.lang || "en");
const dateFormat = new Intl.DateTimeFormat(document.documentElement.lang || "en", {
  day: "numeric",
  month: "short",
  year: "numeric",
  timeZone: "UTC",
});

let catalogue = null;

const labelOverrides = new Map([
  ["ai-native", "AI-native"],
  ["native", "AI-native"],
  ["core", "AI-native"],
  ["ai-features", "AI features"],
  ["features", "AI features"],
  ["feature", "AI features"],
  ["assisted", "AI-assisted"],
  ["no-ai", "No AI"],
  ["none", "No AI"],
  ["free", "Free"],
  ["freemium", "Freemium"],
  ["paid", "Paid"],
  ["per-use", "Per use"],
  ["free-for-students", "Free for students"],
  ["open-source", "Open source"],
  ["institutional", "Institutional"],
  ["pay-as-you-go", "Pay as you go"],
  ["active", "Active"],
  ["maintenance", "Maintenance"],
  ["at-risk", "At risk"],
  ["renamed", "Renamed"],
  ["acquired", "Acquired"],
  ["discontinued", "Discontinued"],
  ["defunct", "Discontinued"],
  ["unverified", "Unverified"],
]);

function cleanString(value, fallback = "") {
  return typeof value === "string" && value.trim() ? value.trim() : fallback;
}

function cleanList(value) {
  if (!Array.isArray(value)) return [];

  return [...new Set(value.map((item) => cleanString(item)).filter(Boolean))];
}

function keyFor(value) {
  return cleanString(value)
    .normalize("NFKC")
    .toLocaleLowerCase()
    .replace(/[\s_]+/g, "-")
    .replace(/-+/g, "-");
}

function humanize(value) {
  const key = keyFor(value);
  if (!key) return "Not specified";
  if (labelOverrides.has(key)) return labelOverrides.get(key);

  return key
    .split("-")
    .filter(Boolean)
    .map((part) => part.charAt(0).toLocaleUpperCase() + part.slice(1))
    .join(" ");
}

function searchable(value) {
  return cleanString(value)
    .normalize("NFKD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLocaleLowerCase();
}

function safeWebUrl(value) {
  const raw = cleanString(value);
  if (!raw) return "";

  try {
    const url = new URL(raw);
    return url.protocol === "https:" || url.protocol === "http:" ? url.href : "";
  } catch {
    return "";
  }
}

function normalizeDefinitions(rawDefinitions, referencedIds) {
  const definitions = [];
  const known = new Set();

  if (Array.isArray(rawDefinitions)) {
    rawDefinitions.forEach((item) => {
      if (!item || typeof item !== "object") return;
      const id = keyFor(item.id);
      if (!id || known.has(id)) return;

      known.add(id);
      definitions.push({
        id,
        name: cleanString(item.name, humanize(id)),
        emoji: cleanString(item.emoji),
      });
    });
  }

  referencedIds.forEach((id) => {
    if (!known.has(id)) {
      known.add(id);
      definitions.push({ id, name: humanize(id), emoji: "" });
    }
  });

  return definitions;
}

function normalizeCatalogue(payload) {
  if (!payload || typeof payload !== "object" || !Array.isArray(payload.tools)) {
    throw new Error("The catalogue data does not contain a tools array.");
  }

  const tools = payload.tools
    .filter((item) => item && typeof item === "object")
    .map((item, index) => {
      const categories = cleanList(item.categories).map(keyFor).filter(Boolean);
      const regions = cleanList(item.regions).map(keyFor).filter(Boolean);
      const aiRole = keyFor(item.ai_role);
      const access = keyFor(item.access);
      const status = keyFor(item.status || "active");
      const name = cleanString(item.name);

      if (!name) return null;

      return {
        id: cleanString(item.id, `tool-${index + 1}`),
        name,
        url: safeWebUrl(item.url),
        description: cleanString(
          item.description,
          "No description is available for this entry yet."
        ),
        categories,
        regions,
        aiRole,
        access,
        platforms: cleanList(item.platforms),
        countries: cleanList(item.countries),
        status,
        maintainerAffiliated: item.maintainer_affiliated === true,
        lastReviewed: cleanString(item.last_reviewed),
      };
    })
    .filter(Boolean)
    .sort((a, b) => a.name.localeCompare(b.name, undefined, { sensitivity: "base" }));

  const referencedCategoryIds = new Set(tools.flatMap((tool) => tool.categories));
  const referencedRegionIds = new Set(tools.flatMap((tool) => tool.regions));
  const categories = normalizeDefinitions(payload.categories, referencedCategoryIds);
  const regions = normalizeDefinitions(payload.regions, referencedRegionIds);
  const categoryById = new Map(categories.map((item) => [item.id, item]));
  const regionById = new Map(regions.map((item) => [item.id, item]));

  tools.forEach((tool) => {
    const categoryText = tool.categories
      .map((id) => categoryById.get(id)?.name || humanize(id))
      .join(" ");
    const regionText = tool.regions
      .map((id) => regionById.get(id)?.name || humanize(id))
      .join(" ");

    tool.searchText = searchable(
      [
        tool.name,
        tool.description,
        categoryText,
        regionText,
        tool.aiRole,
        tool.access,
        tool.status,
        ...tool.platforms,
        ...tool.countries,
      ].join(" ")
    );
  });

  return { tools, categories, regions, categoryById, regionById };
}

function createOption(value, label) {
  const option = document.createElement("option");
  option.value = value;
  option.textContent = label;
  return option;
}

function resetOptions(select, firstLabel) {
  select.replaceChildren(createOption("", firstLabel));
}

function populateFilters() {
  resetOptions(ui.category, "All categories");
  resetOptions(ui.region, "All regions");
  resetOptions(ui.aiRole, "Any AI role");
  resetOptions(ui.access, "Any access model");

  catalogue.categories.forEach((item) => {
    const prefix = item.emoji ? `${item.emoji} ` : "";
    ui.category.append(createOption(item.id, `${prefix}${item.name}`));
  });

  catalogue.regions.forEach((item) => {
    const prefix = item.emoji ? `${item.emoji} ` : "";
    ui.region.append(createOption(item.id, `${prefix}${item.name}`));
  });

  const aiRoles = [...new Set(catalogue.tools.map((tool) => tool.aiRole).filter(Boolean))];
  const accessModels = [
    ...new Set(catalogue.tools.map((tool) => tool.access).filter(Boolean)),
  ];

  aiRoles
    .sort((a, b) => humanize(a).localeCompare(humanize(b)))
    .forEach((value) => ui.aiRole.append(createOption(value, humanize(value))));

  accessModels
    .sort((a, b) => humanize(a).localeCompare(humanize(b)))
    .forEach((value) => ui.access.append(createOption(value, humanize(value))));
}

function setControlsDisabled(disabled) {
  [...ui.form.elements].forEach((control) => {
    control.disabled = disabled;
  });
  ui.clear.disabled = disabled;
}

function selectHasValue(select, value) {
  return [...select.options].some((option) => option.value === value);
}

function applyQueryState() {
  const params = new URLSearchParams(window.location.search);
  ui.search.value = cleanString(params.get("q")).slice(0, 240);

  [
    [ui.category, "category"],
    [ui.region, "region"],
    [ui.aiRole, "ai"],
    [ui.access, "access"],
  ].forEach(([select, parameter]) => {
    const value = keyFor(params.get(parameter));
    select.value = value && selectHasValue(select, value) ? value : "";
  });
}

function currentState() {
  return {
    q: ui.search.value.trim(),
    category: ui.category.value,
    region: ui.region.value,
    ai: ui.aiRole.value,
    access: ui.access.value,
  };
}

function hasActiveFilters(state = currentState()) {
  return Object.values(state).some(Boolean);
}

function writeQueryState(state) {
  const url = new URL(window.location.href);
  QUERY_KEYS.forEach((key) => url.searchParams.delete(key));

  QUERY_KEYS.forEach((key) => {
    if (state[key]) url.searchParams.set(key, state[key]);
  });

  const nextUrl = `${url.pathname}${url.search}${url.hash}`;
  window.history.replaceState(null, "", nextUrl);
}

function filteredTools(state) {
  const terms = searchable(state.q).split(/\s+/).filter(Boolean);

  return catalogue.tools.filter((tool) => {
    if (state.category && !tool.categories.includes(state.category)) return false;
    if (state.region && !tool.regions.includes(state.region)) return false;
    if (state.ai && tool.aiRole !== state.ai) return false;
    if (state.access && tool.access !== state.access) return false;
    return terms.every((term) => tool.searchText.includes(term));
  });
}

function createPill(text, className = "", dataStatus = "") {
  const pill = document.createElement("span");
  pill.className = `pill${className ? ` ${className}` : ""}`;
  pill.textContent = text;
  if (dataStatus) pill.dataset.status = dataStatus;
  return pill;
}

function formatDefinitions(ids, definitions) {
  return ids
    .map((id) => {
      const item = definitions.get(id);
      if (!item) return humanize(id);
      return item.emoji ? `${item.emoji} ${item.name}` : item.name;
    })
    .join(", ");
}

function createDetailRow(term, description) {
  const row = document.createElement("div");
  row.className = "detail-row";
  const dt = document.createElement("dt");
  const dd = document.createElement("dd");
  dt.textContent = term;
  dd.textContent = description;
  row.append(dt, dd);
  return row;
}

function reviewedDate(value) {
  const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(value);
  if (!match) return "";

  const year = Number(match[1]);
  const month = Number(match[2]);
  const day = Number(match[3]);
  const date = new Date(Date.UTC(year, month - 1, day));

  if (
    date.getUTCFullYear() !== year ||
    date.getUTCMonth() !== month - 1 ||
    date.getUTCDate() !== day
  ) {
    return "";
  }

  return dateFormat.format(date);
}

function createToolCard(tool) {
  const item = document.createElement("li");
  item.className = "tool-card";
  item.dataset.toolId = tool.id;

  const topline = document.createElement("div");
  topline.className = "card-topline";
  if (tool.aiRole) topline.append(createPill(humanize(tool.aiRole)));
  if (tool.access) topline.append(createPill(humanize(tool.access), "access-pill"));
  if (tool.status && tool.status !== "active") {
    topline.append(createPill(humanize(tool.status), "status-pill", tool.status));
  }
  if (tool.maintainerAffiliated) {
    topline.append(createPill("Maintainer-affiliated", "affiliation-pill"));
  }

  const title = document.createElement("h3");
  title.className = "tool-title";
  if (tool.url) {
    const link = document.createElement("a");
    link.href = tool.url;
    link.rel = "noopener noreferrer";
    link.textContent = tool.name;
    const arrow = document.createElement("span");
    arrow.className = "link-arrow";
    arrow.setAttribute("aria-hidden", "true");
    arrow.textContent = "↗";
    link.append(arrow);
    title.append(link);
  } else {
    title.textContent = tool.name;
  }

  const description = document.createElement("p");
  description.className = "tool-description";
  description.textContent = tool.description;

  const details = document.createElement("dl");
  details.className = "card-details";
  if (tool.categories.length) {
    details.append(
      createDetailRow(
        tool.categories.length === 1 ? "Category" : "Categories",
        formatDefinitions(tool.categories, catalogue.categoryById)
      )
    );
  }
  if (tool.regions.length) {
    details.append(
      createDetailRow(
        tool.regions.length === 1 ? "Region" : "Regions",
        formatDefinitions(tool.regions, catalogue.regionById)
      )
    );
  }
  if (tool.countries.length) {
    details.append(
      createDetailRow(
        tool.countries.length === 1 ? "Country" : "Countries",
        tool.countries.join(", ")
      )
    );
  }
  if (tool.platforms.length) {
    details.append(createDetailRow("Platforms", tool.platforms.join(", ")));
  }

  item.append(topline, title, description);
  if (details.childElementCount) item.append(details);

  const formattedReviewDate = reviewedDate(tool.lastReviewed);
  if (formattedReviewDate) {
    const reviewed = document.createElement("p");
    reviewed.className = "reviewed-date";
    reviewed.textContent = `Reviewed ${formattedReviewDate}`;
    item.append(reviewed);
  }

  return item;
}

function render({ updateUrl = true } = {}) {
  if (!catalogue) return;

  const state = currentState();
  const tools = filteredTools(state);
  const total = catalogue.tools.length;
  const fragment = document.createDocumentFragment();
  tools.forEach((tool) => fragment.append(createToolCard(tool)));
  ui.list.replaceChildren(fragment);

  const visible = numberFormat.format(tools.length);
  const all = numberFormat.format(total);
  ui.resultCount.textContent = `Showing ${visible} of ${all} ${total === 1 ? "tool" : "tools"}`;
  ui.empty.hidden = tools.length !== 0;
  ui.list.hidden = tools.length === 0;
  ui.clear.hidden = !hasActiveFilters(state);
  ui.resultsStatus.setAttribute("aria-busy", "false");

  if (updateUrl) writeQueryState(state);
}

function clearFilters({ focusSearch = true } = {}) {
  ui.form.reset();
  render();
  if (focusSearch) ui.search.focus();
}

function showLoading() {
  setControlsDisabled(true);
  ui.resultsStatus.setAttribute("aria-busy", "true");
  ui.loading.hidden = false;
  ui.error.hidden = true;
  ui.empty.hidden = true;
  ui.list.hidden = true;
  ui.clear.hidden = true;
  ui.resultCount.textContent = "Loading tools…";
}

function showError() {
  setControlsDisabled(true);
  ui.resultsStatus.setAttribute("aria-busy", "false");
  ui.loading.hidden = true;
  ui.error.hidden = false;
  ui.empty.hidden = true;
  ui.list.hidden = true;
  ui.clear.hidden = true;
  ui.resultCount.textContent = "Catalogue unavailable";
  ui.total.textContent = "—";
  ui.coverage.textContent = "Catalogue coverage is temporarily unavailable.";
}

async function loadCatalogue() {
  showLoading();

  try {
    const response = await fetch(DATA_URL, {
      cache: "no-cache",
      headers: { Accept: "application/json" },
    });
    if (!response.ok) throw new Error(`Catalogue request failed with ${response.status}.`);

    const payload = await response.json();
    catalogue = normalizeCatalogue(payload);
    populateFilters();
    applyQueryState();
    setControlsDisabled(false);

    ui.loading.hidden = true;
    ui.error.hidden = true;
    ui.total.textContent = numberFormat.format(catalogue.tools.length);
    const categoryCount = numberFormat.format(catalogue.categories.length);
    const regionCount = numberFormat.format(catalogue.regions.length);
    ui.coverage.textContent = `${categoryCount} ${
      catalogue.categories.length === 1 ? "category" : "categories"
    } across ${regionCount} ${catalogue.regions.length === 1 ? "region" : "regions"}`;
    render({ updateUrl: false });
  } catch (error) {
    console.error("Unable to load the study-tool catalogue.", error);
    catalogue = null;
    showError();
  }
}

ui.form.addEventListener("submit", (event) => event.preventDefault());
ui.search.addEventListener("input", () => render());
[ui.category, ui.region, ui.aiRole, ui.access].forEach((select) => {
  select.addEventListener("change", () => render());
});
ui.clear.addEventListener("click", () => clearFilters());
ui.emptyClear.addEventListener("click", () => clearFilters());
ui.retry.addEventListener("click", () => loadCatalogue());

window.addEventListener("popstate", () => {
  if (!catalogue) return;
  applyQueryState();
  render({ updateUrl: false });
});

loadCatalogue();
