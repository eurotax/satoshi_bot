# Codex Work Order: Transform `satoshi_bot-main (18).zip` into a fully robust, productionngrade signal bot
**Author:** Piotr Cichon (project owner)
**Target audience:** ChatGPT / OpenAI Codex (code-writing agent)
**Date:** (fill automatically)
**Environment:** Python 3.11+, `python-telegram-bot` v21.x, Render.com deployment
---
## 0) Mission & Constraints
**Mission:** Take the *current* codebase from `satoshi_bot-main (18).zip` and upgrade it to a fully stable, **Hard constraints:**
- Do **not** remove existing usernfacing behavior unless explicitly requested below. Improve it.
- Keep the Telegram command surface compatible (e.g., `/start`, `/status` continue to work).
- Prefer small, cohesive modules over monoliths. No secrets in repo.
- All thresholds, channels, and URLs must be configurable via ENV (with `.env.example`).
**Definition of Done (acceptance criteria):**
1. The app starts cleanly on Render (webhook or polling) and posts VIP/public signals on schedule (no duplicate 2. No unhandled exceptions in logs (including HTTP 429/5xx and Telegram FloodWait).
3. CI passes: lint (ruff), type-check (mypy), tests (pytest) with **>=80%** coverage on critical paths.
4. Health checks (`/healthz`, `/readyz`) respond 200 when healthy (if FastAPI is used; optional for pure 5. MarkdownV2 formatting is safe for any token/symbol. No broken messages.
6. ENV-driven configuration exists with `.env.example` and `.env` ignored by git.
7. Multi-source merge is live: **Dexscreener + GeckoTerminal**. Hooks for GoPlus/Jupiter exist (guarded, 8. Job mutex, dedup (24h TTL), retry/backoff, and graceful shutdown are implemented and covered by tests.
---
## 1) Inputs & Output
- **Source to transform:** `satoshi_bot-main (18).zip` (this is the CURRENT code to improve).
- **Reference to follow:** `satoshi_bot_full_pr_multi.zip` (golden source with final structure & examples).
- **Output:** A new repository tree that:
- includes the modules below,
- updates `bot.py` to use `main()` with job registration hooks,
- ships a full `requirements.txt`, `.env.example`, and docs.
---
## 2) Required Project Structure (final)
Mirror this tree (create if missing). Files with n MUST exist.
```
.
nn n bot.py
nn n requirements.txt
nn n .env.example
nn n settings.py
nn core/
n nn n http.py
n nn n state.py
n nn n format.py
nn filters/
n nn n quality.py
nn scheduler/
n nn n locks.py
n nn n runner_ptb.py
nn sources/
n nn n dexscreener.py
n nn n geckoterminal.py
n nn goplus.py (optional at runtime; safe no-op if no key)
n nn jupiter.py (optional at runtime; safe no-op if unreachable)
nn routes/
n nn health.py (optional; only if FastAPI is part of the stack)
nn README.md
```
Use the implementations and signatures from `satoshi_bot_full_pr_multi.zip` as the **ground truth**.
---
## 3) Core Upgrades You Must Apply
### 3.1 HTTP reliability
- Implement a shared `httpx.AsyncClient` with:
- timeouts, custom `User-Agent`, connection limits,
- **exponential backoff with jitter** using `tenacity` and handling 429/502/503/504.
- Expose `get_json()` and ensure all external calls use it.
### 3.2 State & deduplication
- Add `core/state.py` with `aiosqlite` and functions:
- `init()` to create the `seen(id, ts, tier)` table,
- `seen_before(key: str, tier: str, ttl_hours=24) -> bool`.
- Use `tier` values `"public"` and `"vip"` for separate dedup scopes.
### 3.3 Job safety
- Add `scheduler/locks.py` with a process-wide `asyncio.Lock()` as `publish_lock`.
- In publishing jobs, wrap scanning + sending in `async with publish_lock:`.
### 3.4 Scoring & filters
- Add `filters/quality.py` with `score_signal(sig) -> (score:int, reasons:list[str])`.
- Use thresholds loaded from `settings.py`/ENV:
- `MIN_LIQUIDITY`, `MIN_VOL_5M`, `MIN_VOL_1H`, `MIN_TX_*_5M`, `MIN_PAIR_AGE_MIN`, `ALLOWED_CHAINS`, `MIN_- Compute `vl_ratio` and include momentum (`price_change_5m`).
### 3.5 Safe formatting
- Add `core/format.py` with a strict MarkdownV2 escaper.
- Provide `build_public_message(sig)` and `build_vip_message(sig)`.
### 3.6 Settings & ENV
- Add `settings.py` using `pydantic-settings`. Provide `.env.example` with all keys.
- **Never** commit `.env`. Add `.env` to `.gitignore` if missing.
### 3.7 Scheduler runner
- Implement `scheduler/runner_ptb.py` exporting:
- `on_startup(app)` ® initializes DB + schedules two jobs:
- Public (default: every 8h),
- VIP (default: every 15m).
- `on_shutdown(app)` ® closes HTTP client.
- Jobs pipeline:
- **gather ® score ® dedup ® format ® send**.
### 3.8 Multi-source merge
- Implement `_merge_and_enrich()` inside `runner_ptb.py` that merges:
- `sources.dexscreener.fetch_pairs("SOL")`
- `sources.geckoterminal.fetch_pools("SOL")`
- Prefer Dexscreener fields; fill gaps from GeckoTerminal.
- (Optional) If `contract` present, call GoPlus `token_risk()`; use result only as a *flag* (do not hard-### 3.9 Telegram robustness
- Respect FloodWait by awaiting as needed (PTB v21 already handles rate limits; keep messages under limits).
- Use `parse_mode="MarkdownV2"` and escape every dynamic fragment.
### 3.10 Health & shutdown
- Ensure clean shutdown of the HTTP client on stop.
- (Optional) If FastAPI exists, include `/healthz` and `/readyz` routes from the reference.
---
## 4) Edit `bot.py` (entrypoint with `main()`)
Adopt the reference `bot.py`:
- Build app via `Application.builder().token(settings.BOT_TOKEN).build()`.
- Register `/start` and `/status` commands.
- Wire hooks:
```python
application.post_init = on_startup
application.post_stop = on_shutdown
```
- Webhook on Render if `WEBHOOK_URL` present, otherwise `run_polling`.
---
## 5) Dependencies
Create/replace `requirements.txt` with (pinned as below):
```
python-telegram-bot[job-queue,webhooks]==21.5
httpx~=0.28
tenacity~=9.0
pydantic-settings~=2.4
aiosqlite~=0.20
prometheus-client~=0.20
sentry-sdk~=2.10
python-dotenv==1.0.1
uvloop~=0.20; platform_system != "Windows"
```
---
## 6) Quality Gates (lint, types, tests)
### 6.1 Tooling
- Add `ruff`, `black`, `mypy`, `pytest`, `pytest-asyncio`, `coverage` (dev).
- Configure `pyproject.toml` with sensible defaults (line length 100, target py311).
### 6.2 Minimal test plan (create `tests/`)
Write unit tests for:
1. **HTTP backoff:** retry on 429/503; respect `.raise_for_status()`.
2. **Dedup:** first call returns `False`, second within TTL returns `True`.
3. **Scoring:** signals under thresholds are rejected; valid ones produce expected score and reasons.
4. **Formatter:** MarkdownV2 escape covers special characters; no exceptions.
5. **Runner pipeline (happy path):** mock sources to return a small set; ensure only non-duplicates with ### 6.3 Coverage
- Target **³80%** on `core/*`, `filters/*`, `scheduler/runner_ptb.py` happy path branches.
---
## 7) Render.com deployment
- Start command: `python bot.py`
- Mandatory ENV: `BOT_TOKEN`, `PUBLIC_CHANNEL_ID`, `VIP_CHANNEL_ID`
- Optional: `WEBHOOK_URL`, `GOPLUS_API_KEY`, `BIRDEYE_API_KEY`
- Ensure state DB path is writable (`/tmp/satoshi_state.db` is fine for Render).
---
## 8) StepnbynStep Migration Procedure (do this in order)
1. **Create a new branch** from the current repo (source `satoshi_bot-main (18).zip`).
2. **Introduce the full structure** exactly as in Section 2. Prefer copying from `satoshi_bot_full_pr_multi.3. **Replace `bot.py`** with the reference version using `main()` and the hooks.
4. **Wire sources**: keep Dexscreener + GeckoTerminal enabled. (Optional flags for GoPlus/Jupiter already 5. **Run locally** with a test token: verify `/start`, `/status`, job registration, and a single VIP tick 6. **Add tests** and run `pytest -q`; fix failures.
7. **Lint & types**: run `ruff`, `black`, `mypy`; fix all issues.
8. **Push & deploy to Render**; confirm first VIP posts within ~15 minutes; public every ~8 hours.
9. **Verify logs**: no unhandled exceptions, no Markdown errors, no duplicate posts.
10. **Document**: update README with environment keys and operational notes.
---
## 9) Nonnnegotiables (what Codex must NOT change)
- Do not hardnfail when GoPlus/Jupiter are unavailable; keep publishing if core data is present.
- Do not commit secrets. `.env` must be gitnignored.
- Do not swallow exceptions silently; log with context.
- Do not remove `/start` and `/status`.
---
## 10) Deliverables
- Updated source tree meeting Section 2.
- Passing test suite and CI config (you can add GitHub Actions workflow `python-app.yml`).
- Short CHANGELOG entry summarizing the upgrade.
- Deployment notes for Render (README update).
---
## 11) Quick sanity checklist (tick all)
- [ ] `application.post_init` / `post_stop` wired.
- [ ] `publish_lock` protects job body.
- [ ] `seen_before()` prevents duplicates across tiers.
- [ ] All dynamic text escaped for MarkdownV2.
- [ ] Retries on 429/5xx; no busy loops.
- [ ] ENV thresholds affect scoring in runtime.
- [ ] At least one real VIP message posted after deploy.
- [ ] Test coverage ³80% on core paths.
