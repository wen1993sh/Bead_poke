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

async function fetchIndex() {
  const response = await fetch("/api/index");
  const payload = await response.json();
  state.items = payload.items || [];
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
  cardsEl.innerHTML = filtered.map((item) => `
    <label class="card">
      <header>
        <strong>${item.id}</strong>
        <input type="checkbox" ${state.selected.has(item.id) ? "checked" : ""} data-id="${item.id}" />
      </header>
      <div>${item.name || "未命名"}</div>
      <div class="badge">模板：${item.template || "unknown"}</div>
      <div class="badge ${formatStatus(item.status)}">状态：${item.status || "error"}</div>
      <div class="badge">总豆数：${item.total ?? 0}</div>
      <div class="badge">置信度：${Number(item.confidence ?? 0).toFixed(2)}</div>
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

  summaryEl.innerHTML = [
    `<div class="summary-row"><span>已选条目</span><strong>${selectedItems.length}</strong></div>`,
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
