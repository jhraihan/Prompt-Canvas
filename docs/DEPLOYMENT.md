# Deploying Prompt Canvas

## Target

| Piece | Where | Address |
|---|---|---|
| React SPA | Vercel | `https://<APP_DOMAIN>` |
| Django API | Hostinger VPS `<VPS_IP>` | `https://<API_DOMAIN>` |
| Generated images | Same VPS, served by nginx from disk | `https://<API_DOMAIN>/media/…` |
| PostgreSQL | Same VPS, bound to localhost | not reachable from the internet |

The VPS runs **Ubuntu 24.04 with CloudPanel**. CloudPanel owns nginx, so the
site is created through its UI and Prompt Canvas slots in behind a reverse proxy on
`127.0.0.1:8021`. Do not hand-write files into `/etc/nginx/sites-available` on
this box — CloudPanel regenerates them.

Because the SPA and the API sit on different origins, every API call is
cross-site. That single fact drives the cookie flags, the CORS list, and the
Origin check. Part 5 explains why each is what it is.

---

## Before you start

Fill these in once and substitute them wherever this guide shows a placeholder.

| Placeholder | Meaning | Example |
|---|---|---|
| `<API_DOMAIN>` | Domain serving the Django API | `api.promptcanvas.example.com` |
| `<APP_DOMAIN>` | Domain serving the React SPA | `promptcanvas.example.com` |
| `<VPS_IP>` | Public IP of your VPS | `203.0.113.10` |
| `<SITE_USER>` | CloudPanel site user | `prompt-canvas` |

### Checklist

| Step | Owner |
|---|---|
| DNS: `A` record `<API_DOMAIN>` → `<VPS_IP>` (TTL 300) | You, before Part 1 |
| DNS for `<APP_DOMAIN>` | Vercel creates it when you attach the domain (Part 4). If your apex is not on Vercel's nameservers, add the `CNAME` Vercel shows you |
| CloudPanel site + TLS | You (Part 1) |
| VPS bootstrap | You (Part 2) |
| GitHub repo, variables, secrets, deploy key | You (Part 3) |
| Vercel project + domain | You (Part 4) |

> Verify DNS has propagated before issuing TLS — Let's Encrypt validates over
> HTTP and will fail if the record has not landed yet:
> `dig +short <API_DOMAIN>` should return `<VPS_IP>`.

---

## Part 1 — Create the site in CloudPanel

1. Open CloudPanel (usually `https://<VPS_IP>:8443`).
2. **Sites → Add Site → Create a Reverse Proxy.**

   | Field | Value |
   |---|---|
   | Domain Name | `<API_DOMAIN>` |
   | Reverse Proxy URL | `http://127.0.0.1:8021` |
   | Site User | `prompt-canvas` |

3. Note the site user password CloudPanel shows you.

This creates the Linux user `prompt-canvas`, the directory
`/home/prompt-canvas/htdocs/<API_DOMAIN>`, and an nginx vhost.
Nothing is listening on 8021 yet, so the site will 502 until Part 2 finishes.
That is expected.

---

## Part 2 — Bootstrap the backend

The script carries no host-specific values. It reads them from the
environment, which is why `sudo -E` (preserve environment) is required:

| Variable | Required | Meaning |
|---|---|---|
| `API_DOMAIN` | **Yes** | Domain serving the API |
| `APP_ORIGIN` | **Yes** | Frontend origin, scheme included |
| `REPO_URL` | First run | Repository to clone |
| `SITE_USER` | No | CloudPanel site user (default `prompt-canvas`) |
| `GUNICORN_PORT` | No | Reverse-proxy port (default `8021`) |
| `GIT_BRANCH` | No | Branch to deploy (default `main`) |

Reading it first is recommended — it touches PostgreSQL, systemd, and sudoers:

```bash
ssh root@<VPS_IP>

git clone https://github.com/YOUR_USER/prompt-canvas.git /tmp/promptcanvas
less /tmp/promptcanvas/deploy/bootstrap.sh

API_DOMAIN=<API_DOMAIN> \
APP_ORIGIN=https://<APP_DOMAIN> \
REPO_URL=https://github.com/YOUR_USER/prompt-canvas.git \
  sudo -E bash /tmp/promptcanvas/deploy/bootstrap.sh
```

It is idempotent — re-running it is safe, and it never overwrites an existing
`.env`. It:

- installs PostgreSQL, Python build tools, and git
- creates the `promptcanvas` role and `promptcanvas` database with a generated password
- clones the repo into the CloudPanel site directory
- builds the virtualenv and installs `requirements.txt`
- writes `backend/.env` (mode 600) with a fresh `DJANGO_SECRET_KEY`
- runs `migrate` and `collectstatic`
- installs and starts the `promptcanvas-api` systemd unit on `127.0.0.1:8021`
- installs `/home/prompt-canvas/deploy.sh` for CI to call
- grants the site user password-less sudo for **exactly** `systemctl restart
  promptcanvas-api` and nothing else
- schedules the weekly expired-token cleanup
- health-checks gunicorn before declaring success

### 2a. Add the media and static location blocks

CloudPanel's vhost proxies everything to gunicorn. Serving 1.5 MB PNGs through
Python is wasteful, so hand `/media/` and `/static/` to nginx:

**CloudPanel → Sites → <API_DOMAIN> → Vhost.** Paste the two
blocks from [`deploy/cloudpanel-vhost.conf`](../deploy/cloudpanel-vhost.conf)
above the existing `location /` block, then save.

While in that editor, raise the timeout on the main `location /` block:

```nginx
proxy_read_timeout 180s;
proxy_send_timeout 180s;
```

CloudPanel's default is 60s. A cold FLUX model regularly takes longer, and
without this you get a 504 while the image is still being generated.

### 2b. Issue the certificate

**CloudPanel → Sites → <API_DOMAIN> → SSL/TLS → Let's Encrypt →
Issue.**

The A record already resolves, so validation should pass immediately.

### 2c. Create your admin account

```bash
cd /home/prompt-canvas/htdocs/<API_DOMAIN>/backend
sudo -u prompt-canvas DJANGO_SETTINGS_MODULE=config.settings.prod \
  .venv/bin/python manage.py createsuperuser
```

### 2d. Add the Hugging Face token

Bootstrap leaves `IMAGE_PROVIDER=stub`, so the API works end to end from the
first minute, generating placeholder gradients. To switch to real generation:

```bash
sudo nano /home/prompt-canvas/htdocs/<API_DOMAIN>/backend/.env
```

```bash
HF_TOKEN=hf_your_real_token
IMAGE_PROVIDER=huggingface
```

Verify the credential **before** restarting:

```bash
cd /home/prompt-canvas/htdocs/<API_DOMAIN>/backend
sudo -u prompt-canvas DJANGO_SETTINGS_MODULE=config.settings.prod \
  .venv/bin/python manage.py check_provider
sudo systemctl restart promptcanvas-api
```

`check_provider` prints the provider, model, sampler settings, byte count, and
elapsed time. It never prints the token.

### 2e. Confirm

```bash
curl https://<API_DOMAIN>/api/health/
# {"status":"ok"}
```

---

## Part 3 — GitHub

### 3a. Create the deploy key

The CI job SSHes in as `prompt-canvas`. Give it a dedicated key that exists for
nothing else. Generate it **on your machine**, not on the server:

```bash
ssh-keygen -t ed25519 -N "" -C "prompt-canvas-github-actions" -f ~/.ssh/pc_deploy
```

Install the public half on the VPS:

```bash
ssh root@<VPS_IP> 'mkdir -p /home/prompt-canvas/.ssh && chmod 700 /home/prompt-canvas/.ssh'
ssh-copy-id -i ~/.ssh/pc_deploy.pub -o 'User=root' prompt-canvas@<VPS_IP> 2>/dev/null || \
  cat ~/.ssh/pc_deploy.pub | ssh root@<VPS_IP> \
    'cat >> /home/prompt-canvas/.ssh/authorized_keys &&
     chown -R prompt-canvas:prompt-canvas /home/prompt-canvas/.ssh &&
     chmod 600 /home/prompt-canvas/.ssh/authorized_keys'
```

Capture the host key so CI is not trusting whatever answers on the day:

```bash
ssh-keyscan -H <VPS_IP>
```

### 3b. Add the variables

The deploy workflow reads the two public origins from repository **variables**,
not from literals in the tree, so a new environment needs no code change.

**Settings → Secrets and variables → Actions → Variables → New repository
variable.**

| Variable | Value | Notes |
|---|---|---|
| `API_ORIGIN` | `https://<API_DOMAIN>` | No trailing slash |
| `APP_ORIGIN` | `https://<APP_DOMAIN>` | No trailing slash |
| `DEPLOY_SCRIPT_PATH` | `~/deploy.sh` | Optional; only if you changed `SITE_USER` |

These are public values — the API origin is compiled into the client bundle
regardless — so a variable is correct here and a secret would be wrong: masked
secrets break the bundle-verification step that greps the built assets.

### 3c. Add the secrets

**Settings → Secrets and variables → Actions → New repository secret.**

| Secret | Value |
|---|---|
| `VPS_HOST` | `<VPS_IP>` |
| `VPS_USER` | `<SITE_USER>` |
| `VPS_PORT` | `22` (omit if 22) |
| `VPS_SSH_KEY` | Full contents of `~/.ssh/pc_deploy` — the **private** key, including the BEGIN/END lines |
| `VPS_HOST_KEY` | Output of the `ssh-keyscan` above (optional but recommended) |
| `VERCEL_TOKEN` | Vercel → Account Settings → Tokens → Create |
| `VERCEL_ORG_ID` | From `frontend/.vercel/project.json` after Part 4 |
| `VERCEL_PROJECT_ID` | Same file |

> The private key grants shell access as `prompt-canvas`. Paste it only into the
> GitHub secret. If it ever leaks, remove the line from
> `/home/prompt-canvas/.ssh/authorized_keys` and generate a new pair — rotating the
> GitHub secret alone does nothing, because the old key still opens the door.

### 3d. What the workflows do

**`.github/workflows/ci.yml`** runs on every branch and PR:
backend pytest against a PostgreSQL service container, a missing-migration
check, frontend vitest + production build, and a secret scan that
fails the build if a real `hf_…` token or a tracked `.env` appears.

**`.github/workflows/deploy.yml`** runs on push to `main`:

```
test ──┬─→ backend  (ssh → /home/prompt-canvas/deploy.sh → health check)
       └─→ frontend (vercel pull → build → deploy → health check)
```

Nothing deploys unless the full suite passes. The two deploys run in parallel
once tests are green. `concurrency: cancel-in-progress: false` means an
in-flight deploy is never killed part-way through a migration.

---

## Part 4 — Vercel

1. **vercel.com/new** → import the repository.
2. **Root Directory: `frontend`.** Vercel reads `frontend/vercel.json` for the
   build command, output directory, SPA rewrite, and security headers.
3. **Environment Variables**, for Production, Preview, and Development:

   | Name | Value |
   |---|---|
   | `VITE_API_BASE_URL` | `https://<API_DOMAIN>` |

   No trailing slash. Vite bakes this in at build time, so changing it needs a
   redeploy, not a restart.
4. Deploy once from the dashboard.
5. **Settings → Domains → Add `<APP_DOMAIN>`.** Because
   `<your apex domain>` already uses Vercel's nameservers, the record is created
   automatically — there is no CNAME to add anywhere.
6. Link the project locally so you can read the two IDs:

   ```bash
   cd frontend
   npx vercel link
   cat .vercel/project.json
   ```

   Copy `orgId` and `projectId` into the GitHub secrets from Part 3b.
   `.vercel/` is gitignored.

### Preview deployments will not sign in

Each Vercel preview gets its own generated origin, and none of them are in the
VPS `CORS_ALLOWED_ORIGINS`. Sign-in will fail there. That is the Origin guard
working correctly, not a bug. Either add a specific preview origin to the
server's list when you need one, or test auth against production only.

**Do not use a wildcard.** `CORS_ALLOW_CREDENTIALS = True` and `*` are mutually
exclusive in browsers, and allowing arbitrary origins would defeat the CSRF
protection described below.

---

## Part 5 — Why the cookie settings are what they are

The refresh token is an httpOnly cookie. Cross-origin, that forces one specific
combination:

| Setting | Value | What breaks if you change it |
|---|---|---|
| `httpOnly` | `True` | Script could read the refresh token; XSS becomes account takeover |
| `SameSite` | `None` | Anything else and the browser drops the cookie on Vercel → VPS requests. Sign-in appears to work, then a reload signs the user out |
| `Secure` | `True` | Chrome rejects `SameSite=None` without it, so plain HTTP fails entirely |
| `Path` | `/api/auth/` | The cookie stops riding along on image and generation requests |

Because `SameSite=None` means the browser attaches the cookie to a cross-site
POST from *any* page, SameSite provides no CSRF protection here. That job
belongs to [`accounts/security.py`](../backend/accounts/security.py): the
`refresh` and `logout` endpoints validate the `Origin` header against
`CORS_ALLOWED_ORIGINS`. A browser stamps `Origin` from the requesting page and
will not let script forge it, so an attacker's page cannot drive either
endpoint.

**This is why `CORS_ALLOWED_ORIGINS` is a security control rather than a
convenience setting. Keep it exact and minimal.**

---

## Routine deploys

Push to `main`. That is the whole procedure.

To deploy by hand:

```bash
sudo -u prompt-canvas /home/prompt-canvas/deploy.sh
```

It pulls, installs, runs `check --deploy` with `--fail-level WARNING`,
migrates, collects static files, restarts gunicorn, and polls the health
endpoint. A failure at any step leaves the previous version serving.

---

## Operations

```bash
# Logs, live
sudo journalctl -u promptcanvas-api -f

# Service state
sudo systemctl status promptcanvas-api

# Django shell
cd /home/prompt-canvas/htdocs/<API_DOMAIN>/backend
sudo -u prompt-canvas DJANGO_SETTINGS_MODULE=config.settings.prod .venv/bin/python manage.py shell

# Database backup
sudo -u postgres pg_dump promptcanvas | gzip > ~/promptcanvas_$(date +%F).sql.gz

# Disk used by generated images
du -sh /home/prompt-canvas/htdocs/<API_DOMAIN>/backend/media
```

Generated images accumulate and are never pruned automatically. The VPS has
100 GB; at roughly 1.5 MB per image that is a lot of headroom, but it is worth
a periodic look.

---

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `502 Bad Gateway` | gunicorn is down | `sudo systemctl status promptcanvas-api`, then `journalctl -u promptcanvas-api -n 50` |
| Site loads, API calls fail with a CORS error | Origin mismatch | `CORS_ALLOWED_ORIGINS` must be exactly `https://<APP_DOMAIN>`. Restart `promptcanvas-api` after editing |
| Signed out after every reload | Refresh cookie rejected | Both sides must be HTTPS, with `Secure=True` and `SameSite=None`. Check the certificate actually issued |
| `403` from `/api/auth/refresh/` | Origin not allowlisted | Same list. This is the CSRF guard doing its job |
| Images 404 | `/media/` block missing or unreadable | Confirm the block is in the CloudPanel vhost and that the alias path ends in `/`. `chmod o+x` is needed on each parent directory |
| Images load but Download navigates instead of saving | `Access-Control-Allow-Origin` missing on `/media/` | It is in the `/media/` block in `cloudpanel-vhost.conf` |
| `503 provider_unconfigured` | Bad, missing, or gated `HF_TOKEN` | `manage.py check_provider`; confirm model access on huggingface.co |
| `504` on the first generation | Cold model, and nginx gave up first | Raise `HF_TIMEOUT`, and `proxy_read_timeout` must be at least as large |
| `429` immediately | Rate limits | Tune `GENERATION_RATE` in `.env` |
| CI deploy fails with `Permission denied (publickey)` | Deploy key not installed for `prompt-canvas` | Re-run Part 3a; confirm `/home/prompt-canvas/.ssh/authorized_keys` is mode 600 and owned by `prompt-canvas` |
| CI deploy fails on `systemctl restart` | sudoers rule missing | Re-run `bootstrap.sh`; check `/etc/sudoers.d/promptcanvas-api` |
