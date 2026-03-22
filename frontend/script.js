// GLOBAL ERROR HANDLER
window.addEventListener("error", (event) => {
  console.error("Global error:", event.error);
  const statusDiv = document.getElementById("status");
  if (statusDiv) {
    statusDiv.className = "status error";
    statusDiv.textContent = "System error: " + (event.error?.message || "Unknown error");
  }
});

window.addEventListener("unhandledrejection", (event) => {
  console.error("Unhandled promise rejection:", event.reason);
  const statusDiv = document.getElementById("status");
  if (statusDiv) {
    statusDiv.className = "status error";
    statusDiv.textContent = "Network error: " + (event.reason?.message || "Request failed");
  }
});

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
  return "unknown";
}

function getReportHistory() {
  try {
    return JSON.parse(localStorage.getItem("REPORT_HISTORY") || "[]");
  } catch {
    return [];
  }
}

function setReportHistory(history) {
  localStorage.setItem("REPORT_HISTORY", JSON.stringify(history));
}

function getStoredResult() {
  try {
    return JSON.parse(localStorage.getItem("dfis_latest") || "null");
  } catch {
    return null;
  }
}

function setStoredResult(data) {
  localStorage.setItem("dfis_latest", JSON.stringify(data));
}

function setReportMeta(meta) {
  localStorage.setItem("dfis_report_meta", JSON.stringify(meta));
}

function getReportMeta() {
  try {
    return JSON.parse(localStorage.getItem("dfis_report_meta") || "null") || {};
  } catch {
    return {};
  }
}

async function getLatestResult() {
  const res = await fetch("/api/latest");
  if (!res.ok) {
    throw new Error("No analysis found. Upload a file first.");
  }
  const data = await res.json();
  setStoredResult(data);
  return data;
}

function metricCard(label, value) {
  return `<div class="metric"><div class="k">${escapeHtml(label)}</div><div class="v">${escapeHtml(value)}</div></div>`;
}

function qualityLabel(score) {
  const n = Number(score || 0);
  if (n >= 90) return "Excellent";
  if (n >= 75) return "Good";
  if (n >= 55) return "Fair";
  return "Poor";
}

function riskLabel(level) {
  const l = String(level || "").toLowerCase();
  if (l === "low") return "Low concern";
  if (l === "medium") return "Moderate concern";
  if (l === "high") return "High concern";
  return "Unknown concern";
}

function computeSystemStatus(data) {
  const counts = data.counts || { spikes: 0, drops: 0, anomalies: 0 };
  const spikes = Number(counts.spikes || 0);
  const drops = Number(counts.drops || 0);
  const anomalies = Number(counts.anomalies || 0);
  const risk = String(data.risk || "").toLowerCase();

  if (risk === "high" || anomalies >= 5 || spikes + drops >= 14) {
    return {
      status: "CRITICAL",
      reason: "High risk with frequent abnormal events detected.",
      meaning: "This system is currently critical and needs immediate attention to avoid service impact.",
      css: "critical",
    };
  }

  if (risk === "medium" || anomalies >= 2 || spikes + drops >= 4) {
    return {
      status: "UNSTABLE",
      reason: "Moderate anomalies and spikes detected.",
      meaning: "This system is mostly stable but shows occasional disruptions indicating temporary issues.",
      css: "unstable",
    };
  }

  return {
    status: "STABLE",
    reason: "No major anomaly pattern was detected.",
    meaning: "The system behavior is stable with normal variation.",
    css: "stable",
  };
}

function formatGenerated(value) {
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return "-";
  return d.toLocaleString();
}

function formatTimeRange(seriesTime) {
  if (!Array.isArray(seriesTime) || seriesTime.length === 0) return "-";
  return `${seriesTime[0]} to ${seriesTime[seriesTime.length - 1]}`;
}

function executiveSummary(data, statusInfo) {
  const counts = data.counts || { spikes: 0, drops: 0, anomalies: 0 };
  const trend = data.trend || "stable";
  const confidenceText = data?.confidence?.text || "Confidence: unavailable";
  return `The system shows ${statusInfo.status.toLowerCase()} behavior with ${counts.spikes} spikes, ${counts.drops} drops, and ${counts.anomalies} anomalies. Overall trend is ${trend}, with ${statusInfo.reason.toLowerCase()}. ${confidenceText}.`;
}

function keyFindings(data) {
  const counts = data.counts || { spikes: 0, drops: 0, anomalies: 0 };
  const timeAnalysis = data.time_analysis || {};
  const distribution = data.distribution || {};
  return [
    `Spikes: ${counts.spikes} spike events indicate sudden load increases.`,
    `Drops: ${counts.drops} drop events indicate temporary reductions or interruptions.`,
    `Anomalies: ${counts.anomalies} anomalies indicate behavior outside normal patterns.`,
    `Trend: ${data.trend || "stable"} trend indicates overall directional behavior.`,
    `Peak interval: ${timeAnalysis.frequent_spike_period || "No peak interval detected."}`,
    `Distribution: mean ${Number(distribution.mean || 0).toFixed(2)}, median ${Number(distribution.median || 0).toFixed(2)}, variance ${Number(distribution.variance || 0).toFixed(2)}.`,
  ];
}

function riskJustification(data, statusInfo) {
  const risk = String(data.risk || "unknown").toLowerCase();
  const counts = data.counts || { spikes: 0, drops: 0, anomalies: 0 };
  return `Risk is ${risk} because the system recorded ${counts.spikes} spikes, ${counts.drops} drops, and ${counts.anomalies} anomalies. This supports a ${statusInfo.status.toLowerCase()} classification.`;
}

async function loadComparisonSection() {
  const summaryEl = document.getElementById("comparison-summary");
  const listEl = document.getElementById("comparison-list");
  if (!summaryEl || !listEl) return;

  try {
    const res = await fetch("/api/compare");
    const comparison = await res.json();

    summaryEl.textContent = comparison.summary || comparison.message || "Comparison unavailable.";
    const items = Array.isArray(comparison.items) ? comparison.items : [];
    listEl.innerHTML = items.length
      ? items.map((item) => `<li>${escapeHtml(item.dataset)}: stability ${escapeHtml(item.stability)}, risk ${escapeHtml(item.risk)}, anomalies ${Number(item.anomalies || 0)}, variance ${Number(item.variance || 0).toFixed(2)}</li>`).join("")
      : "<li>Upload at least two datasets to compare.</li>";
  } catch {
    summaryEl.textContent = "Comparison unavailable.";
    listEl.innerHTML = "<li>Could not load comparison.</li>";
  }
}

let DOMAIN_CONFIG = {};

fetch("domains.json")
  .then(r => r.json())
  .then(data => {
    DOMAIN_CONFIG = data;
    console.log("domains loaded", DOMAIN_CONFIG);
  })
  .catch(e => console.error("domain load failed", e));

function updateDomainUI(domainKey) {
  console.log("selected domain:", domainKey);

  const config = DOMAIN_CONFIG[domainKey];
  const domainInfo = document.getElementById("domain-info");
  const genericNote = document.getElementById("generic-note");
  const schemaRequirements = document.getElementById("schema-requirements");
  const sampleFormat = document.getElementById("sample-format");
  const requiredFields = document.getElementById("required-fields");
  const optionalFields = document.getElementById("optional-fields");
  const sampleContent = document.getElementById("sample-content");

  if (!config) {
    console.error("domain config missing");
    if (domainInfo) domainInfo.style.display = "none";
    return;
  }

  // Always show domain-info
  if (domainInfo) domainInfo.style.display = "block";

  if (domainKey === "generic") {
    // Generic domain: show note, hide schema
    if (genericNote) genericNote.style.display = "block";
    if (schemaRequirements) schemaRequirements.style.display = "none";
    if (sampleFormat) sampleFormat.style.display = "none";
  } else {
    // Schema domains: hide note, show schema and sample
    if (genericNote) genericNote.style.display = "none";
    if (schemaRequirements) schemaRequirements.style.display = "block";
    if (sampleFormat) sampleFormat.style.display = "block";

    // Populate required fields
    if (requiredFields) {
      requiredFields.innerText = config.required.length ? config.required.join(", ") : "(none)";
    }

    // Populate optional fields
    if (optionalFields) {
      optionalFields.innerText = config.optional.length ? config.optional.join(", ") : "(none)";
    }

    // Populate sample format
    if (sampleContent) {
      sampleContent.innerText = Object.keys(config.sample).length ? JSON.stringify(config.sample, null, 2) : "{}";
    }
  }
}

async function initUpload() {
  const form = document.getElementById("upload-form");
  const fileInput = document.getElementById("file-input");
  const fileLabel = document.getElementById("file-label-text");
  const button = document.getElementById("analyze-btn");
  const status = document.getElementById("status");
  const domainSelect = document.getElementById("domain-select");
  const validationFeedback = document.getElementById("validation-feedback");
  const validationStatus = document.getElementById("validation-status");

  if (fileInput) {
    fileInput.addEventListener("change", () => {
      if (fileInput.files && fileInput.files.length > 0) {
        const fileName = fileInput.files[0].name;
        if (fileLabel) fileLabel.textContent = `${fileName} selected`;
        if (button) button.disabled = false;
      } else {
        if (fileLabel) fileLabel.textContent = "Select file or drag here";
        if (button) button.disabled = true;
      }
    });
  }

  form.addEventListener("submit", async (event) => {
    event.preventDefault();

    if (!fileInput.files || fileInput.files.length === 0) {
      status.className = "status error";
      status.textContent = "Please select a file.";
      return;
    }

    button.disabled = true;
    status.className = "status";
    status.textContent = "Running pipeline...";
    if (validationFeedback) validationFeedback.style.display = "none";

    try {
      const body = new FormData();
      const selectedFile = fileInput.files[0];
      const selectedDomain = domainSelect ? domainSelect.value : "generic";
      
      body.append("file", selectedFile);
      body.append("domain", selectedDomain);

      const res = await fetch("/upload", {
        method: "POST",
        body,
      });

      const data = await res.json();
      
      if (!res.ok) {
        if (data.validation_error) {
          if (validationFeedback && validationStatus) {
            validationStatus.className = "validation-status invalid";
            validationStatus.textContent = data.error || "Dataset does not match selected domain schema";
            validationFeedback.style.display = "block";
          }
          status.textContent = "";
        } else {
          throw new Error(data.error || "Analysis failed");
        }
        button.disabled = false;
        return;
      }

      if (validationFeedback && validationStatus) {
        validationStatus.className = "validation-status valid";
        validationStatus.textContent = "Dataset matches selected domain";
        validationFeedback.style.display = "block";
      }

      const reportId = "report_" + Date.now();
      const history = getReportHistory();
      history.push({
        id: reportId,
        name: selectedFile.name,
        domain: selectedDomain,
        created_at: new Date().toISOString(),
        result: data
      });
      setReportHistory(history);
      setStoredResult(data);
      setReportMeta({
        datasetName: selectedFile.name,
        domain: selectedDomain,
        generatedAt: new Date().toISOString(),
      });

      status.className = "status";
      status.textContent = "Report generated successfully";
      
      window.setTimeout(() => {
        window.location.href = "/dashboard.html";
      }, 1000);
    } catch (error) {
      status.className = "status error";
      status.textContent = error.message || "Analysis failed";
      button.disabled = false;
    }
  });
}


async function initDashboard() {
  const emptyState = document.getElementById("empty-state");
  const dashboardContent = document.getElementById("dashboard-content");

  let data = getStoredResult();

  if (!data) {
    try {
      data = await getLatestResult();
    } catch {
      if (emptyState) emptyState.style.display = "block";
      if (dashboardContent) dashboardContent.style.display = "none";
      return;
    }
  }

  if (!data || !data.counts) {
    if (emptyState) emptyState.style.display = "block";
    if (dashboardContent) dashboardContent.style.display = "none";
    return;
  }

  if (emptyState) emptyState.style.display = "none";
  if (dashboardContent) dashboardContent.style.display = "block";

  const metricSpikes = document.getElementById("metric-spikes");
  const metricDrops = document.getElementById("metric-drops");
  const metricAnomalies = document.getElementById("metric-anomalies");
  const metricQuality = document.getElementById("metric-quality");
  const metaDataset = document.getElementById("meta-dataset");
  const metaTimeRange = document.getElementById("meta-time-range");
  const systemStatus = document.getElementById("system-status");
  const findingsEl = document.getElementById("key-findings");
  const recommendationsEl = document.getElementById("recommendations");

  const counts = data.counts || { spikes: 0, drops: 0, anomalies: 0 };
  if (metricSpikes) metricSpikes.textContent = counts.spikes || 0;
  if (metricDrops) metricDrops.textContent = counts.drops || 0;
  if (metricAnomalies) metricAnomalies.textContent = counts.anomalies || 0;
  if (metricQuality) metricQuality.textContent = `${data.quality || 0}`;

  const meta = getReportMeta();
  if (metaDataset) metaDataset.textContent = meta.datasetName || "Uploaded Dataset";
  if (metaTimeRange) metaTimeRange.textContent = formatTimeRange(data?.series?.time || []);

  const info = computeSystemStatus(data);
  if (systemStatus) systemStatus.textContent = `System Status: ${info.status}`;
  if (findingsEl) findingsEl.innerHTML = keyFindings(data).map((x) => `<li>${escapeHtml(x)}</li>`).join("");
  if (recommendationsEl) {
    const recs = data.recommendations || [];
    recommendationsEl.innerHTML = recs.length
      ? recs.map((x) => `<li>${escapeHtml(x)}</li>`).join("")
      : [
          "Reduce load during peak times.",
          "Check system stability and service health.",
          "Inspect logs for unusual patterns.",
        ].map((x) => `<li>${escapeHtml(x)}</li>`).join("");
  }

  drawGraph(
    (data.series && data.series.data_rate ? data.series.data_rate : []).map((x) => Number(x)),
    (data.series && data.series.time ? data.series.time : []),
    data.spikes || [],
    data.drops || [],
    data.anomalies || []
  );
}

function eventExplanation(event) {
  if (event.type === "spike") {
    return "A spike means sudden traffic/load increase that may indicate overload or burst activity.";
  }
  if (event.type === "drop") {
    return "A drop means sudden traffic/load decrease that may indicate interruption or temporary failure.";
  }
  return "An anomaly means behavior that does not match normal pattern and should be investigated.";
}

function renderEventExplorer(events) {
  const list = document.getElementById("event-list");
  const detail = document.getElementById("event-detail");
  if (!list || !detail) return;

  if (!events.length) {
    list.innerHTML = "<li>No events detected.</li>";
    detail.textContent = "No event explanation available.";
    return;
  }

  list.innerHTML = events
    .map((e, i) => {
      const symbol = e.type === "spike" ? "▲" : e.type === "drop" ? "▼" : "●";
      return `<li data-event-index="${i}">${symbol} ${escapeHtml(e.type.toUpperCase())} at ${escapeHtml(e.time)} (${Number(e.value).toFixed(2)}) - ${escapeHtml(String(e.severity || "minor"))}</li>`;
    })
    .join("");

  list.querySelectorAll("li[data-event-index]").forEach((node) => {
    node.addEventListener("click", () => {
      const idx = Number(node.getAttribute("data-event-index"));
      const e = events[idx];
      detail.textContent = `${e.type.toUpperCase()} EVENT (${String(e.severity || "minor").toUpperCase()}): ${eventExplanation(e)} Time: ${e.time}. Value: ${Number(e.value).toFixed(2)}.`;
    });
  });
}

function drawGraph(series, seriesTime, spikes, drops, anomalies) {
  const graph = document.getElementById("graph");
  graph.innerHTML = "";

  if (!series || series.length === 0) {
    return;
  }

  const width = 900;
  const height = 260;
  const pad = 20;
  let min = Math.min(...series);
  let max = Math.max(...series);

  if (min === max) {
    min -= 1;
    max += 1;
  }

  const toPoint = (idx, val) => {
    const x = pad + (idx * (width - pad * 2)) / Math.max(series.length - 1, 1);
    const y = pad + ((max - val) * (height - pad * 2)) / (max - min);
    return { x, y };
  };

  const points = series.map((val, idx) => {
    const p = toPoint(idx, Number(val));
    return `${p.x},${p.y}`;
  });

  const path = document.createElementNS("http://www.w3.org/2000/svg", "polyline");
  path.setAttribute("points", points.join(" "));
  path.setAttribute("fill", "none");
  path.setAttribute("stroke", "#111111");
  path.setAttribute("stroke-width", "1.7");
  graph.appendChild(path);

  const events = [];

  function marker(index, value, symbol, color, type, time) {
    if (index < 0 || index >= series.length) return;
    const p = toPoint(index, Number(value));
    const text = document.createElementNS("http://www.w3.org/2000/svg", "text");
    text.setAttribute("x", p.x);
    text.setAttribute("y", p.y - 8);
    text.setAttribute("text-anchor", "middle");
    text.setAttribute("fill", color);
    text.setAttribute("font-size", "13");
    text.setAttribute("class", "marker");
    text.textContent = symbol;

    const eventObj = {
      type,
      time: time || (seriesTime[index] || `Index ${index}`),
      value: Number(value),
      severity: itemSeverity(type, Number(value), series),
    };
    text.addEventListener("click", () => {
      const detail = document.getElementById("event-detail");
      if (detail) {
        detail.textContent = `${eventObj.type.toUpperCase()} EVENT (${String(eventObj.severity || "minor").toUpperCase()}): ${eventExplanation(eventObj)} Time: ${eventObj.time}. Value: ${Number(eventObj.value).toFixed(2)}.`;
      }
    });

    events.push(eventObj);
    graph.appendChild(text);
  }

  spikes.forEach((item) => marker(Number(item.index), Number(item.data_rate), "▲", "#000000", "spike", item.time));
  drops.forEach((item) => marker(Number(item.index), Number(item.data_rate), "▼", "#6f6f6f", "drop", item.time));

  anomalies.forEach((item) => {
    const index = series.findIndex((v) => Number(v) === Number(item.data_rate));
    marker(index, Number(item.data_rate), "●", "#b0b0b0", "anomaly", item.time);
  });

  renderEventExplorer(events);
}

function insightCard(title, text) {
  return `<div class="insight-card"><div class="insight-title">${escapeHtml(title)}</div><div class="insight-body">${escapeHtml(text)}</div></div>`;
}

function itemSeverity(type, value, series) {
  const numeric = Array.isArray(series) ? series.filter((x) => Number.isFinite(Number(x))).map((x) => Number(x)) : [];
  if (!numeric.length) return "minor";
  const mean = numeric.reduce((a, b) => a + b, 0) / numeric.length;
  const variance = numeric.reduce((acc, x) => acc + (x - mean) * (x - mean), 0) / numeric.length;
  const std = Math.sqrt(Math.max(variance, 0));
  if (!Number.isFinite(std) || std === 0) return "minor";
  const deviation = type === "drop" ? (mean - value) / std : (value - mean) / std;
  if (deviation >= 2.5) return "severe";
  if (deviation >= 1.2) return "moderate";
  return "minor";
}

function buildExportText(data) {
  const meta = getReportMeta();
  const status = computeSystemStatus(data);
  const findings = keyFindings(data).map((x) => `- ${x}`).join("\n");
  const recommendations = (data.recommendations || []).map((x) => `- ${x}`).join("\n") || "- No recommendations.";

  return [
    "Data Flow Analysis Report",
    "",
    `Dataset: ${meta.datasetName || data.dataset_name || "Uploaded Dataset"}`,
    `Domain: ${meta.domain || "Generic"}`,
    `Generated: ${formatGenerated(meta.generatedAt || new Date().toISOString())}`,
    `Time Range: ${formatTimeRange(data?.series?.time || [])}`,
    "",
    "Executive Summary",
    executiveSummary(data, status),
    "",
    "Key Findings",
    findings,
    "",
    "Risk Justification",
    riskJustification(data, status),
    "",
    "Recommendations",
    recommendations,
    "",
  ].join("\n");
}

function downloadTextFile(filename, content) {
  const blob = new Blob([content], { type: "text/plain;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}

function setupExport(data) {
  const exportTxt = document.getElementById("export-txt");
  const exportStructured = document.getElementById("export-structured");
  if (!exportTxt || !exportStructured) return;

  exportTxt.addEventListener("click", () => {
    downloadTextFile("data_flow_report.txt", buildExportText(data));
  });

  exportStructured.addEventListener("click", () => {
    const structured = buildExportText(data)
      .replace("Data Flow Analysis Report", "DATA FLOW ANALYSIS REPORT")
      .replace("Executive Summary", "=== EXECUTIVE SUMMARY ===")
      .replace("Key Findings", "=== KEY FINDINGS ===")
      .replace("Risk Justification", "=== RISK JUSTIFICATION ===")
      .replace("Recommendations", "=== RECOMMENDATIONS ===");
    downloadTextFile("data_flow_report_structured.txt", structured);
  });
}

function buildInsightBlocks(insights) {
  if (!insights.length) {
    return insightCard("INFO", "No insights generated.");
  }

  return insights
    .map((line) => {
      const lower = String(line).toLowerCase();
      if (lower.includes("spike") || lower.includes("overload")) {
        return insightCard("OVERLOAD DETECTED", line);
      }
      if (lower.includes("drop") || lower.includes("interrupt")) {
        return insightCard("INTERRUPTION DETECTED", line);
      }
      if (lower.includes("anomal")) {
        return insightCard("ANOMALY DETECTED", line);
      }
      if (lower.includes("trend")) {
        return insightCard("TREND UPDATE", line);
      }
      return insightCard("SYSTEM NOTE", line);
    })
    .join("");
}

async function initReport() {
  const emptyState = document.getElementById("empty-state");
  const reportContent = document.getElementById("report-content");

  let data = getStoredResult();

  if (!data) {
    try {
      data = await getLatestResult();
    } catch {
      if (emptyState) emptyState.style.display = "block";
      if (reportContent) reportContent.style.display = "none";
      return;
    }
  }

  if (!data || !data.counts) {
    if (emptyState) emptyState.style.display = "block";
    if (reportContent) reportContent.style.display = "none";
    return;
  }

  if (emptyState) emptyState.style.display = "none";
  if (reportContent) reportContent.style.display = "block";

  const statusBar = document.getElementById("status-bar");
  const statusInfo = computeSystemStatus(data);
  
  if (statusBar) {
    statusBar.innerHTML = [
      ["Trend", data.trend || "-"],
      ["Risk", `${data.risk || "-"} (${riskLabel(data.risk)})`],
      ["Quality", `${data.quality || 0} (${qualityLabel(data.quality)})`],
      ["Status", statusInfo.status],
    ]
      .map((item) => `<div class="status-chip"><div class="k">${escapeHtml(item[0])}</div><div class="v">${escapeHtml(item[1])}</div></div>`)
      .join("");
  }

  const insights = data.insights || [];
  const insightsEl = document.getElementById("insights");
  if (insightsEl) insightsEl.innerHTML = buildInsightBlocks(insights);

  const recommendationsEl = document.getElementById("recommendations");
  if (recommendationsEl) {
    const recs = data.recommendations || [];
    recommendationsEl.innerHTML = recs.length
      ? recs.map((x) => `<li>${escapeHtml(x)}</li>`).join("")
      : [
          "Reduce load during peak times.",
          "Check system stability and service health.",
          "Inspect logs for unusual patterns.",
        ].map((x) => `<li>${escapeHtml(x)}</li>`).join("");
  }

  drawGraph(
    (data.series && data.series.data_rate ? data.series.data_rate : []).map((x) => Number(x)),
    (data.series && data.series.time ? data.series.time : []),
    data.spikes || [],
    data.drops || [],
    data.anomalies || []
  );

  setupExport(data);
}

let comparisonState = {
  allReports: [],
  selected: [],
};

async function fetchAllReports() {
  try {
    const res = await fetch("/api/compare");
    const comparison = await res.json();
    const items = Array.isArray(comparison.items) ? comparison.items : [];
    comparisonState.allReports = items;
    return items;
  } catch {
    return [];
  }
}

function renderReportsList(reports) {
  const container = document.getElementById("reports-list");
  if (!container) return;

  comparisonState.allReports = reports;

  container.innerHTML = reports.length
    ? reports
        .map(
          (report, idx) => `
    <div class="report-item">
      <input type="checkbox" id="report-${idx}" data-index="${idx}" class="report-checkbox">
      <label for="report-${idx}">${escapeHtml(report.name)} (Domain: ${escapeHtml(report.domain || "generic")})</label>
    </div>
  `
        )
        .join("")
    : "<p class='muted'>No reports available. Upload datasets first.</p>";

  container.querySelectorAll(".report-checkbox").forEach((checkbox) => {
    checkbox.addEventListener("change", () => {
      handleReportSelection();
    });
  });
}

function handleReportSelection() {
  const checkboxes = document.querySelectorAll(".report-checkbox:checked");
  comparisonState.selected = Array.from(checkboxes).map((cb) => {
    const idx = Number(cb.getAttribute("data-index"));
    return comparisonState.allReports[idx];
  });

  const warning = document.getElementById("warning-container");
  if (comparisonState.selected.length > 3) {
    const checkboxes = document.querySelectorAll(".report-checkbox");
    checkboxes.forEach((cb) => (cb.checked = false));
    comparisonState.selected = [];
    if (warning) {
      warning.innerHTML = '<div class="warning-box">Max 3 reports allowed. Selection cleared.</div>';
    }
    document.getElementById("comparison-view-section").style.display = "none";
    document.getElementById("comparison-table-section").style.display = "none";
    document.getElementById("comparison-insight-section").style.display = "none";
    return;
  }

  if (warning) {
    warning.innerHTML = comparisonState.selected.length > 0 ? "" : '<div class="info-box">Select 1-3 reports to compare.</div>';
  }

  if (comparisonState.selected.length === 1) {
    renderSingleReportView();
    document.getElementById("comparison-view-section").style.display = "block";
    document.getElementById("comparison-table-section").style.display = "none";
    document.getElementById("comparison-insight-section").style.display = "none";
  } else if (comparisonState.selected.length > 1) {
    renderComparisonView();
    renderComparisonTable();
    renderComparisonInsight();
    document.getElementById("comparison-view-section").style.display = "block";
    document.getElementById("comparison-table-section").style.display = "block";
    document.getElementById("comparison-insight-section").style.display = "block";
  } else {
    document.getElementById("comparison-view-section").style.display = "none";
    document.getElementById("comparison-table-section").style.display = "none";
    document.getElementById("comparison-insight-section").style.display = "none";
  }
}

function renderSingleReportView() {
  const container = document.getElementById("comparison-columns");
  if (!container || comparisonState.selected.length !== 1) return;

  const report = comparisonState.selected[0];
  const result = report.result;

  container.style.gridTemplateColumns = "1fr";
  container.innerHTML = `
    <div class="comparison-column">
      <div class="column-header">${escapeHtml(report.name)}</div>
      <div class="column-meta">Domain: ${escapeHtml(report.domain || "generic")}</div>
      <div class="column-meta">Created: ${escapeHtml(new Date(report.created_at).toLocaleDateString())}</div>
      <div class="column-metric">Spikes: <strong>${Number(result.counts.spikes || 0)}</strong></div>
      <div class="column-metric">Drops: <strong>${Number(result.counts.drops || 0)}</strong></div>
      <div class="column-metric">Anomalies: <strong>${Number(result.counts.anomalies || 0)}</strong></div>
      <div class="column-metric">Quality: <strong>${Number(result.quality || 0)}</strong></div>
      <div class="column-metric">Risk: <strong>${escapeHtml(result.risk || "unknown")}</strong></div>
    </div>
  `;
}

function renderComparisonView() {
  const container = document.getElementById("comparison-columns");
  if (!container) return;

  const count = comparisonState.selected.length;
  const columns = count === 1 ? 1 : count === 2 ? 2 : 3;
  container.style.gridTemplateColumns = `repeat(${columns}, 1fr)`;

  container.innerHTML = comparisonState.selected
    .map(
      (report) => {
        const result = report.result;
        return `
    <div class="comparison-column">
      <div class="column-header">${escapeHtml(report.name)}</div>
      <div class="column-meta">Domain: ${escapeHtml(report.domain || "generic")}</div>
      <div class="column-metric">Spikes: <strong>${Number(result.counts.spikes || 0)}</strong></div>
      <div class="column-metric">Drops: <strong>${Number(result.counts.drops || 0)}</strong></div>
      <div class="column-metric">Anomalies: <strong>${Number(result.counts.anomalies || 0)}</strong></div>
      <div class="column-metric">Quality: <strong>${Number(result.quality || 0)}</strong></div>
      <div class="column-metric">Risk: <strong>${escapeHtml(result.risk || "unknown")}</strong></div>
    </div>
  `;
      }
    )
    .join("");
}

function renderComparisonTable() {
  const container = document.getElementById("comparison-table-container");
  if (!container || comparisonState.selected.length === 0) return;

  const metrics = ["Spikes", "Drops", "Anomalies", "Quality"];
  const values = metrics.map((metric) => {
    const vals = comparisonState.selected.map((report) => {
      const result = report.result;
      if (metric === "Spikes") return Number(result.counts.spikes || 0);
      if (metric === "Drops") return Number(result.counts.drops || 0);
      if (metric === "Anomalies") return Number(result.counts.anomalies || 0);
      if (metric === "Quality") return Number(result.quality || 0);
      return 0;
    });

    const highest = Math.max(...vals);
    const lowest = Math.min(...vals);

    return { metric, vals, highest, lowest };
  });

  const headers = ["Metric", ...comparisonState.selected.map((r) => escapeHtml(r.name))].join("</th><th>");
  const rows = values
    .map(
      (row) =>
        `<tr><td><strong>${row.metric}</strong></td>${row.vals
          .map((val) => {
            let cls = "";
            if (val === row.highest && row.highest !== row.lowest) cls = "cell-highlight-high";
            if (val === row.lowest && row.highest !== row.lowest) cls = "cell-highlight-low";
            return `<td class="${cls}">${escapeHtml(String(val))}</td>`;
          })
          .join("")}</tr>`
    )
    .join("");

  container.innerHTML = `<table class="comparison-table"><thead><tr><th>${headers}</th></tr></thead><tbody>${rows}</tbody></table>`;
}

function renderComparisonInsight() {
  const container = document.getElementById("comparison-insight");
  if (!container || comparisonState.selected.length === 0) return;

  const insights = [];

  const spikeCounts = comparisonState.selected.map((r) => Number(r.result.counts.spikes || 0));
  const maxSpikes = Math.max(...spikeCounts);
  const minSpikes = Math.min(...spikeCounts);
  const maxSpikeIdx = comparisonState.selected.findIndex((r) => Number(r.result.counts.spikes || 0) === maxSpikes);

  if (maxSpikes > minSpikes) {
    insights.push(
      `${escapeHtml(comparisonState.selected[maxSpikeIdx].name)} has highest spikes (${maxSpikes}).`
    );
  }

  const anomalyCounts = comparisonState.selected.map((r) => Number(r.result.counts.anomalies || 0));
  const maxAnomalies = Math.max(...anomalyCounts);
  const maxAnomalyIdx = comparisonState.selected.findIndex((r) => Number(r.result.counts.anomalies || 0) === maxAnomalies);

  if (maxAnomalies >= 5) {
    insights.push(
      `${escapeHtml(comparisonState.selected[maxAnomalyIdx].name)} has highest anomalies (${maxAnomalies}).`
    );
  }

  const qualityCounts = comparisonState.selected.map((r) => Number(r.result.quality || 0));
  const maxQuality = Math.max(...qualityCounts);
  const minQuality = Math.min(...qualityCounts);
  const maxQualityIdx = comparisonState.selected.findIndex((r) => Number(r.result.quality || 0) === maxQuality);

  if (maxQuality > minQuality) {
    insights.push(
      `${escapeHtml(comparisonState.selected[maxQualityIdx].name)} has best quality (${maxQuality}).`
    );
  }

  if (insights.length === 0) {
    insights.push("All reports show similar characteristics.");
  }

  container.textContent = insights.join(" ");
}

async function initComparison() {
  const emptyState = document.getElementById("empty-state");
  const comparisonContent = document.getElementById("comparison-content");
  const reportsList = document.getElementById("reports-list");

  if (!reportsList) return;

  const history = getReportHistory();

  if (history.length === 0) {
    if (emptyState) emptyState.style.display = "block";
    if (comparisonContent) comparisonContent.style.display = "none";
    reportsList.innerHTML = "<p class='muted'>No reports available. Upload datasets first.</p>";
    return;
  }

  if (emptyState) emptyState.style.display = "none";
  if (comparisonContent) comparisonContent.style.display = "block";

  renderReportsList(history);
}

function reset() {
  localStorage.removeItem("dfis_latest");
  localStorage.removeItem("dfis_report_meta");
  
  const emptyStates = document.querySelectorAll(".empty-state");
  const contents = document.querySelectorAll("#dashboard-content, #report-content, #comparison-content");
  
  emptyStates.forEach((el) => { el.style.display = "block"; });
  contents.forEach((el) => { el.style.display = "none"; });
  
  const graphs = document.querySelectorAll("#graph");
  graphs.forEach((svg) => { svg.innerHTML = ""; });
  
  window.location.href = "/dashboard.html";
}

document.addEventListener("DOMContentLoaded", () => {
  const domainSelect = document.getElementById("domain-select");

  if (!domainSelect) {
    console.error("domain-select not found");
  } else {
    domainSelect.addEventListener("change", (e) => {
      updateDomainUI(e.target.value);
      const validationFeedback = document.getElementById("validation-feedback");
      if (validationFeedback) validationFeedback.style.display = "none";
    });
  }

  setTimeout(() => {
    const select = document.getElementById("domain-select");
    if (select) updateDomainUI(select.value);
  }, 500);
});

async function boot() {
  const page = detectPage();
  if (page === "upload") return initUpload();
  if (page === "dashboard") return initDashboard();
  if (page === "report") return initReport();
  if (page === "comparison") return initComparison();
}

boot().catch((error) => {
  const panel = document.querySelector(".panel");
  if (panel) {
    panel.insertAdjacentHTML("beforeend", `<div class="status error">${escapeHtml(error.message || "Unexpected error")}</div>`);
  }
});
