// State management
const state = {
  currentStep: 1,
  reqMode: "direct",
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
    model: "claude-sonnet-5",
    hint: "Anthropic Claude API. Alternatives: claude-opus-5, claude-haiku-4-5-20251001"
  }
};

document.addEventListener("DOMContentLoaded", () => {
  initEventListeners();
  // Only auto-verify when we actually have what the provider needs: a key for cloud
  // providers, nothing for local Ollama. Otherwise a pointless "Offline" badge shows
  // up before the user has had a chance to enter credentials.
  const provider = document.getElementById("llmProvider").value;
  const hasKey = Boolean(document.getElementById("llmApiKey").value.trim());
  if (provider === "ollama" || hasKey) {
    testLlmConnection(true);
  } else {
    document.getElementById("llmFeedback").textContent =
      "Enter your API key for this provider, then click Test Connection.";
  }
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
  document.getElementById("btnImprovePlan").addEventListener("click", () => refinePlan("improve"));
  document.getElementById("btnRegeneratePlan").addEventListener("click", () => refinePlan("regenerate"));

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

// --- Requirement Mode Switcher (Direct Story vs Jira) ---
function switchRequirementMode(mode) {
  state.reqMode = mode;
  const btnDirect = document.getElementById("btnModeDirect");
  const btnJira = document.getElementById("btnModeJira");
  const cardDirect = document.getElementById("cardDirectStory");
  const cardJira = document.getElementById("cardJiraFetch");

  if (mode === "direct") {
    btnDirect.classList.add("active");
    btnJira.classList.remove("active");
    cardDirect.classList.remove("hidden");
    cardJira.classList.add("hidden");
  } else {
    btnDirect.classList.remove("active");
    btnJira.classList.add("active");
    cardDirect.classList.add("hidden");
    cardJira.classList.remove("hidden");
  }
}

// Pre-fill realistic sample story
function loadSampleStory() {
  document.getElementById("directProductName").value = "XSM";
  document.getElementById("directStoryTitle").value = "Change Management - Test Task scheduling within the Testing Window";
  document.getElementById("directStoryText").value =
    "As a Change Manager, I want Test Task planned dates to be constrained to the Testing Window defined on the Change request, so that test scheduling cannot drift outside the approved window.";

  document.getElementById("directAcceptanceCriteria").value =
    "1. Enabling 'Testing Required' on a Change reveals the Testing Start Date and Testing End Date fields.\n" +
    "2. Default Test Tasks inherit Planned Start and Planned End dates from the Change Testing Window.\n" +
    "3. Saving a Test Task with dates outside the Testing Window is blocked with a validation error.\n" +
    "4. Testing End Date cannot be earlier than Testing Start Date.\n" +
    "5. Editing the Testing Window on an approved Change requires re-approval.\n" +
    "6. The audit trail records every date change with actor, timestamp, and previous value.\n" +
    "7. Test Tasks cannot be closed while the parent Change is still in Scheduled status.";

  document.getElementById("directAdditionalNotes").value =
    "Environment under test: https://xsmtest.dryice-aws.com/\n" +
    "Focus on boundary conditions at the window start and end dates, timezone handling, and negative validation when dates fall outside the Testing Window.";

  const feedback = document.getElementById("directFeedback");
  feedback.textContent = "✓ Sample story loaded! You can now edit it or click 'Generate Test Plan Now'.";
  feedback.className = "test-feedback success";
}

// Convert direct input into a standardized requirement issue
function useDirectStory(generateImmediately = false) {
  const prodName = document.getElementById("directProductName").value.trim() || "Web Application";
  const title = document.getElementById("directStoryTitle").value.trim();
  const storyText = document.getElementById("directStoryText").value.trim();
  const criteriaText = document.getElementById("directAcceptanceCriteria").value.trim();
  const extraNotes = document.getElementById("directAdditionalNotes").value.trim();
  const feedback = document.getElementById("directFeedback");

  if (!title) {
    feedback.textContent = "✕ Please provide a Story Title or Feature Name.";
    feedback.className = "test-feedback error";
    document.getElementById("directStoryTitle").focus();
    return;
  }

  if (!criteriaText) {
    feedback.textContent = "✕ Please provide at least one Acceptance Criterion or rule.";
    feedback.className = "test-feedback error";
    document.getElementById("directAcceptanceCriteria").focus();
    return;
  }

  // Parse acceptance criteria into list
  const criteriaList = criteriaText
    .split("\n")
    .map(line => line.trim())
    .filter(line => line.length > 0)
    .map(line => line.replace(/^(\d+[\.\)]|\-|\*)\s*/, ""));

  const directIssue = {
    key: "STORY-01",
    summary: title,
    description: storyText || title,
    acceptance_criteria: criteriaList,
    type: "User Story",
    priority: "High"
  };

  state.fetchedIssues = [directIssue];
  state.selectedIssueKeys = new Set(["STORY-01"]);

  if (extraNotes) {
    const existingReviewNotes = document.getElementById("reviewContext").value;
    if (!existingReviewNotes.includes(extraNotes)) {
      document.getElementById("reviewContext").value = existingReviewNotes 
        ? `${existingReviewNotes}\n${extraNotes}` 
        : extraNotes;
    }
  }

  feedback.textContent = `✓ Story packaged (${criteriaList.length} criteria). Ready for test planning.`;
  feedback.className = "test-feedback success";

  renderReviewIssues();

  if (generateImmediately) {
    goToStep(4);
    generatePlan();
  } else {
    goToStep(3);
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
    project_key: document.getElementById("projectKey").value || "XSM",
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
      // Every downstream step keys off issue.key. A Jira issue that arrives
      // without one (permission-filtered field, unusual deployment) would
      // otherwise land in fetchedIssues but never match a selected key, so
      // the plan would silently generate from zero issues.
      state.fetchedIssues = (data.issues || []).map((issue, idx) => ({
        ...issue,
        key: issue.key || `ISSUE-${idx + 1}`
      }));
      state.selectedIssueKeys = new Set(state.fetchedIssues.map(i => i.key));
      console.info(
        "[fetchJiraIssues] %d issue(s), keys:", state.fetchedIssues.length,
        [...state.selectedIssueKeys]
      );

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

  // Distinguish "nothing fetched" from "fetched but nothing ticked" - the old
  // message sent the user back to Step 2 even when the issues were sitting
  // right there on Step 3 with their checkboxes cleared.
  if (state.fetchedIssues.length === 0) {
    alert("No requirements loaded yet.\n\nGo to Step 2 and either write a story directly or fetch issues from Jira.");
    goToStep(2);
    return;
  }
  if (state.selectedIssueKeys.size === 0) {
    alert(`${state.fetchedIssues.length} issue(s) are loaded but none are selected.\n\nTick at least one issue checkbox in the list above, then click Generate again.`);
    return;
  }

  spinner.classList.remove("hidden");
  btn.disabled = true;
  btn.innerHTML = `<span class="spinner"></span> AI is analyzing requirements & generating test plan...`;

  const selectedIssues = state.fetchedIssues.filter(i => state.selectedIssueKeys.has(i.key));
  const reviewNotes = document.getElementById("reviewContext").value;

  // Guard against a key mismatch between the fetched list and the selection
  // set - without this the request goes out with an empty issues array and
  // the model invents a plan with nothing to base it on.
  if (selectedIssues.length === 0) {
    console.error(
      "[generatePlan] key mismatch. fetched:", state.fetchedIssues.map(i => i.key),
      "selected:", [...state.selectedIssueKeys]
    );
    // The button was already put into its loading state above, so restore it
    // before bailing out - otherwise it stays disabled and looks hung.
    spinner.classList.add("hidden");
    btn.disabled = false;
    btn.innerHTML = `✨ Generate Test Plan`;
    alert("Could not match the selected issues to the fetched list.\n\nPlease re-fetch the issues in Step 2 and try again.");
    return;
  }
  
  await runPlanGeneration({
    selectedIssues,
    extraContext: reviewNotes,
    button: btn,
    spinner,
    idleLabel: `✨ Generate Test Plan`
  });
}

// 4b. Refine the plan already on screen.
//     mode "improve"    -> send the current plan back so the model revises it
//     mode "regenerate" -> discard it and generate fresh from the requirements
async function refinePlan(mode) {
  const btnImprove = document.getElementById("btnImprovePlan");
  const btnRegen = document.getElementById("btnRegeneratePlan");
  const spinner = document.getElementById("refineSpinner");
  const feedback = document.getElementById("refineFeedback");
  const refineNotes = document.getElementById("refineContext").value.trim();

  if (mode === "improve" && !state.generatedPlan) {
    alert("There is no plan on screen to improve yet. Generate one first.");
    return;
  }
  if (mode === "improve" && !refineNotes) {
    feedback.textContent = "✕ Describe what to improve before running a refinement.";
    feedback.className = "test-feedback error";
    document.getElementById("refineContext").focus();
    return;
  }
  if (mode === "regenerate" &&
      !confirm("Regenerate from scratch?\n\nThe current plan will be replaced.")) {
    return;
  }

  const selectedIssues = state.fetchedIssues.filter(i => state.selectedIssueKeys.has(i.key));
  if (selectedIssues.length === 0) {
    alert("The original requirements are no longer loaded.\n\nGo back to Step 2 and load them again.");
    goToStep(2);
    return;
  }

  const reviewNotes = document.getElementById("reviewContext")?.value || "";
  // Both buttons drive the same request, so disable the pair for the duration.
  btnRegen.disabled = true;

  const ok = await runPlanGeneration({
    selectedIssues,
    extraContext: [reviewNotes, refineNotes].filter(Boolean).join("\n\n"),
    existingPlan: mode === "improve" ? state.generatedPlan : null,
    button: btnImprove,
    spinner,
    idleLabel: `✨ Improve This Plan`,
    verb: mode === "improve" ? "Improving" : "Regenerating"
  });

  btnRegen.disabled = false;
  if (ok) {
    feedback.textContent = mode === "improve"
      ? "✓ Plan improved. Review the updated test cases above."
      : "✓ Plan regenerated from the original requirements.";
    feedback.className = "test-feedback success";
    document.getElementById("refineContext").value = "";
  }
}

// Shared request path for every kind of plan run (new, improve, regenerate).
// Returns true on success so callers can report their own outcome.
async function runPlanGeneration({ selectedIssues, extraContext, existingPlan = null,
                                   button, spinner, idleLabel, verb = "Generating" }) {
  const isDirect = state.reqMode === "direct";
  const prodName = (isDirect
    ? document.getElementById("directProductName")?.value
    : document.getElementById("productName")?.value) || "XSM";
  const projKey = (isDirect
    ? (document.getElementById("directStoryTitle")?.value?.slice(0, 8)?.replace(/\s+/g, "_") || "XSM")
    : document.getElementById("projectKey")?.value) || "XSM";
  const initialContext = (isDirect
    ? document.getElementById("directAdditionalNotes")?.value
    : document.getElementById("additionalContext")?.value) || "";
  const combinedContext = [initialContext, extraContext].filter(Boolean).join("\n\n");

  const payload = {
    provider: document.getElementById("llmProvider").value,
    config: {
      base_url: document.getElementById("llmBaseUrl").value,
      model: document.getElementById("llmModel").value,
      api_key: document.getElementById("llmApiKey").value
    },
    issues: selectedIssues,
    context: combinedContext,
    product_name: prodName,
    project_key: projKey,
    template_type: state.templateType
  };
  if (existingPlan) payload.existing_plan = existingPlan;

  if (spinner) spinner.classList.remove("hidden");
  button.disabled = true;

  // A local model can take minutes. Without a running clock a static spinner
  // is indistinguishable from a hung page.
  const startedAt = Date.now();
  const isLocalOllama = payload.provider === "ollama" && !payload.config.model.endsWith("-cloud");
  const ticker = setInterval(() => {
    const secs = Math.round((Date.now() - startedAt) / 1000);
    button.innerHTML =
      `<span class="spinner"></span> ${verb}... ${secs}s` +
      (isLocalOllama ? ` (local model, may take minutes)` : ``);
  }, 1000);

  const reset = () => {
    clearInterval(ticker);
    if (spinner) spinner.classList.add("hidden");
    button.disabled = false;
    button.innerHTML = idleLabel;
  };

  try {
    const res = await fetch("/api/generate-plan", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    const data = await res.json();
    reset();

    if (data.status === "success") {
      state.generatedPlan = data.plan;
      renderPlanView(data.plan);
      goToStep(4);
      return true;
    }
    // detail/log_file are added by the backend so a failure points at the
    // log rather than leaving the user guessing.
    const extra = data.log_file ? `\n\nFull traceback: ${data.log_file}` : "";
    alert(`Plan Generation Error: ${data.message}${extra}`);
    return false;
  } catch (err) {
    reset();
    alert(`Failed to communicate with generator: ${err.message}`);
    return false;
  }
}

// 5. Render Step 4 Plan View
function renderPlanView(plan) {
  document.getElementById("emptyPlanState").classList.add("hidden");
  document.getElementById("planContentContainer").classList.remove("hidden");

  const meta = plan.metadata || {};
  document.getElementById("planTitle").textContent = `Test Plan: ${meta.product_name || "Platform"}`;
  document.getElementById("planKeyTag").textContent = meta.project_key || "XSM";
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
  // Template columns are Name / Env url; fall back to the older
  // category/specification shape so previously generated plans still render.
  const envs = plan.test_environments || [];
  document.getElementById("planEnvironmentsList").innerHTML = envs
    .map(e => `<span class="env-badge">${e.name || e.category || "Environment"}: ${e.url || e.specification || "TBD"}</span>`)
    .join("");

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
