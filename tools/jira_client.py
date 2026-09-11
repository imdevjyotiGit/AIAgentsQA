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

from test_connection import normalize_jira_host
from agent_logger import get_logger

logger = get_logger("jira_client")

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
        # Representative sample issues for XSM (service management) testing.
        return {
            "status": "success",
            "source": "sample_mock",
            "total": 3,
            "issues": [
                {
                    "key": f"{project_key or 'XSM'}-101",
                    "type": "Story",
                    "summary": "Enforce Test Task planned dates within the Change Testing Window",
                    "priority": "High",
                    "status": "Ready for QA",
                    "description": "As a Change Manager, I want Test Task planned dates to be constrained to the Testing Window defined on the Change request, so that test scheduling cannot drift outside the approved window.",
                    "acceptance_criteria": [
                        "Enabling 'Testing Required' on a Change reveals Testing Start Date and Testing End Date fields.",
                        "Default Test Tasks inherit the Planned Start and Planned End dates from the Change Testing Window.",
                        "Saving a Test Task with dates outside the Testing Window is blocked with a validation error.",
                        "Testing End Date cannot be earlier than Testing Start Date."
                    ],
                    "components": ["Change Management", "Test Tasks"]
                },
                {
                    "key": f"{project_key or 'XSM'}-102",
                    "type": "Story",
                    "summary": "Incident priority derived from Impact and Urgency matrix",
                    "priority": "Critical",
                    "status": "In Review",
                    "description": "As a Service Desk agent, I want Incident priority to be calculated automatically from the Impact and Urgency matrix, so that SLA targets are applied consistently.",
                    "acceptance_criteria": [
                        "Selecting Impact and Urgency sets Priority per the configured matrix without manual entry.",
                        "Changing either value recalculates Priority and the attached SLA target.",
                        "Manual Priority override is restricted to users holding the Incident Manager role.",
                        "The SLA timer starts on ticket creation and pauses while the ticket is On Hold."
                    ],
                    "components": ["Incident Management", "SLA"]
                },
                {
                    "key": f"{project_key or 'XSM'}-103",
                    "type": "Bug",
                    "summary": "Approval notification is not resent after an approver is reassigned",
                    "priority": "Medium",
                    "status": "Fixed",
                    "description": "When an approver is reassigned on a pending Service Request, the new approver receives no notification and the request stalls in Pending Approval.",
                    "acceptance_criteria": [
                        "Reassigning an approver sends the approval notification to the new approver.",
                        "The audit trail records the reassignment with actor, timestamp, and reason.",
                        "The previous approver can no longer action the request."
                    ],
                    "components": ["Service Requests", "Notifications"]
                }
            ]
        }

    clean_host = normalize_jira_host(host)

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

    # Atlassian REMOVED GET /rest/api/3/search on Jira Cloud - it now answers
    # 410 Gone. The replacement is /rest/api/3/search/jql. Jira Server/Data
    # Center never got that endpoint and still serves the classic /search,
    # so try the modern Cloud path first and fall back for on-prem.
    #
    # Note: the new endpoint takes an explicit field list - the old
    # "customfield_*" wildcard is not accepted.
    fields_param = "summary,description,issuetype,priority,status,components,labels"
    query = urllib.parse.urlencode({
        "jql": jql,
        "maxResults": max_results,
        "fields": fields_param
    })
    candidate_urls = [
        f"{clean_host}/rest/api/3/search/jql?{query}",  # Jira Cloud (current)
        f"{clean_host}/rest/api/2/search?{query}",      # Jira Server / DC
    ]

    try:
        data = None
        last_http_error = None
        for url in candidate_urls:
            req = urllib.request.Request(url, headers={
                "Authorization": auth_header,
                "Accept": "application/json",
                "User-Agent": "IntelligentTestPlanner/1.0"
            })
            try:
                with urllib.request.urlopen(req, timeout=20, context=ssl_context) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                logger.info("Jira issues fetched via %s", url.split("?")[0])
                break
            except urllib.error.HTTPError as he:
                # 410 Gone / 404 Not Found mean "wrong endpoint for this
                # deployment" - try the next candidate. Auth and syntax
                # errors are real and must surface immediately.
                last_http_error = he
                logger.warning(
                    "Jira endpoint %s returned HTTP %s (%s)",
                    url.split("?")[0], he.code, he.reason
                )
                if he.code in (404, 410):
                    continue
                raise

        if data is None:
            if last_http_error is not None:
                raise last_http_error
            raise RuntimeError("No Jira search endpoint responded.")

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
                "type": (fields.get("issuetype") or {}).get("name", "Story"),
                "summary": fields.get("summary", "No summary"),
                "priority": (fields.get("priority") or {}).get("name", "Medium"),
                "status": (fields.get("status") or {}).get("name", "Open"),
                "description": desc,
                "acceptance_criteria": ac_list,
                "components": [c.get("name") for c in (fields.get("components") or [])]
            })

        logger.info("Normalized %d Jira issue(s)", len(normalized))
        return {
            "status": "success",
            "source": "live_jira",
            "total": len(normalized),
            "issues": normalized
        }
    except urllib.error.HTTPError as e:
        body = ""
        try:
            body = e.read().decode("utf-8")[:300]
        except Exception:
            pass
        logger.error("Jira fetch failed: HTTP %s %s | %s", e.code, e.reason, body)
        if e.code == 410:
            msg = ("Jira returned 410 Gone - this Jira Cloud site no longer serves "
                   "the legacy search endpoint. The client now calls "
                   "/rest/api/3/search/jql; if you still see this, the site may "
                   "require an updated API token scope.")
        elif e.code in (401, 403):
            msg = (f"Jira authentication failed (HTTP {e.code}). Check the email "
                   "and API token, and that the token has read access to this project.")
        elif e.code == 400:
            msg = f"Jira rejected the JQL query (HTTP 400). {body}"
        else:
            msg = f"Failed to fetch Jira issues: HTTP {e.code} {e.reason}. {body}"
        return {"status": "error", "message": msg}
    except Exception as e:
        logger.error("Jira fetch failed: %s", e, exc_info=True)
        return {
            "status": "error",
            "message": f"Failed to fetch Jira issues: {str(e)}"
        }

if __name__ == "__main__":
    sample = fetch_jira_issues(host="demo", project_key="XSM")
    print(json.dumps(sample, indent=2))
