# 🔍 Findings & Technical Discoveries: Intelligent Test Planning Agent

## 1. UI Flow & State Breakdown (From Screenshots)
- **Step 1: Setup (`Testplantool1.png`)**
  - Jira Connection Card: "Add New Connection" action with on-the-fly credentials entry.
  - Import from Test Management Tools: Grid with cards for Jira (Available), TestRail, Zephyr, Xray, Qase, Azure DevOps (Coming Soon / Connect).
  - *New User Requirement:* Needs an **LLM Connection Card/Modal** with:
    - Provider dropdown: Ollama (Local), Groq, Grok (xAI), OpenAI, etc.
    - Fields: Base URL, Model Name, API Key.
    - An explicit **"Test Connection" button** that executes an immediate ping/handshake test before saving.
- **Step 2: Fetch Issues (`Testplantool2.png`)**
  - Inputs: Product Name (e.g. `XSM`), Project Key (required, e.g. `XSM`), Sprint/Fix Version (optional, e.g. `Sprint 15`), Additional Context (optional textarea).
  - Action: "Fetch Jira Issues" button.
- **Step 3: Review (`Testplantool3.png`)**
  - Additional Context & Notes textarea.
  - Review Jira Issues list showing retrieved stories, summary, acceptance criteria.
  - *Template Section:* Inbuilt Template vs Custom Template (Excel/Word).
  - Action: "Generate Test Plan" primary button.
- **Step 4: Test Plan Output (`Testplantool4.png`)**
  - Empty state when not generated.
  - Rendered test plan view with tabs: Overview, Scope, Test Strategy, Test Cases, Defect Procedure, Approvals.
  - Actions: Export to Word (`.docx`), Export to Excel (`.xlsx`), Copy Markdown, Share link/file.

---

## 2. Test Plan Template Analysis (`Test Plan - Template.docx`)
The document template contains standardized sections:
1. **Document Metadata & Header:** Product/Platform name, Version, Date, Authors.
2. **Objective:** Executive goal of testing.
3. **Scope:** Inclusions (features, UI, workflows), Exclusions / Out-of-scope.
4. **Test Environments:** Operating systems, browsers, URLs, databases, servers.
5. **Defect Reporting Procedure:** Bug life-cycle, severity/priority tiers.
6. **Test Strategy:** Types of testing (Functional, Smoke, Negative, Automation).
7. **Test Schedule & Milestones:** Timelines, iterations.
8. **Test Deliverables:** Plans, automated scripts, test run reports.
9. **Entry and Exit Criteria:** Pre-execution conditions and release gates.
10. **Tools & Equipment:** Testing tools (Playwright, Selenium, Jira, Postman).
11. **Risks and Mitigations:** Contingency plans.
12. **Approvals / Sign-Off:** QA Lead, Product Manager, Dev Lead.

---

## 3. Supported LLM Connection Specifications
- **Ollama (Local):**
  - Default URL: `http://localhost:11434`
  - Handshake: `GET /api/tags` or `POST /api/chat`
  - Does not require API Key; requires model name (e.g., `llama3`, `mistral`, `qwen2.5`).
- **Groq:**
  - Base URL: `https://api.groq.com/openai/v1`
  - Models: `llama-3.3-70b-versatile`, `mixtral-8x7b-32768`, etc.
  - Requires Groq API Key (`gsk_...`).
  - Handshake: Minimal token generation test (`POST /chat/completions`).
- **Grok (xAI):**
  - Base URL: `https://api.x.ai/v1`
  - Models: `grok-beta`, `grok-2`
  - Requires xAI API Key (`xai-...`).
  - Handshake: `POST /chat/completions`.
