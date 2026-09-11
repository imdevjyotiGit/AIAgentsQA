# Deployment Guide
## Intelligent Test Planning Agent

Two ways to run this: **local** (one person, on their own machine) and **server**
(hosted for the team). Start with local — server hosting is the same app with a
container around it.

---

# Part A — Local hosting (single user)

## A1. Prerequisites

| Requirement | Check it with | If missing |
|---|---|---|
| Python 3.10+ | `python --version` | https://www.python.org/downloads/ |
| Ollama | `ollama --version` | https://ollama.com/download |

> On Windows, Ollama installs to `%LOCALAPPDATA%\Programs\Ollama\ollama.exe` and may
> not be on your PATH. Use the full path, or reopen your terminal after installing.

## A2. Install Python dependencies

```bash
pip install -r requirements.txt
```

Installs `python-docx` and `openpyxl` (used for Word and Excel export). Everything
else uses the Python standard library.

## A3. Pull a model

Ollama must be running — the desktop app starts it automatically; otherwise run
`ollama serve`.

```bash
ollama pull gemma4:26b        # recommended: good quality, stays on your machine
# or
ollama pull llama3.2:3b       # ~2 GB, fast but produces thin plans
```

Verify it registered:

```bash
ollama list
```

## A4. Start the app

```bash
python tools/server.py 8088
```

You should see:

```
Test Planner Agent Server running at: http://127.0.0.1:8088 (bound to 127.0.0.1)
```

## A5. Open it

Go to **http://127.0.0.1:8088**

## A6. First run

1. **Step 1 — Setup**
   - LLM Provider: `Ollama`, Model: the model you pulled, Base URL: `http://localhost:11434`
   - Click **Test Connection** → expect green
   - Jira Host: `https://hclsw-io.atlassian.net`, your email, your API token → **Test Jira Connection**
   - No Jira? Put `demo` in the host field to use built-in XSM sample issues.
2. **Step 2 — Requirements**: fetch from Jira, or write a story directly.
3. **Step 3 — Review**: tick the issues you want, add context.
4. **Step 4 — Generate**, then refine or export.

## A7. Stopping it

`Ctrl+C` in the terminal.

## A8. Local troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `Could not reach Ollama` | Ollama not running | Start the Ollama app, or `ollama serve` |
| Generation times out | Model too slow for the timeout | `set LLM_TIMEOUT_SECONDS=1200` (Windows) / `export …` (macOS/Linux) before starting |
| `LLM generation failed` | Varies | Read `logs/agent.log` — it records the request, token counts, raw model output, and the full traceback |
| Jira `410 Gone` | Legacy Atlassian endpoint | Already handled; ensure the host is the **site URL**, not a project key |
| Jira `getaddrinfo failed` | Host is not resolvable | Use the full URL: `https://hclsw-io.atlassian.net` |
| UI changes don't appear | Browser cache | Hard refresh: `Ctrl+Shift+R` |
| Port already in use | Another instance running | `python tools/server.py 8090` |

---

# Part B — Server hosting (team)

> ⚠️ **Read this first.** The app has **no authentication**. Anyone who can reach the
> port can use it. Do not expose it to an untrusted network until you have put SSO or a
> reverse proxy with auth in front of it. See §B6.

## B1. Prerequisites

| Requirement | Check it with |
|---|---|
| Docker Engine 20.10+ | `docker --version` |
| Docker Compose v2 | `docker compose version` |

## B2. Choose where Ollama runs

This decides one setting — the Base URL users enter in the UI.

| Option | Base URL to use | When |
|---|---|---|
| **1. Ollama in the same compose stack** | `http://ollama:11434` | Simplest; self-contained |
| **2. Ollama on the host machine** | `http://host.docker.internal:11434` | You already run Ollama there |
| **3. Ollama on another server** | `http://<that-host>:11434` | Shared GPU box |

## B3. Deploy

**Option 1 — bundled Ollama (recommended to start):**

```bash
docker compose --profile with-ollama up -d --build
```

Then pull a model into the Ollama container (one time, persists in a volume):

```bash
docker exec -it test-planning-ollama ollama pull gemma4:26b
```

**Option 2 — use an existing Ollama:**

```bash
docker compose up -d --build
```

## B4. Verify

```bash
docker compose ps                                  # both services "running"/"healthy"
curl http://localhost:8088/health                  # {"status":"ok",...}
docker compose logs -f agent                       # follow logs
```

Open **http://\<server-ip\>:8088**

## B5. Configuration

Create a `.env` next to `docker-compose.yml` to override defaults:

```bash
APP_PORT=8088              # host port to publish
LLM_TIMEOUT_SECONDS=900    # raise for large/slow models
OLLAMA_NUM_CTX=16384       # context window
APP_VERSION=1.0.0          # surfaced by /health
```

Apply with `docker compose up -d`.

## B6. Put authentication in front of it — required

The app itself has none. Minimum viable protection is a reverse proxy. Example nginx
with basic auth (replace with your SSO where possible):

```nginx
server {
    listen 80;
    server_name testplanner.internal;

    auth_basic "Test Planning Agent";
    auth_basic_user_file /etc/nginx/.htpasswd;

    location / {
        proxy_pass http://127.0.0.1:8088;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;

        # A plan can take several minutes - default 60s would cut it off.
        proxy_read_timeout 900s;
        proxy_send_timeout 900s;
    }
}
```

Bind the app to localhost only so it cannot be reached bypassing the proxy — publish
`127.0.0.1:8088:8088` instead of `8088:8088` in `docker-compose.yml`.

## B7. Updating

```bash
git pull
docker compose up -d --build
curl http://localhost:8088/health
```

## B8. Data and persistence

| Volume | Contents | Notes |
|---|---|---|
| `agent-exports` | Generated `.docx` / `.xlsx` / `.md` | Safe to prune periodically |
| `agent-logs` | `agent.log` | **Contains full requirement text** — apply your retention policy |
| `ollama-models` | Downloaded models | Multi-GB; keep to avoid re-pulling |

Back up or inspect:

```bash
docker run --rm -v agent-exports:/data -v "$PWD":/backup alpine \
  tar czf /backup/exports-backup.tar.gz -C /data .
```

## B9. Server troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| Port unreachable from other machines | Bound to loopback | `HOST=0.0.0.0` is set in the image; check the host firewall and the compose port mapping |
| Container restarting | Health check failing | `docker compose logs agent` |
| `Could not reach Ollama` from container | Wrong Base URL | Use the table in §B2 — `localhost` inside a container means the container itself |
| Generation cut off at ~60s | Proxy timeout | Raise `proxy_read_timeout` (§B6) |
| Slow with several users | Model server saturated | Ollama serialises work; give it a GPU or run more replicas |

---

# Part C — CI/CD (Jenkins)

`Jenkinsfile` runs: checkout → compile + committed-secret scan → import smoke test →
docker build → container health smoke test → push → deploy.

**One-time Jenkins setup**

1. Create a Pipeline job pointing at this repository.
2. Add a **Username/Password** credential with ID `registry-credentials` for your
   container registry.
3. Set `DOCKER_REGISTRY` as an environment variable (or edit the default in the
   `environment` block).
4. Ensure the Jenkins agent has Docker and can run `docker build`.

Push and deploy stages run on `main` only. No application secrets are needed at build
time — Jira and LLM credentials are entered per user at runtime.

---

# Appendix — Environment variables

| Variable | Default | Effect |
|---|---|---|
| `HOST` | `127.0.0.1` | Bind address. Must be `0.0.0.0` in a container |
| `PORT` | `8088` | Listen port |
| `LLM_TIMEOUT_SECONDS` | `600` | Per-generation timeout |
| `OLLAMA_NUM_CTX` | `16384` | Context window; too small silently truncates output |
| `APP_VERSION` | `dev` | Reported by `/health` |
