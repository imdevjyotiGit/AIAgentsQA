# 🤖 Intelligent Test Planning Agent (B.L.A.S.T. Framework)

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Framework](https://img.shields.io/badge/Architecture-B.L.A.S.T.-orange.svg)](#the-blast-framework)

An enterprise-grade, AI-driven QA Test Planning agent that connects directly to requirement and issue tracking platforms (Jira, Azure DevOps, Xray), extracts user stories and acceptance criteria on the fly, tests LLM connections in real time, and synthesizes comprehensive, audit-ready Test Plans matching industry standards (IEEE 829 / custom enterprise templates).

The agent outputs formatted test plans in **Microsoft Word (`.docx`)**, **Microsoft Excel (`.xlsx`)**, and **Confluence-compatible Markdown (`.md`)**.

---

## 🌟 Key Capabilities

- **Flexible Dual Requirements Ingestion**:
  - **Direct Story / Text Input (Instant / No Jira Needed)**: Never feel blocked by tooling! Write or paste user story descriptions, acceptance criteria, or PRD notes directly into the agent. Click 1-click test plan generation immediately.
  - **On-the-Fly Jira Integration**: Connects via Jira REST API using Host URL, Email, and API Token. Includes an offline **Demo Mode** with realistic sample user stories (e.g., VWO A/B Testing platform requirements).
  - **Sample Story Preloader**: Includes 1-click realistic enterprise story loading to test generation instantly.
- **Multi-Provider LLM Support**:
  - **Ollama (Local / Privacy-First)**: Local offline inference (`llama3.2:3b`, `llama3:8b`, `deepseek-r1`, `mistral`) ensuring zero sensitive requirement data leaves company infrastructure.
  - **OpenAI / ChatGPT**: `gpt-4o`, `gpt-4o-mini`
  - **Groq**: Ultra-low latency cloud inference (`llama-3.3-70b-versatile`)
  - **Anthropic Claude**: `claude-3-5-sonnet`, `claude-3-haiku`
  - **xAI Grok**: `grok-2`
- **Real-Time Handshake & Connectivity Testing**: Instant validation of Jira credentials and LLM endpoint health with visual status indicators before running expensive operations.
- **Enterprise Test Plan Synthesis**:
  - Executive Summary & Scope (In-scope vs. Out-of-scope)
  - Assumptions, Risks & Mitigations
  - Detailed Test Scenarios categorized by Type (Functional, Boundary, Edge Cases, Security, Performance)
  - Concrete Test Cases with Preconditions, Step-by-Step Instructions, Test Data, and Expected Results
  - Requirements Traceability Matrix (RTM) linking test cases back to Requirements/Jira Issue Keys
- **Multi-Format Document Exporter**:
  - **Word (`.docx`)**: Styled executive document with formatted tables and headers matching standard corporate templates.
  - **Excel (`.xlsx`)**: Multi-tab workbook (`Overview`, `Test Scenarios`, `Detailed Test Cases`, `Traceability Matrix`) with styled headers and column auto-sizing.
  - **Markdown (`.md`)**: Formatted for direct paste into Confluence, Jira comments, or GitHub Wiki.

---

## 🏗️ Architecture & Project Structure

```
AIAgentsQA/
├── README.md                           # Main documentation & reproduction guide
├── learnings.md                        # Technical insights & architecture takeaways
├── feature_improvements.md             # Product roadmap & future enhancements
├── .gitignore                          # Git ignore rules
│
├── architecture/                       # Standard Operating Procedures (SOPs)
│   ├── sop_llm_generator.md            # SOP for prompt engineering & schema validation
│   └── sop_template_export.md          # SOP for DOCX & Excel document formatting
│
├── tools/                              # Backend services & agent tools
│   ├── server.py                       # Lightweight zero-dependency HTTP/JSON API server
│   ├── jira_client.py                  # Jira REST API client with fallback demo dataset
│   ├── llm_generator.py                # Multi-provider LLM prompt router & parser
│   ├── test_connection.py              # Connectivity verification for Jira & LLM endpoints
│   └── test_plan_exporter.py           # Multi-format document builder (Word, Excel, MD)
│
├── web/                                # Production web frontend (Vanilla HTML5/CSS3/JS)
│   ├── index.html                      # 4-step wizard UI layout
│   ├── style.css                       # Modern dark/light ready design system
│   └── app.js                          # Client state management & API integration
│
├── frontend/                           # React + Vite frontend workspace
│   ├── package.json
│   ├── vite.config.js
│   └── src/
│
├── Test Plan Template/                 # Reference enterprise templates
│   └── Test Plan - Template.docx       # Standard corporate Word template
│
└── UI Screenshots/                     # System design & UI reference mockups
    ├── Testplantool1.png
    ├── Testplantool2.png
    ├── Testplantool3.png
    └── Testplantool4.png
```

---

## ⚡ Quick Start & Usage

### 1. Prerequisites
- **Python 3.10+** installed
- Optional: [Ollama](https://ollama.ai/) installed locally for offline generation
- Optional: Node.js 18+ (if running the React frontend)

### 2. Install Python Dependencies
```bash
pip install requests python-docx openpyxl
```

### 3. Launch the Backend Server
```bash
python tools/server.py 8088
```
The server starts at `http://127.0.0.1:8088` and automatically serves both the API endpoints and the frontend application.

### 4. Open in Browser
Navigate to:
```
http://127.0.0.1:8088
```

---

## 🖥️ End-to-End Workflow

```
+------------------+     +-------------------+     +------------------+     +--------------------+
|  Step 1: Setup   | --> | Step 2: Fetch     | --> | Step 3: Review   | --> | Step 4: Generate   |
|  - Jira Host     |     | - Project Key     |     | - Inspect issues |     | - LLM generates    |
|  - LLM Provider  |     | - Issue Keys      |     | - Context notes  |     | - Word / Excel / MD|
|  - Test Handshake|     | - Sprint query    |     | - Select template|     | - Instant download |
+------------------+     +-------------------+     +------------------+     +--------------------+
```

1. **Step 1: Setup & Connection Verification**
   - **Jira (Optional)**: Input your Jira Cloud domain (e.g. `https://mycompany.atlassian.net`), email, and API token, or keep `"demo"`. Alternatively, skip Jira entirely if you want to write/paste requirements directly!
   - **LLM**: Select your provider (Ollama, ChatGPT, Groq, Claude, Grok). Enter Base URL and API Key if applicable. Click **Test LLM Connection**.
2. **Step 2: Enter Requirements (Direct Story or Jira)**
   - **Option A (Direct Story Input - Default)**: Type or paste Story Title, User Story statement, and Acceptance Criteria. Click **⚡ Generate Test Plan Now** for instant generation, or click **✨ Load Sample Story** for a one-click demo.
   - **Option B (Fetch from Jira)**: Query by Project Key, specific Issue Keys (e.g. `VWO-101`), or Sprint.
3. **Step 3: Review & Refine Context**
   - Inspect the structured user story or fetched tickets.
   - Add custom domain context (e.g. *"Focus heavily on cross-browser compatibility and edge cases with slow networks"*).
   - Choose your template format: **Inbuilt Standardized Template** or **Custom Template**.
4. **Step 4: Generate & Export Test Plan**
   - Click **Generate Test Plan with AI**.
   - The agent builds the plan and renders it in interactive tabs: *Summary*, *Scenarios*, *Test Cases*, and *Raw Markdown*.
   - Click **Export Word (.docx)**, **Export Excel (.xlsx)**, or **Download Markdown (.md)**.

---

## 🛠️ Step-by-Step Guide: How to Create This Project From Scratch

If you want to build this application from the ground up, follow this B.L.A.S.T. roadmap:

### Step 1: Blueprint (Define Data Contracts & Schemas)
Define the canonical JSON schema for test plans so every LLM provider returns a predictable, structured output.
Key schema attributes:
- `metadata`: `product_name`, `project_key`, `date`, `author`
- `executive_summary`: High-level test objective
- `scope`: `in_scope` and `out_of_scope` lists
- `test_scenarios`: `id`, `title`, `type` (Functional / Boundary / Security), `priority`
- `test_cases`: `id`, `scenario_id`, `title`, `preconditions`, `steps`, `test_data`, `expected_result`
- `traceability`: Mapping from `jira_issue_key` to `test_case_ids`

### Step 2: Link Layer (Connectivity Verification)
Create `tools/test_connection.py` to validate external dependencies before executing pipelines:
1. **Ollama**: Query `GET http://localhost:11434/api/tags` to check server status and enumerate installed models.
2. **Jira**: Query `GET {host}/rest/api/3/myself` with HTTP Basic Auth (`base64(email:api_token)`).
3. **Cloud LLMs**: Send a minimal completion request (`"ping"`) to verify API key validity.

### Step 3: Architect Layer (Core Tools)
Build isolated, reusable modules:
1. **`tools/jira_client.py`**:
   - Use Atlassian REST API `/rest/api/3/search` or `/rest/api/3/issue/{key}`.
   - Parse Jira Document Format (ADF) / plain text descriptions and acceptance criteria into plain text.
   - Include a fallback demo mock dataset for zero-friction local developer onboarding.
2. **`tools/llm_generator.py`**:
   - Craft a detailed system prompt enforcing IEEE 829 test planning standards.
   - Inject the Jira issues and extra context.
   - Request strict JSON output conforming to the blueprint schema.
   - Implement JSON extraction logic to handle markdown code fences (````json ... ````).
3. **`tools/test_plan_exporter.py`**:
   - **DOCX**: Use `python-docx` to generate styled documents with corporate tables (Header cell styling, alternating row shading, custom borders).
   - **XLSX**: Use `openpyxl` to generate a 4-tab workbook (`Overview`, `Scenarios`, `Test Cases`, `Traceability`) with bold headers and auto-adjusted column widths.
   - **Markdown**: Generate clean GitHub / Confluence flavored Markdown.

### Step 4: Controller & API Layer
Create `tools/server.py` using Python's built-in `http.server`:
- Implement `TestPlannerRequestHandler` handling CORS headers.
- Route endpoints:
  - `POST /api/test-connection/jira`
  - `POST /api/test-connection/llm`
  - `POST /api/fetch-issues`
  - `POST /api/generate-plan`
  - `POST /api/export`
  - `GET /api/download/<filename>`
- Automatically serve static frontend files from `web/`.

### Step 5: Stylize Layer (Frontend UI/UX)
Build an intuitive, responsive user experience in `web/index.html`:
- 4-step linear wizard with active step progression.
- Live status indicators (Online/Offline badges) for Jira and LLM endpoints.
- Collapsible cards, tabbed test plan viewer, and single-click file downloads.

---

## 📡 REST API Reference

| Endpoint | Method | Payload | Description |
|---|---|---|---|
| `/api/test-connection/jira` | `POST` | `{"host", "email", "api_token"}` | Verifies Jira credentials |
| `/api/test-connection/llm` | `POST` | `{"provider", "base_url", "api_key", "model"}` | Tests LLM connection |
| `/api/fetch-issues` | `POST` | `{"host", "email", "api_token", "project_key", "issue_keys"}` | Extracts Jira tickets |
| `/api/generate-plan` | `POST` | `{"provider", "config", "issues", "context", "product_name"}` | Generates test plan via LLM |
| `/api/export` | `POST` | `{"plan", "format": "docx"\|"xlsx"\|"md", "template_type"}` | Generates export file |
| `/api/download/<file>` | `GET` | None | Downloads generated document |

---

## 🛡️ Privacy & Security Best Practices

1. **Zero Secret Hardcoding**: API tokens and credentials are never stored on disk. They are transmitted dynamically per session.
2. **Local Model Isolation**: By selecting **Ollama**, all prompt processing, ticket analysis, and test case generation happen completely offline on your workstation.
3. **Traceability**: Every generated test case is linked directly back to the original Jira issue key for compliance and audit readiness.

---

## 📄 License
This project is open-source and available under the [MIT License](LICENSE).
