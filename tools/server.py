"""
tools/server.py
B.L.A.S.T. Phase 3 (Layer 2 - Navigation / Controller):
Lightweight Python server serving the frontend and orchestrating API calls.
Zero heavy frameworks needed - uses Python's standard http.server with JSON routing.
"""

import os
import sys
import json
import urllib.parse
from http.server import HTTPServer, SimpleHTTPRequestHandler

# Import Layer 3 tools
from test_connection import test_ollama, test_jira, test_openai_compatible, test_claude
from jira_client import fetch_jira_issues
from llm_generator import generate_test_plan
from test_plan_exporter import export_docx, export_xlsx, export_markdown

WEB_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "web"))
TMP_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".tmp"))
os.makedirs(TMP_DIR, exist_ok=True)

class TestPlannerRequestHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=WEB_DIR, **kwargs)

    def _send_json(self, data, status_code=200):
        body = json.dumps(data).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self):
        content_length = int(self.headers.get("Content-Length", 0))
        if content_length > 0:
            post_data = self.rfile.read(content_length)
            return json.loads(post_data.decode("utf-8"))
        return {}

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        # Download generated export files
        if parsed.path.startswith("/api/download/"):
            filename = os.path.basename(parsed.path)
            file_path = os.path.join(TMP_DIR, filename)
            if os.path.exists(file_path):
                self.send_response(200)
                if filename.endswith(".docx"):
                    self.send_header("Content-Type", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
                elif filename.endswith(".xlsx"):
                    self.send_header("Content-Type", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
                elif filename.endswith(".md"):
                    self.send_header("Content-Type", "text/markdown; charset=utf-8")
                else:
                    self.send_header("Content-Type", "application/octet-stream")
                self.send_header("Content-Disposition", f'attachment; filename="{filename}"')
                self.send_header("Content-Length", str(os.path.getsize(file_path)))
                self.end_headers()
                with open(file_path, "rb") as f:
                    self.wfile.write(f.read())
                return
            else:
                self._send_json({"status": "error", "message": "File not found"}, 404)
                return

        # Fallback to serving web frontend static files
        super().do_GET()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        try:
            req_data = self._read_json()

            # 1. Test LLM Connection
            if path == "/api/test-connection/llm":
                provider = req_data.get("provider", "ollama")
                base_url = req_data.get("base_url", "http://localhost:11434")
                api_key = req_data.get("api_key", "")
                model = req_data.get("model", "llama3.2:3b")

                if provider == "ollama":
                    res = test_ollama(base_url=base_url, model=model)
                elif provider in ("chatgpt", "openai"):
                    res = test_openai_compatible("ChatGPT", base_url or "https://api.openai.com/v1", api_key, model or "gpt-4o-mini")
                elif provider == "groq":
                    res = test_openai_compatible("Groq", base_url or "https://api.groq.com/openai/v1", api_key, model or "llama-3.3-70b-versatile")
                elif provider == "grok":
                    res = test_openai_compatible("Grok", base_url or "https://api.x.ai/v1", api_key, model or "grok-2")
                elif provider == "claude":
                    res = test_claude(api_key, model or "claude-3-5-sonnet-20241022")
                else:
                    res = {"status": "error", "message": f"Unknown provider: {provider}"}
                self._send_json(res)
                return

            # 2. Test Jira Connection
            if path == "/api/test-connection/jira":
                host = req_data.get("host", "")
                email = req_data.get("email", "")
                api_token = req_data.get("api_token", "")
                if host.lower() == "demo":
                    res = {"status": "success", "provider": "jira", "user": "Demo QA Engineer", "message": "Demo mode active! Ready to fetch mock Jira requirements."}
                else:
                    res = test_jira(host, email, api_token)
                self._send_json(res)
                return

            # 3. Fetch Jira Issues
            if path == "/api/fetch-issues":
                host = req_data.get("host", "")
                email = req_data.get("email", "")
                api_token = req_data.get("api_token", "")
                project_key = req_data.get("project_key", "")
                issue_keys = req_data.get("issue_keys", "")
                sprint = req_data.get("sprint", "")
                res = fetch_jira_issues(host=host, email=email, api_token=api_token, project_key=project_key, issue_keys=issue_keys, sprint=sprint)
                self._send_json(res)
                return

            # 4. Generate Test Plan
            if path == "/api/generate-plan":
                provider = req_data.get("provider", "ollama")
                config = req_data.get("config", {})
                issues = req_data.get("issues", [])
                context = req_data.get("context", "")
                product_name = req_data.get("product_name", "VWO Platform")
                project_key = req_data.get("project_key", "VWOAPP")
                res = generate_test_plan(
                    provider=provider,
                    config=config,
                    issues=issues,
                    context=context,
                    product_name=product_name,
                    project_key=project_key
                )
                self._send_json(res)
                return

            # 5. Export Test Plan
            if path == "/api/export":
                plan = req_data.get("plan", {})
                format_type = req_data.get("format", "docx")
                template_type = req_data.get("template_type", "inbuilt")
                safe_name = plan.get("metadata", {}).get("project_key", "TEST_PLAN").replace(" ", "_")

                if format_type == "docx":
                    fname = f"{safe_name}_TestPlan.docx"
                    out_path = os.path.join(TMP_DIR, fname)
                    export_docx(plan, out_path)
                elif format_type == "xlsx":
                    fname = f"{safe_name}_TestPlan.xlsx"
                    out_path = os.path.join(TMP_DIR, fname)
                    export_xlsx(plan, out_path, template_type=template_type)
                elif format_type == "md":
                    fname = f"{safe_name}_TestPlan.md"
                    out_path = os.path.join(TMP_DIR, fname)
                    export_markdown(plan, out_path)
                else:
                    self._send_json({"status": "error", "message": f"Unsupported format: {format_type}"}, 400)
                    return

                self._send_json({
                    "status": "success",
                    "filename": fname,
                    "download_url": f"/api/download/{fname}"
                })
                return

            self._send_json({"status": "error", "message": "Unknown endpoint"}, 404)

        except Exception as e:
            self._send_json({"status": "error", "message": str(e)}, 500)

def run_server(port=8088):
    server_address = ("127.0.0.1", port)
    httpd = HTTPServer(server_address, TestPlannerRequestHandler)
    print(f"Test Planner Agent Server running at: http://127.0.0.1:{port}")
    httpd.serve_forever()

if __name__ == "__main__":
    port = 8088
    if len(sys.argv) > 1:
        port = int(sys.argv[1])
    run_server(port)
