# Deploy Office Copilot (100% free tier)

Use **Render** (free web app) + **Neon** (free PostgreSQL). No credit card on Neon; Render free tier sleeps after 15 min idle (first load may take ~1 minute).

## Step 1 — Free database (Neon)

1. Go to https://neon.tech and sign up (GitHub is fine).
2. **New Project** → name: `office-copilot`
3. Copy the connection string (looks like `postgresql://user:pass@ep-xxx.neon.tech/neondb?sslmode=require`).

## Step 2 — Push latest code

```powershell
Set-Location "C:\Users\LekhanaG\Desktop\office-copilot"
git add .
git commit -m "Add free production deploy config"
git push
```

## Step 3 — Free web app (Render)

1. Go to https://render.com and sign up with GitHub.
2. **New +** → **Blueprint** → connect repo `Lekhana-G123/office-copilot`  
   **OR** **New +** → **Web Service** → connect the same repo.
3. Settings:

| Field | Value |
|--------|--------|
| Plan | **Free** |
| Build Command | `pip install -r requirements.txt` |
| Start Command | `uvicorn app.main:app --host 0.0.0.0 --port $PORT` |

4. **Environment** variables:

| Key | Value |
|-----|--------|
| `DATABASE_URL` | Paste Neon connection string |
| `SECRET_KEY` | Long random string (or use Render “Generate”) |
| `GROQ_API_KEY` | Your Groq API key |
| `RUN_SEED` | `true` (first deploy only; demo users load once) |
| `CORS_ORIGINS` | `https://YOUR-APP-NAME.onrender.com` |

Replace `YOUR-APP-NAME` with your actual Render service name after create.

5. Click **Deploy**.

## Step 4 — Open your app

After deploy succeeds:

- Home: `https://YOUR-APP-NAME.onrender.com`
- Dashboard: `https://YOUR-APP-NAME.onrender.com/dashboard`

Demo login: `intern@office.com` / `intern123`

## Free tier limits

| Service | Limit |
|---------|--------|
| Render | App sleeps after 15 min; cold start ~30–60s |
| Neon | 0.5 GB storage; enough for demo |

## After first successful deploy

Set `RUN_SEED=false` on Render (optional — seed only runs if DB is empty anyway).

## Troubleshooting

- **Build fails on psycopg2** — Render uses Linux; `psycopg2-binary` in requirements handles this.
- **Database connection error** — Ensure Neon URL includes `?sslmode=require`.
- **CORS / login issues** — `CORS_ORIGINS` must match your exact Render URL (https, no trailing slash).
