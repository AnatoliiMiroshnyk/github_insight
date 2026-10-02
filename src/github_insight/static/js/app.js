"use strict";

const $ = (selector) => document.querySelector(selector);
const form = $("#analysis-form");
const usernameInput = $("#username");
const report = $("#report");
const loading = $("#loading");
const errorState = $("#error-state");
let lastUsername = "";

function setTheme(theme) {
  document.documentElement.dataset.theme = theme;
  try { localStorage.setItem("github-insight-theme", theme); } catch (_) { /* Private mode fallback. */ }
}
const storedTheme = (() => { try { return localStorage.getItem("github-insight-theme"); } catch (_) { return null; } })();
setTheme(storedTheme || (matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light"));
$("#theme-toggle").addEventListener("click", () => setTheme(document.documentElement.dataset.theme === "dark" ? "light" : "dark"));

async function api(path, options = {}) {
  const response = await fetch(path, {headers: {"Content-Type": "application/json"}, ...options});
  if (!response.ok) {
    let detail = "Unexpected server error";
    try { const body = await response.json(); detail = body.detail || detail; } catch (_) { /* Keep safe message. */ }
    throw new Error(Array.isArray(detail) ? detail[0]?.msg : detail);
  }
  return response.status === 204 ? null : response.json();
}

function showState(name) {
  loading.classList.toggle("hidden", name !== "loading");
  errorState.classList.toggle("hidden", name !== "error");
  report.classList.toggle("hidden", name !== "report");
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const username = usernameInput.value.trim();
  $("#form-error").textContent = "";
  if (!/^[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,37}[a-zA-Z0-9])?$/.test(username)) {
    $("#form-error").textContent = "Enter a valid GitHub username.";
    return;
  }
  lastUsername = username;
  showState("loading");
  try {
    const result = await api("/api/v1/analyses", {method: "POST", body: JSON.stringify({username})});
    renderReport(result);
    showState("report");
    report.scrollIntoView({behavior: "smooth", block: "start"});
    loadHistory();
  } catch (error) {
    $("#error-message").textContent = error.message;
    showState("error");
  }
});
$("#retry-button").addEventListener("click", () => { usernameInput.value = lastUsername; form.requestSubmit(); });

function renderReport(result) {
  const data = result.data;
  $("#avatar").src = data.profile.avatar_url;
  $("#avatar").alt = `${data.profile.username}'s GitHub avatar`;
  $("#username-label").textContent = `@${data.profile.username}`;
  $("#report-title").textContent = data.profile.name || data.profile.username;
  $("#bio").textContent = data.profile.bio || "No public bio provided.";
  $("#github-link").href = data.profile.html_url;
  $("#profile-meta").innerHTML = [data.profile.location, `${data.profile.followers} followers`, `${data.profile.public_repos} public repos`].filter(Boolean).map(escapeHtml).map(v => `<span>${v}</span>`).join("");
  const kpis = [["Stars",data.totals.stars],["Forks",data.totals.forks],["Original repos",data.totals.original_repositories],["Recent events",data.activity.reduce((sum,item)=>sum+item.count,0)]];
  $("#kpi-grid").innerHTML = kpis.map(([label,value]) => `<article class="kpi"><span>${label}</span><strong>${Number(value).toLocaleString()}</strong></article>`).join("");
  renderLanguages(data.languages);
  renderActivity(data.activity);
  renderRepositories(data.top_repositories);
  $("#insight-list").innerHTML = data.insights.map(item => `<li>${escapeHtml(item)}</li>`).join("");
  $("#cache-note").textContent = `${result.cached ? "Loaded from the local cache" : "Fresh GitHub API analysis"} · Snapshot #${result.id}${data.rate_limit_remaining === null ? "" : ` · ${data.rate_limit_remaining} API requests remaining`}`;
  $("#csv-link").href = `/api/v1/analyses/${result.id}/export.csv`;
}

function renderLanguages(items) {
  if (!items.length) { $("#language-chart").innerHTML = '<p class="muted">No language data available.</p>'; return; }
  const stack = items.map((item,index) => `<span style="width:${item.percentage}%;--i:${index}" title="${escapeHtml(item.name)} ${item.percentage}%"></span>`).join("");
  const legend = items.map(item => `<div class="legend-row"><span><i class="dot"></i>${escapeHtml(item.name)}</span><span class="bar-track"><span style="width:${item.percentage}%"></span></span><strong>${item.percentage}%</strong></div>`).join("");
  $("#language-chart").innerHTML = `<div class="language-stack" aria-hidden="true">${stack}</div><div class="legend">${legend}</div>`;
}

function renderActivity(items) {
  if (!items.length) { $("#activity-chart").innerHTML = '<p class="muted">No recent public events.</p>'; return; }
  const max = Math.max(...items.map(item => item.count), 1);
  $("#activity-chart").innerHTML = `<div class="activity-bars">${items.map(item => `<div class="bar-row"><span>${escapeHtml(item.event_type)}</span><span class="bar-track"><span style="width:${item.count/max*100}%"></span></span><strong>${item.count}</strong></div>`).join("")}</div>`;
}

function renderRepositories(repositories) {
  $("#repository-body").innerHTML = repositories.length ? repositories.map(repo => `<tr><td><a class="repo-name" href="${safeUrl(repo.html_url)}" target="_blank" rel="noopener">${escapeHtml(repo.name)}</a><p class="repo-description">${escapeHtml(repo.description || "No description")}</p></td><td><span class="lang-chip">${escapeHtml(repo.language || "—")}</span></td><td>${repo.stars}</td><td>${repo.forks}</td><td>${repo.updated_at ? new Date(repo.updated_at).toLocaleDateString() : "—"}</td></tr>`).join("") : '<tr><td colspan="5" class="muted">No original public repositories found.</td></tr>';
}

async function loadHistory() {
  try {
    const items = await api("/api/v1/history?limit=10");
    $("#history-list").innerHTML = items.length ? items.map(item => `<article class="history-item"><img src="${safeUrl(item.avatar_url)}" width="44" height="44" alt=""><div><strong>${escapeHtml(item.display_name || item.username)}</strong><p>@${escapeHtml(item.username)} · ${new Date(item.analyzed_at).toLocaleString()}</p></div><button class="history-open" data-open="${item.id}">Open</button><button class="history-delete" data-delete="${item.id}" aria-label="Delete ${escapeHtml(item.username)} snapshot">Delete</button></article>`).join("") : '<p class="muted">No analyses saved yet. Search for a profile to create the first snapshot.</p>';
  } catch (_) { $("#history-list").innerHTML = '<p class="muted">History is temporarily unavailable.</p>'; }
}

$("#history-list").addEventListener("click", async (event) => {
  const openId = event.target.dataset.open;
  const deleteId = event.target.dataset.delete;
  try {
    if (openId) { const result = await api(`/api/v1/analyses/${openId}`); renderReport(result); showState("report"); report.scrollIntoView({behavior:"smooth"}); }
    if (deleteId) { await api(`/api/v1/history/${deleteId}`, {method:"DELETE"}); loadHistory(); }
  } catch (error) { $("#error-message").textContent = error.message; showState("error"); }
});
$("#refresh-history").addEventListener("click", loadHistory);

function escapeHtml(value) { const node = document.createElement("div"); node.textContent = String(value); return node.innerHTML; }
function safeUrl(value) { try { const url = new URL(value); return ["http:","https:"].includes(url.protocol) ? url.href : "#"; } catch (_) { return "#"; } }
loadHistory();
