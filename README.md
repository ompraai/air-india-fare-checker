# ✈️ Air India ORD → BLR Daily Fare Checker

Automatically searches for the **cheapest Air India fares** from Chicago O'Hare (ORD)
to Kempegowda International Bangalore (BLR) across flexible dates, and emails a digest
every morning to `om.prakash@riversideinsights.com`.

---

## How It Works

```
GitHub Actions (cron: 8 AM CST daily)
        │
        ▼
flight_checker.py
        │
        ├─ [1] Authenticates with Amadeus API
        ├─ [2] Calls /v1/shopping/flight-dates → gets cheapest dates ORD→BLR
        ├─ [3] For each cheap date → calls /v2/shopping/flight-offers
        │       filtered to Air India (AI) only
        ├─ [4] Ranks results by price
        └─ [5] Sends HTML email via Gmail SMTP
```

---

## One-Time Setup (≈ 15 minutes)

### Step 1 — Get a Free Amadeus API Key

1. Go to → https://developers.amadeus.com/register
2. Sign up (free, no credit card)
3. Create an app → copy your **API Key** and **API Secret**
4. The free tier gives you **2,000 calls/month** on the **test environment**

> **Note:** The test environment may have limited BLR data. Once ready for production,
> change `AMADEUS_BASE` in `flight_checker.py` from `test.api.amadeus.com`
> to `api.amadeus.com` and request production access in the Amadeus portal.

---

### Step 2 — Set Up Gmail App Password (for SMTP)

1. Go to your Google Account → Security → 2-Step Verification (must be ON)
2. Then: Security → **App Passwords**
3. Create one named "AirIndiaFareBot" → copy the 16-character password

> If you use a work email (`@riversideinsights.com`) on Google Workspace,
> your admin must allow Less Secure App access or App Passwords.
> Alternative: use **SendGrid** (free 100 emails/day) — raise an issue if needed.

---

### Step 3 — Create a GitHub Repository

```bash
# On your local machine
mkdir air-india-fare-checker
cd air-india-fare-checker
git init
# Copy all files from this package into the folder
git add .
git commit -m "Initial commit"
# Push to GitHub (create a new repo first at github.com)
git remote add origin https://github.com/YOUR_USERNAME/air-india-fare-checker.git
git push -u origin main
```

---

### Step 4 — Add GitHub Secrets

In your GitHub repo → **Settings → Secrets and variables → Actions → New repository secret**

Add these 4 secrets:

| Secret Name        | Value                                      |
|--------------------|--------------------------------------------|
| `AMADEUS_API_KEY`  | Your Amadeus API Key                       |
| `AMADEUS_API_SECRET` | Your Amadeus API Secret                  |
| `SMTP_USER`        | Your Gmail address (e.g. you@gmail.com)    |
| `SMTP_PASSWORD`    | Your Gmail App Password (16 chars)         |

---

### Step 5 — Enable GitHub Actions

1. Go to your repo → **Actions** tab
2. Click **"I understand my workflows, go ahead and enable them"**
3. The workflow runs automatically at **8:00 AM CST** every day

**To run it manually right now:**
- Actions tab → "✈️ Daily Air India ORD→BLR Fare Check" → **Run workflow**

---

## Files

```
├── flight_checker.py                        # Main script
├── requirements.txt                         # Python dependencies
├── .github/
│   └── workflows/
│       └── daily_fare_check.yml             # GitHub Actions scheduler
└── README.md                                # This file
```

---

## Customization

| What to change         | Where                              |
|------------------------|------------------------------------|
| Departure city         | `ORIGIN = "ORD"` in flight_checker.py |
| Destination city       | `DESTINATION = "BLR"`              |
| Run time               | `cron: '0 13 * * *'` in YAML (UTC) |
| Number of results      | `TOP_RESULTS = 5`                  |
| Number of dates probed | `TOP_DATES = 15`                   |
| Email recipient        | `TO_EMAIL` in flight_checker.py    |

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| `401 Unauthorized` from Amadeus | Check API Key/Secret secrets in GitHub |
| `SMTPAuthenticationError` | Regenerate Gmail App Password |
| No Air India flights found | Normal on test tier; switch to production Amadeus |
| Workflow not triggering | Check Actions is enabled; GitHub free tier cron can delay up to 15 min |
