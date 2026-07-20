/* Résumé Studio — frontend logic (framework-free). */

"use strict";

/* ----------------------------------------------------------------- helpers */

const $ = (sel) => document.querySelector(sel);

function el(tag, attrs = {}, ...children) {
  const node = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (k === "class") node.className = v;
    else if (k === "html") node.innerHTML = v;
    else if (k.startsWith("on") && typeof v === "function") {
      node.addEventListener(k.slice(2), v);
    } else if (v !== null && v !== undefined && v !== false) {
      node.setAttribute(k, v);
    }
  }
  for (const c of children.flat()) {
    if (c == null) continue;
    node.appendChild(typeof c === "string" ? document.createTextNode(c) : c);
  }
  return node;
}

const uid = () => {
  const a = new Uint8Array(7);
  crypto.getRandomValues(a);
  return Array.from(a, b => b.toString(36)).join('');
};

function label(text) {
  return el("label", { class: "lbl" }, text);
}

function textInput(placeholder, value, onInput, type = "text") {
  const input = el("input", {
    type,
    placeholder: placeholder || "",
    value: value ?? "",
  });
  input.addEventListener("input", (e) => onInput(e.target.value));
  return input;
}

function textareaInput(placeholder, value, onInput) {
  const ta = el("textarea", { placeholder: placeholder || "" }, value ?? "");
  ta.addEventListener("input", (e) => onInput(e.target.value));
  return ta;
}

function fieldBlock(text, inputEl) {
  return el("div", { class: "field-block" }, label(text), inputEl);
}

function iconBtn(symbol, onClick) {
  return el("button", {
    class: "icon-btn",
    type: "button",
    title: "Remove",
    onclick: onClick,
  }, symbol);
}

function addSmallBtn(text, onClick) {
  return el("button", { class: "add-btn", type: "button", onclick: onClick }, text);
}

/* ----------------------------------------------------------- section types */

const SECTION_TYPES = {
  summary: { label: "Summary", title: "Professional Summary", addLabel: "Add bullet" },
  experience: { label: "Experience", title: "Experience", addLabel: "Add experience entry" },
  education: { label: "Education", title: "Education", addLabel: "Add education entry" },
  projects: { label: "Projects", title: "Projects", addLabel: "Add project entry" },
  skills: { label: "Skills", title: "Skills", addLabel: "Add skill entry" },
  certifications: { label: "Certifications", title: "Certifications", addLabel: "Add certification entry" },
  custom: { label: "Custom", title: "Custom Section", addLabel: "Add entry" },
};

function newEntry(type) {
  switch (type) {
    case "summary":
      return { text: "" };
    case "experience":
      return { company: "", position: "", start_date: "", end_date: "", location: "", summary: "", highlights: [] };
    case "education":
      return { institution: "", area: "", degree: "", start_date: "", end_date: "", location: "", highlights: [] };
    case "projects":
      return { name: "", date: "", summary: "", highlights: [] };
    case "skills":
      return { label: "", details: "" };
    case "certifications":
      return { bullet: "" };
    case "custom":
      return { name: "", date: "", summary: "", highlights: [] };
    default:
      return { text: "" };
  }
}

/* --------------------------------------------------------------- state */

const state = {
  cv: {
    name: "", headline: "", location: "", email: "", phone: "",
    website: "", photo: "", social_networks: [],
    sections: [],
  },
  design: { theme: "engineeringresumes", pageSize: "a4", showFooter: false, accent: "#4f46e5" },
  locale: {},
  settings: {},
  ui: { autopreview: true },
};

let previewUrl = null;
let activeField = null;

function setActiveField(el) {
  activeField = el;
}

function formatActiveField(before, after) {
  const el = activeField;
  if (!el || (el.tagName !== "TEXTAREA" && el.tagName !== "INPUT")) return;
  const start = el.selectionStart;
  const end = el.selectionEnd;
  const text = el.value;
  const selected = text.substring(start, end);
  const replacement = before + selected + after;
  const newValue = text.substring(0, start) + replacement + text.substring(end);
  el.value = newValue;
  const newPos = start + before.length + selected.length;
  el.setSelectionRange(newPos, newPos);
  el.focus();
  el.dispatchEvent(new Event("input", { bubbles: true }));
  schedulePreview();
  saveState();
}

/* ----------------------------------------------------------- API calls */

async function apiGet(url) {
  const r = await fetch(url);
  return r.json();
}

async function renderPdf(url, payload) {
  const r = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!r.ok) {
    const data = await r.json().catch(() => ({}));
    throw new Error(JSON.stringify(data.errors || [data.detail || "Render failed"]));
  }
  return r.blob();
}

function buildPayload() {
  const cv = state.cv;
  const sections = {};
  for (const s of cv.sections) {
    sections[toTitleCase(s.title)] = entriesToData(s.type, s.entries);
  }
  const out = {
    cv: {
      name: cv.name || null,
      headline: cv.headline || null,
      location: cv.location || null,
      email: cv.email || null,
      phone: cv.phone || null,
      website: cv.website || null,
      photo: cv.photo || null,
      social_networks: (cv.social_networks || []).filter(
        (n) => n.network || n.username
      ).map((n) => ({ network: n.network, username: n.username })),
      sections,
    },
    design: {
      theme: state.design.theme,
      page: {
        size: "a4",
        show_footer: state.design.showFooter,
        show_top_note: false,
      },
      colors: {
        section_titles: state.design.accent,
        links: state.design.accent,
        connections: state.design.accent,
      },
    },
    locale: state.locale,
    settings: state.settings,
  };
  return out;
}

function entriesToData(type, entries) {
  const clean = (obj) => {
    const o = {};
    for (const [k, v] of Object.entries(obj)) {
      if (v === "" || v === null || v === undefined) continue;
      if (Array.isArray(v) && v.length === 0) continue;
      o[k] = v;
    }
    return o;
  };
  if (type === "summary") {
    return entries.map((e) => e.text).filter((t) => t.trim() !== "");
  }
  return entries.map((e) => clean(e)).filter((o) => Object.keys(o).length > 0);
}

/* --------------------------------------------------------- preview / download */

let previewTimer = null;
function schedulePreview() {
  if (!$(AUTOPREVIEW_CHECKBOX).checked) return;
  clearTimeout(previewTimer);
  previewTimer = setTimeout(updatePreview, 700);
}

async function updatePreview() {
  const overlay = $("#preview-empty");
  overlay.classList.remove("hidden");
  try {
    const blob = await renderPdf("/api/preview", buildPayload());
    if (previewUrl) URL.revokeObjectURL(previewUrl);
    previewUrl = URL.createObjectURL(blob);
    $("#preview").src = previewUrl;
    overlay.classList.add("hidden");
  } catch (err) {
    overlay.classList.add("hidden");
    showToast(parseErrors(err), true);
  }
}

async function downloadPdf() {
  try {
    const blob = await renderPdf("/api/render", buildPayload());
    const url = URL.createObjectURL(blob);
    const a = el("a", { href: url, download: filenameFromState() });
    document.body.appendChild(a);
    a.click();
    a.remove();
    setTimeout(() => URL.revokeObjectURL(url), 4000);
    showToast("PDF downloaded.");
  } catch (err) {
    showToast(parseErrors(err), true);
  }
}

function filenameFromState() {
  const n = (state.cv.name || "Resume").trim().replace(/\s+/g, "_");
  return `${n || "Resume"}.pdf`;
}

function parseErrors(err) {
  try {
    const arr = JSON.parse(err.message);
    if (Array.isArray(arr)) return arr.join("\n");
  } catch {}
  return err.message;
}

let toastTimer = null;
function showToast(msg, isError = false) {
  const t = $("#toast");
  const lines = String(msg).split("\n").filter(Boolean);
  t.innerHTML = "";
  if (lines.length > 1) {
    t.appendChild(el("div", {}, "Please fix the following:"));
    const ul = el("ul");
    lines.forEach((l) => ul.appendChild(el("li", {}, l)));
    t.appendChild(ul);
  } else {
    t.textContent = lines[0] || msg;
  }
  t.className = "toast show" + (isError ? " error" : "");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => (t.className = "toast"), 5000);
}

/* ----------------------------------------------------------- form rendering */

function renderAll() {
  const editor = $(EDITOR_SELECT);
  editor.innerHTML = "";
  editor.appendChild(renderBasics());
  editor.appendChild(renderSocial());
  state.cv.sections.forEach((section, idx) => {
    editor.appendChild(renderSection(section, idx));
  });
  editor.appendChild(renderAddSection());
}

function renderBasics() {
  const cv = state.cv;
  const card = el("div", { class: "card" });
  card.appendChild(
    el("div", { class: "card-head" }, el("div", { class: "card-title" },
      el("span", { class: "dot" }), "Basics"))
  );
  card.appendChild(
    el("div", { class: "grid-2" },
      fieldBlock("Full name", textInput("Jane Doe", cv.name, (v) => { cv.name = v; schedulePreview(); saveState(); })),
      fieldBlock("Headline", textInput("Software Engineer", cv.headline, (v) => { cv.headline = v; schedulePreview(); saveState(); }))
    )
  );
  card.appendChild(
    el("div", { class: "grid-2" },
      fieldBlock("Location", textInput("City, Country", cv.location, (v) => { cv.location = v; schedulePreview(); saveState(); })),
      fieldBlock("Email", textInput("you@example.com", cv.email, (v) => { cv.email = v; schedulePreview(); saveState(); }, "email"))
    )
  );
  card.appendChild(
    el("div", { class: "grid-2" },
      fieldBlock("Phone", textInput("+1 555 123 4567", cv.phone, (v) => { cv.phone = v; schedulePreview(); saveState(); }, "tel")),
      fieldBlock("Website", textInput("https://yoursite.com", cv.website, (v) => { cv.website = v; schedulePreview(); saveState(); }, "url"))
    )
  );
  return card;
}

function renderSocial() {
  const card = el("div", { class: "card" });
  card.appendChild(
    el("div", { class: "card-head" }, el("div", { class: "card-title" },
      el("span", { class: "dot" }), "Social networks"))
  );
  const list = el("div");
  state.cv.social_networks.forEach((net, i) => {
    const row = el("div", { class: "grid-2", style: "margin-bottom:8px" },
      textInput("LinkedIn", net.network, (v) => { net.network = v; schedulePreview(); saveState(); }),
      el("div", { style: "display:flex;gap:8px" },
        textInput("username or url", net.username, (v) => { net.username = v; schedulePreview(); saveState(); }),
        iconBtn("×", () => { state.cv.social_networks.splice(i, 1); renderAll(); saveState(); })
      )
    );
    list.appendChild(row);
  });
  card.appendChild(list);
  card.appendChild(
    addSmallBtn("Add social network", () => {
      state.cv.social_networks.push({ network: "", username: "" });
      renderAll();
      saveState();
    })
  );
  return card;
}

function renderSection(section, idx) {
  const card = el("div", { class: "card" });
  const titleInput = textInput("Section title", section.title, (v) => {
    section.title = v; schedulePreview(); saveState();
  });
  titleInput.style.fontWeight = "700";
  titleInput.style.fontSize = "15px";
  titleInput.style.border = "none";
  titleInput.style.padding = "0";
  titleInput.style.background = "transparent";
  titleInput.style.boxShadow = "none";
  titleInput.addEventListener("focus", () => (titleInput.style.border = "1px solid var(--line-strong)"));
  titleInput.addEventListener("blur", () => (titleInput.style.border = "none"));

  card.appendChild(
    el("div", { class: "card-head" },
      el("div", { class: "card-title" }, el("span", { class: "dot" }), titleInput),
      el("div", { class: "card-controls" },
        el("button", {
          class: "card-move", type: "button", title: "Move up", disabled: idx === 0,
          onclick: () => moveSection(idx, idx - 1),
        }, "↑"),
        el("button", {
          class: "card-move", type: "button", title: "Move down",
          disabled: idx === state.cv.sections.length - 1,
          onclick: () => moveSection(idx, idx + 1),
        }, "↓"),
        el("button", { class: "card-remove", type: "button", onclick: () => {
          state.cv.sections.splice(idx, 1); renderAll(); saveState();
        } }, "Remove")
      )
    )
  );

  if (section.type === "summary") {
    if (!section.entries.length) section.entries.push(newEntry("summary"));
    const summaryArea = textareaInput("Write a short professional summary…", section.entries[0].text, (v) => {
      section.entries[0].text = v;
      summaryArea.style.height = "auto";
      summaryArea.style.height = summaryArea.scrollHeight + "px";
      schedulePreview(); saveState();
    });
    summaryArea.style.minHeight = "160px";
    summaryArea.style.lineHeight = "1.6";
    requestAnimationFrame(() => {
      summaryArea.style.height = "auto";
      summaryArea.style.height = summaryArea.scrollHeight + "px";
    });
    card.appendChild(fieldBlock("Summary", summaryArea));
    return card;
  }

  section.entries.forEach((entry, eIdx) => {
    card.appendChild(renderEntry(section.type, entry, () => { renderAll(); saveState(); }));
  });

  card.appendChild(
    addSmallBtn(SECTION_TYPES[section.type].addLabel, () => {
      section.entries.push(newEntry(section.type));
      renderAll(); saveState();
    })
  );
  return card;
}

function renderEntry(type, entry, rerender) {
  const node = el("div", { class: "entry" });
  node.appendChild(
    el("div", { class: "entry-head" },
      el("span", {}, SECTION_TYPES[type].label + " entry"),
      el("button", { class: "entry-remove", type: "button", onclick: () => {
        const sec = currentSectionOf(entry);
        if (sec) {
          const i = sec.entries.indexOf(entry);
          if (i >= 0) sec.entries.splice(i, 1);
        }
        rerender();
      } }, "Remove")
    )
  );

  if (type === "summary") {
    node.appendChild(fieldBlock("Bullet / line", textareaInput("One sentence about you…", entry.text, (v) => { entry.text = v; schedulePreview(); saveState(); })));
  } else if (type === "experience") {
    node.appendChild(
      el("div", { class: "grid-2" },
        fieldBlock("Company", textInput("Acme Inc.", entry.company, (v) => { entry.company = v; schedulePreview(); saveState(); })),
        fieldBlock("Position", textInput("Engineer", entry.position, (v) => { entry.position = v; schedulePreview(); saveState(); }))
      )
    );
    node.appendChild(dateRow(entry));
    node.appendChild(fieldBlock("Location", textInput("City", entry.location, (v) => { entry.location = v; schedulePreview(); saveState(); })));
    node.appendChild(fieldBlock("Summary (optional)", textareaInput("Short description…", entry.summary, (v) => { entry.summary = v; schedulePreview(); saveState(); })));
    node.appendChild(renderHighlights(entry, type));
  } else if (type === "education") {
    const instArea = textareaInput("University", entry.institution, (v) => { entry.institution = v; schedulePreview(); saveState(); });
    instArea.style.minHeight = "52px";
    instArea.style.lineHeight = "1.5";
    node.appendChild(fieldBlock("Institution", instArea));
    node.appendChild(fieldBlock("Degree", textInput("B.Sc.", entry.degree, (v) => { entry.degree = v; schedulePreview(); saveState(); })));
    node.appendChild(fieldBlock("Area", textInput("Computer Science", entry.area, (v) => { entry.area = v; schedulePreview(); saveState(); })));
    node.appendChild(fieldBlock("Location", textInput("City", entry.location, (v) => { entry.location = v; schedulePreview(); saveState(); })));
    node.appendChild(dateRow(entry));
    node.appendChild(renderHighlights(entry, type));
  } else if (type === "projects") {
    const nameArea = textareaInput("Project name", entry.name, (v) => { entry.name = v; schedulePreview(); saveState(); });
    nameArea.style.minHeight = "52px";
    nameArea.style.lineHeight = "1.5";
    node.appendChild(fieldBlock("Name", nameArea));
    node.appendChild(fieldBlock("Date (optional)", textInput("2024-11", entry.date, (v) => { entry.date = v; schedulePreview(); saveState(); })));
    node.appendChild(fieldBlock("Summary", textareaInput("What it does…", entry.summary, (v) => { entry.summary = v; schedulePreview(); saveState(); })));
    node.appendChild(renderHighlights(entry, type));
  } else if (type === "skills") {
    node.appendChild(fieldBlock("Label", textInput("Languages", entry.label, (v) => { entry.label = v; schedulePreview(); saveState(); })));
    node.appendChild(
      fieldBlock("Details", textareaInput("Python, Go, Rust, …", entry.details, (v) => { entry.details = v; schedulePreview(); saveState(); }))
    );
  } else if (type === "certifications") {
    node.appendChild(fieldBlock("Certification", textareaInput("AWS Certified …", entry.bullet, (v) => { entry.bullet = v; schedulePreview(); saveState(); })));
  } else if (type === "custom") {
    node.appendChild(
      el("div", { class: "grid-2" },
        fieldBlock("Title", textInput("Item title", entry.name, (v) => { entry.name = v; schedulePreview(); saveState(); })),
        fieldBlock("Date (optional)", textInput("2024", entry.date, (v) => { entry.date = v; schedulePreview(); saveState(); }))
      )
    );
    node.appendChild(fieldBlock("Summary", textareaInput("Description…", entry.summary, (v) => { entry.summary = v; schedulePreview(); saveState(); })));
    node.appendChild(renderHighlights(entry, type));
  }
  return node;
}

function dateRow(entry) {
  return el("div", { class: "grid-2" },
    fieldBlock("Start date", textInput("2021-01 or 2021", entry.start_date, (v) => { entry.start_date = v; schedulePreview(); saveState(); })),
    fieldBlock("End date", textInput("present or 2023-05", entry.end_date, (v) => { entry.end_date = v; schedulePreview(); saveState(); }))
  );
}

function renderHighlights(entry, type) {
  const wrap = el("div", { class: "field-block" });
  wrap.appendChild(label("Highlights"));
  const list = el("div");
  const minHeight = type === "experience" ? "96px" : "38px";
  (entry.highlights || []).forEach((h, i) => {
    const input = textareaInput("Achievement or responsibility", h, (v) => {
      entry.highlights[i] = v;
      input.style.height = "auto";
      input.style.height = input.scrollHeight + "px";
      schedulePreview(); saveState();
    });
    input.style.minHeight = minHeight;
    input.style.lineHeight = "1.5";
    const item = el("div", { class: "list-item" },
      input,
      iconBtn("×", () => { entry.highlights.splice(i, 1); renderAll(); })
    );
    list.appendChild(item);
  });
  wrap.appendChild(list);
  wrap.appendChild(addSmallBtn("Add highlight", () => {
    entry.highlights.push(""); renderAll(); saveState();
  }));
  return wrap;
}

function renderAddSection() {
  const wrap = el("div", { class: "section-add" });
  const select = el("select");
  for (const [key, meta] of Object.entries(SECTION_TYPES)) {
    select.appendChild(el("option", { value: key }, meta.label));
  }
  wrap.appendChild(select);
  wrap.appendChild(
    el("button", { class: "btn primary", type: "button", onclick: () => {
      const type = select.value;
      state.cv.sections.push({
        title: SECTION_TYPES[type].title,
        type,
        entries: [newEntry(type)],
      });
      renderAll(); saveState();
    } }, "Add section")
  );
  return wrap;
}

function currentSectionOf(entry) {
  return state.cv.sections.find((s) => s.entries.includes(entry));
}

function moveSection(from, to) {
  if (to < 0 || to >= state.cv.sections.length) return;
  const arr = state.cv.sections;
  [arr[from], arr[to]] = [arr[to], arr[from]];
  renderAll();
  schedulePreview();
  saveState();
}

/* ----------------------------------------------------------- load defaults */

function inferType(entries) {
  if (!entries || entries.length === 0) return "experience";
  const first = entries[0];
  if (typeof first === "string") return "summary";
  if ("company" in first && "position" in first) return "experience";
  if ("institution" in first) return "education";
  if ("label" in first && "details" in first) return "skills";
  if ("bullet" in first) return "certifications";
  if ("name" in first) return "projects";
  return "experience";
}

function convertEntries(type, entries) {
  if (type === "summary") {
    const first = entries[0];
    return [{ text: typeof first === "string" ? first : (first?.text || "") }];
  }
  return entries.map((e) => {
    const o = {};
    for (const [k, v] of Object.entries(e)) {
      if (k === "highlights") o.highlights = Array.isArray(v) ? [...v] : [];
      else o[k] = v;
    }
    if (!o.highlights) o.highlights = [];
    return o;
  });
}

function applyDefaults(data) {
  const cv = data.cv || {};
  state.cv.name = cv.name || "";
  state.cv.headline = cv.headline || "";
  state.cv.location = cv.location || "";
  state.cv.email = cv.email || "";
  state.cv.phone = cv.phone || "";
  state.cv.website = cv.website || "";
  state.cv.photo = cv.photo || "";
  state.cv.social_networks = (cv.social_networks || []).map((n) => ({ ...n }));
  state.cv.sections = Object.entries(cv.sections || {}).map(([title, entries]) => {
    const type = inferType(entries);
    return { title: toTitleCase(title), type, entries: convertEntries(type, entries) };
  });

  const design = data.design || {};
  state.design.theme = design.theme || "engineeringresumes";
  state.design.pageSize = "a4";
  state.design.showFooter = !!(design.page && design.page.show_footer);
  const accent =
    (design.colors && (design.colors.section_titles || design.colors.name)) || "#4f46e5";
  state.design.accent = toHex(accent) === "#000000" ? "#4f46e5" : toHex(accent);

  state.locale = data.locale || {};
  state.settings = data.settings || {};
}

function saveState() {
  try {
    localStorage.setItem("rendercv_state", JSON.stringify({
      cv: state.cv,
      design: state.design,
      locale: state.locale,
      settings: state.settings,
      ui: state.ui,
    }));
  } catch {}
}

function loadState() {
  try {
    const raw = localStorage.getItem("rendercv_state");
    if (!raw) return null;
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

function mergeState(saved) {
  if (!saved) return;
  if (saved.cv) {
    state.cv = { ...state.cv, ...saved.cv };
    if (saved.cv.social_networks) state.cv.social_networks = saved.cv.social_networks;
    if (saved.cv.sections) state.cv.sections = saved.cv.sections;
  }
  if (saved.design) state.design = { ...state.design, ...saved.design };
  if (saved.locale) state.locale = { ...state.locale, ...saved.locale };
  if (saved.settings) state.settings = { ...state.settings, ...saved.settings };
  if (saved.ui) state.ui = { ...state.ui, ...saved.ui };
}

/* ----------------------------------------------------------- bootstrap */

async function init() {
  try {
    const [defaults, themes] = await Promise.all([
      apiGet("/api/defaults"),
      apiGet("/api/themes"),
    ]);

    applyDefaults(defaults);
    const saved = loadState();
    if (saved) {
      mergeState(saved);
    }

    const themeSel = $(THEME_SELECT);
    (themes.themes || []).forEach((t) => {
      themeSel.appendChild(el("option", { value: t }, themeDisplayName(t)));
    });

    const validThemes = new Set((themes.themes || []).map(String));
    if (!validThemes.has(state.design.theme)) {
      state.design.theme = "engineeringresumes";
    }
    themeSel.value = state.design.theme;
    $("#accent-color").value = toHex(state.design.accent);
    $(AUTOPREVIEW_CHECKBOX).checked = state.ui.autopreview !== false;

    themeSel.addEventListener("change", (e) => {
      state.design.theme = e.target.value;
      updatePreview();
      saveState();
    });
    $("#accent-color").addEventListener("input", (e) => {
      state.design.accent = e.target.value;
      schedulePreview();
      saveState();
    });
    $(AUTOPREVIEW_CHECKBOX).addEventListener("change", (e) => {
      state.ui.autopreview = e.target.checked;
      saveState();
    });
    $("#preview-btn").addEventListener("click", () => {
      updatePreview();
      saveState();
    });
    $("#download-btn").addEventListener("click", () => {
      downloadPdf();
      saveState();
    });
    document.querySelector(BOLD_BUTTON).addEventListener("click", () => {
      formatActiveField("**", "**");
      saveState();
    });
    document.querySelector(".format-toolbar--global [data-action='italic']").addEventListener("click", () => {
      formatActiveField("*", "*");
      saveState();
    });
    $(EDITOR_SELECT).addEventListener("focusin", (e) => {
      if (e.target.tagName === "TEXTAREA" || e.target.tagName === "INPUT") setActiveField(e.target);
    });

    renderAll();
    updatePreview();
  } catch (err) {
    showToast("Failed to load: " + err.message, true);
  }
}

function toHex(color) {
  if (!color) return "#4f46e5";
  if (color.startsWith("#")) return color;
  const m = color.match(/(\d+),\s*(\d+),\s*(\d+)/);
  if (m) {
    const h = (n) => Number.parseInt(n, 10).toString(16).padStart(2, "0");
    return "#" + h(m[1]) + h(m[2]) + h(m[3]);
  }
  return "#4f46e5";
}

function toTitleCase(str) {
  return String(str || "")
    .trim()
    .replace(/\w\S*/g, (w) => w.charAt(0).toUpperCase() + w.slice(1).toLowerCase());
}

function themeDisplayName(name) {
  const map = {
    classic: "Classic",
    ember: "Ember",
    engineeringclassic: "Engineering Classic",
    engineeringresumes: "Engineering Resumes",
    harvard: "Harvard",
    ink: "Ink",
    moderncv: "Modern Cv",
    opal: "Opal",
    sb2nov: "Sb2Nov",
  };
  return map[name] || toTitleCase(name);
}

init();
