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
                    res["selected_model"] = model
                    res["model_installed"] = matched
                    if not matched:
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
    
    clean_host = host.strip().rstrip("/")
    if not clean_host.startswith("http://") and not clean_host.startswith("https://"):
        clean_host = "https://" + clean_host
        
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
            return {
                "status": "error",
                "provider": "jira",
                "host": clean_host,
                "message": f"Connection failed to {clean_host}. Error: {e.reason}"
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

def test_claude(api_key, model="claude-3-5-sonnet-20241022"):
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
