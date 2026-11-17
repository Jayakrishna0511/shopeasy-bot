# ShopEasy Support Bot: Agent Context

Save this file in the repo root as `CLAUDE.md` (Claude Code) or `AGENTS.md` (other agents). Read it fully before doing anything. Follow the working rules in section 2 on every task.

---

## 1. Project goal

Build a **customer support bot** for a fictional online electronics store, **ShopEasy** (Hyderabad, India). The bot:

1. Answers policy questions from documents (RAG with citations, says "I don't know" when the docs don't cover it).
2. Looks up and cancels a user's orders (tools, with approval for risky actions).
3. Later: runs approved background jobs through an agent (human approval, Celery).
4. Finally: accepts **voice input** (speech to text), runs the same pipeline, and shows the transcript, answer, and cited sources on screen.

The owner is **learning**. Explain what you build in 3 to 6 plain lines, keep code simple and readable, and prefer clarity over cleverness.

---

## 2. Working rules for the agent (important)

1. **One small step at a time.** Do one step from section 7, then stop and report. Never build several phases at once.
2. **Each step ends with a verification** the owner can run (a URL, a command, a test). State exactly what output to expect.
3. **Ask before** adding a new dependency, changing the folder structure, or doing anything not in the current step.
4. **Never print, log, commit, or echo secrets.** Real values live only in `.env`. `.env.example` holds placeholders only. Before any commit run `git status` and `git diff --cached` and check no secret is staged.
5. **Do not touch `.env`.** If a new variable is needed, add a placeholder to `.env.example` and tell the owner to add the real value to `.env` themselves.
6. **Windows environment** (see section 3). Give PowerShell commands, not bash.
7. **Small commits** with clear messages after each working step. Do not push unless the owner asks.
8. **Security in code, not prompts:** permissions, allowlists, parameter validation and approval flows are enforced in code. Prompts are only requests the model can be talked out of.
9. If something fails, show the exact error, explain the likely cause, and fix one thing at a time. Do not guess repeatedly.
10. Keep files small and single-purpose. Add short comments only where the reason isn't obvious.

---

## 3. Environment (fixed facts)

| Item | Value |
|---|---|
| OS | **Windows**, shell is **PowerShell** (venv activate: `venv\Scripts\activate`; copy: `copy`; no `touch`, no `mkdir -p`) |
| Project path | `C:\Users\Jaya krishna\OneDrive\Desktop\shopeasy-bot` (inside **OneDrive**: never create files containing secrets outside `.env`) |
| Python | 3.11+ with a venv at `backend\venv` |
| Node | 20+ |
| Database | **Neon** hosted Postgres (AWS Singapore), project `shopeasy`, branch `production`, database `neondb`, role `neondb_owner`, with the **pgvector** extension enabled |
| Docker | **Not installed. Do not use Docker.** `docker-compose.yml` and `db/init.sql` exist but are empty and unused |
| pgAdmin | Installed with a local PostgreSQL 18 that has **no pgvector**. Do not use the local Postgres. pgAdmin may only be used to browse the Neon DB |
| GitHub | `https://github.com/Jayakrishna0511/shopeasy-bot` (branch `main`) |
| LLM | Claude via the Anthropic API. Model id: `claude-sonnet-5-5` (cheaper option: `claude-haiku-5-5`) |

---

## 4. Tech stack

- **Frontend:** React + TypeScript (Vite), port 5173. Vite proxies `/api` to the backend.
- **Backend:** FastAPI, port 8000, all routes under `/api`.
- **DB access:** SQLAlchemy 2.x with the `psycopg` (v3) driver. Migrations with Alembic (to be added in Phase A).
- **Vectors:** Postgres + pgvector.
- **Embeddings:** local `sentence-transformers` model `all-MiniLM-L6-v2` (384 dimensions) to start.
- **Agent:** hand-written tool loop first, LangGraph later for approval flows.
- **Jobs (later):** Celery + Redis. Redis will need a hosted free tier (Upstash or similar) since Docker is not available.
- **Voice (later):** browser microphone then speech to text then the same text pipeline.

---

## 5. Current state (already done and verified)

- Git repo created and pushed to GitHub.
- Folder skeleton exists.
- Neon project created; `CREATE EXTENSION vector` succeeded.
- **Backend works:** `GET /api/health` returns `{"status":"ok","db":"up","pgvector":true}`.
- **Frontend works:** React page at `http://localhost:5173` shows API ok, Database up, pgvector enabled (React to FastAPI to Neon verified).
- A previous leak of the Neon password via `.env.example` was fixed: password reset, `.env.example` now holds placeholders only.

### Current folder structure

```
shopeasy-bot/
├── .env                  # real secrets, git-ignored, NEVER touch or print
├── .env.example          # placeholders only
├── .gitignore
├── README.md
├── docker-compose.yml    # empty, unused
├── db/init.sql           # empty, unused
├── backend/
│   ├── requirements.txt
│   ├── venv/             # git-ignored
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py       # FastAPI app, CORS, mounts routers under /api
│   │   ├── config.py     # pydantic-settings, reads ../.env
│   │   ├── db.py         # engine, SessionLocal, get_db()
│   │   ├── api/          # health.py exists; chat.py etc. to come
│   │   ├── core/         # auth, rate limit, guardrails (later)
│   │   ├── rag/          # chunking, ingest, retrieve, rerank (later)
│   │   ├── agent/        # tools, LangGraph (later)
│   │   ├── services/     # llm.py, stt.py, tts.py (later)
│   │   └── models/       # SQLAlchemy tables (later)
│   ├── scripts/          # make_data.py, make_orders.py, make_eval.py
│   ├── data/docs/        # generated policy documents
│   ├── evals/            # eval_data.json, eval_suite.py
│   └── tests/
└── frontend/             # Vite + React + TypeScript
    └── src/
        ├── api/client.ts # fetch helpers
        └── App.tsx       # health-check page
```

Planned frontend folders: `src/components/` (ChatWindow, MessageBubble, SourceCards, MicButton), `src/hooks/` (useChat, useAudioRecorder).

### Environment variables (`.env`; only placeholders are shown here)

```
DATABASE_URL=postgresql+psycopg://USER:PASSWORD@HOST/DBNAME?sslmode=require
ANTHROPIC_API_KEY=
CORS_ORIGINS=["http://localhost:5173"]
```

The Neon string may carry extra parameters such as `channel_binding=require`. Leave them as they are. The prefix must be `postgresql+psycopg://`.

### Installed backend packages (`requirements.txt`)

fastapi, uvicorn[standard], pydantic-settings, sqlalchemy>=2.0, psycopg[binary]>=3.1, pgvector. Add others only when a step needs them (alembic, anthropic, sentence-transformers, pypdf, rank-bm25, langgraph, celery, redis, etc.).

### How to run

```powershell
# Backend (from backend\)
venv\Scripts\activate
uvicorn app.main:app --reload --port 8000

# Frontend (from frontend\), in a second terminal
npm run dev
```

---

## 6. The fictional business: ShopEasy

Online electronics store in Hyderabad, India. Currency: rupees. Support hours Monday to Saturday, 9am to 7pm IST.

### Ground-truth facts (the source of ALL policy documents and eval answers)

Policy documents must be generated **only** from these facts, with no new numbers, prices, or promises added.

**Returns and refunds**
- Returns within 30 days of delivery with the original receipt.
- Items must be unused and in original packaging.
- Refunds go to the original payment method within 5-7 business days after the item is received.
- Premium members get free return pickup. Others pay 99 rupees.
- Opened software, earbuds, and gift cards cannot be returned.

**Damaged or wrong items**
- Report within 48 hours of delivery.
- Send 2 photos of the item and packaging to support@shopeasy.example.
- Free replacement within 3 business days of approving the report.

**Shipping**
- Standard delivery in India takes 3-5 business days; free above 999 rupees, otherwise 49 rupees.
- Express takes 1-2 business days and costs 150 rupees extra.
- Express is available only in Hyderabad, Bengaluru, Chennai, Mumbai, and Delhi.
- No shipping outside India.
- Tracking links are emailed once the order ships.

**Cancellations**
- An order can be cancelled only while its status is `processing`.
- Once `shipped` it cannot be cancelled (refuse delivery or start a return).
- Cancelled orders are refunded within 3-5 business days.

**Payments**
- UPI, credit cards, debit cards, net banking.
- Cash on delivery for orders up to 5000 rupees.
- EMI on orders above 10000 rupees with selected banks.
- Error P-1042: payment gateway timed out, wait 10 minutes and retry.
- Error P-2210: card declined by the bank, contact the bank or use another method.

**Warranty**
- 1-year manufacturer warranty from delivery on all electronics.
- Not covered: water damage or physical damage caused by the customer.
- Laptops: 2-year extended warranty for 2999 rupees if bought within 30 days of purchase.

**Premium membership**
- 499 rupees per year.
- Free express delivery, free return pickup, early access to sales.
- Cancel within 7 days for a full refund; after that non-refundable.

**Support and account**
- Support Monday to Saturday, 9am to 7pm IST; closed Sundays and national holidays.
- Email support@shopeasy.example; replies within 24 hours.
- Password reset: "Forgot password" on the login page; the link expires in 30 minutes.
- Account deletion: email privacy@shopeasy.example; completes within 14 days.

### Fake data to create

- **users:** `ravi` (premium), `priya`, `arjun`.
- **orders:** about 8 per user. Columns: id (like `A1001`), user_id, item, price, status (`processing` | `shipped` | `delivered` | `cancelled`), city, eta_days.
- Items: Wireless Earbuds, Laptop 15-inch, Phone Case, USB-C Charger, Smartwatch, Bluetooth Speaker.

---

## 7. Build plan (one step at a time; stop and verify after each)

### Phase A: Database tables and fake data
- A1. Add Alembic; configure it to use `DATABASE_URL`. *Verify: `alembic current` runs.*
- A2. Models and migration for `users`, `orders`. *Verify: tables visible in Neon.*
- A3. Seed script `scripts/make_orders.py` (fake data above, idempotent). *Verify: a SELECT shows rows.*
- A4. Tables for `documents` and `chunks` (chunk text, `embedding vector(384)`, source, page, metadata, plus a full-text search column for later). *Verify: migration applies.*

### Phase B: RAG on pgvector
- B1. `scripts/make_data.py`: generate policy docs into `data/docs/` from the facts in section 6 using Claude (temperature 0.7; prompt forbids new facts). **Owner reviews every generated file** for invented numbers.
- B2. Ingest: load files, chunk (about 200 words, 40 overlap), embed, upsert into `chunks` with stable ids. *Verify: row count in Neon.*
- B3. Retrieve: vector search with similarity threshold. Answer function with grounding prompt: use only sources, cite `[n]`, otherwise reply exactly "I don't know based on the provided documents." *Verify with the three sample questions below.*

### Phase C: Chat API and UI
- C1. `POST /api/chat` (message, session_id), returns answer plus sources. Store messages in a `messages` table.
- C2. React chat UI: message list, input, source cards, loading and error states.
- C3. Streaming (SSE) of the answer.

### Phase D: Tools, auth, permissions
- D1. Auth (start simple: API-key or JWT mapped to a user). User identity comes from auth, **never from the model**.
- D2. Tools: `search_docs`, `get_order_status`, `cancel_order`. Order queries use `WHERE id=%s AND user_id=%s` with bound parameters (never string formatting).
- D3. Agent loop (max 6 steps). `cancel_order` requires a confirm flow: the tool returns "pending", the UI shows Confirm, a separate `/api/approve` endpoint executes it (single use, expiring, owner-checked).
- D4. Rate limiting and input length caps.

### Phase E: Retrieval quality
- E1. Hybrid search (Postgres full-text plus vector) merged with Reciprocal Rank Fusion.
- E2. Reranking with a cross-encoder (retrieve about 20, keep 4).
- E3. Query rewriting for follow-up questions.

### Phase F: Safety, observability, evaluation
- F1. Guardrails: PII masking (before LLM and before logs), prompt-injection screen, output checks (citation validity, groundedness), canary token.
- F2. Tracing: trace and span records for each request (rewrite, retrieve, rerank, llm, tools), tokens and latency.
- F3. Eval suite in `backend/evals/`: retrieval (recall@k, MRR), answers (correctness, refusal on unanswerable, wrong-refusal rate), agent tool-path checks, baseline file, fail on regression.
- F4. Red-team script of attacks, re-run before each deploy.

### Phase G: Voice
- G1. `useAudioRecorder` hook (MediaRecorder) and a mic button.
- G2. `POST /api/voice`: audio in, speech-to-text, then the **same pipeline as `/api/chat`**. Owner decides STT: browser Web Speech API (quick prototype) or a server model (e.g. faster-whisper).
- G3. UI shows transcript, answer, and cited source cards. Optional spoken reply (TTS).

### Phase H (optional)
- Job-runner agent: allowlisted jobs, LangGraph approval pause, Celery + hosted Redis, `get_job_status`.
- Prompt caching, model routing, deployment.

---

## 8. Test questions for Phase B (expected answers from the facts)

| Question | Expected |
|---|---|
| How long do I have to return an item? | 30 days, with receipt, cites a source |
| My package arrived broken, what do I do? | Report within 48 hours with 2 photos, free replacement |
| What is the capital of Japan? | "I don't know based on the provided documents." |
| Can I return earbuds? | No, earbuds cannot be returned |
| Is express shipping available in Pune? | No, only the five listed cities |
| Do you ship to the USA? | No, not outside India |

Multi-turn examples for later: "What's your return policy?" then "what about for earbuds?"; "Is express available?" then "in Pune?".

Unanswerable examples (must refuse): gift cards sold?, CEO's name?, student discounts?, crypto payment?, physical store in Pune?, refund policy for gift cards (tricky: sounds answerable).

---

## 9. Security and quality rules (apply everywhere)

- Secrets only in `.env`; `.env.example` is placeholders. Never log secrets or full connection strings.
- All SQL uses bound parameters.
- Permission checks live in code and SQL (`user_id` in the WHERE clause), and also as metadata filters before retrieval where documents have owners or teams.
- Retrieved text and user text are **data, not instructions**: wrap in delimiters (for example `<sources>...</sources>`) and say so in the system prompt.
- The model only requests tools; the code runs them. Validate every tool argument in code. Cap steps, tokens, and input length.
- Risky writes (cancel, refund, run job) always go through the code-enforced approval flow.
- Mask PII before sending to the LLM and before logging.
- Never trust model output blindly: parse and validate JSON, retry on failure.
- Change one thing at a time and re-run the eval set before and after.

---

## 10. First task for the agent

1. Read this file and inspect the repo (`git ls-files`, view `backend/app/*`, `frontend/src/*`). Do not read or print `.env`.
2. Confirm in 5 lines that you understand the current state and rules.
3. Do **only Step A1** (Alembic setup), explain it in plain language, state how to verify it, and stop.
