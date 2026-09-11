"""
tools/llm_generator.py
B.L.A.S.T. Phase 3 (Tools): Intelligent Test Plan Generator
Orchestrates prompt creation, invokes the selected LLM provider (Ollama, Groq, Grok, Claude, ChatGPT),
and validates the resulting JSON against the Project Constitution in gemini.md.
"""

import sys
import os
import json
import re
import time
import urllib.request
import urllib.error
import ssl

from agent_logger import get_logger, log_payload, LOG_FILE as LOG_FILE_PATH

logger = get_logger("llm_generator")

ssl_context = ssl.create_default_context()

# Local models on CPU generate a full test plan far slower than a cloud API.
# 90s was not enough for even a single issue, so allow a generous ceiling and
# let it be tuned per environment without a code change.
LLM_TIMEOUT_SECONDS = int(os.environ.get("LLM_TIMEOUT_SECONDS", "600"))

# Ollama's num_ctx covers prompt AND response. The system prompt alone is
# ~700 tokens before issues are added, and a full plan is several thousand
# more, so 4096 silently truncated the output.
OLLAMA_NUM_CTX = int(os.environ.get("OLLAMA_NUM_CTX", "16384"))

SYSTEM_PROMPT = """You are an expert QA Automation Architect and Test Planner.
Your task is to generate a comprehensive, enterprise-grade test plan based on the provided Jira issues, product context, and testing requirements.

You must output STRICT JSON matching this schema:
{
  "metadata": {
    "product_name": "string",
    "project_key": "string",
    "sprint": "string",
    "generated_date": "YYYY-MM-DD",
    "llm_model": "string"
  },
  "objective": "Detailed paragraph describing overall testing objective.",
  "scope": {
    "inclusions": ["Detailed list of in-scope components/flows"],
    "exclusions": ["Detailed list of out-of-scope items"]
  },
  "test_environments": [
    { "name": "QA | Pre Prod | UAT | Prod", "url": "https://xsmtest.dryice-aws.com/" }
  ],
  "defect_reporting": {
    "procedure": "How defects are raised, triaged, and tracked to closure.",
    "contacts": [
      { "area": "New Frontend | Backend | Dev Ops", "poc": "Owner name or role" }
    ]
  },
  "test_strategy": {
    "types": ["Functional", "Smoke", "Regression", "Negative", "Edge Case", "Security"],
    "automation_approach": "Strategy detailing Playwright/automation coverage."
  },
  "test_schedule": [
    { "task": "Creating Test Plan | Test Case Creation | Test Case Execution | Summary Reports Submission Date", "dates": "Planned window or TBD" }
  ],
  "test_deliverables": ["Test Plan", "Test Cases", "Defect Reports", "Test Summary Report"],
  "tools": [
    { "purpose": "Test Management | Automation | Defect Tracking | CI", "tool": "Tool name" }
  ],
  "test_cases": [
    {
      "id": "TC-001",
      "jira_reference": "ISSUE-KEY",
      "module": "Feature or Module name",
      "title": "Clear concise test scenario title",
      "type": "Positive / Smoke / Negative / Boundary",
      "priority": "Critical / High / Medium / Low",
      "preconditions": "Setup or data requirements",
      "steps": "1. Step one\\n2. Step two\\n3. Step three",
      "expected_result": "Exact verifiable outcome",
      "status": "Draft",
      "automation": "Yes (Playwright) or Manual"
    }
  ],
  "entry_criteria": ["Criteria before testing starts"],
  "exit_criteria": ["Criteria for testing sign-off"],
  "test_execution": {
    "entry_criteria": ["Criteria before test execution begins"],
    "exit_criteria": ["Criteria to complete test execution"]
  },
  "test_closure": {
    "entry_criteria": ["Criteria before test closure begins"],
    "exit_criteria": ["Criteria to sign off and close testing"]
  },
  "risks_and_mitigations": [
    { "risk": "Description of risk", "impact": "High / Medium / Low", "mitigation": "Mitigation steps" }
  ],
  "approvals": [
    { "role": "QA Lead", "name": "Pending Review", "status": "Pending" },
    { "role": "Product Owner", "name": "Pending Review", "status": "Pending" },
    { "role": "Engineering Lead", "name": "Pending Review", "status": "Pending" }
  ]
}

Ensure test cases cover: Happy paths, error validations, boundary conditions, edge cases, and security basics.

This schema mirrors the standard corporate Test Plan template. Populate EVERY top-level
key - including defect_reporting, test_schedule, test_deliverables, tools, test_execution
and test_closure. Where a real value is unknown (owner names, calendar dates), use "TBD"
rather than omitting the field, so the exported document keeps the required structure.

Return ONLY valid JSON. Do not include markdown code block quotes (like ```json), commentary, or chit-chat.
"""

def _call_ollama(base_url, model, user_prompt):
    url = f"{base_url.rstrip('/')}/api/chat"
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ],
        "stream": False,
        "format": "json",
        "options": {
            "temperature": 0.2,
            "num_ctx": OLLAMA_NUM_CTX
        }
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )

    logger.info(
        "Ollama request -> %s | model=%s | num_ctx=%d | timeout=%ds | prompt=%d chars",
        url, model, OLLAMA_NUM_CTX, LLM_TIMEOUT_SECONDS, len(user_prompt)
    )
    started = time.time()
    try:
        with urllib.request.urlopen(req, timeout=LLM_TIMEOUT_SECONDS) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.URLError as e:
        # A socket timeout surfaces here as URLError("timed out") with no
        # HTTP status, which is why the old message was so uninformative.
        logger.error(
            "Ollama call failed after %.1fs: %s (timeout is %ds - raise "
            "LLM_TIMEOUT_SECONDS or use a smaller/faster model)",
            time.time() - started, e.reason, LLM_TIMEOUT_SECONDS
        )
        raise

    elapsed = time.time() - started
    content = data.get("message", {}).get("content", "")
    # eval_count / prompt_eval_count are Ollama's own token counters - the
    # cheapest way to see whether the context window was the real limit.
    logger.info(
        "Ollama responded in %.1fs | done_reason=%s | prompt_tokens=%s | "
        "output_tokens=%s | content=%d chars",
        elapsed, data.get("done_reason"), data.get("prompt_eval_count"),
        data.get("eval_count"), len(content)
    )
    if data.get("done_reason") == "length":
        logger.warning(
            "Ollama stopped at the context limit (num_ctx=%d) - the JSON is "
            "likely truncated. Raise OLLAMA_NUM_CTX.", OLLAMA_NUM_CTX
        )
    log_payload(logger, "Ollama raw output", content)
    return content

def _call_openai_compatible(base_url, api_key, model, user_prompt):
    url = f"{base_url.rstrip('/')}/chat/completions"
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.2,
        "response_format": {"type": "json_object"}
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key.strip()}",
            "Content-Type": "application/json"
        }
    )
    logger.info("OpenAI-compatible request -> %s | model=%s", url, model)
    started = time.time()
    with urllib.request.urlopen(req, timeout=LLM_TIMEOUT_SECONDS, context=ssl_context) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    content = data["choices"][0]["message"]["content"]
    logger.info("Responded in %.1fs | content=%d chars", time.time() - started, len(content))
    log_payload(logger, "OpenAI-compatible raw output", content)
    return content

def _call_claude(api_key, model, user_prompt):
    url = "https://api.anthropic.com/v1/messages"
    payload = {
        "model": model,
        "max_tokens": 4000,
        "system": SYSTEM_PROMPT,
        "messages": [{"role": "user", "content": user_prompt}]
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "x-api-key": api_key.strip(),
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json"
        }
    )
    logger.info("Claude request -> %s | model=%s", url, model)
    started = time.time()
    with urllib.request.urlopen(req, timeout=LLM_TIMEOUT_SECONDS, context=ssl_context) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    content = data["content"][0]["text"]
    logger.info("Responded in %.1fs | content=%d chars", time.time() - started, len(content))
    log_payload(logger, "Claude raw output", content)
    return content

def _clean_json_output(raw_text):
    text = raw_text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?", "", text)
        text = re.sub(r"```$", "", text).strip()
    match = re.search(r"(\{.*\})", text, re.DOTALL)
    if match:
        text = match.group(1)
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        # Truncated output is the usual cause. Log the exact failure position
        # and the payload so the log file shows what the model actually sent.
        logger.error(
            "JSON parse failed at line %d column %d (char %d): %s",
            e.lineno, e.colno, e.pos, e.msg
        )
        log_payload(logger, "Unparseable model output", raw_text, limit=8000)
        raise

def generate_test_plan(provider="ollama", config=None, issues=None, context=None,
                       product_name="XSM", project_key="XSM", existing_plan=None):
    """
    Unified generator that calls the chosen provider and returns clean parsed JSON.

    When `existing_plan` is supplied the call becomes a refinement: the current
    plan is handed back to the model together with the reviewer's instructions,
    and the model revises it instead of starting over. This is what lets a user
    iterate on a plan without losing the test cases already accepted.
    """
    config = config or {}
    issues = issues or []
    base_url = config.get("base_url", "http://localhost:11434")
    model = config.get("model", "llama3.2:3b")
    api_key = config.get("api_key", "")

    # Compile user prompt
    issues_text = ""
    for idx, iss in enumerate(issues, 1):
        ac_str = "\n".join(f"  - {ac}" for ac in iss.get("acceptance_criteria", [])) or "  - [No explicit AC provided]"
        issues_text += f"""
Issue #{idx}:
- Key: {iss.get('key')} ({iss.get('type', 'Story')})
- Summary: {iss.get('summary')}
- Priority: {iss.get('priority')}
- Description: {iss.get('description')}
- Acceptance Criteria:
{ac_str}
"""

    if existing_plan:
        # Refinement pass: keep what is already good, apply the reviewer's
        # instructions, and preserve existing test case IDs so traceability
        # and any external references to TC-00x stay valid across revisions.
        prompt = f"""
Revise the EXISTING Test Plan below for:
- Product: {product_name}
- Project Key: {project_key}

REVIEWER INSTRUCTIONS (apply these):
{context or 'Improve depth, coverage and specificity throughout.'}

ORIGINAL REQUIREMENTS:
{issues_text}

EXISTING TEST PLAN (JSON):
{json.dumps(existing_plan, indent=2)}

Rules for the revision:
- Keep every existing test case that is still valid, preserving its "id".
- Apply the reviewer instructions: add missing coverage, deepen weak cases, correct inaccuracies.
- Add new test cases with new sequential ids continuing from the highest existing id.
- Keep the same JSON schema exactly. Return the COMPLETE revised plan, not a diff.
"""
    else:
        prompt = f"""
Generate a complete, structured Test Plan for:
- Product: {product_name}
- Project Key: {project_key}
- Additional Context / Focus: {context or 'Standard end-to-end regression and functional coverage.'}

JIRA ISSUES TO BE TESTED:
{issues_text}

Generate comprehensive test cases (at least 2-3 per issue covering Smoke, Positive, Negative, and Edge Cases), environments, strategy, risks, and acceptance criteria.
"""

    logger.info("-" * 70)
    logger.info(
        "generate_test_plan | mode=%s | provider=%s | model=%s | issues=%d | "
        "product=%s | project=%s | prompt=%d chars",
        "refine" if existing_plan else "new",
        provider, model, len(issues), product_name, project_key, len(prompt)
    )
    run_started = time.time()

    try:
        if provider == "ollama":
            raw_result = _call_ollama(base_url, model, prompt)
        elif provider in ("chatgpt", "groq", "grok", "openai"):
            raw_result = _call_openai_compatible(base_url, api_key, model, prompt)
        elif provider == "claude":
            raw_result = _call_claude(api_key, model, prompt)
        else:
            raise ValueError(f"Unsupported LLM provider: {provider}")

        parsed_plan = _clean_json_output(raw_result)
        # Ensure metadata is filled
        if "metadata" not in parsed_plan:
            parsed_plan["metadata"] = {}
        parsed_plan["metadata"]["product_name"] = product_name
        parsed_plan["metadata"]["project_key"] = project_key
        parsed_plan["metadata"]["llm_model"] = f"{provider} ({model})"

        # Persist intermediate copy in .tmp/
        tmp_dir = os.path.join(os.path.dirname(__file__), "..", ".tmp")
        os.makedirs(tmp_dir, exist_ok=True)
        with open(os.path.join(tmp_dir, "latest_test_plan.json"), "w", encoding="utf-8") as f:
            json.dump(parsed_plan, f, indent=2)

        logger.info(
            "Plan generated OK in %.1fs | test_cases=%d | inclusions=%d | risks=%d",
            time.time() - run_started,
            len(parsed_plan.get("test_cases", [])),
            len(parsed_plan.get("scope", {}).get("inclusions", [])),
            len(parsed_plan.get("risks_and_mitigations", []))
        )
        return {"status": "success", "plan": parsed_plan}

    except Exception as e:
        # exc_info records the full traceback in the log file; the browser
        # still gets the short message.
        logger.error(
            "Generation FAILED after %.1fs | provider=%s | model=%s | %s: %s",
            time.time() - run_started, provider, model,
            type(e).__name__, e, exc_info=True
        )
        return {
            "status": "error",
            "message": f"LLM generation failed: {str(e)}",
            "detail": f"{type(e).__name__}: {e}",
            "log_file": LOG_FILE_PATH
        }

if __name__ == "__main__":
    from jira_client import fetch_jira_issues
    print("Testing test plan generation with local Ollama...")
    sample_data = fetch_jira_issues(host="demo")["issues"][:1]
    res = generate_test_plan(
        provider="ollama",
        config={"base_url": "http://localhost:11434", "model": "llama3.2:3b"},
        issues=sample_data,
        product_name="XSM",
        project_key="XSM"
    )
    print("Status:", res.get("status"))
    if res.get("status") == "success":
        print("Generated Test Cases count:", len(res["plan"].get("test_cases", [])))
    else:
        print("Error:", res.get("message"))
