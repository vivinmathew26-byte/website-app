// ===========================================================
// Mother Teresa Transport — site behaviour
// ===========================================================

// TODO: replace with the real business WhatsApp number, country code first, no spaces or symbols.
// Example: "919876543210" for an Indian number starting 98765 43210.
const WHATSAPP_NUMBER = "910000000000";

// API base URL. Leave this empty ("") when deployed behind the nginx config
// in /nginx — it proxies /api/ to the backend container, so requests from the
// browser are same-origin and no CORS setup is needed.
// If you're pointing directly at a standalone backend instead (e.g. during
// local dev without nginx), set the full URL, e.g. "http://localhost:8000".
const API_BASE_URL = "";

// Footer year
const yearEl = document.getElementById("year");
if (yearEl) yearEl.textContent = new Date().getFullYear();

// Mobile nav toggle
const navToggle = document.getElementById("navToggle");
const mainNav = document.getElementById("mainNav");
if (navToggle) {
  navToggle.addEventListener("click", () => {
    const isOpen = mainNav.classList.toggle("open");
    navToggle.setAttribute("aria-expanded", String(isOpen));
  });
  mainNav.querySelectorAll("a").forEach((link) => {
    link.addEventListener("click", () => {
      mainNav.classList.remove("open");
      navToggle.setAttribute("aria-expanded", "false");
    });
  });
}

// ---------- Booking form -> backend API -> WhatsApp handoff ----------
const bookingForm = document.getElementById("bookingForm");
const bookingStatusEl = document.getElementById("bookingStatus");

function setBookingStatus(message, kind) {
  if (!bookingStatusEl) return;
  bookingStatusEl.textContent = message;
  bookingStatusEl.dataset.kind = kind || "";
}

if (bookingForm) {
  bookingForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const data = new FormData(bookingForm);
    const submitBtn = bookingForm.querySelector("button[type=submit]");

    const payload = {
      customer_name: data.get("name").trim(),
      phone: data.get("phone").trim(),
      pickup_location: data.get("pickup").trim(),
      drop_location: data.get("drop").trim(),
      goods_type: data.get("goods").trim(),
      preferred_date: data.get("date") || null,
      notes: data.get("notes").trim() || null,
    };

    submitBtn.disabled = true;
    setBookingStatus("Sending your booking…", "pending");

    try {
      const res = await fetch(`${API_BASE_URL}/api/bookings`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || "Could not save the booking.");
      }

      const result = await res.json();
      setBookingStatus(
        `Booking saved. Your tracking code is ${result.tracking_code} — save it to check status later.`,
        "success"
      );

      // Hand off to WhatsApp with a human-readable summary, including the tracking code.
      const lines = [
        "New booking request — Mother Teresa Transport",
        `Tracking code: ${result.tracking_code}`,
        `Name: ${payload.customer_name}`,
        `Phone: ${payload.phone}`,
        `Pickup: ${payload.pickup_location}`,
        `Drop: ${payload.drop_location}`,
        `Goods: ${payload.goods_type}`,
        `Preferred date: ${payload.preferred_date || "-"}`,
      ];
      if (payload.notes) lines.push(`Notes: ${payload.notes}`);
      const waUrl = `https://wa.me/${WHATSAPP_NUMBER}?text=${encodeURIComponent(lines.join("\n"))}`;
      window.open(waUrl, "_blank", "noopener");

      bookingForm.reset();
    } catch (err) {
      console.error(err);
      setBookingStatus(
        "Couldn't reach the booking service. Please try again, or message us directly on WhatsApp.",
        "error"
      );
    } finally {
      submitBtn.disabled = false;
    }
  });
}

// ---------- Tracking widget (used on track.html) ----------
const trackForm = document.getElementById("trackForm");
const trackResult = document.getElementById("trackResult");

const STATUS_LABELS = {
  received: "Received",
  confirmed: "Confirmed",
  picked_up: "Picked up",
  in_transit: "In transit",
  delivered: "Delivered",
  cancelled: "Cancelled",
};

if (trackForm) {
  trackForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const data = new FormData(trackForm);
    const payload = {
      tracking_code: data.get("tracking_code").trim().toUpperCase(),
      phone: data.get("phone").trim(),
    };

    trackResult.innerHTML = `<p class="track-pending">Looking that up…</p>`;

    try {
      const res = await fetch(`${API_BASE_URL}/api/bookings/track`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        trackResult.innerHTML = `<p class="track-error">No booking found for that tracking code and phone number. Double-check both and try again.</p>`;
        return;
      }

      const booking = await res.json();
      const historyItems = booking.history
        .map(
          (h) =>
            `<li><span class="track-history-status">${STATUS_LABELS[h.status] || h.status}</span><span class="track-history-time">${new Date(h.changed_at).toLocaleString()}</span>${h.note ? `<span class="track-history-note">${h.note}</span>` : ""}</li>`
        )
        .join("");

      trackResult.innerHTML = `
        <div class="track-card">
          <div class="track-card-head">
            <span class="track-code">${booking.tracking_code}</span>
            <span class="track-status track-status-${booking.status}">${STATUS_LABELS[booking.status] || booking.status}</span>
          </div>
          <p class="track-route">${booking.pickup_location} &rarr; ${booking.drop_location}</p>
          <p class="track-goods">${booking.goods_type}</p>
          <ul class="track-history">${historyItems}</ul>
        </div>
      `;
    } catch (err) {
      console.error(err);
      trackResult.innerHTML = `<p class="track-error">Couldn't reach the tracking service. Please try again shortly.</p>`;
    }
  });
}
