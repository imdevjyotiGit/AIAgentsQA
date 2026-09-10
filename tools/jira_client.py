"""
tools/jira_client.py
B.L.A.S.T. Phase 3 (Tools): Jira Issue Fetcher & Normalizer
Fetches user stories, bug reports, and requirements from Jira Cloud / Server.
Supports both live Jira REST API and fallback sample data for development/demo.
"""

import json
import base64
import urllib.request
import urllib.parse
import urllib.error
import ssl

ssl_context = ssl.create_default_context()

def _extract_text_from_adf(node):
    """Recursively extract plain text from Atlassian Document Format (ADF)."""
    if isinstance(node, str):
        return node
    if isinstance(node, list):
        return "\n".join(_extract_text_from_adf(item) for item in node if item)
    if isinstance(node, dict):
        text_parts = []
        if node.get("type") == "text" and "text" in node:
            return node["text"]
        if "content" in node:
            text_parts.append(_extract_text_from_adf(node["content"]))
        return "\n".join(tp for tp in text_parts if tp)
    return ""

def fetch_jira_issues(host=None, email=None, api_token=None, project_key=None, issue_keys=None, sprint=None, max_results=10):
    """
    Fetches Jira issues matching project key or specific issue keys.
    If no host or credentials provided, or if 'demo' mode requested, returns representative sample user stories.
    """
    if not host or not api_token or host.lower() == "demo":
        # Realistic sample issues for VWO/App testing
        return {
            "status": "success",
            "source": "sample_mock",
            "total": 3,
            "issues": [
                {
                    "key": f"{project_key or 'VWOAPP'}-101",
                    "type": "Story",
                    "summary": "Implement Guest and Social Authentication at Checkout",
                    "priority": "High",
                    "status": "Ready for QA",
                    "description": "As an online visitor, I want to proceed to checkout either by signing in with Google/Apple or using guest email, so that friction is minimized.",
                    "acceptance_criteria": [
                        "Guest email input validates proper RFC email format.",
                        "One-click OAuth buttons for Google and Apple redirect and exchange tokens correctly.",
                        "Existing registered users entering their email are prompted for password or magic link.",
                        "Security: Password field is masked and enforces rate limiting (5 attempts/min)."
                    ],
                    "components": ["Checkout", "Authentication"]
                },
                {
                    "key": f"{project_key or 'VWOAPP'}-102",
                    "type": "Story",
                    "summary": "Real-time Metrics Dashboard Card Aggregation",
                    "priority": "Critical",
                    "status": "In Review",
                    "description": "The analytics dashboard must display leading and lagging indicator cards with sub-2s query response time.",
                    "acceptance_criteria": [
                        "Dashboard cards render conversion rate, revenue per visitor, and bounce rate.",
                        "Data updates in real-time or upon manual refresh with active loading state.",
                        "Guardrail metric alerts fire when bounce rate exceeds baseline by 15%."
                    ],
                    "components": ["Analytics", "Dashboard UI"]
                },
                {
                    "key": f"{project_key or 'VWOAPP'}-103",
                    "type": "Bug",
                    "summary": "Cart item counter fails to increment when clicking rapid Add-to-Cart",
                    "priority": "Medium",
                    "status": "Fixed",
                    "description": "When users rapidly click 'Add to Cart' on mobile browsers, the badge counter occasionally desynchronizes.",
                    "acceptance_criteria": [
                        "Button debounces clicks while network payload is in flight.",
                        "Cart badge count matches server session state exactly."
                    ],
                    "components": ["Cart", "Mobile UI"]
                }
            ]
        }

    clean_host = host.strip().rstrip("/")
    if not clean_host.startswith("http://") and not clean_host.startswith("https://"):
        clean_host = "https://" + clean_host

    # Build auth header
    if email and email.strip():
        creds = f"{email.strip()}:{api_token.strip()}".encode("utf-8")
        auth_header = f"Basic {base64.b64encode(creds).decode('utf-8')}"
    else:
        auth_header = f"Bearer {api_token.strip()}"

    # Build JQL query
    jql_clauses = []
    if project_key:
        jql_clauses.append(f"project = '{project_key.strip()}'")
    if issue_keys:
        if isinstance(issue_keys, list):
            keys_str = ",".join(f"'{k.strip()}'" for k in issue_keys if k.strip())
        else:
            keys_str = ",".join(f"'{k.strip()}'" for k in issue_keys.split(",") if k.strip())
        jql_clauses.append(f"issueKey in ({keys_str})")
    if sprint:
        jql_clauses.append(f"sprint = '{sprint.strip()}'")

    jql = " AND ".join(jql_clauses) if jql_clauses else "order by created DESC"
    url = f"{clean_host}/rest/api/3/search?" + urllib.parse.urlencode({
        "jql": jql,
        "maxResults": max_results,
        "fields": "summary,description,issuetype,priority,status,components,customfield_*"
    })

    try:
        req = urllib.request.Request(url, headers={
            "Authorization": auth_header,
            "Accept": "application/json",
            "User-Agent": "IntelligentTestPlanner/1.0"
        })
        with urllib.request.urlopen(req, timeout=15, context=ssl_context) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            raw_issues = data.get("issues", [])
            normalized = []
            for item in raw_issues:
                fields = item.get("fields", {})
                desc_raw = fields.get("description")
                if isinstance(desc_raw, dict):
                    desc = _extract_text_from_adf(desc_raw)
                else:
                    desc = str(desc_raw or "")

                # Extract acceptance criteria from description or common custom fields
                ac_list = []
                for line in desc.split("\n"):
                    clean_l = line.strip()
                    if clean_l.startswith(("- [ ]", "- [x]", "* ", "- ", "• ")):
                        ac_list.append(clean_l.lstrip("-*• [ ]x").strip())

                normalized.append({
                    "key": item.get("key"),
                    "type": fields.get("issuetype", {}).get("name", "Story"),
                    "summary": fields.get("summary", "No summary"),
                    "priority": fields.get("priority", {}).get("name", "Medium"),
                    "status": fields.get("status", {}).get("name", "Open"),
                    "description": desc,
                    "acceptance_criteria": ac_list,
                    "components": [c.get("name") for c in fields.get("components", [])]
                })

            return {
                "status": "success",
                "source": "live_jira",
                "total": len(normalized),
                "issues": normalized
            }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to fetch Jira issues: {str(e)}"
        }

if __name__ == "__main__":
    sample = fetch_jira_issues(host="demo", project_key="VWOAPP")
    print(json.dumps(sample, indent=2))
