const state = {
  items: [],
  selected: new Set(),
  query: "",
  reviewOnly: false,
  colorLibrary: { codes: {}, palette: [], source: "" },
  detailItem: null,
};

const cardsEl = document.querySelector("#cards");
const summaryEl = document.querySelector("#summary");
const summaryTextEl = document.querySelector("#summaryText");
const countEl = document.querySelector("#count");
const searchEl = document.querySelector("#search");
const sourceModeEl = document.querySelector("#sourceMode");
const selectionCountEl = document.querySelector("#selectionCount");
const selectAllEl = document.querySelector("#selectAll");
const clearAllEl = document.querySelector("#clearAll");
const toggleReviewOnlyEl = document.querySelector("#toggleReviewOnly");
const colorLibraryEl = document.querySelector("#colorLibrary");
const rebuildColorLibraryEl = document.querySelector("#rebuildColorLibrary");

const detailModalEl = document.querySelector("#detailModal");
const detailImageWrapEl = document.querySelector("#detailImageWrap");
const detailImageEl = document.querySelector("#detailImage");
const detailImageCaptionEl = document.querySelector("#detailImageCaption");
const detailTitleEl = document.querySelector("#detailTitle");
const detailMetaEl = document.querySelector("#detailMeta");
const detailStatusEl = document.querySelector("#detailStatus");
const detailReviewerEl = document.querySelector("#detailReviewer");
const detailBeadsEl = document.querySelector("#detailBeads");
const closeDetailModalEl = document.querySelector("#closeDetailModal");
const addBeadRowEl = document.querySelector("#addBeadRow");
const normalizeCodesEl = document.querySelector("#normalizeCodes");
const codeQualityHintEl = document.querySelector("#codeQualityHint");
const saveReviewEl = document.querySelector("#saveReview");

const VALID_CODE_PATTERN = /^[A-Z]\d{1,2}$/;

const DEMO_ITEMS = [
  {
    id: "0001",
    name: "妙蛙种子",
    template: "sample-0001",
    status: "ok",
    total: 251,
    confidence: 0.98,
    image: "/images/0001.jpg",
    beads: [
      { code: "B3", count: 42 },
      { code: "B8", count: 66 },
      { code: "B15", count: 35 },
      { code: "B25", count: 21 },
      { code: "F4", count: 1 },
      { code: "F19", count: 1 },
      { code: "H2", count: 5 },
      { code: "H3", count: 1 },
      { code: "H6", count: 21 },
      { code: "H7", count: 58 },
    ],
  },
  {
    id: "0002",
    name: "妙蛙草",
    template: "sample-0001",
    status: "review",
    total: 186,
    confidence: 0.87,
    image: "/images/0002.jpg",
    beads: [
      { code: "B3", count: 38 },
      { code: "B8", count: 54 },
      { code: "B15", count: 31 },
      { code: "H6", count: 29 },
      { code: "H7", count: 34 },
    ],
  },
  {
    id: "0007",
    name: "杰尼龟",
    template: "sample-0009",
    status: "ok",
    total: 174,
    confidence: 0.96,
    image: "/images/0007.jpg",
    beads: [
      { code: "B3", count: 18 },
      { code: "B8", count: 42 },
      { code: "H6", count: 37 },
      { code: "H7", count: 77 },
    ],
  },
  {
    id: "0009",
    name: "超梦",
    template: "sample-0009",
    status: "error",
    total: 0,
    confidence: 0.12,
    image: "/images/0009.jpg",
    beads: [],
  },
];

let usingDemoData = true;

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function fallbackColorFromCode(code) {
  let hash = 0;
  const text = String(code || "");
  for (let i = 0; i < text.length; i += 1) {
    hash = ((hash << 5) - hash + text.charCodeAt(i)) | 0;
  }
  const hue = Math.abs(hash) % 360;
  return `hsl(${hue} 45% 58%)`;
}

function colorForCode(code) {
  const normalized = String(code || "").trim().toUpperCase();
  return state.colorLibrary.codes?.[normalized] || fallbackColorFromCode(normalized);
}

async function fetchColorLibrary() {
  try {
    const response = await fetch(`/api/color-library?t=${Date.now()}`);
    if (!response.ok) {
      throw new Error(`color-library-http-${response.status}`);
    }
    state.colorLibrary = await response.json();
  } catch (error) {
    state.colorLibrary = { codes: {}, palette: [], source: "fallback" };
  }
}

async function fetchIndex() {
  try {
    const response = await fetch(`/api/index?t=${Date.now()}`);
    const payload = await response.json();
    state.items = payload.items && payload.items.length ? payload.items : DEMO_ITEMS;
    usingDemoData = !(payload.items && payload.items.length);
  } catch (error) {
    state.items = DEMO_ITEMS;
    usingDemoData = true;
  }
  state.selected = new Set(state.items.map((item) => item.id));
  await fetchColorLibrary();
  render();
}

function formatStatus(status) {
  if (status === "ok") return "status-ok";
  if (status === "review") return "status-review";
  return "status-error";
}

function formatStatusLabel(status) {
  if (status === "ok") return "已通过";
  if (status === "review") return "待校正";
  return "异常";
}

function getFilteredItems() {
  return state.items.filter((item) => {
    const needle = state.query.trim().toLowerCase();
    const matchedByText = !needle
      || [item.id, item.name, item.template].some((value) => String(value).toLowerCase().includes(needle));
    const matchedByStatus = !state.reviewOnly || item.status === "review" || item.status === "error";
    return matchedByText && matchedByStatus;
  });
}

function renderCards() {
  const filtered = getFilteredItems();

  countEl.textContent = `${filtered.length} / ${state.items.length}`;
  if (sourceModeEl) {
    sourceModeEl.textContent = usingDemoData ? "示例数据" : "真实数据";
  }
  if (toggleReviewOnlyEl) {
    toggleReviewOnlyEl.textContent = state.reviewOnly ? "显示全部" : "仅看待校验";
  }

  cardsEl.innerHTML = filtered.map((item) => `
    <article class="card">
      <div class="card-media">
        <div class="thumb">
          ${item.image ? `<img src="${item.image}" alt="${item.name || item.id}" />` : `<span class="placeholder">暂无缩略图</span>`}
        </div>
        <div class="card-flag ${formatStatus(item.status)}">${formatStatusLabel(item.status)}</div>
      </div>
      <div class="card-head">
        <div>
          <p class="card-id">#${item.id}</p>
          <h3>${item.name || "未命名"}</h3>
        </div>
        <div class="card-head-actions">
          <input type="checkbox" ${state.selected.has(item.id) ? "checked" : ""} data-id="${item.id}" aria-label="选择 ${item.name || item.id}" />
          <button class="tool-btn detail-btn" data-detail-id="${item.id}">详情</button>
        </div>
      </div>
      <div class="meta-grid">
        <div>
          <span>模板</span>
          <strong>${item.template || "unknown"}</strong>
        </div>
        <div>
          <span>总豆数</span>
          <strong>${item.total ?? 0}</strong>
        </div>
        <div>
          <span>置信度</span>
          <strong>${Number(item.confidence ?? 0).toFixed(2)}</strong>
        </div>
        <div>
          <span>色号数</span>
          <strong>${(item.beads || []).length}</strong>
        </div>
      </div>
      <div class="chip-row">
        <span class="chip">${item.status || "error"}</span>
        <span class="chip chip-muted">${item.image ? "有缩略图" : "无缩略图"}</span>
      </div>
    </article>
  `).join("");

  cardsEl.querySelectorAll('input[type="checkbox"]').forEach((checkbox) => {
    checkbox.addEventListener("change", (event) => {
      const id = event.target.dataset.id;
      if (event.target.checked) {
        state.selected.add(id);
      } else {
        state.selected.delete(id);
      }
      renderSummary();
    });
  });

  cardsEl.querySelectorAll(".detail-btn").forEach((button) => {
    button.addEventListener("click", async (event) => {
      const itemId = event.currentTarget.dataset.detailId;
      if (!itemId) return;
      await openDetailModal(itemId);
    });
  });
}

function aggregateSelection() {
  const selectedItems = state.items.filter((item) => state.selected.has(item.id));
  const counts = new Map();
  for (const item of selectedItems) {
    for (const bead of item.beads || []) {
      counts.set(bead.code, (counts.get(bead.code) || 0) + Number(bead.count || 0));
    }
  }
  return { selectedItems, counts };
}

function renderSummary() {
  const { selectedItems, counts } = aggregateSelection();
  const rows = [...counts.entries()].sort(([a], [b]) => a.localeCompare(b));
  const selectedTotal = selectedItems.reduce((sum, item) => sum + Number(item.total || 0), 0);
  const beadTotal = rows.reduce((sum, [, count]) => sum + Number(count || 0), 0);

  if (selectionCountEl) {
    selectionCountEl.textContent = String(selectedItems.length);
  }

  summaryEl.innerHTML = [
    `<div class="summary-row"><span>已选条目</span><strong>${selectedItems.length}</strong></div>`,
    `<div class="summary-row"><span>条目总豆数</span><strong>${selectedTotal}</strong></div>`,
    `<div class="summary-row"><span>汇总总豆数</span><strong>${beadTotal}</strong></div>`,
    `<div class="summary-row"><span>当前模式</span><strong>${usingDemoData ? "示例数据" : "真实数据"}</strong></div>`,
    ...rows.map(([code, count]) => `<div class="summary-row"><span>${code}</span><strong>${count}</strong></div>`),
  ].join("");

  summaryTextEl.value = rows.length
    ? rows.map(([code, count]) => `${code}\t${count}`).join("\n")
    : "未选择任何条目";

  renderColorLibrary(rows.map(([code]) => code));
}

function renderColorLibrary(priorityCodes = []) {
  const allCodes = new Set(priorityCodes);
  state.items.forEach((item) => {
    (item.beads || []).forEach((bead) => {
      if (bead.code) allCodes.add(String(bead.code).toUpperCase());
    });
  });

  const codes = [...allCodes].sort((a, b) => a.localeCompare(b));
  colorLibraryEl.innerHTML = codes.map((code) => {
    const colorHex = colorForCode(code);
    return `
      <label class="color-item">
        <span class="swatch" style="background:${colorHex}"></span>
        <span class="color-code">${escapeHtml(code)}</span>
        <input type="color" value="${normalizeColorHex(colorHex)}" data-color-code="${escapeHtml(code)}" />
      </label>
    `;
  }).join("");

  colorLibraryEl.querySelectorAll("input[type='color']").forEach((input) => {
    input.addEventListener("change", async (event) => {
      const code = event.target.dataset.colorCode;
      if (!code) return;
      const value = event.target.value;
      state.colorLibrary.codes = state.colorLibrary.codes || {};
      state.colorLibrary.codes[code] = value;
      await fetch("/api/color-library/update", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ codes: { [code]: value } }),
      });
      render();
    });
  });
}

function normalizeColorHex(value) {
  const text = String(value || "").trim();
  const match = /^#([0-9a-fA-F]{6})$/.exec(text);
  if (match) return `#${match[1].toLowerCase()}`;
  return "#9aa5b1";
}

function normalizeCode(rawCode) {
  const compact = String(rawCode || "").toUpperCase().replaceAll(" ", "");
  if (!compact) return "";
  const matched = /^([A-Z])([A-Z0-9]{1,3})$/.exec(compact);
  if (!matched) return compact;

  const suffixMap = {
    O: "0",
    D: "0",
    Q: "0",
    I: "1",
    L: "1",
    Z: "2",
    S: "5",
  };
  const normalizedSuffix = [...matched[2]]
    .map((char) => (/\d/.test(char) ? char : (suffixMap[char] || char)))
    .join("");
  return `${matched[1]}${normalizedSuffix}`;
}

function isValidCode(code) {
  return VALID_CODE_PATTERN.test(String(code || "").toUpperCase());
}

function buildBeadRow(code = "", count = 0) {
  const normalizedCode = normalizeCode(code);
  const invalidClass = normalizedCode && !isValidCode(normalizedCode) ? "code-invalid" : "";
  return `
    <tr class="${invalidClass}">
      <td><input class="bead-code" type="text" value="${escapeHtml(normalizedCode)}" placeholder="B3" /></td>
      <td><input class="bead-count" type="number" min="0" value="${Number(count || 0)}" /></td>
      <td><span class="swatch small" style="background:${colorForCode(normalizedCode)}"></span></td>
      <td><button class="tool-btn row-remove">删除</button></td>
    </tr>
  `;
}

function refreshDetailCodeValidation() {
  const rows = [...detailBeadsEl.querySelectorAll("tr")];
  let invalidCount = 0;
  rows.forEach((row) => {
    const codeInput = row.querySelector(".bead-code");
    const code = normalizeCode(codeInput?.value || "");
    const valid = !code || isValidCode(code);
    row.classList.toggle("code-invalid", !valid);
    if (!valid) invalidCount += 1;
  });

  if (codeQualityHintEl) {
    if (invalidCount > 0) {
      codeQualityHintEl.textContent = `发现 ${invalidCount} 个疑似异常色号，请检查后再保存。`;
      codeQualityHintEl.classList.add("warning");
    } else {
      codeQualityHintEl.textContent = "色号格式：字母 + 1-2 位数字（如 B3、H7、F19）";
      codeQualityHintEl.classList.remove("warning");
    }
  }
}

function wireDetailRowEvents() {
  detailBeadsEl.querySelectorAll(".row-remove").forEach((button) => {
    button.addEventListener("click", (event) => {
      event.preventDefault();
      event.currentTarget.closest("tr")?.remove();
      refreshDetailCodeValidation();
    });
  });

  detailBeadsEl.querySelectorAll(".bead-code").forEach((input) => {
    input.addEventListener("input", (event) => {
      const row = event.target.closest("tr");
      if (!row) return;
      const swatch = row.querySelector(".swatch");
      if (!swatch) return;
      swatch.style.background = colorForCode(normalizeCode(event.target.value));
      refreshDetailCodeValidation();
    });

    input.addEventListener("blur", (event) => {
      event.target.value = normalizeCode(event.target.value);
      refreshDetailCodeValidation();
    });
  });
}

function closeDetailModal() {
  detailModalEl.classList.add("hidden");
  detailModalEl.setAttribute("aria-hidden", "true");
  state.detailItem = null;
}

async function openDetailModal(itemId) {
  const response = await fetch(`/api/items/${encodeURIComponent(itemId)}?t=${Date.now()}`);
  if (!response.ok) return;
  const item = await response.json();
  state.detailItem = item;

  detailTitleEl.textContent = `${item.id} ${item.name || ""}`.trim();

  if (item.image) {
    detailImageEl.src = item.image;
    detailImageEl.alt = item.name || item.id || "条目大图";
    detailImageCaptionEl.textContent = `原图：${item.name || item.id}`;
    detailImageWrapEl.classList.remove("hidden");
    detailImageWrapEl.setAttribute("aria-hidden", "false");
  } else {
    detailImageEl.removeAttribute("src");
    detailImageCaptionEl.textContent = "";
    detailImageWrapEl.classList.add("hidden");
    detailImageWrapEl.setAttribute("aria-hidden", "true");
  }

  detailStatusEl.value = item.status || "review";
  detailReviewerEl.value = "web";
  detailMetaEl.innerHTML = `
    <div><span>模板</span><strong>${escapeHtml(item.template || "unknown")}</strong></div>
    <div><span>总豆数</span><strong>${Number(item.total || 0)}</strong></div>
    <div><span>置信度</span><strong>${Number(item.confidence || 0).toFixed(2)}</strong></div>
    <div><span>状态</span><strong>${escapeHtml(item.status || "error")}</strong></div>
  `;

  detailBeadsEl.innerHTML = (item.beads || []).map((bead) => buildBeadRow(bead.code, bead.count)).join("") || buildBeadRow();
  wireDetailRowEvents();
  refreshDetailCodeValidation();

  detailModalEl.classList.remove("hidden");
  detailModalEl.setAttribute("aria-hidden", "false");
}

function collectDetailBeads() {
  const rows = [...detailBeadsEl.querySelectorAll("tr")];
  return rows.map((row) => {
    const code = normalizeCode(row.querySelector(".bead-code")?.value || "");
    const count = Number(row.querySelector(".bead-count")?.value || 0);
    return { code, count };
  }).filter((item) => item.code && isValidCode(item.code) && Number.isFinite(item.count) && item.count >= 0);
}

function getInvalidDetailCodes() {
  const rows = [...detailBeadsEl.querySelectorAll("tr")];
  const invalidCodes = rows.map((row) => normalizeCode(row.querySelector(".bead-code")?.value || ""))
    .filter((code) => code && !isValidCode(code));
  return [...new Set(invalidCodes)];
}

async function saveDetailReview() {
  if (!state.detailItem) return;
  const invalidCodes = getInvalidDetailCodes();
  if (invalidCodes.length) {
    alert(`有疑似异常色号：${invalidCodes.join(", ")}。请先修正后再保存。`);
    return;
  }

  const beads = collectDetailBeads();
  const payload = {
    beads,
    reviewer: detailReviewerEl.value?.trim() || "web",
    status: detailStatusEl.value || "ok",
  };

  const response = await fetch(`/api/items/${encodeURIComponent(state.detailItem.id)}/review`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!response.ok) return;

  closeDetailModal();
  await fetchIndex();
}

function render() {
  renderCards();
  renderSummary();
}

document.querySelector("#refresh").addEventListener("click", async () => {
  await fetch("/api/rebuild", { method: "POST" });
  await fetchIndex();
});

document.querySelector("#copy").addEventListener("click", async () => {
  await navigator.clipboard.writeText(summaryTextEl.value);
});

toggleReviewOnlyEl.addEventListener("click", () => {
  state.reviewOnly = !state.reviewOnly;
  renderCards();
  renderSummary();
});

selectAllEl.addEventListener("click", () => {
  getFilteredItems().forEach((item) => state.selected.add(item.id));
  render();
});

clearAllEl.addEventListener("click", () => {
  getFilteredItems().forEach((item) => state.selected.delete(item.id));
  render();
});

rebuildColorLibraryEl.addEventListener("click", async () => {
  await fetch("/api/color-library/rebuild", { method: "POST" });
  await fetchColorLibrary();
  render();
});

closeDetailModalEl.addEventListener("click", closeDetailModal);
detailModalEl.addEventListener("click", (event) => {
  if (event.target.dataset.closeModal === "true") {
    closeDetailModal();
  }
});

addBeadRowEl.addEventListener("click", () => {
  detailBeadsEl.insertAdjacentHTML("beforeend", buildBeadRow());
  wireDetailRowEvents();
  refreshDetailCodeValidation();
});

normalizeCodesEl.addEventListener("click", () => {
  detailBeadsEl.querySelectorAll(".bead-code").forEach((input) => {
    input.value = normalizeCode(input.value);
  });
  refreshDetailCodeValidation();
});

saveReviewEl.addEventListener("click", async () => {
  await saveDetailReview();
});

searchEl.addEventListener("input", (event) => {
  state.query = event.target.value;
  renderCards();
});

fetchIndex();
