/**
 * OnCall Memory - Single-Page Dashboard Interactivity
 * Handles side-by-side analysis, feedback loop, Hindsight Reflect insights,
 * guided demo mode, and memory bank inspection.
 */

// Application State
const state = {
  samples: [],
  scenarios: [],
  currentStep: 1,
  activeFeedbackStatus: "SUCCESS",
  lastAnalysis: null,
  cachedMemories: []
};

// DOM Elements
const elements = {
  inputAlert: document.getElementById("inputAlert"),
  inputLogs: document.getElementById("inputLogs"),
  selectService: document.getElementById("selectService"),
  btnAnalyze: document.getElementById("btnAnalyze"),
  btnClear: document.getElementById("btnClear"),
  analysisStatus: document.getElementById("analysisStatus"),
  
  colWithoutMemory: document.getElementById("colWithoutMemory"),
  contentWithoutMemory: document.getElementById("contentWithoutMemory"),
  colWithMemory: document.getElementById("colWithMemory"),
  contentWithMemory: document.getElementById("contentWithMemory"),
  latencyWithout: document.getElementById("latencyWithout"),
  latencyWith: document.getElementById("latencyWith"),
  recalledCountBadge: document.getElementById("recalledCountBadge"),
  
  feedbackSection: document.getElementById("feedbackSection"),
  btnFeedbackSuccess: document.getElementById("btnFeedbackSuccess"),
  btnFeedbackFailed: document.getElementById("btnFeedbackFailed"),
  inputResolutionNotes: document.getElementById("inputResolutionNotes"),
  btnSubmitFeedback: document.getElementById("btnSubmitFeedback"),
  
  memoryCountDisplay: document.getElementById("memoryCountDisplay"),
  bankIdDisplay: document.getElementById("bankIdDisplay"),
  
  btnSystemicInsights: document.getElementById("btnSystemicInsights"),
  modalInsights: document.getElementById("modalInsights"),
  insightsContent: document.getElementById("insightsContent"),
  btnCloseInsights: document.getElementById("btnCloseInsights"),
  btnCloseInsightsFooter: document.getElementById("btnCloseInsightsFooter"),
  btnExportInsights: document.getElementById("btnExportInsights"),
  
  btnExploreBank: document.getElementById("btnExploreBank"),
  modalBankExplorer: document.getElementById("modalBankExplorer"),
  memoriesTableBody: document.getElementById("memoriesTableBody"),
  filterBankInput: document.getElementById("filterBankInput"),
  btnCloseExplorer: document.getElementById("btnCloseExplorer"),
  btnCloseExplorerFooter: document.getElementById("btnCloseExplorerFooter"),
  explorerTotalMemories: document.getElementById("explorerTotalMemories"),
  
  btnToggleDemoMode: document.getElementById("btnToggleDemoMode"),
  demoBanner: document.getElementById("demoBanner"),
  demoStepDescription: document.getElementById("demoStepDescription"),
  btnRunDemoStep: document.getElementById("btnRunDemoStep"),
  btnNextDemoStep: document.getElementById("btnNextDemoStep"),
  btnCloseDemo: document.getElementById("btnCloseDemo"),
  
  toastContainer: document.getElementById("toastContainer")
};

// Initialize Application
document.addEventListener("DOMContentLoaded", async () => {
  await loadMetadata();
  await refreshMemoryStats();
  setupEventListeners();
});

// Load Samples and Scenarios from API
async function loadMetadata() {
  try {
    const res = await fetch("/api/samples");
    const data = await res.json();
    state.samples = data.samples || [];
    state.scenarios = data.scenarios || [];
  } catch (err) {
    console.error("Failed to load sample incidents:", err);
  }
}

// Refresh Live Memory Stats
async function refreshMemoryStats() {
  try {
    const res = await fetch("/api/memories/stats");
    const data = await res.json();
    if (elements.memoryCountDisplay) {
      elements.memoryCountDisplay.textContent = `${data.total_memories} In Bank`;
    }
    if (elements.bankIdDisplay) {
      elements.bankIdDisplay.textContent = data.bank_id;
    }
    if (elements.explorerTotalMemories) {
      elements.explorerTotalMemories.textContent = data.total_memories;
    }
  } catch (err) {
    console.error("Failed to refresh memory stats:", err);
  }
}

// Setup Event Listeners
function setupEventListeners() {
  // 1-Click Sample Pills
  document.querySelectorAll(".pill-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      const sampleId = btn.getAttribute("data-sample");
      const sample = state.samples.find(s => s.id === sampleId);
      if (sample) {
        populateIncidentForm(sample.alert, sample.logs, sample.service);
        showToast(`Loaded scenario: ${sample.name}`);
      }
    });
  });

  // Analyze Button
  elements.btnAnalyze.addEventListener("click", runAnalysis);

  // Clear Button
  elements.btnClear.addEventListener("click", () => {
    elements.inputAlert.value = "";
    elements.inputLogs.value = "";
    elements.feedbackSection.style.display = "none";
  });

  // Feedback Toggle Buttons
  elements.btnFeedbackSuccess.addEventListener("click", () => setFeedbackStatus("SUCCESS"));
  elements.btnFeedbackFailed.addEventListener("click", () => setFeedbackStatus("FAILED"));

  // Submit Feedback
  elements.btnSubmitFeedback.addEventListener("click", submitFeedback);

  // Insights Modal
  elements.btnSystemicInsights.addEventListener("click", openInsightsModal);
  elements.btnCloseInsights.addEventListener("click", () => elements.modalInsights.style.display = "none");
  elements.btnCloseInsightsFooter.addEventListener("click", () => elements.modalInsights.style.display = "none");
  elements.btnExportInsights.addEventListener("click", () => {
    const text = elements.insightsContent.innerText;
    navigator.clipboard.writeText(text);
    showToast("Systemic Audit copied to clipboard!");
  });

  // Memory Explorer Modal
  elements.btnExploreBank.addEventListener("click", openBankExplorer);
  elements.btnCloseExplorer.addEventListener("click", () => elements.modalBankExplorer.style.display = "none");
  elements.btnCloseExplorerFooter.addEventListener("click", () => elements.modalBankExplorer.style.display = "none");
  elements.filterBankInput.addEventListener("input", filterExplorerTable);

  // Demo Mode
  elements.btnToggleDemoMode.addEventListener("click", toggleDemoMode);
  elements.btnCloseDemo.addEventListener("click", () => elements.demoBanner.style.display = "none");
  elements.btnRunDemoStep.addEventListener("click", runCurrentDemoStep);
  elements.btnNextDemoStep.addEventListener("click", advanceDemoStep);
}

// Populate Form Helper
function populateIncidentForm(alert, logs, service) {
  elements.inputAlert.value = alert || "";
  elements.inputLogs.value = logs || "";
  if (service) {
    elements.selectService.value = service;
  }
}

// Run Side-by-Side Analysis
async function runAnalysis() {
  const alertText = elements.inputAlert.value.trim();
  const logsText = elements.inputLogs.value.trim();
  const service = elements.selectService.value;

  if (!alertText && !logsText) {
    showToast("Please enter an alert title or error logs", "error");
    return;
  }

  // Show loading indicator
  elements.btnAnalyze.disabled = true;
  elements.analysisStatus.style.display = "flex";
  elements.contentWithoutMemory.innerHTML = renderSkeleton();
  elements.contentWithMemory.innerHTML = renderSkeleton();
  elements.feedbackSection.style.display = "none";

  try {
    const res = await fetch("/api/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        alert: alertText || "Production Incident Alert",
        logs: logsText || "No stack trace provided",
        service: service
      })
    });

    const data = await res.json();
    state.lastAnalysis = data;

    // Render Left (Without Memory)
    renderWithoutMemory(data.without_memory);

    // Render Right (With Hindsight Memory)
    renderWithMemory(data.with_memory);

    // Show Feedback Form
    elements.feedbackSection.style.display = "block";
    elements.inputResolutionNotes.value = "";
    setFeedbackStatus("SUCCESS");

    // Scroll to results
    document.getElementById("comparisonGrid").scrollIntoView({ behavior: "smooth", block: "nearest" });

  } catch (err) {
    console.error("Analysis request failed:", err);
    showToast("Analysis request failed: " + err.message, "error");
  } finally {
    elements.btnAnalyze.disabled = false;
    elements.analysisStatus.style.display = "none";
  }
}

// Render Left Column (Without Memory)
function renderWithoutMemory(diag) {
  elements.latencyWithout.textContent = `Latency: ${diag.latency_ms || 420}ms`;

  const confNum = parseInt(diag.confidence) || 60;
  
  let html = `
    <div class="diag-section">
      <div class="diag-title">Generic Root Cause Diagnosis</div>
      <div class="diag-box">${escapeHtml(diag.root_cause)}</div>
      <div class="confidence-row">
        <span class="confidence-score med">${escapeHtml(diag.confidence)}</span>
        <div class="confidence-bar">
          <div class="confidence-fill med" style="width: ${confNum}%;"></div>
        </div>
      </div>
    </div>

    <div class="diag-section">
      <div class="diag-title">Standard Troubleshooting Steps</div>
      <ul class="steps-list">
        ${diag.remediation_steps.map(step => `<li>${escapeHtml(step)}</li>`).join("")}
      </ul>
    </div>

    <div class="diag-section">
      <div class="diag-title">Generic Notes</div>
      <div class="diag-box" style="font-size: 0.8rem; color: var(--text-dim);">
        ${escapeHtml(diag.summary || "No company memory available. Suggested textbook remediation actions.")}
      </div>
    </div>
  `;

  elements.contentWithoutMemory.innerHTML = html;
}

// Render Right Column (With Hindsight Memory)
function renderWithMemory(diag) {
  elements.latencyWith.textContent = `Latency: ${diag.latency_ms || 380}ms`;
  
  const count = diag.recalled_count || (diag.citations ? diag.citations.length : 3);
  elements.recalledCountBadge.innerHTML = `<span class="pulse-dot"></span> Recalled from ${count} past incidents`;

  const confNum = parseInt(diag.confidence) || 95;

  let citationsHtml = "";
  if (diag.citations && diag.citations.length > 0) {
    citationsHtml = `
      <div class="citations-group">
        <div class="diag-title">Corroborated Past Post-Mortems (${diag.citations.length})</div>
        ${diag.citations.map(c => `
          <div class="citation-card ${c.outcome === 'FAILED' ? 'failed-outcome' : ''}">
            <div class="citation-header">
              <span class="citation-id">${escapeHtml(c.id)}</span>
              <span class="outcome-badge ${c.outcome === 'SUCCESS' ? 'success' : 'failed'}">
                ${c.outcome === 'SUCCESS' ? '✓ Fix Worked' : '✗ Failed Attempt'}
              </span>
            </div>
            <div class="citation-title">${escapeHtml(c.title)}</div>
            <div class="citation-meta">
              Resolved by <strong>${escapeHtml(c.engineer)}</strong> &bull; ${escapeHtml(c.date)}
            </div>
            ${c.failed_reason ? `<div style="font-size: 0.76rem; color: #fda4af; margin-top: 4px;">⚠️ ${escapeHtml(c.failed_reason)}</div>` : ''}
          </div>
        `).join("")}
      </div>
    `;
  }

  let warningHtml = "";
  if (diag.warning_avoid) {
    warningHtml = `
      <div class="trap-warning-box">
        <div class="trap-title">⚠️ Historical Trap to Avoid</div>
        <div class="trap-desc">${escapeHtml(diag.warning_avoid)}</div>
      </div>
    `;
  }

  let rawMemoriesHtml = "";
  if (diag.raw_memories && diag.raw_memories.length > 0) {
    rawMemoriesHtml = `
      <div class="raw-memories-accordion">
        <button class="accordion-toggle" onclick="toggleRawMemories()">
          <span>🔍</span> Inspect Exact Recalled Memory Chunks (${diag.raw_memories.length})
        </button>
        <div class="raw-memories-content" id="rawMemoriesPanel" style="display: none;">
          ${diag.raw_memories.map((m, i) => `[Fact #${i+1}]\n${escapeHtml(m)}\n`).join("\n")}
        </div>
      </div>
    `;
  }

  let html = `
    <div class="diag-section">
      <div class="diag-title">Pinpointed Root Cause (Hindsight Memory)</div>
      <div class="diag-box highlight">${escapeHtml(diag.root_cause)}</div>
      <div class="confidence-row">
        <span class="confidence-score high">${escapeHtml(diag.confidence)}</span>
        <div class="confidence-bar">
          <div class="confidence-fill high" style="width: ${confNum}%;"></div>
        </div>
      </div>
    </div>

    <div class="diag-section">
      <div class="diag-title">Precision Remediation Runbook</div>
      <ul class="steps-list precision">
        ${diag.remediation_steps.map(step => `<li>${formatStepText(step)}</li>`).join("")}
      </ul>
    </div>

    ${warningHtml}
    ${citationsHtml}
    ${rawMemoriesHtml}
  `;

  elements.contentWithMemory.innerHTML = html;
}

// Toggle Raw Memories Accordion
function toggleRawMemories() {
  const panel = document.getElementById("rawMemoriesPanel");
  if (panel) {
    panel.style.display = panel.style.display === "none" ? "block" : "none";
  }
}

// Step formatting to highlight SQL, commands, or codes
function formatStepText(text) {
  const escaped = escapeHtml(text);
  // Highlight inline sql or backticks
  return escaped.replace(/`([^`]+)`/g, '<span class="code-snippet">$1</span>')
                .replace(/(SELECT [^;]+;)/gi, '<span class="code-snippet">$1</span>');
}

// Feedback Status Toggle
function setFeedbackStatus(status) {
  state.activeFeedbackStatus = status;
  if (status === "SUCCESS") {
    elements.btnFeedbackSuccess.className = "feedback-toggle-btn active-success";
    elements.btnFeedbackFailed.className = "feedback-toggle-btn";
    elements.inputResolutionNotes.placeholder = "e.g. Cleared idle connection handles with pg_terminate_backend and applied connection pool patch.";
  } else {
    elements.btnFeedbackSuccess.className = "feedback-toggle-btn";
    elements.btnFeedbackFailed.className = "feedback-toggle-btn active-failed";
    elements.inputResolutionNotes.placeholder = "e.g. Hard DB reboot crashed the replica because app pods flooded back with a thundering herd.";
  }
}

// Submit Feedback
async function submitFeedback() {
  const alertText = elements.inputAlert.value.trim();
  const logsText = elements.inputLogs.value.trim();
  const service = elements.selectService.value;
  const notes = elements.inputResolutionNotes.value.trim();

  if (!notes) {
    showToast("Please provide details on what actually happened", "error");
    return;
  }

  elements.btnSubmitFeedback.disabled = true;
  try {
    const res = await fetch("/api/feedback", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        alert: alertText || "Live incident feedback",
        logs: logsText || "",
        service: service,
        fix_status: state.activeFeedbackStatus,
        solution_notes: notes,
        suggested_root_cause: state.lastAnalysis?.with_memory?.root_cause || ""
      })
    });

    const data = await res.json();
    showToast(`Memory updated! Retained incident ${data.incident_id} (${data.fix_status})`);
    
    await refreshMemoryStats();
    elements.inputResolutionNotes.value = "";
  } catch (err) {
    showToast("Failed to retain memory: " + err.message, "error");
  } finally {
    elements.btnSubmitFeedback.disabled = false;
  }
}

// Systemic Insights Modal (Reflect)
async function openInsightsModal() {
  elements.modalInsights.style.display = "flex";
  elements.insightsContent.innerHTML = `
    <div class="loading-container">
      <div class="spinner"></div>
      <p>Running Hindsight Reflect with high exploration budget across all retained production memories...</p>
    </div>
  `;

  try {
    const res = await fetch("/api/insights", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        query: "What patterns keep causing our incidents and what should we fix permanently?"
      })
    });
    const data = await res.json();
    renderInsightsMarkdown(data.reflection || "No reflection generated.");
  } catch (err) {
    elements.insightsContent.innerHTML = `<div style="color: var(--rose); padding: 1rem;">Failed to fetch insights: ${err.message}</div>`;
  }
}

function renderInsightsMarkdown(md) {
  // Simple markdown renderer for headers, bold, bullets
  let html = md
    .replace(/^### (.*$)/gim, '<h3>$1</h3>')
    .replace(/^## (.*$)/gim, '<h2>$1</h2>')
    .replace(/\*\*(.*?)\*\*/gim, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/gim, '<em>$1</em>')
    .replace(/^- (.*$)/gim, '<li>$1</li>')
    .replace(/\n\n/gim, '<br><br>');
    
  elements.insightsContent.innerHTML = `<div class="insights-markdown">${html}</div>`;
}

// Bank Explorer Modal
async function openBankExplorer() {
  elements.modalBankExplorer.style.display = "flex";
  elements.memoriesTableBody.innerHTML = `<tr><td colspan="6" style="text-align:center; padding: 2rem;">Loading memories from Hindsight bank...</td></tr>`;

  try {
    const res = await fetch("/api/memories/list?limit=50");
    const data = await res.json();
    state.cachedMemories = data.items || [];
    renderExplorerTable(state.cachedMemories);
  } catch (err) {
    elements.memoriesTableBody.innerHTML = `<tr><td colspan="6" style="color: var(--rose); text-align:center;">Failed to load memories</td></tr>`;
  }
}

function renderExplorerTable(items) {
  if (!items || items.length === 0) {
    elements.memoriesTableBody.innerHTML = `<tr><td colspan="6" style="text-align:center;">No memories found.</td></tr>`;
    return;
  }

  elements.memoriesTableBody.innerHTML = items.map(m => `
    <tr>
      <td class="inc-id">${escapeHtml(m.id)}</td>
      <td><span class="code-snippet">${escapeHtml(m.service)}</span></td>
      <td><strong>${escapeHtml(m.title)}</strong></td>
      <td>${escapeHtml(m.who_fixed_it)}</td>
      <td>${escapeHtml(m.date || '-')}</td>
      <td>
        <span class="outcome-badge ${m.fix_status === 'SUCCESS' ? 'success' : 'failed'}">
          ${m.fix_status === 'SUCCESS' ? 'SUCCESS' : 'FAILED'}
        </span>
      </td>
    </tr>
  `).join("");
}

function filterExplorerTable() {
  const query = elements.filterBankInput.value.toLowerCase();
  const filtered = state.cachedMemories.filter(m => 
    (m.id && m.id.toLowerCase().includes(query)) ||
    (m.service && m.service.toLowerCase().includes(query)) ||
    (m.title && m.title.toLowerCase().includes(query)) ||
    (m.who_fixed_it && m.who_fixed_it.toLowerCase().includes(query))
  );
  renderExplorerTable(filtered);
}

// Demo Mode Wizard
function toggleDemoMode() {
  const isVisible = elements.demoBanner.style.display !== "none";
  elements.demoBanner.style.display = isVisible ? "none" : "block";
  if (!isVisible) {
    loadDemoStep(1);
  }
}

function loadDemoStep(stepNum) {
  state.currentStep = stepNum;
  document.querySelectorAll(".demo-step").forEach((el, idx) => {
    el.classList.toggle("active", idx + 1 === stepNum);
  });

  const scenario = state.scenarios.find(s => s.step === stepNum);
  if (scenario) {
    elements.demoStepDescription.innerHTML = `<strong>Step ${scenario.step}: ${escapeHtml(scenario.title)}</strong><br>${escapeHtml(scenario.description)}`;
    populateIncidentForm(scenario.incident.alert, scenario.incident.logs, scenario.incident.service);
  }
}

async function runCurrentDemoStep() {
  loadDemoStep(state.currentStep);
  await runAnalysis();
}

function advanceDemoStep() {
  let next = state.currentStep + 1;
  if (next > 3) next = 1;
  loadDemoStep(next);
  runAnalysis();
}

// Toast Notifications
function showToast(message, type = "success") {
  const toast = document.createElement("div");
  toast.className = `toast ${type === "error" ? "toast-error" : ""}`;
  toast.innerHTML = `<span>${type === "error" ? "❌" : "✨"}</span> <span>${escapeHtml(message)}</span>`;
  elements.toastContainer.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = "0";
    toast.style.transform = "translateY(10px)";
    toast.style.transition = "all 0.3s ease";
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}

// Skeleton Loader Helper
function renderSkeleton() {
  return `
    <div style="padding: 1.5rem; display: flex; flex-direction: column; gap: 1rem; opacity: 0.5;">
      <div style="height: 18px; width: 40%; background: var(--bg-card-alt); border-radius: 4px;"></div>
      <div style="height: 50px; width: 100%; background: var(--bg-card-alt); border-radius: 6px;"></div>
      <div style="height: 18px; width: 60%; background: var(--bg-card-alt); border-radius: 4px;"></div>
      <div style="height: 80px; width: 100%; background: var(--bg-card-alt); border-radius: 6px;"></div>
    </div>
  `;
}

function escapeHtml(text) {
  if (!text) return "";
  return String(text)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}
