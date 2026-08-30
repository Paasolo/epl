# Multi-league match predictor (2026/27)

Interactive Python model that predicts user-selected fixtures across nine European top flights — a custom slate or an official matchweek.

Supported leagues: **Premier League**, **La Liga**, **Bundesliga**, **Ligue 1**, **Serie A**, **Eredivisie**, **Primeira Liga**, **Süper Lig**, and **Belgian Pro League**.

Each league is fitted on football-data.co.uk results from **2000/01 through 2025/26**, plus any completed **2026/27** scores fetched live from the same provider. Summer 2026 signings and coaching changes are applied as a small overlay.

## Run

From this folder:

```bash
py -m pip install -r requirements.txt
py -m streamlit run app.py
```

### Authentication (required)

The app is gated behind **Supabase** email/password accounts. Create a free project at [supabase.com](https://supabase.com), enable **Authentication → Email**, then add secrets locally in `.streamlit/secrets.toml` (gitignored) or in Streamlit Cloud **App settings → Secrets**:

```toml
[supabase]
url = "https://YOUR_PROJECT.supabase.co"
key = "YOUR_ANON_KEY"
```

Use the Project URL and the **anon public** key (Settings → API). Without these secrets the login screen shows setup instructions and the predictor stays locked.

If email confirmation is enabled in Supabase, new users must confirm their inbox before signing in; if it is disabled, sign-up signs them in immediately.

**Create account** collects email, phone number, and password. The phone is stored in Supabase `user_metadata.phone` (also attached to Paystack checkout metadata when the customer pays).

### Paystack weekly unlock (Customers)

**Customer** accounts must pay **GHS 50** per official matchweek (via [Paystack](https://paystack.com)) before ranked prediction results, cards, and downloads are shown. One payment unlocks that matchweek across **all leagues**. **Admin** accounts skip payment.

Add Paystack keys (test or live) to `.streamlit/secrets.toml` or Streamlit Cloud secrets. Enable **GHS** in your Paystack dashboard:

```toml
[paystack]
public_key = "pk_test_..."
secret_key = "sk_test_..."
```

Optional: set `APP_URL = "https://your-app.streamlit.app"` so Paystack can redirect back after checkout when the auto-detected URL is wrong.

### Nalo SMS (payment confirmation)

After a successful Paystack unlock, the app sends an SMS to the customer’s phone via [Nalo Solutions](https://www.nalosolutions.com/). Add a `[NaloSms]` block to `.streamlit/secrets.toml` (or Streamlit Cloud secrets):

```toml
[NaloSms]
Enabled = true
NaloApiUrl = "https://sms.nalosolutions.com/smsbackend/clientapi/Resl_Nalo/send-message/"
NaloApiKey = "your_nalo_api_key"
NaloSenderId = "SpareLink"
RequestDeliveryReport = true
```

`NaloSenderId` must be an approved sender ID on your Nalo account (max 11 characters). Set `Enabled = false` to turn SMS off without removing keys. Payment unlock still works if SMS is disabled or misconfigured.

### Google AdSense (Customers · Predict tab)

Customer accounts see AdSense display units on the **Predict matches** tab (above and below prediction results / the paywall). Admins do not see ads.

1. Create a [Google AdSense](https://www.google.com/adsense/) account and add your Streamlit Cloud site URL.
2. When AdSense asks you to paste the site script into `<head>`, you only need to set `client_id` — the app injects that script on the public sign-in page (Streamlit has no editable HTML `<head>`).
3. Create two **Display** ad units (top and bottom banners) and set their slot IDs.
4. Add secrets:

```toml
[adsense]
client_id = "ca-pub-xxxxxxxxxxxxxxxx"
slot_top = "##########"
slot_bottom = "##########"
```

Ads may not fill on `localhost`, and Google must approve the site before inventory serves in production. Display slots are skipped until `slot_top` / `slot_bottom` are real IDs.

The app opens in your browser with a **League** switcher in the sidebar and three tabs:

- **Predict matches** — load any official matchweek (or add/remove fixtures by hand). Finished games are excluded automatically when you load a matchweek. Toggle the summer overlay on/off, then click **Predict**. Download the ranked slate as CSV or JSON.
- **Team strength** — Elo, attack/defence, recent form, manager, and promotion status for the current league.
- **Backtest explorer** — walk-forward 2025/26 accuracy by confidence band, month, and biggest misses.

Use **Refresh results** in the sidebar to re-fetch the latest scores and refit the **active** league. Primary source is football-data.co.uk; if that season’s CSV is not published yet, the app falls back to fixturedownload.com (where a feed exists). Belgian Pro League uses a custom slate only (no fixture feed).

First open of a non-EPL league downloads ~26 season CSVs into `data/` (one-time), then caches the fitted model under `epl_predictor/cache/`.

## What the model uses

- Historical results plus a shots-on-target **xG proxy** (falls back to goals when shots are missing)
- Live completed 2026/27 scores merged from football-data.co.uk (when reachable)
- Time-decayed attack/defence ratings with learned home advantage and season carry-over
- Elo strength blended with a Dixon–Coles Poisson score grid
- Walk-forward **temperature calibration** on 2023/24–2025/26 so probabilities are not over-confident
- Recent form, same-venue head-to-head, and a shrinkage prior for promoted clubs
- 2026 summer context: net spend, key ins/outs, manager changes (optional overlay)

**Every training and backtest prediction uses only earlier matches** — ratings are updated after each game is scored, never before.

The headline output is the most likely 1X2 result with a confidence band. Supporting markets (most likely score, over/under, BTTS) are shown when they are useful.

Football match outcomes are noisy. Lean on **High** confidence picks; treat Low as little more than a lean.
