// State management
const state = {
  currentStep: 1,
  jira: {
    host: "demo",
    email: "",
    api_token: "",
    connected: false
  },
  llm: {
    provider: "ollama",
    base_url: "http://localhost:11434",
    model: "llama3.2:3b",
    api_key: "",
    connected: false
  },
  templateType: "inbuilt",
  fetchedIssues: [],
  selectedIssueKeys: new Set(),
  generatedPlan: null
};

// Provider Defaults mapping
const PROVIDER_DEFAULTS = {
  ollama: {
    url: "http://localhost:11434",
    model: "llama3.2:3b",
    hint: "Local inference. Detected locally: llama3.2:3b, llama3.2:1b"
  },
  groq: {
    url: "https://api.groq.com/openai/v1",
    model: "llama-3.3-70b-versatile",
    hint: "Fast cloud inference via Groq Cloud API"
  },
  grok: {
    url: "https://api.x.ai/v1",
    model: "grok-2",
    hint: "xAI Grok API endpoint"
  },
  chatgpt: {
    url: "https://api.openai.com/v1",
    model: "gpt-4o-mini",
    hint: "OpenAI ChatGPT API endpoint"
  },
  claude: {
    url: "https://api.anthropic.com/v1",
    model: "claude-3-5-sonnet-20241022",
    hint: "Anthropic Claude API"
  }
};

document.addEventListener("DOMContentLoaded", () => {
  initEventListeners();
  // Automatically verify Ollama on load
  testLlmConnection(true);
});

function initEventListeners() {
  // Stepper tabs
  document.querySelectorAll(".step-tab").forEach(tab => {
    tab.addEventListener("click", () => {
      const step = parseInt(tab.dataset.step);
      goToStep(step);
    });
  });

  // LLM Provider select change
  document.getElementById("llmProvider").addEventListener("change", (e) => {
    const p = e.target.value;
    const defaults = PROVIDER_DEFAULTS[p];
    if (defaults) {
      document.getElementById("llmBaseUrl").value = defaults.url;
      document.getElementById("llmModel").value = defaults.model;
      document.getElementById("llmModelHint").textContent = defaults.hint;
    }
  });

  // Template toggle
  document.querySelectorAll('input[name="templateChoice"]').forEach(radio => {
    radio.addEventListener("change", (e) => {
      state.templateType = e.target.value;
      document.querySelectorAll(".template-option").forEach(opt => opt.classList.remove("active"));
      e.target.closest(".template-option").classList.add("active");
      
      const dropZone = document.getElementById("customDropZone");
      if (state.templateType === "custom") {
        dropZone.classList.remove("hidden");
      } else {
        dropZone.classList.add("hidden");
      }
    });
  });

  // Buttons
  document.getElementById("btnTestJira").addEventListener("click", testJiraConnection);
  document.getElementById("btnTestLlm").addEventListener("click", () => testLlmConnection(false));
  document.getElementById("btnFetchIssues").addEventListener("click", fetchJiraIssues);
  document.getElementById("btnGeneratePlan").addEventListener("click", generatePlan);

  // Plan viewer tabs
  document.querySelectorAll(".plan-tab").forEach(tab => {
    tab.addEventListener("click", () => {
      document.querySelectorAll(".plan-tab").forEach(t => t.classList.remove("active"));
      document.querySelectorAll(".plan-tab-pane").forEach(p => p.classList.remove("active"));
      tab.classList.add("active");
      const targetPane = document.getElementById(tab.dataset.tab);
      if (targetPane) targetPane.classList.add("active");
    });
  });
}

function goToStep(stepNumber) {
  state.currentStep = stepNumber;
  document.querySelectorAll(".step-tab").forEach(tab => {
    tab.classList.toggle("active", parseInt(tab.dataset.step) === stepNumber);
  });
  document.querySelectorAll(".step-section").forEach(sec => {
    sec.classList.remove("active");
  });
  const activeSec = document.getElementById(`step${stepNumber}`);
  if (activeSec) activeSec.classList.add("active");
  window.scrollTo({ top: 0, behavior: "smooth" });
}

function togglePassword(inputId) {
  const input = document.getElementById(inputId);
  input.type = input.type === "password" ? "text" : "password";
}

// 1. Test LLM Connection
async function testLlmConnection(silent = false) {
  const spinner = document.getElementById("llmSpinner");
  const feedback = document.getElementById("llmFeedback");
  const pill = document.getElementById("globalStatusPill");
  const pillText = document.getElementById("globalStatusText");
  const badge = document.getElementById("llmStatusBadge");

  if (!silent) {
    spinner.classList.remove("hidden");
    feedback.textContent = "Pinging LLM endpoint...";
    feedback.className = "test-feedback";
  }

  const payload = {
    provider: document.getElementById("llmProvider").value,
    base_url: document.getElementById("llmBaseUrl").value,
    model: document.getElementById("llmModel").value,
    api_key: document.getElementById("llmApiKey").value
  };

  try {
    const res = await fetch("/api/test-connection/llm", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    const data = await res.json();

    if (!silent) spinner.classList.add("hidden");

    if (data.status === "success") {
      state.llm = { ...payload, connected: true };
      badge.textContent = `${payload.provider.toUpperCase()} Online`;
      badge.className = "badge badge-success";
      pill.querySelector(".status-dot").className = "status-dot online";
      pillText.textContent = `${payload.provider}: ${payload.model}`;

      if (!silent) {
        feedback.textContent = `✓ ${data.message}`;
        feedback.className = "test-feedback success";
      }
    } else {
      state.llm.connected = false;
      badge.textContent = "Offline";
      badge.className = "badge badge-neutral";
      pill.querySelector(".status-dot").className = "status-dot error";
      pillText.textContent = "LLM Offline";

      if (!silent) {
        feedback.textContent = `✕ ${data.message}`;
        feedback.className = "test-feedback error";
      }
    }
  } catch (err) {
    if (!silent) {
      spinner.classList.add("hidden");
      feedback.textContent = `✕ Connection error: ${err.message}`;
      feedback.className = "test-feedback error";
    }
  }
}

// 2. Test Jira Connection
async function testJiraConnection() {
  const spinner = document.getElementById("jiraSpinner");
  const feedback = document.getElementById("jiraFeedback");
  const badge = document.getElementById("jiraStatusBadge");

  spinner.classList.remove("hidden");
  feedback.textContent = "Verifying Jira credentials...";
  feedback.className = "test-feedback";

  const payload = {
    host: document.getElementById("jiraUrl").value,
    email: document.getElementById("jiraEmail").value,
    api_token: document.getElementById("jiraToken").value
  };

  try {
    const res = await fetch("/api/test-connection/jira", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    const data = await res.json();
    spinner.classList.add("hidden");

    if (data.status === "success") {
      state.jira = { ...payload, connected: true };
      badge.textContent = `Connected (${data.user})`;
      badge.className = "badge badge-success";
      feedback.textContent = `✓ ${data.message}`;
      feedback.className = "test-feedback success";
    } else {
      state.jira.connected = false;
      badge.textContent = "Auth Failed";
      badge.className = "badge badge-neutral";
      feedback.textContent = `✕ ${data.message}`;
      feedback.className = "test-feedback error";
    }
  } catch (err) {
    spinner.classList.add("hidden");
    feedback.textContent = `✕ Network error: ${err.message}`;
    feedback.className = "test-feedback error";
  }
}

// 3. Fetch Jira Issues
async function fetchJiraIssues() {
  const spinner = document.getElementById("fetchSpinner");
  const feedback = document.getElementById("fetchFeedback");
  const btnProceed = document.getElementById("btnProceedToReview");

  spinner.classList.remove("hidden");
  feedback.textContent = "Querying requirements from Jira...";
  feedback.className = "test-feedback";

  const payload = {
    host: document.getElementById("jiraUrl").value || "demo",
    email: document.getElementById("jiraEmail").value,
    api_token: document.getElementById("jiraToken").value,
    project_key: document.getElementById("projectKey").value || "VWOAPP",
    issue_keys: document.getElementById("specificIssues").value,
    sprint: document.getElementById("sprintVersion").value
  };

  try {
    const res = await fetch("/api/fetch-issues", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    const data = await res.json();
    spinner.classList.add("hidden");

    if (data.status === "success") {
      state.fetchedIssues = data.issues || [];
      state.selectedIssueKeys = new Set(state.fetchedIssues.map(i => i.key));

      feedback.textContent = `✓ Found ${state.fetchedIssues.length} issues from Jira.`;
      feedback.className = "test-feedback success";

      btnProceed.disabled = false;
      btnProceed.textContent = `Proceed to Review (${state.fetchedIssues.length} Issues) →`;

      renderReviewIssues();
      goToStep(3);
    } else {
      feedback.textContent = `✕ Fetch error: ${data.message}`;
      feedback.className = "test-feedback error";
    }
  } catch (err) {
    spinner.classList.add("hidden");
    feedback.textContent = `✕ Network error: ${err.message}`;
    feedback.className = "test-feedback error";
  }
}

// Render Review Issues in Step 3
function renderReviewIssues() {
  const container = document.getElementById("issuesContainer");
  const badge = document.getElementById("issueCountBadge");
  badge.textContent = state.fetchedIssues.length;

  if (state.fetchedIssues.length === 0) {
    container.innerHTML = `<div class="empty-state"><p>No issues found. Please adjust your query in Step 2.</p></div>`;
    return;
  }

  container.innerHTML = state.fetchedIssues.map(issue => {
    const isChecked = state.selectedIssueKeys.has(issue.key);
    const acItems = (issue.acceptance_criteria || [])
      .map(ac => `<li>${ac}</li>`)
      .join("");

    return `
      <div class="issue-card">
        <div class="issue-card-top">
          <div class="issue-key-title">
            <input type="checkbox" ${isChecked ? "checked" : ""} onchange="toggleIssueSelection('${issue.key}', this.checked)">
            <span class="issue-key">${issue.key}</span>
            <span class="issue-summary">${issue.summary}</span>
          </div>
          <div>
            <span class="badge badge-primary">${issue.type || "Story"}</span>
            <span class="badge badge-neutral">${issue.priority || "Medium"}</span>
          </div>
        </div>
        <p class="issue-desc">${issue.description || "No description provided."}</p>
        ${acItems ? `
          <div class="ac-block">
            <h5>Acceptance Criteria:</h5>
            <ul>${acItems}</ul>
          </div>
        ` : ""}
      </div>
    `;
  }).join("");
}

function toggleIssueSelection(key, checked) {
  if (checked) {
    state.selectedIssueKeys.add(key);
  } else {
    state.selectedIssueKeys.delete(key);
  }
}

// 4. Generate Test Plan
async function generatePlan() {
  const spinner = document.getElementById("generateSpinner");
  const btn = document.getElementById("btnGeneratePlan");

  if (state.selectedIssueKeys.size === 0) {
    alert("Please select at least one Jira issue to test!");
    return;
  }

  spinner.classList.remove("hidden");
  btn.disabled = true;
  btn.innerHTML = `<span class="spinner"></span> AI is analyzing requirements & generating test plan...`;

  const selectedIssues = state.fetchedIssues.filter(i => state.selectedIssueKeys.has(i.key));
  const reviewNotes = document.getElementById("reviewContext").value;
  const initialContext = document.getElementById("additionalContext").value;
  const combinedContext = [initialContext, reviewNotes].filter(Boolean).join("\n\n");

  const payload = {
    provider: document.getElementById("llmProvider").value,
    config: {
      base_url: document.getElementById("llmBaseUrl").value,
      model: document.getElementById("llmModel").value,
      api_key: document.getElementById("llmApiKey").value
    },
    issues: selectedIssues,
    context: combinedContext,
    product_name: document.getElementById("productName").value || "VWO Platform",
    project_key: document.getElementById("projectKey").value || "VWOAPP",
    template_type: state.templateType
  };

  try {
    const res = await fetch("/api/generate-plan", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    const data = await res.json();

    btn.disabled = false;
    btn.innerHTML = `✨ Generate Test Plan`;

    if (data.status === "success") {
      state.generatedPlan = data.plan;
      renderPlanView(data.plan);
      goToStep(4);
    } else {
      alert(`Plan Generation Error: ${data.message}`);
    }
  } catch (err) {
    btn.disabled = false;
    btn.innerHTML = `✨ Generate Test Plan`;
    alert(`Failed to communicate with generator: ${err.message}`);
  }
}

// 5. Render Step 4 Plan View
function renderPlanView(plan) {
  document.getElementById("emptyPlanState").classList.add("hidden");
  document.getElementById("planContentContainer").classList.remove("hidden");

  const meta = plan.metadata || {};
  document.getElementById("planTitle").textContent = `Test Plan: ${meta.product_name || "Platform"}`;
  document.getElementById("planKeyTag").textContent = meta.project_key || "VWOAPP";
  document.getElementById("planModelTag").textContent = meta.llm_model || "AI Model";
  document.getElementById("planCasesCountTag").textContent = `${(plan.test_cases || []).length} Test Cases`;

  // Overview & Scope
  document.getElementById("planObjective").textContent = plan.objective || "No objective defined.";
  const scope = plan.scope || {};
  document.getElementById("planInclusions").innerHTML = (scope.inclusions || ["Core application flows"]).map(i => `<li>${i}</li>`).join("");
  document.getElementById("planExclusions").innerHTML = (scope.exclusions || ["Out-of-scope integrations"]).map(e => `<li>${e}</li>`).join("");

  // Test Cases Table
  renderTestCasesTable(plan.test_cases || []);

  // Strategy & Environments
  const strat = plan.test_strategy || {};
  document.getElementById("planStrategyText").textContent = `Testing Types: ${(strat.types || []).join(", ")}. Automation Strategy: ${strat.automation_approach || "Standard automated regression suite."}`;
  const envs = plan.test_environments || [];
  document.getElementById("planEnvironmentsList").innerHTML = envs.map(e => `<span class="env-badge">${e.category}: ${e.specification}</span>`).join("");

  // Entry & Exit
  document.getElementById("planEntryCriteria").innerHTML = (plan.entry_criteria || []).map(c => `<li>${c}</li>`).join("");
  document.getElementById("planExitCriteria").innerHTML = (plan.exit_criteria || []).map(c => `<li>${c}</li>`).join("");

  // Risks
  const risks = plan.risks_and_mitigations || [];
  document.getElementById("planRisksBody").innerHTML = risks.map(r => `
    <tr>
      <td>${r.risk}</td>
      <td><span class="badge badge-neutral">${r.impact || "Medium"}</span></td>
      <td>${r.mitigation}</td>
    </tr>
  `).join("");
}

function renderTestCasesTable(cases) {
  const tbody = document.getElementById("tcTableBody");
  tbody.innerHTML = cases.map(tc => `
    <tr>
      <td><strong>${tc.id}</strong></td>
      <td><span class="issue-key">${tc.jira_reference || "-"}</span></td>
      <td>${tc.title}</td>
      <td><span class="badge badge-primary">${tc.type || "Functional"}</span></td>
      <td><span class="badge badge-neutral">${tc.priority || "Medium"}</span></td>
      <td style="white-space: pre-line; font-size: 0.78rem;">${tc.steps}</td>
      <td style="font-size: 0.78rem;">${tc.expected_result}</td>
      <td><span class="badge badge-success">${tc.automation || "Yes"}</span></td>
    </tr>
  `).join("");
}

function filterTestCases() {
  const query = document.getElementById("tcSearch").value.toLowerCase();
  if (!state.generatedPlan) return;
  const filtered = (state.generatedPlan.test_cases || []).filter(tc => {
    return (
      (tc.title || "").toLowerCase().includes(query) ||
      (tc.jira_reference || "").toLowerCase().includes(query) ||
      (tc.type || "").toLowerCase().includes(query) ||
      (tc.id || "").toLowerCase().includes(query)
    );
  });
  renderTestCasesTable(filtered);
}

// 6. Export Plan
async function exportPlan(format) {
  if (!state.generatedPlan) return;
  try {
    const res = await fetch("/api/export", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        plan: state.generatedPlan,
        format: format,
        template_type: state.templateType
      })
    });
    const data = await res.json();
    if (data.status === "success" && data.download_url) {
      window.location.href = data.download_url;
    } else {
      alert(`Export error: ${data.message}`);
    }
  } catch (err) {
    alert(`Export failed: ${err.message}`);
  }
}

function copyMarkdown() {
  if (!state.generatedPlan) return;
  const plan = state.generatedPlan;
  let md = `# Test Plan: ${plan.metadata?.product_name || "System"}\n\n`;
  md += `## Objective\n${plan.objective}\n\n`;
  md += `## Test Cases\n\n`;
  md += `| ID | Title | Priority | Expected Result |\n|---|---|---|---|\n`;
  for (const tc of plan.test_cases || []) {
    md += `| ${tc.id} | ${tc.title} | ${tc.priority} | ${tc.expected_result} |\n`;
  }
  navigator.clipboard.writeText(md).then(() => {
    alert("Test Plan Markdown copied to clipboard!");
  });
}
