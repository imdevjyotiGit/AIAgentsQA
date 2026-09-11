"""
tools/test_connection.py
B.L.A.S.T. Phase 2: Link Verification Tool
Unified connection tester for Jira, Ollama, Groq, Grok, ChatGPT, and Claude.
"""

import sys
import json
import base64
import urllib.request
import urllib.error
import ssl

# Default SSL context (allows secure https)
ssl_context = ssl.create_default_context()


def normalize_jira_host(host):
    """
    Normalizes user-entered Jira hosts into a resolvable base URL.

    Accepts 'mysite', 'mysite.atlassian.net', or a full 'https://jira.company.com'.
    A bare single-label name (no dot) is assumed to be an Atlassian Cloud site name,
    since that is the most common entry mistake — typing the site or project name
    alone produces an unresolvable host like 'https://mysite'.
    """
    clean = (host or "").strip().rstrip("/")
    if not clean:
        return clean
    if not clean.startswith("http://") and not clean.startswith("https://"):
        # Bare name with no domain part -> assume Atlassian Cloud
        if "." not in clean.split("/")[0]:
            clean = f"{clean}.atlassian.net"
        clean = "https://" + clean
    return clean

def test_ollama(base_url="http://localhost:11434", model=None):
    """Verifies local Ollama service availability and installed models."""
    base = base_url.rstrip("/")
    url = f"{base}/api/tags"
    try:
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=5) as response:
            if response.status == 200:
                data = json.loads(response.read().decode("utf-8"))
                models = [m.get("name") for m in data.get("models", [])]
                res = {
                    "status": "success",
                    "provider": "ollama",
                    "base_url": base,
                    "available_models": models,
                    "message": f"Ollama online! Found {len(models)} installed model(s)."
                }
                if model:
                    matched = any(m == model or m.startswith(f"{model}:") for m in models)
                    # Ollama Cloud models (the "-cloud" suffix) execute on
                    # Ollama's servers and never appear in local /api/tags, so
                    # a missing entry is expected rather than a misconfiguration.
                    is_cloud = model.endswith("-cloud")
                    res["selected_model"] = model
                    res["model_installed"] = matched
                    res["is_cloud_model"] = is_cloud
                    if is_cloud:
                        res["message"] = (
                            f"Ollama online. '{model}' is a CLOUD model - it runs on "
                            "Ollama's servers, so prompt text leaves this machine."
                        )
                    elif not matched:
                        res["warning"] = f"Model '{model}' is not listed in local Ollama tags. Available: {', '.join(models)}"
                return res
    except urllib.error.URLError as e:
        return {
            "status": "error",
            "provider": "ollama",
            "base_url": base,
            "message": f"Could not reach Ollama at {base}. Is the Ollama desktop app or service running? Error: {e.reason}"
        }
    except Exception as e:
        return {
            "status": "error",
            "provider": "ollama",
            "base_url": base,
            "message": f"Unexpected error checking Ollama: {str(e)}"
        }

def test_jira(host, email, api_token):
    """Verifies Jira credentials by calling the Jira /rest/api/3/myself endpoint."""
    if not host or not api_token:
        return {"status": "error", "provider": "jira", "message": "Jira URL and API Token are required."}
    
    clean_host = normalize_jira_host(host)

    auth_header = None
    if email and email.strip():
        # Cloud Basic Auth (email:api_token)
        creds = f"{email.strip()}:{api_token.strip()}".encode("utf-8")
        auth_header = f"Basic {base64.b64encode(creds).decode('utf-8')}"
    else:
        # Personal Access Token (Bearer token)
        auth_header = f"Bearer {api_token.strip()}"
        
    endpoints = [
        f"{clean_host}/rest/api/3/myself",
        f"{clean_host}/rest/api/2/myself"
    ]
    
    last_error = None
    for url in endpoints:
        try:
            req = urllib.request.Request(url, headers={
                "Authorization": auth_header,
                "Accept": "application/json",
                "User-Agent": "IntelligentTestPlanner/1.0"
            })
            with urllib.request.urlopen(req, timeout=10, context=ssl_context) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode("utf-8"))
                    display_name = data.get("displayName") or data.get("name") or "Authenticated User"
                    return {
                        "status": "success",
                        "provider": "jira",
                        "host": clean_host,
                        "user": display_name,
                        "email": data.get("emailAddress", email),
                        "message": f"Successfully connected to Jira as {display_name}."
                    }
        except urllib.error.HTTPError as e:
            last_error = f"HTTP {e.code}: {e.reason}"
            if e.code in (401, 403):
                return {
                    "status": "error",
                    "provider": "jira",
                    "host": clean_host,
                    "message": f"Authentication failed ({last_error}). Verify your email and API Token."
                }
        except urllib.error.URLError as e:
            reason = str(e.reason)
            # getaddrinfo/DNS failures almost always mean the site URL is wrong,
            # so give an actionable hint instead of the raw socket error.
            if "getaddrinfo" in reason or "Name or service not known" in reason:
                hint = (
                    f"Host '{clean_host}' could not be resolved (DNS lookup failed). "
                    "Enter the full Jira base URL, e.g. https://hclsw-io.atlassian.net "
                    "for Jira Cloud or https://jira.your-company.com for Jira Server/Data Center. "
                    "This should be the site URL, not the project key."
                )
            else:
                hint = f"Connection failed to {clean_host}. Error: {reason}"
            return {
                "status": "error",
                "provider": "jira",
                "host": clean_host,
                "message": hint
            }
        except Exception as e:
            last_error = str(e)
            
    return {
        "status": "error",
        "provider": "jira",
        "host": clean_host,
        "message": f"Could not connect to Jira API ({last_error})."
    }

def test_openai_compatible(provider_name, base_url, api_key, model):
    """Verifies connection to OpenAI-compatible APIs (Groq, Grok, ChatGPT)."""
    if not api_key:
        return {"status": "error", "provider": provider_name, "message": f"API Key required for {provider_name}."}
    
    clean_url = base_url.rstrip("/")
    endpoint = f"{clean_url}/chat/completions"
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": "ping"}],
        "max_tokens": 5
    }
    
    try:
        req = urllib.request.Request(
            endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {api_key.strip()}",
                "Content-Type": "application/json",
                "User-Agent": "IntelligentTestPlanner/1.0"
            }
        )
        with urllib.request.urlopen(req, timeout=12, context=ssl_context) as resp:
            if resp.status == 200:
                data = json.loads(resp.read().decode("utf-8"))
                return {
                    "status": "success",
                    "provider": provider_name,
                    "model": model,
                    "message": f"Successfully connected to {provider_name} using model {model}."
                }
    except urllib.error.HTTPError as e:
        err_body = ""
        try:
            err_body = e.read().decode("utf-8")
        except:
            pass
        return {
            "status": "error",
            "provider": provider_name,
            "message": f"API returned error {e.code} ({e.reason}): {err_body[:200]}"
        }
    except Exception as e:
        return {
            "status": "error",
            "provider": provider_name,
            "message": f"Connection failed: {str(e)}"
        }

def test_claude(api_key, model="claude-sonnet-5"):
    """Verifies connection to Anthropic Claude API."""
    if not api_key:
        return {"status": "error", "provider": "claude", "message": "Anthropic API Key required."}
    
    endpoint = "https://api.anthropic.com/v1/messages"
    payload = {
        "model": model,
        "max_tokens": 5,
        "messages": [{"role": "user", "content": "ping"}]
    }
    try:
        req = urllib.request.Request(
            endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "x-api-key": api_key.strip(),
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json"
            }
        )
        with urllib.request.urlopen(req, timeout=12, context=ssl_context) as resp:
            if resp.status == 200:
                return {
                    "status": "success",
                    "provider": "claude",
                    "model": model,
                    "message": f"Successfully connected to Anthropic Claude ({model})."
                }
    except urllib.error.HTTPError as e:
        err_body = ""
        try:
            err_body = e.read().decode("utf-8")
        except:
            pass
        return {
            "status": "error",
            "provider": "claude",
            "message": f"Anthropic API returned error {e.code}: {err_body[:200]}"
        }
    except Exception as e:
        return {
            "status": "error",
            "provider": "claude",
            "message": f"Connection failed: {str(e)}"
        }

if __name__ == "__main__":
    # If run directly as a CLI verification: test local Ollama by default
    print("Testing local Ollama connection...")
    result = test_ollama(model="llama3.2:3b")
    print(json.dumps(result, indent=2))
