const STORAGE_KEY_RESULT = "dfis_latest";
const STORAGE_KEY_META = "dfis_report_meta";
const STORAGE_KEY_HISTORY = "dfis_report_history";

let DOMAIN_CONFIG = {};

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function detectPage() {
  if (document.getElementById("upload-form")) return "upload";
  if (document.getElementById("dashboard-content")) return "dashboard";
  if (document.getElementById("report-content")) return "report";
  if (document.getElementById("comparison-content")) return "comparison";
  if (document.getElementById("ai-insights-content")) return "ai";
  return "unknown";
}

function getStoredResult() {
  try {
    return JSON.parse(localStorage.getItem(STORAGE_KEY_RESULT) || "null");
  } catch {
    return null;
  }
}

function setStoredResult(data) {
  localStorage.setItem(STORAGE_KEY_RESULT, JSON.stringify(data || null));
}

function getStoredMeta() {
  try {
    return JSON.parse(localStorage.getItem(STORAGE_KEY_META) || "{}");
  } catch {
    return {};
  }
}

function setStoredMeta(meta) {
  localStorage.setItem(STORAGE_KEY_META, JSON.stringify(meta || {}));
}

function getHistory() {
  try {
    return JSON.parse(localStorage.getItem(STORAGE_KEY_HISTORY) || "[]");
  } catch {
    return [];
  }
}

function setHistory(history) {
  localStorage.setItem(STORAGE_KEY_HISTORY, JSON.stringify(history || []));
}

function addToHistory(name, domain, result) {
  const history = getHistory();
  history.push({
    id: `r_${Date.now()}`,
    name,
    domain,
    created_at: new Date().toISOString(),
    result,
  });
  setHistory(history.slice(-30));
}

async function fetchLatestResult() {
  const res = await fetch("/api/latest");
  if (!res.ok) {
    throw new Error("No analysis found. Upload a file first.");
  }
  const data = await res.json();
  setStoredResult(data);
  return data;
}

function formatTimeRange(seriesTime) {
  if (!Array.isArray(seriesTime) || seriesTime.length === 0) return "-";
  return `${seriesTime[0]} to ${seriesTime[seriesTime.length - 1]}`;
}

function severityClass(severity) {
  const s = String(severity || "").toLowerCase();
  if (s === "critical") return "sev-critical";
  if (s === "high") return "sev-high";
  if (s === "medium") return "sev-medium";
  return "sev-low";
}

function urgencyClass(urgency) {
  const u = String(urgency || "").toLowerCase();
  if (u === "immediate") return "urg-immediate";
  if (u === "high") return "urg-immediate";
  if (u === "medium") return "urg-monitor";
  return "urg-low";
}

function statusClass(systemStatus) {
  const s = String(systemStatus || "").toUpperCase();
  if (s === "CRITICAL") return "sev-critical";
  if (s === "WARNING") return "sev-high";
  return "sev-low";
}

function computeSystemStatus(data) {
  const counts = data?.counts || { spikes: 0, drops: 0, anomalies: 0 };
  const totalSignals = Number(counts.spikes || 0) + Number(counts.drops || 0) + Number(counts.anomalies || 0);
  const risk = String(data?.risk || "").toLowerCase();

  if (risk === "high" || totalSignals >= 12) return "CRITICAL";
  if (risk === "medium" || totalSignals >= 5) return "UNSTABLE";
  return "STABLE";
}

function drawGraph(series, spikes, drops, anomalies) {
  const graph = document.getElementById("graph");
  if (!graph) return;

  graph.innerHTML = "";

  const values = Array.isArray(series) ? series.map((v) => Number(v)).filter((v) => Number.isFinite(v)) : [];
  if (!values.length) return;

  const width = 900;
  const height = 260;
  const pad = 24;

  let min = Math.min(...values);
  let max = Math.max(...values);
  if (min === max) {
    min -= 1;
    max += 1;
  }

  const point = (i, v) => {
    const x = pad + (i * (width - 2 * pad)) / Math.max(values.length - 1, 1);
    const y = pad + ((max - v) * (height - 2 * pad)) / (max - min);
    return { x, y };
  };

  const polyline = document.createElementNS("http://www.w3.org/2000/svg", "polyline");
  polyline.setAttribute(
    "points",
    values
      .map((v, i) => {
        const p = point(i, v);
        return `${p.x},${p.y}`;
      })
      .join(" ")
  );
  polyline.setAttribute("fill", "none");
  polyline.setAttribute("stroke", "#1b1b1b");
  polyline.setAttribute("stroke-width", "1.6");
  graph.appendChild(polyline);

  const addMarker = (idx, symbol, cssClass) => {
    if (!Number.isInteger(idx) || idx < 0 || idx >= values.length) return;
    const p = point(idx, values[idx]);
    const t = document.createElementNS("http://www.w3.org/2000/svg", "text");
    t.textContent = symbol;
    t.setAttribute("x", p.x);
    t.setAttribute("y", p.y - 8);
    t.setAttribute("text-anchor", "middle");
    t.setAttribute("class", `graph-marker ${cssClass}`);
    graph.appendChild(t);
  };

  (spikes || []).forEach((s) => addMarker(Number(s.index), "▲", "mark-spike"));
  (drops || []).forEach((d) => addMarker(Number(d.index), "▼", "mark-drop"));
  (anomalies || []).forEach((a) => {
    const idx = values.findIndex((v) => v === Number(a.data_rate));
    addMarker(idx, "●", "mark-anomaly");
  });
}

function ensureAiAnalysis(result) {
  const ai = result?.ai_analysis;
  if (ai && typeof ai === "object") return ai;

  const counts = result?.counts || { spikes: 0, drops: 0, anomalies: 0 };
  return {
    summary: `Signals detected: ${counts.spikes} spikes, ${counts.drops} drops, ${counts.anomalies} anomalies.`,
    affected_layer: "processing",
    root_cause: "AI analysis unavailable in current payload.",
    severity: "medium",
    impact: "Signal-level analytics are present but AI-generated diagnostics are unavailable.",
    recommendations: ["Retry AI analysis endpoint with current signal payload."],
    urgency: "medium",
    confidence: "medium",
    system_status: "WARNING",
    diagnosis: "AI diagnostics unavailable; using local fallback interpretation.",
    decision: {
      action_required: true,
      priority: "medium",
      next_step: "Retry AI analysis endpoint.",
    },
    actions: [
      {
        label: "Retry Analysis",
        type: "test",
        description: "Re-run AI analysis endpoint with the latest signal payload.",
      },
    ],
    source: "local_fallback",
  };
}

async function fetchAiAnalysisFromApi(result) {
  const payload = {
    data: {
      spikes: result?.spikes || [],
      drops: result?.drops || [],
      anomalies: result?.anomalies || [],
      counts: result?.counts || {},
      trend: result?.trend || "stable",
      risk_score: Number(result?.risk_score || 0),
      quality: Number(result?.quality || 0),
      distribution: result?.distribution || {},
    },
  };

  const res = await fetch("/api/ai-analysis", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (!res.ok) {
    throw new Error("AI analysis endpoint failed");
  }

  const data = await res.json();
  if (!data || typeof data.ai_analysis !== "object") {
    throw new Error("AI analysis endpoint returned invalid response");
  }

  return data.ai_analysis;
}

function renderEmptyState(emptyStateId, contentId) {
  const empty = document.getElementById(emptyStateId);
  const content = document.getElementById(contentId);
  if (empty) empty.style.display = "block";
  if (content) content.style.display = "none";
}

function renderReadyState(emptyStateId, contentId) {
  const empty = document.getElementById(emptyStateId);
  const content = document.getElementById(contentId);
  if (empty) empty.style.display = "none";
  if (content) content.style.display = "block";
}

async function initUpload() {
  const form = document.getElementById("upload-form");
  const fileInput = document.getElementById("file-input");
  const fileLabel = document.getElementById("file-label-text");
  const submit = document.getElementById("analyze-btn");
  const status = document.getElementById("status");
  const domainSelect = document.getElementById("domain-select");

  if (!form || !fileInput || !submit || !status) return;

  fileInput.addEventListener("change", () => {
    const hasFile = !!(fileInput.files && fileInput.files.length > 0);
    submit.disabled = !hasFile;
    if (fileLabel) {
      fileLabel.textContent = hasFile ? `${fileInput.files[0].name} selected` : "Select file or drag here";
    }
  });

  form.addEventListener("submit", async (event) => {
    event.preventDefault();

    if (!fileInput.files || fileInput.files.length === 0) {
      status.className = "status error";
      status.textContent = "Please select a file.";
      return;
    }

    submit.disabled = true;
    status.className = "status";
    status.textContent = "Analyzing dataset...";

    try {
      const file = fileInput.files[0];
      const domain = domainSelect ? domainSelect.value : "generic";
      const body = new FormData();
      body.append("file", file);
      body.append("domain", domain);

      const res = await fetch("/upload", { method: "POST", body });
      const data = await res.json();

      if (!res.ok) {
        throw new Error(data?.error || "Upload failed");
      }

      if (!data?.ai_analysis) {
        try {
          data.ai_analysis = await fetchAiAnalysisFromApi(data);
        } catch {
          data.ai_analysis = ensureAiAnalysis(data);
        }
      }

      setStoredResult(data);
      setStoredMeta({
        datasetName: file.name,
        domain,
        generatedAt: new Date().toISOString(),
      });
      addToHistory(file.name, domain, data);

      if (String(data?.ai_analysis?.error || "") === "AI service not configured") {
        status.className = "status error";
        status.textContent = "AI insights unavailable";
      } else {
        status.className = "status";
        status.textContent = "Analysis completed.";
      }

      window.setTimeout(() => {
        window.location.href = "/dashboard.html";
      }, 650);
    } catch (error) {
      status.className = "status error";
      status.textContent = error.message || "Analysis failed";
      submit.disabled = false;
    }
  });

  loadDomainConfig();
  if (domainSelect) {
    domainSelect.addEventListener("change", () => updateDomainUI(domainSelect.value));
    setTimeout(() => updateDomainUI(domainSelect.value), 150);
  }
}

function updateDomainUI(domainKey) {
  const config = DOMAIN_CONFIG[domainKey];
  const domainInfo = document.getElementById("domain-info");
  const genericNote = document.getElementById("generic-note");
  const schemaReq = document.getElementById("schema-requirements");
  const sampleFormat = document.getElementById("sample-format");
  const requiredFields = document.getElementById("required-fields");
  const optionalFields = document.getElementById("optional-fields");
  const sampleContent = document.getElementById("sample-content");

  if (!domainInfo) return;
  domainInfo.style.display = "block";

  if (!config || domainKey === "generic") {
    if (genericNote) genericNote.style.display = "block";
    if (schemaReq) schemaReq.style.display = "none";
    if (sampleFormat) sampleFormat.style.display = "none";
    return;
  }

  if (genericNote) genericNote.style.display = "none";
  if (schemaReq) schemaReq.style.display = "block";
  if (sampleFormat) sampleFormat.style.display = "block";
  if (requiredFields) requiredFields.textContent = (config.required || []).join(", ") || "(none)";
  if (optionalFields) optionalFields.textContent = (config.optional || []).join(", ") || "(none)";
  if (sampleContent) sampleContent.textContent = JSON.stringify(config.sample || {}, null, 2);
}

function loadDomainConfig() {
  fetch("/domains.json")
    .then((res) => res.json())
    .then((data) => {
      DOMAIN_CONFIG = data || {};
    })
    .catch(() => {
      DOMAIN_CONFIG = {};
    });
}

async function resolveResultOrEmpty(emptyStateId, contentId) {
  let result = getStoredResult();

  if (!result) {
    try {
      result = await fetchLatestResult();
    } catch {
      renderEmptyState(emptyStateId, contentId);
      return null;
    }
  }

  if (!result || typeof result !== "object") {
    renderEmptyState(emptyStateId, contentId);
    return null;
  }

  renderReadyState(emptyStateId, contentId);
  return result;
}

async function initDashboard() {
  const result = await resolveResultOrEmpty("empty-state", "dashboard-content");
  if (!result) return;

  const counts = result.counts || { spikes: 0, drops: 0, anomalies: 0 };
  const ai = ensureAiAnalysis(result);
  const meta = getStoredMeta();

  const metricSpikes = document.getElementById("metric-spikes");
  const metricDrops = document.getElementById("metric-drops");
  const metricAnomalies = document.getElementById("metric-anomalies");
  const metricQuality = document.getElementById("metric-quality");
  const dataset = document.getElementById("meta-dataset");
  const timeRange = document.getElementById("meta-time-range");
  const status = document.getElementById("system-status");
  const findings = document.getElementById("key-findings");
  const recommendations = document.getElementById("recommendations");

  if (metricSpikes) metricSpikes.textContent = String(counts.spikes || 0);
  if (metricDrops) metricDrops.textContent = String(counts.drops || 0);
  if (metricAnomalies) metricAnomalies.textContent = String(counts.anomalies || 0);
  if (metricQuality) metricQuality.textContent = String(result.quality || 0);
  if (dataset) dataset.textContent = meta.datasetName || result.dataset_name || "Uploaded Dataset";
  if (timeRange) timeRange.textContent = formatTimeRange(result?.series?.time || []);
  if (status) status.textContent = `System Status: ${computeSystemStatus(result)}`;

  if (findings) {
    const keyFindings = [
      `Trend: ${result.trend || "stable"}`,
      `Risk score: ${Number(result.risk_score || 0)}`,
      `AI severity: ${String(ai.severity || "medium")}`,
      `AI root cause: ${String(ai.root_cause || "n/a")}`,
      `Distribution variance: ${Number(result?.distribution?.variance || 0).toFixed(2)}`,
    ];
    findings.innerHTML = keyFindings.map((item) => `<li>${escapeHtml(item)}</li>`).join("");
  }

  if (recommendations) {
    const recs = Array.isArray(ai.recommendations) ? ai.recommendations : [];
    recommendations.innerHTML = recs.length
      ? recs.map((item) => `<li>${escapeHtml(item)}</li>`).join("")
      : "<li>No recommendation available.</li>";
  }

  drawGraph(result?.series?.data_rate || [], result.spikes || [], result.drops || [], result.anomalies || []);
}

async function initReport() {
  const result = await resolveResultOrEmpty("empty-state", "report-content");
  if (!result) return;

  const ai = ensureAiAnalysis(result);
  const statusBar = document.getElementById("status-bar");
  const insights = document.getElementById("insights");
  const recommendations = document.getElementById("recommendations");

  if (statusBar) {
    statusBar.innerHTML = [
      ["Trend", result.trend || "stable"],
      ["Risk", `${String(result.risk || "unknown").toUpperCase()} (${Number(result.risk_score || 0)})`],
      ["Quality", String(result.quality || 0)],
      ["Severity", String(ai.severity || "medium").toUpperCase()],
    ]
      .map(([k, v]) => `<div class="status-chip"><div class="k">${escapeHtml(k)}</div><div class="v">${escapeHtml(v)}</div></div>`)
      .join("");
  }

  if (insights) {
    insights.innerHTML = [
      ["Summary", ai.summary],
      ["Root Cause", ai.root_cause],
      ["Impact", ai.impact],
    ]
      .map(([title, text]) => `<div class="insight-card"><div class="insight-title">${escapeHtml(title)}</div><div class="insight-body">${escapeHtml(text || "-")}</div></div>`)
      .join("");
  }

  if (recommendations) {
    const recs = Array.isArray(ai.recommendations) ? ai.recommendations : [];
    recommendations.innerHTML = recs.length
      ? recs.map((r) => `<li>${escapeHtml(r)}</li>`).join("")
      : "<li>No recommendation available.</li>";
  }

  const events = document.getElementById("event-list");
  if (events) {
    const items = [
      ...(result.spikes || []).map((s) => `Spike at ${s.time} (${Number(s.data_rate).toFixed(2)})`),
      ...(result.drops || []).map((d) => `Drop at ${d.time} (${Number(d.data_rate).toFixed(2)})`),
      ...(result.anomalies || []).map((a) => `Anomaly at ${a.time} (${Number(a.data_rate).toFixed(2)})`),
    ];
    events.innerHTML = items.length ? items.map((x) => `<li>${escapeHtml(x)}</li>`).join("") : "<li>No events detected.</li>";
  }

  const detail = document.getElementById("event-detail");
  if (detail) {
    detail.textContent = `Urgency: ${String(ai.urgency || "monitor")}. Source: ${String(ai.source || "unknown")}.`;
  }

  drawGraph(result?.series?.data_rate || [], result.spikes || [], result.drops || [], result.anomalies || []);
}

async function initAiInsights() {
  const result = await resolveResultOrEmpty("empty-state", "ai-insights-content");
  if (!result) return;

  const apiStatus = document.getElementById("ai-api-status");

  const renderAi = (ai) => {
    const systemStatus = document.getElementById("ai-system-status");
    const layer = document.getElementById("ai-layer");
    const confidence = document.getElementById("ai-confidence");
    const summary = document.getElementById("ai-summary");
    const root = document.getElementById("ai-root-cause");
    const severity = document.getElementById("ai-severity");
    const impact = document.getElementById("ai-impact");
    const recommendations = document.getElementById("ai-recommendations");
    const urgency = document.getElementById("ai-urgency");
    const nextStep = document.getElementById("ai-next-step");
    const actions = document.getElementById("ai-actions");

    const resolvedStatus = String(
      ai.system_status || (String(ai.severity || "").toLowerCase() === "critical" ? "CRITICAL" : (String(ai.severity || "").toLowerCase() === "low" ? "STABLE" : "WARNING"))
    ).toUpperCase();
    const resolvedLayer = String(ai.affected_layer || "processing").toLowerCase();
    const resolvedConfidence = String(ai.confidence || "medium").toUpperCase();
    const resolvedNextStep = String(ai?.decision?.next_step || (Array.isArray(ai.recommendations) && ai.recommendations[0]) || "No immediate step available.");

    if (systemStatus) {
      systemStatus.textContent = resolvedStatus;
      systemStatus.className = `badge ${statusClass(resolvedStatus)}`;
    }
    if (layer) layer.textContent = resolvedLayer;
    if (confidence) {
      confidence.textContent = resolvedConfidence;
      confidence.className = `badge ${severityClass(String(ai.severity || "medium").toLowerCase())}`;
    }
    if (summary) summary.textContent = ai.summary || "-";
    if (root) root.textContent = ai.root_cause || "-";
    if (impact) impact.textContent = ai.impact || "-";
    if (nextStep) nextStep.textContent = resolvedNextStep;

    if (severity) {
      severity.textContent = String(ai.severity || "medium").toUpperCase();
      severity.className = `badge ${severityClass(ai.severity)}`;
    }

    if (urgency) {
      urgency.textContent = String(ai.urgency || "medium").toUpperCase();
      urgency.className = `badge ${urgencyClass(ai.urgency)}`;
    }

    if (recommendations) {
      const recs = Array.isArray(ai.recommendations) ? ai.recommendations : [];
      recommendations.innerHTML = recs.length
        ? recs.map((item) => `<li>${escapeHtml(item)}</li>`).join("")
        : "<li>No recommendation available.</li>";
    }

    if (actions) {
      const actionItems = Array.isArray(ai.actions) ? ai.actions : [];
      actions.innerHTML = actionItems.length
        ? actionItems
            .map((item) => {
              const label = escapeHtml(String(item?.label || "Action"));
              const type = escapeHtml(String(item?.type || "monitor").toUpperCase());
              const desc = escapeHtml(String(item?.description || ""));
              return `<li><strong>${label}</strong> (${type}) - ${desc}</li>`;
            })
            .join("")
        : "<li>No action available.</li>";
    }

    if (apiStatus) {
      if (String(ai?.error || "") === "AI service not configured") {
        apiStatus.className = "status error";
        apiStatus.textContent = "AI insights unavailable";
      } else {
        apiStatus.className = "status";
        apiStatus.textContent = "";
      }
    }
  };

  let ai = ensureAiAnalysis(result);
  if (ai.source === "local_fallback") {
    try {
      ai = await fetchAiAnalysisFromApi(result);
      result.ai_analysis = ai;
      setStoredResult(result);
    } catch (error) {
      if (String(error.message || "") === "AI analysis endpoint failed") {
        ai = { error: "AI service not configured" };
      } else {
        ai = ensureAiAnalysis(result);
      }
    }
  }

  if (ai && String(ai.error || "") === "AI service not configured") {
    ai = {
      summary: "AI insights unavailable",
      affected_layer: "processing",
      root_cause: "AI service not configured",
      severity: "medium",
      impact: "Core signal analytics are available, but AI explanation is unavailable.",
      recommendations: ["Configure the AI service key on the backend environment."],
      urgency: "medium",
      confidence: "medium",
      system_status: "WARNING",
      diagnosis: "AI service key is missing on backend runtime configuration.",
      decision: {
        action_required: true,
        priority: "medium",
        next_step: "Configure backend AI key and restart server.",
      },
      actions: [
        {
          label: "Configure Backend Key",
          type: "investigate",
          description: "Set backend environment key and restart runtime process.",
        },
      ],
      error: "AI service not configured",
      source: "unavailable",
    };
  }

  renderAi(ai);
}

function buildComparisonSummary(selected) {
  if (!selected.length) return "Select one or more reports to compare.";

  const withSignals = selected.map((r) => {
    const counts = r?.result?.counts || { spikes: 0, drops: 0, anomalies: 0 };
    const total = Number(counts.spikes || 0) + Number(counts.drops || 0) + Number(counts.anomalies || 0);
    return { report: r, total };
  });

  const least = withSignals.reduce((a, b) => (a.total <= b.total ? a : b));
  const most = withSignals.reduce((a, b) => (a.total >= b.total ? a : b));

  return `${least.report.name} appears more stable than ${most.report.name} based on lower total signal events.`;
}

async function initComparison() {
  const history = getHistory();
  if (!history.length) {
    renderEmptyState("empty-state", "comparison-content");
    return;
  }

  renderReadyState("empty-state", "comparison-content");

  const list = document.getElementById("reports-list");
  const warning = document.getElementById("warning-container");
  const viewSection = document.getElementById("comparison-view-section");
  const tableSection = document.getElementById("comparison-table-section");
  const insightSection = document.getElementById("comparison-insight-section");
  const columns = document.getElementById("comparison-columns");
  const tableContainer = document.getElementById("comparison-table-container");
  const insight = document.getElementById("comparison-insight");

  if (!list) return;

  const rows = history
    .map(
      (item, i) => `
      <div class="report-item">
        <input class="report-checkbox" type="checkbox" data-index="${i}" id="rep-${i}">
        <label for="rep-${i}">${escapeHtml(item.name)} (${escapeHtml(item.domain || "generic")})</label>
      </div>
    `
    )
    .join("");

  list.innerHTML = rows;
  if (warning) warning.innerHTML = '<div class="info-box">Select up to 3 reports to compare.</div>';

  const checkboxes = Array.from(document.querySelectorAll(".report-checkbox"));
  const renderSelection = () => {
    const selected = checkboxes
      .filter((cb) => cb.checked)
      .map((cb) => history[Number(cb.getAttribute("data-index"))])
      .slice(0, 3);

    checkboxes.forEach((cb, idx) => {
      if (idx >= 3 && selected.length >= 3) cb.disabled = !cb.checked;
      else cb.disabled = false;
    });

    if (!selected.length) {
      if (viewSection) viewSection.style.display = "none";
      if (tableSection) tableSection.style.display = "none";
      if (insightSection) insightSection.style.display = "none";
      return;
    }

    if (viewSection) viewSection.style.display = "block";
    if (tableSection) tableSection.style.display = selected.length > 1 ? "block" : "none";
    if (insightSection) insightSection.style.display = "block";

    if (columns) {
      columns.style.gridTemplateColumns = `repeat(${Math.min(selected.length, 3)}, 1fr)`;
      columns.innerHTML = selected
        .map((entry) => {
          const counts = entry.result?.counts || { spikes: 0, drops: 0, anomalies: 0 };
          const ai = ensureAiAnalysis(entry.result || {});
          return `
            <article class="comparison-column">
              <div class="column-header">${escapeHtml(entry.name)}</div>
              <div class="column-meta">Domain: ${escapeHtml(entry.domain || "generic")}</div>
              <div class="column-metric">Spikes: <strong>${Number(counts.spikes || 0)}</strong></div>
              <div class="column-metric">Drops: <strong>${Number(counts.drops || 0)}</strong></div>
              <div class="column-metric">Anomalies: <strong>${Number(counts.anomalies || 0)}</strong></div>
              <div class="column-metric">Severity: <strong>${escapeHtml(String(ai.severity || "medium").toUpperCase())}</strong></div>
            </article>
          `;
        })
        .join("");
    }

    if (tableContainer && selected.length > 1) {
      const header = ["Metric", ...selected.map((s) => escapeHtml(s.name))];
      const metricRows = ["spikes", "drops", "anomalies", "quality"];
      tableContainer.innerHTML = `
        <table class="comparison-table">
          <thead><tr>${header.map((h) => `<th>${h}</th>`).join("")}</tr></thead>
          <tbody>
            ${metricRows
              .map((metric) => {
                const values = selected.map((s) => {
                  if (metric === "quality") return Number(s.result?.quality || 0);
                  return Number(s.result?.counts?.[metric] || 0);
                });
                return `<tr><td><strong>${escapeHtml(metric.toUpperCase())}</strong></td>${values
                  .map((v) => `<td>${v}</td>`)
                  .join("")}</tr>`;
              })
              .join("")}
          </tbody>
        </table>
      `;
    }

    if (insight) {
      insight.textContent = buildComparisonSummary(selected);
    }
  };

  checkboxes.forEach((cb) => cb.addEventListener("change", renderSelection));
}

window.addEventListener("error", (event) => {
  const status = document.getElementById("status");
  if (status) {
    status.className = "status error";
    status.textContent = event.error?.message || "Unexpected error";
  }
});

window.addEventListener("unhandledrejection", () => {
  const status = document.getElementById("status");
  if (status) {
    status.className = "status error";
    status.textContent = "Unexpected network error";
  }
});

async function boot() {
  const page = detectPage();
  if (page === "upload") return initUpload();
  if (page === "dashboard") return initDashboard();
  if (page === "report") return initReport();
  if (page === "comparison") return initComparison();
  if (page === "ai") return initAiInsights();
}

boot();
