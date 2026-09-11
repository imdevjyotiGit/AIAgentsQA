# 📋 Task Plan: Intelligent Test Planning Agent

**Status:** In Progress (Phase 2: Link)  
**Protocol:** B.L.A.S.T. Framework  
**Project Root:** `AI Agents/`

---

## 🎯 Project Overview
An intelligent agent application that connects to requirement & issue tracking platforms (Jira, Azure DevOps, Xray), fetches user stories / requirements, configures LLM providers (Claude default, Ollama, Groq, Grok, ChatGPT) with real-time connection testing, and generates comprehensive, structured test plans matching standardized organizational templates (Word `.docx` and Excel `.xlsx`).

---

## 🛣️ B.L.A.S.T. Execution Roadmap

### 🟢 Protocol 0: Initialization (Mandatory)
- [x] Create project memory: `task_plan.md`
- [x] Create project memory: `findings.md`
- [x] Create project memory: `progress.md`
- [x] Initialize Project Constitution: `gemini.md`
- [x] Halt execution and proceed to Blueprint Discovery

### 🏗️ Phase 1: B - Blueprint (Vision & Logic)
- [x] Present the 5 Discovery Questions to the user
- [x] Synthesize requirements from UI screenshots (`Testplantool1-4.png`) and template (`Test Plan - Template.docx`)
- [x] Confirm LLM integration requirements (Claude default, Ollama, Groq, Grok, ChatGPT)
- [x] Confirm requirement sources (Jira on-the-fly with URL + API Token + Email)
- [x] Confirm lightweight frontend architecture (HTML + CSS + JS)
- [x] Define JSON Data Schemas in `gemini.md`
- [x] Secured user approval for the Blueprint

### ⚡ Phase 2: L - Link (Connectivity)
- [ ] Implement & test local Ollama handshake (`http://localhost:11434`)
- [ ] Implement & test Jira connection verification tool
- [ ] Implement & test Cloud LLM connection testing (Groq, Grok, Claude, ChatGPT)
- [ ] Create `tools/test_connection.py` with unified testing for Jira & LLMs

### ⚙️ Phase 3: A - Architect (3-Layer Build)
- [ ] **Layer 1 (Architecture SOPs):**
  - `architecture/sop_jira_fetch.md`: Fetching and parsing user stories, acceptance criteria, subtasks
  - `architecture/sop_test_plan_generation.md`: Prompt engineering, template alignment, schema enforcement
  - `architecture/sop_export_formatting.md`: Word (.docx), Excel (.xlsx), Markdown generation
- [ ] **Layer 2 (Navigation / Agent Controller):**
  - Workflow router: Setup → Fetch Issues → Review & Custom Context → Test Plan Generation → Export
- [ ] **Layer 3 (Tools):**
  - `tools/jira_client.py`: Dynamic Jira connection and issue extraction
  - `tools/llm_client.py`: Unified LLM client with test connection routine
  - `tools/test_plan_generator.py`: LLM-powered test plan builder
  - `tools/template_parser.py`: Inbuilt and custom template reader
  - `tools/exporter.py`: Output exporter for Docx, Excel, Markdown

### ✨ Phase 4: S - Stylize (UI & UX)
- [ ] Build intuitive interactive frontend adhering to UI screenshots:
  - Screen 1: Setup (Jira connection modal/form + LLM connection modal/form + Test Connection button)
  - Screen 2: Fetch Issues (Product Name, Project Key, Sprint, Context)
  - Screen 3: Review & Refine (Context notes, Jira issues table, Template selection: Inbuilt vs Custom Excel)
  - Screen 4: Test Plan Viewer & Export (Interactive plan tabs, Export to Docx/Excel/Markdown, Share)
- [ ] Polished modern aesthetics with responsive layout and micro-interactions

### 🛰️ Phase 5: T - Trigger & Deployment
- [ ] Setup local CLI and Web server triggers (`npm run dev` / `python app.py`)
- [ ] Build validation tests for self-healing error handling
- [ ] Complete Maintenance Log in `gemini.md`
