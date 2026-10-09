# Deploy APPI (simple checklist)

You have **two** cloud pieces. Do them in this order.

---

## A. API brain (Render) — do this first

1. Open https://dashboard.render.com and sign in (GitHub login is fine).
2. **New → Web Service**.
3. Connect repo `owosoayomide02-pixel/appi`.
4. Settings:
   - **Root Directory**: leave blank (repo root)
   - **Dockerfile Path**: `services/api/Dockerfile`
   - **Docker Context**: `.` (repo root)
5. Add environment variables (copy from your local `.env`, do not commit them):

| Key | Example / value |
|-----|-----------------|
| `DATABASE_URL` | `postgresql+asyncpg://postgres.cmpkbbmntnrywisuioik:DB_PASSWORD@aws-1-eu-west-1.pooler.supabase.com:5432/postgres` |
| `CORS_ORIGINS` | `https://appi-project01.netlify.app,http://localhost:3000` |
| `APP_URL` | `https://appi-project01.netlify.app` |
| `NEXT_PUBLIC_APP_URL` | `https://appi-project01.netlify.app` |
| `NEXT_PUBLIC_API_URL` | `https://YOUR-SERVICE.onrender.com` (set after first deploy, then redeploy) |
| `SUPABASE_URL` | from `.env` |
| `SUPABASE_ANON_KEY` | from `.env` |
| `SUPABASE_SERVICE_ROLE_KEY` | from `.env` |
| `JWT_SECRET` | from `.env` |
| `ENCRYPTION_KEY` | from `.env` |
| `AI_API_KEY` | from `.env` |
| `AI_PROVIDER` | `openai_compatible` |
| `AI_BASE_URL` | `https://api.groq.com/openai/v1` |
| `AI_MODEL` | `openai/gpt-oss-20b` |
| `GITHUB_CLIENT_ID` / `SECRET` | from `.env` |
| `GOOGLE_CLIENT_ID` / `SECRET` | from `.env` |
| `GITHUB_AUTH_OAUTH_REDIRECT` | `https://YOUR-SERVICE.onrender.com/api/v1/auth/oauth/github/callback` |
| `GOOGLE_AUTH_OAUTH_REDIRECT` | `https://YOUR-SERVICE.onrender.com/api/v1/auth/oauth/google/callback` |

6. Deploy. Open `https://YOUR-SERVICE.onrender.com/api/v1/health` — should show `"ok": true`.
7. Copy that URL. You need it for Netlify and OAuth redirects.

### OAuth apps (required for GitHub / Google **sign in**)

**GitHub** → Settings → Developer settings → OAuth Apps → your app → Authorization callback URL, **add**:
`https://YOUR-SERVICE.onrender.com/api/v1/auth/oauth/github/callback`

**Google Cloud** → APIs & Services → Credentials → OAuth client → Authorized redirect URIs, **add**:
`https://YOUR-SERVICE.onrender.com/api/v1/auth/oauth/google/callback`

(Keep the old `/connections/...` callbacks too — those are for linking Gmail/GitHub as tools.)

---

## B. Website (Netlify)

1. Open https://app.netlify.com → **Add new site → Import an existing project**.
2. Pick GitHub → `owosoayomide02-pixel/appi`.
3. Netlify should read `netlify.toml` (`base = apps/web`).
4. **Site settings → Environment variables** (Production):

| Key | Value |
|-----|--------|
| `NEXT_PUBLIC_APP_URL` | `https://appi-project01.netlify.app` |
| `NEXT_PUBLIC_API_URL` | `https://YOUR-SERVICE.onrender.com` |
| `NEXT_PUBLIC_SUPABASE_URL` | same as `.env` |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | same as `.env` |
| `NEXT_PUBLIC_GITHUB_REPO` | `owosoayomide02-pixel/appi` |

5. **Domain management** → set site name to `appi-project01` if it is not already.
6. Trigger **Deploy**. When green, open https://appi-project01.netlify.app

### CLI alternative (after `netlify.cmd login`)

```powershell
cd C:\Users\User\Downloads\appi.v2\APPI-0.1.0\APPI-0.1.0
netlify.cmd link
netlify.cmd env:set NEXT_PUBLIC_APP_URL https://appi-project01.netlify.app
netlify.cmd env:set NEXT_PUBLIC_API_URL https://YOUR-SERVICE.onrender.com
netlify.cmd deploy --prod
```

---

## Why GitHub / Google were missing on login

They only existed under **Connections** (link Gmail/repos *after* you have an account).  
Account **sign in / sign up** with GitHub & Google is now built on `/login` and `/register`. Buttons show once the API has client id/secret and the redirect URIs above are registered.
