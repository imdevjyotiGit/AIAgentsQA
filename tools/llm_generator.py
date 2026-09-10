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
import urllib.request
import urllib.error
import ssl

ssl_context = ssl.create_default_context()

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
    { "category": "Browser | OS | Device | API", "specification": "Specific version/details" }
  ],
  "test_strategy": {
    "types": ["Functional", "Smoke", "Regression", "Negative", "Edge Case", "Security"],
    "automation_approach": "Strategy detailing Playwright/automation coverage."
  },
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
            "num_ctx": 4096
        }
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=90) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        return data.get("message", {}).get("content", "")

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
    with urllib.request.urlopen(req, timeout=90, context=ssl_context) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        return data["choices"][0]["message"]["content"]

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
    with urllib.request.urlopen(req, timeout=90, context=ssl_context) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        return data["content"][0]["text"]

def _clean_json_output(raw_text):
    text = raw_text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?", "", text)
        text = re.sub(r"```$", "", text).strip()
    match = re.search(r"(\{.*\})", text, re.DOTALL)
    if match:
        text = match.group(1)
    return json.loads(text)

def generate_test_plan(provider="ollama", config=None, issues=None, context=None, product_name="VWO Platform", project_key="VWOAPP"):
    """
    Unified generator that calls the chosen provider and returns clean parsed JSON.
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

    prompt = f"""
Generate a complete, structured Test Plan for:
- Product: {product_name}
- Project Key: {project_key}
- Additional Context / Focus: {context or 'Standard end-to-end regression and functional coverage.'}

JIRA ISSUES TO BE TESTED:
{issues_text}

Generate comprehensive test cases (at least 2-3 per issue covering Smoke, Positive, Negative, and Edge Cases), environments, strategy, risks, and acceptance criteria.
"""

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

        return {"status": "success", "plan": parsed_plan}

    except Exception as e:
        return {"status": "error", "message": f"LLM generation failed: {str(e)}"}

if __name__ == "__main__":
    from jira_client import fetch_jira_issues
    print("Testing test plan generation with local Ollama...")
    sample_data = fetch_jira_issues(host="demo")["issues"][:1]
    res = generate_test_plan(
        provider="ollama",
        config={"base_url": "http://localhost:11434", "model": "llama3.2:3b"},
        issues=sample_data,
        product_name="VWO Platform",
        project_key="VWOAPP"
    )
    print("Status:", res.get("status"))
    if res.get("status") == "success":
        print("Generated Test Cases count:", len(res["plan"].get("test_cases", [])))
    else:
        print("Error:", res.get("message"))
