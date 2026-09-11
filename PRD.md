# Product Requirements Document
## Intelligent Test Planning Agent — BigFix SM (XSM)

| | |
|---|---|
| **Document status** | Draft for team review |
| **Owner** | QA Engineering |
| **Target system under test** | BigFix Service Management (XSM) — `https://xsmtest.dryice-aws.com/` |
| **Requirements source** | Jira Cloud — `https://hclsw-io.atlassian.net`, project key `XSM` |
| **Repository** | `AIAgentsQA` |
| **Last updated** | 2026-09-11 |

> **Scope note.** This PRD covers the *Test Planning Agent* — the internal tool that
> generates test plans. It does **not** specify BigFix SM itself; XSM appears here only
> as the system whose requirements the agent consumes. Items the author could not verify
> are marked **[TBD]** rather than assumed.

---

## 1. Problem statement

Producing a compliant test plan for an XSM story is manual and slow. A QA engineer reads
the Jira issue, re-types the standard template structure, writes scenarios and cases by
hand, and reformats everything into Word or Excel for review. The work is repetitive,
the output varies by author, and template sections are routinely missed under deadline.

The cost is not just time — inconsistent plans make review harder and weaken the
traceability story during audit.

## 2. Goals and non-goals

### Goals
| # | Goal |
|---|---|
| G1 | Turn an XSM Jira issue into a complete, template-conformant draft test plan in minutes |
| G2 | Produce output matching the standard corporate template exactly — every section, every table column |
| G3 | Maintain traceability from every test case back to its Jira issue key |
| G4 | Let a reviewer iterate on a generated plan without losing accepted test cases |
| G5 | Keep requirement data inside company infrastructure by default |
| G6 | Export to Word, Excel, and Markdown without manual reformatting |

### Non-goals
- Not a test *execution* or test-management platform; it produces plans, not results.
- Does not write automation code, though it flags which cases are automation candidates.
- Does not replace QA judgement — every generated plan is a **draft requiring review**.
- Does not modify Jira. Read-only against the requirements source.

## 3. Users

| Persona | Need | Success looks like |
|---|---|---|
| **QA Engineer** (primary) | Draft a plan for an assigned XSM story | Fetches the issue, generates, refines, exports — under 10 minutes |
| **QA Lead** | Consistent, reviewable plans across the team | Every plan carries the same sections; review is about content, not formatting |
| **Automation Engineer** | Identify automation candidates | Each case marked Playwright vs Manual |

## 4. Functional requirements

### 4.1 Requirements ingestion
| ID | Requirement | Status |
|---|---|---|
| FR-1.1 | Fetch issues from Jira Cloud by project key, issue key, or sprint | Implemented |
| FR-1.2 | Accept a story typed or pasted directly, with no Jira connection | Implemented |
| FR-1.3 | Parse Atlassian Document Format descriptions into plain text | Implemented |
| FR-1.4 | Offer an offline demo dataset of representative XSM issues | Implemented |
| FR-1.5 | Support Jira Cloud and Jira Server/Data Center authentication | Implemented |

**Note.** Atlassian removed `GET /rest/api/3/search` from Jira Cloud (returns `410 Gone`).
The client calls `/rest/api/3/search/jql` and falls back to `/rest/api/2/search` for
Server/DC.

### 4.2 Plan generation
| ID | Requirement | Status |
|---|---|---|
| FR-2.1 | Generate a plan conforming to the standard template schema | Implemented |
| FR-2.2 | Produce 2–3+ cases per issue across Smoke, Positive, Negative, Boundary | Implemented |
| FR-2.3 | Each case carries id, Jira reference, module, type, priority, preconditions, steps, expected result, automation flag | Implemented |
| FR-2.4 | Accept free-text context to steer focus areas | Implemented |
| FR-2.5 | Emit `TBD` for unknowable values rather than omitting template fields | Implemented |

### 4.3 Refinement
| ID | Requirement | Status |
|---|---|---|
| FR-3.1 | Improve an existing plan while preserving accepted case IDs | Implemented |
| FR-3.2 | Regenerate from scratch, discarding the current plan | Implemented |
| FR-3.3 | Accept additional context at the review stage | Implemented |

### 4.4 Template conformance
The generated document must mirror `Test Plan Template/Test Plan - Template.docx`:

| Section | Table columns |
|---|---|
| Objective | — |
| Scope (Inclusions / Exclusions) | — |
| Test Environments | `Name` \| `Env url` |
| Defect Reporting Procedure | `Defect Process` \| `POC` |
| Test Strategy | — |
| Test Schedule | `Task` \| `Dates` |
| Test Deliverables | — |
| Detailed Test Cases | ID, Jira Key, Title, Type, Priority, Steps, Expected Result |
| Entry and Exit Criteria | — |
| Test Execution (entry/exit) | — |
| Test Closure (entry/exit) | — |
| Tools | `Purpose` \| `Tool` |
| Risks and Mitigations | Risk, Impact, Mitigation |
| Approvals | Role, Name, Status |

### 4.5 Export
| ID | Requirement | Status |
|---|---|---|
| FR-5.1 | Word `.docx` with corporate styling | Implemented |
| FR-5.2 | Excel `.xlsx` — Overview, Test Cases, Risks & Approvals sheets | Implemented |
| FR-5.3 | Markdown for Confluence/Jira paste | Implemented |

### 4.6 LLM provider support
| ID | Requirement | Status |
|---|---|---|
| FR-6.1 | Ollama (local and cloud models) — default | Implemented |
| FR-6.2 | Anthropic Claude, OpenAI, Groq, xAI Grok | Implemented, **blocked by policy** — see §7 |
| FR-6.3 | Test connectivity before running a generation | Implemented |
| FR-6.4 | Warn when a selected model sends data off-machine | Implemented |

## 5. Non-functional requirements

| ID | Requirement | Current state |
|---|---|---|
| NFR-1 | Generation completes within 60s for a single issue | ~18s on `gemma4:31b-cloud`; ~3 min on `llama3.2:3b` |
| NFR-2 | Concurrent users must not block one another | Addressed via `ThreadingHTTPServer` |
| NFR-3 | Credentials never written to disk | Held in browser memory, sent per request |
| NFR-4 | Requirement data stays on company infrastructure by default | Met with local Ollama models |
| NFR-5 | Failures produce a diagnosable log | `logs/agent.log` — timings, token counts, raw output, tracebacks |
| NFR-6 | Deployable as a container | Dockerfile + compose provided |

## 6. Architecture

```
Browser (4-step wizard, vanilla HTML/CSS/JS)
        |  JSON over HTTP
tools/server.py  (ThreadingHTTPServer, stdlib only)
        |
        +-- jira_client.py        -> Jira Cloud / Server REST
        +-- llm_generator.py      -> Ollama | Claude | OpenAI | Groq | Grok
        +-- test_plan_exporter.py -> .docx / .xlsx / .md
        +-- test_connection.py    -> pre-flight handshakes
        +-- agent_logger.py       -> logs/agent.log
```

**API surface**

| Endpoint | Method | Purpose |
|---|---|---|
| `/health` | GET | Liveness probe (no downstream dependencies) |
| `/api/test-connection/jira` | POST | Verify Jira credentials |
| `/api/test-connection/llm` | POST | Verify LLM endpoint |
| `/api/fetch-issues` | POST | Retrieve Jira issues |
| `/api/generate-plan` | POST | Generate or refine a plan |
| `/api/export` | POST | Produce a document |
| `/api/download/<file>` | GET | Retrieve a generated document |

## 7. Constraints and risks

| # | Risk | Impact | Mitigation |
|---|---|---|---|
| R1 | **Anthropic/OpenAI API keys restricted by org policy** | Cloud providers unusable today | Ollama is the default; provider support retained for when access is approved |
| R2 | Ollama `-cloud` models send prompt text to Ollama's servers | Requirement data leaves company infrastructure | Connection test states this explicitly; local models available. **Requires data-governance sign-off before use with real XSM tickets** |
| R3 | Small local models produce thin plans | Low-quality drafts | Prefer `gemma4:26b` locally; `llama3.2:3b` is smoke-test only |
| R4 | Generated content may be plausible but wrong | Incorrect test coverage | Every plan is a draft requiring QA review — non-negotiable |
| R5 | No authentication on the hosted app | Anyone on the network can use it | **Open — see §9** |
| R6 | Atlassian API deprecations | Fetch breaks without warning | Multi-endpoint fallback; failures logged with actionable messages |

## 8. Deployment

| Artifact | Purpose |
|---|---|
| `Dockerfile` | Container image; non-root; health check |
| `docker-compose.yml` | Single-host deploy, optional bundled Ollama |
| `Jenkinsfile` | Build → static checks → smoke test → push → deploy |
| `requirements.txt` | Pinned runtime dependencies |

**Configuration** (environment variables)

| Variable | Default | Purpose |
|---|---|---|
| `HOST` | `127.0.0.1` | Bind address — must be `0.0.0.0` in a container |
| `PORT` | `8088` | Listen port |
| `LLM_TIMEOUT_SECONDS` | `600` | Per-generation timeout |
| `OLLAMA_NUM_CTX` | `16384` | Context window |
| `APP_VERSION` | `dev` | Reported by `/health` |

## 9. Open questions

These need decisions before a team rollout and are **not** resolved in this document:

1. **Authentication** — the app has none. Who may reach it, and does it sit behind SSO,
   a reverse proxy, or a private network? (R5)
2. **Data governance** — is Ollama Cloud approved for XSM requirement text, or must
   deployments be restricted to local models? (R2)
3. **Hosting target** — single VM via compose, or an existing orchestrator? **[TBD]**
4. **Registry** — which container registry, and what are its credentials in Jenkins? **[TBD]**
5. **Model standard** — one blessed model for consistent output across the team, or
   per-user choice? Different models yield materially different plans.
6. **Template ownership** — who approves changes to `Test Plan - Template.docx`, and how
   does the agent's schema stay in sync when it changes?
7. **Retention** — how long should generated plans and `logs/agent.log` be kept? Logs
   currently contain full requirement text.

## 10. Success metrics

| Metric | Baseline | Target |
|---|---|---|
| Time to first reviewable draft | Manual **[TBD — measure]** | < 10 minutes |
| Template section completeness | Variable | 100% of required sections present |
| Test cases traceable to a Jira key | Variable | 100% |
| Reviewer edits before approval | n/a | Trend down release over release |

> Baselines marked **[TBD]** must be measured before the targets carry meaning.
