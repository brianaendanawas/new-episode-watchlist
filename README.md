# New Episode Watchlist (Week 3)

A tiny serverless app that tags “NEW” episodes automatically and shows them in a simple web page.

## What it does
EventBridge (cron) → Producer Lambda → SQS (+DLQ) → Worker Lambda → writes `flags/<showId>.json` to S3.  
API Lambda (`GET /episodes`) reads `feeds/` + `flags/` and returns `isNew`; the frontend renders ⭐.

## Deployed bits (us-east-1)
- **S3 (data):** `episode-feeds-1jk32k` → `feeds/` (you upload), `flags/` (worker writes)
- **S3 (site):** `episode-site-kj324nd` (index.html, app.js)
- **API Gateway:** `/episodes` → `list_episodes` Lambda
- **CloudFront:** https://d3nygn7m3cuned.cloudfront.net
- **SQS:** `episode-new-refresh` (+ DLQ)
- **EventBridge rule:** `episode-refresh-hourly`

## Env vars (important)
**Worker:** `BUCKET=episode-feeds-1jk32k`, `FEEDS_PREFIX=feeds/`, `FLAGS_PREFIX=flags/`, `NEW_WINDOW_DAYS=14`  
**Producer:** `QUEUE_URL=https://sqs.us-east-1.amazonaws.com/773836683412/episodes-queue`, `SHOWS=show1`  
**List/API:** `BUCKET=episode-feeds-1jk32k`, `FEEDS_PREFIX=feeds/`, `FLAGS_PREFIX=flags/`, `ALLOWED_ORIGIN=https://d3nygn7m3cuned.cloudfront.net`, `ALIASES={"show-wednesday":"show1"}`

## How to use
1) Put your feed at **S3**: `episode-feeds-1jk32k/feeds/show1.json`  
2) Open the site → type **show1** → **Load** → ⭐ shows for recent episodes (≤14 days).

## Refresh (manual)
- Lambda → `episode_producer_enqueue` → **Test** → expect `{"sent": 1}`  
- Worker writes `flags/show1.json` automatically.

## API example
GET https://8c7523bn7g.execute-api.us-east-1.amazonaws.com/episodes?showId=show1

arduino
Copy code
Returns:
```json
{ "count": N, "items": [ { "episodeId": "...", "isNew": true } ] }
Update frontend
If you change index.html/app.js:

Upload to episode-site-kj324nd

CloudFront → Invalidations → create → paths "/*"

Notes
Data bucket blocks public access (no ACLs needed).

Least-privilege IAM: List/API has s3:GetObject (and scoped ListBucket) for "feeds/*", "flags/*".














# New Episode Watchlist — Week 3

**Overview.** EventBridge (cron) → Producer Lambda → **SQS (`episodes-queue`)** (+ DLQ) → Worker Lambda → writes `flags/<showId>.json` in S3.  
API Lambda (`GET /episodes`) reads `feeds/` + `flags/` and the page shows ⭐ for recent episodes.

---

## How to Run

1) **Add/Update feed** → S3 data bucket: `episode-feeds-1jk32k/feeds/show1.json`.
2) **Refresh now (manual)** → Lambda `episode_producer_enqueue` → **Test** (empty event).  
   Worker writes `episode-feeds-1jk32k/flags/show1.json`.
3) **Open site** → CloudFront: https://d3nygn7m3cuned.cloudfront.net → type `show1` → **Load**.
4) **API check (optional)**  
   `GET https://8c7523bn7g.execute-api.us-east-1.amazonaws.com/episodes?showId=show1` → returns `{ count, items: [...] }`.
5) **Frontend changes?** Re-upload to `episode-site-kj324nd` and **CloudFront → Invalidations → Create →** "/*".

---

## Config (env vars)

**Producer**  
- `QUEUE_URL = https://sqs.us-east-1.amazonaws.com/773836683412/episodes-queue`  
- `SHOWS = show1`

**Worker**  
- `BUCKET = episode-feeds-1jk32k`  
- `FEEDS_PREFIX = feeds/`  
- `FLAGS_PREFIX = flags/`  
- `NEW_WINDOW_DAYS = 14`

**List/API**  
- `BUCKET = episode-feeds-1jk32k`  
- `FEEDS_PREFIX = feeds/`  
- `FLAGS_PREFIX = flags/`  
- `ALLOWED_ORIGIN = https://d3nygn7m3cuned.cloudfront.net`  
- `ALIASES = {"show-wednesday":"show1"}`
