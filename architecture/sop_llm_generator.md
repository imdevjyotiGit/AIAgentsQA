# 📐 Standard Operating Procedure: LLM Test Plan Generation

**SOP ID:** SOP-001  
**Layer:** Layer 1 (Architecture)  
**Target Tool:** `tools/llm_generator.py`  
**Schema Authority:** `gemini.md`

---

## 1. Goal & Objective
Translate extracted Jira issue data (Key, Summary, Description, Acceptance Criteria) and additional testing context into a deterministic, comprehensive test plan adhering to the standardized template schema in `gemini.md`.

---

## 2. Inputs
- `provider`: One of `"ollama"`, `"groq"`, `"grok"`, `"claude"`, `"chatgpt"`.
- `connection_config`: Dict containing `base_url`, `api_key`, `model`.
- `jira_issues`: List of normalized Jira issue dicts.
- `template_type`: `"inbuilt_excel"`, `"inbuilt_docx"`, or `"custom_excel"`.
- `additional_context`: User-specified test focus (e.g. cross-browser, security, edge cases).

---

## 3. Tool Logic & Processing Sequence
1. **Prompt Compilation:**
   - Inject the Project Constitution schema from `gemini.md`.
   - Embed user stories and acceptance criteria.
   - Enforce explicit instructions:
     - Minimum 5-8 structured test cases per story spanning Smoke, Functional, Boundary, and Negative tests.
     - Numbered step-by-step reproduction instructions.
     - Deterministic Expected Results.
     - Tag whether test is automatable via Playwright.
     - Extract Environment requirements, Risks & Mitigations, and Entry/Exit gates.
2. **LLM Invocation:**
   - For Ollama: Call `/api/chat` with JSON format option or markdown parsing.
   - For OpenAI / Groq / Grok: Call `/chat/completions` with JSON response mode or structured output.
   - For Claude: Call `/v1/messages` with clear JSON system instructions.
3. **Validation & Fallback Parsing:**
   - Parse the JSON response.
   - Validate against the schema in `gemini.md`.
   - If JSON decoding fails due to model conversational wrapper, extract `{ ... }` block via regex.
   - If any critical fields are missing, populate sensible template defaults.
4. **Intermediate Storage:**
   - Save the generated plan payload to `.tmp/latest_test_plan.json`.

---

## 4. Edge Cases & Guardrails
- **Missing Acceptance Criteria:** Highlight with `[Clarification Needed - Story lacked explicit AC]`.
- **Rate Limits / Timeouts:** If timeout exceeds 60s, return clear error and recommend smaller batch or faster model.
- **Model Offline:** Gracefully fail with error instructing user to run `test_connection.py`.
