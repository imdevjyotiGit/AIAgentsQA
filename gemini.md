# 📜 Project Constitution: Intelligent Test Planning Agent (`gemini.md`)

This document is the **Law** of the project. All code, tools, and UI logic must adhere to the schemas, behavioral rules, and architectural invariants defined herein.

---

## 🏛️ Architectural Invariants
1. **3-Layer Separation (A.N.T.):**
   - **Layer 1: Architecture (`architecture/`):** Markdown SOPs for each operation. Logic changes require updating the SOP before updating code.
   - **Layer 2: Navigation:** Controller logic that orchestrates data flow between user inputs, Jira/ADO APIs, LLMs, and exporters.
   - **Layer 3: Tools (`tools/`):** Atomic, deterministic, isolated Python/Node execution modules.
2. **On-the-Fly Connections:**
   - Jira, ADO, and LLM credentials can be entered dynamically in the UI and tested before execution.
   - Secrets are held in session state or local `.env`—never hardcoded.
3. **Template Fidelity:**
   - Generated test plans must strictly map to the sections present in the approved template (Document Metadata, Objectives, Scope, Environments, Strategy, Schedule, Test Cases, Criteria, Risks, Approvals).

---

## 📦 Core Data Schemas (JSON)

### 1. Jira / Requirement Payload Schema
```json
{
  "connection": {
    "provider": "jira",
    "host": "https://your-domain.atlassian.net",
    "email": "user@domain.com",
    "api_token": "secret_token"
  },
  "query": {
    "product_name": "VWO Platform",
    "project_key": "VWOAPP",
    "issue_ids": ["VWOAPP-101", "VWOAPP-102"],
    "sprint": "Sprint 15",
    "additional_context": "Focus on cross-browser and payment gateway edge cases"
  },
  "fetched_issues": [
    {
      "id": "VWOAPP-101",
      "summary": "User Checkout Authentication Flow",
      "description": "As a shopper, I need to log in or continue as guest at checkout.",
      "acceptance_criteria": [
        "User can enter valid email/password",
        "Guest checkout allows email only",
        "OAuth buttons for Google and Apple work"
      ],
      "issue_type": "Story",
      "priority": "High"
    }
  ]
}
```

### 2. LLM Provider Connection Schema
```json
{
  "provider": "ollama | chatgpt | claude | groq | grok",
  "base_url": "http://localhost:11434 | https://api.openai.com/v1 | https://api.anthropic.com/v1 | https://api.groq.com/openai/v1 | https://api.x.ai/v1",
  "api_key": "optional_for_ollama_or_valid_api_key",
  "model": "llama3.2:3b | llama3.2:1b | gpt-4o | gpt-4o-mini | claude-3-5-sonnet-20241022 | llama-3.3-70b-versatile",
  "temperature": 0.2,
  "connection_status": "untested | connected | failed"
}
```

### 3. Generated Test Plan Schema
```json
{
  "metadata": {
    "product_name": "string",
    "project_key": "string",
    "sprint": "string",
    "generated_date": "ISO-8601",
    "llm_model": "string"
  },
  "objective": "string",
  "scope": {
    "inclusions": ["string"],
    "exclusions": ["string"]
  },
  "test_environments": [
    {
      "category": "Browser | OS | Device | API",
      "specification": "string"
    }
  ],
  "test_strategy": {
    "types": ["Functional", "Smoke", "Regression", "Security"],
    "automation_approach": "string"
  },
  "test_cases": [
    {
      "id": "TC-001",
      "jira_reference": "VWOAPP-101",
      "module": "Authentication",
      "title": "Valid login at checkout",
      "type": "Positive / Smoke",
      "priority": "Critical",
      "preconditions": "User account exists",
      "steps": ["Navigate to checkout", "Enter credentials", "Click Sign In"],
      "expected_result": "Authenticated session started",
      "status": "Draft",
      "automation": "Yes"
    }
  ],
  "entry_criteria": ["string"],
  "exit_criteria": ["string"],
  "risks_and_mitigations": [
    {
      "risk": "string",
      "impact": "High | Medium | Low",
      "mitigation": "string"
    }
  ],
  "approvals": [
    { "role": "QA Lead", "name": "string", "status": "Pending" }
  ]
}
```

---

## 🛑 Behavioral Rules & "Do Nots"
1. **Never Guess Business Logic:** If user stories lack acceptance criteria, mark them explicitly in the test plan as `[Needs Clarification]` rather than hallucinating validation rules.
2. **Never Write Scripts Without Tested Links:** Do not attempt test plan generation before verifying the connection to Jira/ADO and the selected LLM provider.
3. **Deterministic Output:** All test cases must have explicit step-by-step instructions and deterministic pass/fail criteria.
