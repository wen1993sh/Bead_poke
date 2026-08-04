const state = {
  items: [],
  selected: new Set(),
  query: "",
};

const cardsEl = document.querySelector("#cards");
const summaryEl = document.querySelector("#summary");
const summaryTextEl = document.querySelector("#summaryText");
const countEl = document.querySelector("#count");
const searchEl = document.querySelector("#search");
const sourceModeEl = document.querySelector("#sourceMode");
const selectionCountEl = document.querySelector("#selectionCount");

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
  render();
}

function formatStatus(status) {
  if (status === "ok") return "status-ok";
  if (status === "review") return "status-review";
  return "status-error";
}

function renderCards() {
  const filtered = state.items.filter((item) => {
    const needle = state.query.trim().toLowerCase();
    if (!needle) return true;
    return [item.id, item.name, item.template].some((value) => String(value).toLowerCase().includes(needle));
  });

  countEl.textContent = `${filtered.length} / ${state.items.length}`;
  if (sourceModeEl) {
    sourceModeEl.textContent = usingDemoData ? "示例数据" : "真实数据";
  }
  cardsEl.innerHTML = filtered.map((item) => `
    <label class="card">
      <div class="thumb">
        ${item.image ? `<img src="${item.image}" alt="${item.name || item.id}" />` : `<span class="placeholder">暂无缩略图</span>`}
      </div>
      <header>
        <strong>${item.id}</strong>
        <input type="checkbox" ${state.selected.has(item.id) ? "checked" : ""} data-id="${item.id}" />
      </header>
      <div>${item.name || "未命名"}</div>
      <div class="badge">模板：${item.template || "unknown"}</div>
      <div class="badge ${formatStatus(item.status)}">状态：${item.status || "error"}</div>
      <div class="badge">总豆数：${item.total ?? 0}</div>
      <div class="badge">置信度：${Number(item.confidence ?? 0).toFixed(2)}</div>
      <div class="badge">色号：${(item.beads || []).length}</div>
    </label>
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

  if (selectionCountEl) {
    selectionCountEl.textContent = String(selectedItems.length);
  }

  summaryEl.innerHTML = [
    `<div class="summary-row"><span>已选条目</span><strong>${selectedItems.length}</strong></div>`,
    `<div class="summary-row"><span>当前模式</span><strong>${usingDemoData ? "示例数据" : "真实数据"}</strong></div>`,
    ...rows.map(([code, count]) => `<div class="summary-row"><span>${code}</span><strong>${count}</strong></div>`),
  ].join("");

  summaryTextEl.value = rows.length
    ? rows.map(([code, count]) => `${code}\t${count}`).join("\n")
    : "未选择任何条目";
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

searchEl.addEventListener("input", (event) => {
  state.query = event.target.value;
  renderCards();
});

fetchIndex();
