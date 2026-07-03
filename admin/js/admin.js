// ===========================================================
// Mother Teresa Transport — admin panel
// ===========================================================

// API base URL — same convention as ../frontend/js/script.js. Leave empty
// when served behind the nginx config in /nginx (same-origin, proxied /api/).
const API_BASE_URL = "";
const TOKEN_KEY = "mtt_admin_token";

const loginScreen = document.getElementById("loginScreen");
const dashboard = document.getElementById("dashboard");
const loginForm = document.getElementById("loginForm");
const loginError = document.getElementById("loginError");
const adminNameEl = document.getElementById("adminName");
const logoutBtn = document.getElementById("logoutBtn");

const searchInput = document.getElementById("searchInput");
const statusFilter = document.getElementById("statusFilter");
const refreshBtn = document.getElementById("refreshBtn");
const tableBody = document.getElementById("bookingsTableBody");

const detailPanel = document.getElementById("detailPanel");
const detailClose = document.getElementById("detailClose");
const detailTracking = document.getElementById("detailTracking");
const detailStatusBadge = document.getElementById("detailStatusBadge");
const detailFacts = document.getElementById("detailFacts");
const detailHistory = document.getElementById("detailHistory");
const statusForm = document.getElementById("statusForm");
const statusSelect = document.getElementById("statusSelect");
const statusFormMsg = document.getElementById("statusFormMsg");

const STATUS_LABELS = {
  received: "Received",
  confirmed: "Confirmed",
  picked_up: "Picked up",
  in_transit: "In transit",
  delivered: "Delivered",
  cancelled: "Cancelled",
};

let currentBookingId = null;
let searchDebounce = null;

function getToken() {
  return localStorage.getItem(TOKEN_KEY);
}
function setToken(token) {
  localStorage.setItem(TOKEN_KEY, token);
}
function clearToken() {
  localStorage.removeItem(TOKEN_KEY);
}

async function apiFetch(path, options = {}) {
  const token = getToken();
  const res = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers: {
      ...(options.headers || {}),
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
  });
  if (res.status === 401) {
    clearToken();
    showLogin();
    throw new Error("Session expired. Please sign in again.");
  }
  return res;
}

function showLogin() {
  loginScreen.hidden = false;
  dashboard.hidden = true;
}

function showDashboard() {
  loginScreen.hidden = true;
  dashboard.hidden = false;
  loadMe();
  loadBookings();
}

// ---------- Login ----------
loginForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  loginError.textContent = "";
  const data = new FormData(loginForm);
  const body = new URLSearchParams();
  body.set("username", data.get("username"));
  body.set("password", data.get("password"));

  try {
    const res = await fetch(`${API_BASE_URL}/api/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body,
    });
    if (!res.ok) {
      throw new Error("Incorrect username or password.");
    }
    const result = await res.json();
    setToken(result.access_token);
    loginForm.reset();
    showDashboard();
  } catch (err) {
    loginError.textContent = err.message || "Could not sign in.";
  }
});

logoutBtn.addEventListener("click", () => {
  clearToken();
  showLogin();
});

async function loadMe() {
  try {
    const res = await apiFetch("/api/auth/me");
    if (!res.ok) return;
    const me = await res.json();
    adminNameEl.textContent = me.full_name || me.username;
  } catch (_) {
    /* handled by apiFetch */
  }
}

// ---------- Bookings table ----------
async function loadBookings() {
  tableBody.innerHTML = `<tr><td colspan="6" class="table-empty">Loading…</td></tr>`;

  const params = new URLSearchParams();
  if (searchInput.value.trim()) params.set("search", searchInput.value.trim());
  if (statusFilter.value) params.set("status", statusFilter.value);

  try {
    const res = await apiFetch(`/api/bookings?${params.toString()}`);
    if (!res.ok) throw new Error("Could not load bookings.");
    const bookings = await res.json();

    if (bookings.length === 0) {
      tableBody.innerHTML = `<tr><td colspan="6" class="table-empty">No bookings match this view.</td></tr>`;
      return;
    }

    tableBody.innerHTML = bookings
      .map(
        (b) => `
        <tr data-id="${b.id}">
          <td class="tracking-cell">${b.tracking_code}</td>
          <td>${escapeHtml(b.customer_name)}<br><small>${escapeHtml(b.phone)}</small></td>
          <td>${escapeHtml(b.pickup_location)} &rarr; ${escapeHtml(b.drop_location)}</td>
          <td>${escapeHtml(b.goods_type)}</td>
          <td>${b.preferred_date || "-"}</td>
          <td><span class="status-pill ${b.status}">${STATUS_LABELS[b.status] || b.status}</span></td>
        </tr>`
      )
      .join("");

    tableBody.querySelectorAll("tr[data-id]").forEach((row) => {
      row.addEventListener("click", () => openDetail(row.dataset.id));
    });
  } catch (err) {
    tableBody.innerHTML = `<tr><td colspan="6" class="table-empty">${err.message}</td></tr>`;
  }
}

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str ?? "";
  return div.innerHTML;
}

refreshBtn.addEventListener("click", loadBookings);
statusFilter.addEventListener("change", loadBookings);
searchInput.addEventListener("input", () => {
  clearTimeout(searchDebounce);
  searchDebounce = setTimeout(loadBookings, 350);
});

// ---------- Detail panel ----------
async function openDetail(bookingId) {
  currentBookingId = bookingId;
  statusFormMsg.textContent = "";
  detailPanel.hidden = false;

  try {
    const res = await apiFetch(`/api/bookings/${bookingId}`);
    if (!res.ok) throw new Error("Could not load booking.");
    const b = await res.json();

    detailTracking.textContent = b.tracking_code;
    detailStatusBadge.textContent = STATUS_LABELS[b.status] || b.status;
    statusSelect.value = b.status;

    detailFacts.innerHTML = `
      <div><dt>Customer</dt><dd>${escapeHtml(b.customer_name)}</dd></div>
      <div><dt>Phone</dt><dd>${escapeHtml(b.phone)}</dd></div>
      <div><dt>Email</dt><dd>${escapeHtml(b.email || "-")}</dd></div>
      <div><dt>Preferred date</dt><dd>${b.preferred_date || "-"}</dd></div>
      <div><dt>Pickup</dt><dd>${escapeHtml(b.pickup_location)}</dd></div>
      <div><dt>Drop</dt><dd>${escapeHtml(b.drop_location)}</dd></div>
      <div><dt>Goods</dt><dd>${escapeHtml(b.goods_type)}</dd></div>
      <div><dt>Notes</dt><dd>${escapeHtml(b.notes || "-")}</dd></div>
    `;

    detailHistory.innerHTML = b.history
      .map(
        (h) => `
        <li>
          <span class="h-status">${STATUS_LABELS[h.status] || h.status}</span>
          <span class="h-meta">${new Date(h.changed_at).toLocaleString()} · ${escapeHtml(h.changed_by)}${h.note ? " · " + escapeHtml(h.note) : ""}</span>
        </li>`
      )
      .join("");
  } catch (err) {
    detailFacts.innerHTML = `<div><dd>${err.message}</dd></div>`;
  }
}

detailClose.addEventListener("click", () => {
  detailPanel.hidden = true;
  currentBookingId = null;
});

statusForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  if (!currentBookingId) return;

  const data = new FormData(statusForm);
  const payload = {
    status: data.get("status"),
    note: data.get("note")?.trim() || null,
    notify_customer: data.get("notify_customer") === "on",
  };

  statusFormMsg.textContent = "Saving…";
  statusFormMsg.dataset.kind = "";

  try {
    const res = await apiFetch(`/api/bookings/${currentBookingId}/status`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || "Could not update status.");
    }
    statusFormMsg.textContent = "Status updated.";
    statusFormMsg.dataset.kind = "success";
    statusForm.reset();
    statusSelect.value = payload.status;
    openDetail(currentBookingId);
    loadBookings();
  } catch (err) {
    statusFormMsg.textContent = err.message;
    statusFormMsg.dataset.kind = "error";
  }
});

// ---------- Boot ----------
if (getToken()) {
  showDashboard();
} else {
  showLogin();
}
