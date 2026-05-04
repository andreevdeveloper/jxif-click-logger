const ADMIN_API = (location.hostname === "localhost")
  ? "http://localhost:8001"
  : "http://localhost:8001"; // для демо

document.getElementById("adminApi").textContent = ADMIN_API;

const el = (id) => document.getElementById(id);

async function api(path, opts = {}) {
  const res = await fetch(`${ADMIN_API}${path}`, {
    headers: { "content-type": "application/json" },
    ...opts
  });
  if (!res.ok) {
    const txt = await res.text();
    throw new Error(`${res.status} ${res.statusText}: ${txt}`);
  }
  return res.json();
}

function escapeHtml(s) {
  return String(s)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;");
}

async function createLink() {
  const target_url = el("targetUrl").value.trim();
  const code = el("code").value.trim() || null;

  const payload = { target_url, code };
  const data = await api("/links", { method: "POST", body: JSON.stringify(payload) });

  el("createOut").textContent =
    `OK\n` +
    `code: ${data.code}\n` +
    `target: ${data.target_url}\n` +
    `track: ${data.tracking_url}\n` +
    `track(js): ${data.tracking_url_js}\n`;

  await loadLinks();
}

async function loadLinks() {
  const links = await api("/links");
  const box = el("links");
  box.innerHTML = links.map(l => `
    <div class="item">
      <div><b>code</b>: ${escapeHtml(l.code)}</div>
      <div><b>target</b>: ${escapeHtml(l.target_url)}</div>
      <div><b>track</b>: <a href="${escapeHtml(l.tracking_url)}" target="_blank">${escapeHtml(l.tracking_url)}</a></div>
      <div><b>track(js)</b>: <a href="${escapeHtml(l.tracking_url_js)}" target="_blank">${escapeHtml(l.tracking_url_js)}</a></div>
    </div>
  `).join("");
}

async function loadClicks() {
  const code = el("filterCode").value.trim();
  const qs = new URLSearchParams();
  if (code) qs.set("code", code);

  const clicks = await api(`/clicks?${qs.toString()}`);
  const box = el("clicks");

  const rows = clicks.map(c => `
    <tr>
      <td>${escapeHtml(c.created_at)}</td>
      <td>${escapeHtml(c.code)}</td>
      <td>${escapeHtml(c.ip || "")}<br><small>${escapeHtml(c.forwarded_for || "")}</small></td>
      <td>${escapeHtml(c.user_agent || "")}</td>
      <td><small>${escapeHtml(c.referer || "")}</small></td>
      <td><small>${escapeHtml(JSON.stringify(c.query || {}))}</small></td>
      <td><small>${escapeHtml(JSON.stringify(c.client || {}))}</small></td>
    </tr>
  `).join("");

  box.innerHTML = `
    <table>
      <thead>
        <tr>
          <th>when</th>
          <th>code</th>
          <th>ip</th>
          <th>ua</th>
          <th>ref</th>
          <th>query</th>
          <th>client</th>
        </tr>
      </thead>
      <tbody>${rows}</tbody>
    </table>
  `;
}

el("createBtn").addEventListener("click", () => createLink().catch(e => alert(e.message)));
el("reloadLinks").addEventListener("click", () => loadLinks().catch(e => alert(e.message)));
el("reloadClicks").addEventListener("click", () => loadClicks().catch(e => alert(e.message)));

loadLinks().catch(console.error);
loadClicks().catch(console.error);