# TSPI AI Brain — Cloud Deployment, Optimization & Monthly Cost

*Target workload: ~**1,000 treatment plans/day** (~30,000/month) generated with **Claude**. This
covers (1) an optimized cloud deployment, (2) an optimized treatment-plan generation strategy, and
(3) an approximate monthly cost for both cloud infra and Claude tokens. Pricing is current as of
June 2026 (sources at the end).*

---

## 1. Key insight that shapes everything

Because you use **Claude (API)** for the language work, you do **not** need GPUs in your cloud —
that removes the single most expensive infrastructure item. Your servers stay small and cheap; you
pay Anthropic per token instead. And critically, **the medicine is computed in code, not by the
LLM**: the engine already derives axes, NSS, SPS, severity level, module selection, and dosing
deterministically. **Claude is used only to *write the report* from those computed facts** — which
keeps token usage (and cost, and clinical risk) low.

---

## 2. Optimized cloud deployment

### 2.1 Recommended shape (managed, serverless-first)
```
MiHealth (front end)
      │  HTTPS
      ▼
[ API Gateway / Load Balancer ]
      │
      ▼
[ tspi_ai_brain — FastAPI on serverless containers ]   (Cloud Run / ECS Fargate / Azure Container Apps)
   • autoscales on traffic, scales down off-peak
   • stateless; high concurrency (requests are I/O-bound on Claude)
      │                 │                       │
      ▼                 ▼                       ▼
[ Job Queue ]     [ PostgreSQL 15 + pgvector ]   [ Claude API ]
 (Redis/SQS)       (managed: RDS/Cloud SQL/Supabase)  (Bedrock/Vertex/Anthropic)
      │                 │
      ▼                 ▼
[ Worker pool ]   [ Object storage (reports, uploads) ]
 (generates plans)  (S3 / GCS)
```

### 2.2 The 8 optimizations that matter most
1. **Serverless containers + autoscaling** (Cloud Run / Fargate). 1,000/day ≈ 42/hour average,
   so you need very little steady compute; let it scale up for peaks and down to ~1 instance off-peak.
2. **Async job queue for plan generation.** A treatment plan does **not** need to be instant — a
   **doctor reviews it before the patient sees it**. Generate plans as background jobs (return a job
   id, notify when ready). This smooths load **and unlocks the Claude Batch API (−50%)**.
3. **Prompt caching** on the static prefix (system prompt + 39-axis/module reference + framework
   rules — identical for every patient) → **−90%** on those input tokens.
4. **Model routing (tiered):** **Haiku** for cheap structured sub-tasks (lab normalization,
   classification), **Sonnet** for the report narrative, **Opus** only for flagged complex/Level-3
   cases or a final safety-QA pass. Don't pay Opus rates for routine plans.
5. **Deterministic-first:** keep all clinical logic (NSS/SPS/axes/dosing) in code; the LLM only
   composes prose → the smallest possible token footprint.
6. **One database:** PostgreSQL **with the pgvector extension** holds both the relational catalog
   and the embeddings — no separate vector-DB bill. Add PgBouncer pooling; a read replica only if needed.
7. **Compliance path for health data:** call Claude through **AWS Bedrock or Google Vertex** (HIPAA
   BAA, data residency) or Anthropic with **zero-data-retention**; and **de-identify before the LLM**
   (the engine already sends only `case_id` + age band + sex — no PHI). Encrypt at rest/in transit,
   audit logs, consent gating.
8. **Reliability/observability:** retries with backoff + fallback model on overload, per-request
   **token/cost tracking**, dashboards and alerts, blue-green deploys, health checks.

---

## 3. Optimized treatment-plan generation

- **Compute, don't prompt.** The report is assembled from the engine's structured output; Claude is
  instructed to *explain the computed result*, never to "diagnose." Fewer tokens, safer, auditable.
- **Cached, templated sections.** Static framework/methodology text lives in the cached prefix;
  only the patient-specific delta is fresh input each call.
- **Bounded output via structured/templated report** (fixed section order) so output tokens stay
  predictable (~3k for a concise report, ~8k for a full long-form article).
- **Batch overnight** for non-urgent plans; **real-time only** for the few that truly need it.
- **Two-tier quality gate:** Sonnet drafts; Opus reviews only **Level 3 (Advanced Network Failure)**
  cases (a small %), where stakes are highest.
- **Reassess cadence** is every 14–30 days (per the official engine), so each patient generates a
  *new* plan only periodically — not daily — keeping volume predictable.

---

## 4. Monthly cost — Claude tokens

**Assumptions per plan:** ~**10–12k input tokens** (system+framework+RAG+patient) of which ~6k is
the **cacheable** static prefix; output **~3k (concise)** to **~8k (full long-form)**. Volume =
**30,000 plans/month**. Pricing (per 1M tokens): **Sonnet 4.6 $3 in / $15 out**, Haiku 4.5 $1/$5,
Opus 4.8 $5/$25. Batch = −50%; cached input read = 10% of input price.

### Sonnet 4.6 (recommended primary) — cost per plan
| Report size | Standard | + Prompt caching | + Caching **and** Batch |
|---|---|---|---|
| Concise (10k in / 3k out) | $0.075 | ~$0.059 | **~$0.029** |
| Full long-form (12k in / 8k out) | $0.156 | ~$0.140 | **~$0.070** |

### Sonnet 4.6 — monthly (30,000 plans)
| Report size | Standard | + Caching | + Caching **and** Batch |
|---|---|---|---|
| Concise | ~$2,250 | ~$1,760 | **~$880** |
| Full long-form | ~$4,680 | ~$4,190 | **~$2,100** |

### Model comparison (concise plan, standard pricing, 30k/mo)
| Model | $/plan | $/month | Note |
|---|---|---|---|
| Haiku 4.5 | $0.025 | ~$750 | cheapest; fine for sub-tasks, thinner clinical prose |
| **Sonnet 4.6** | **$0.075** | **~$2,250** | **best quality/cost for the report (recommended)** |
| Opus 4.8 | $0.125 | ~$3,750 | reserve for complex/Level-3 or QA only |

> **Realistic Claude spend with optimizations on: ~$900–$2,100/month** (Sonnet, concise→full,
> caching + batch). Haiku for sub-tasks can pull this lower; a small Opus QA slice adds a little.

---

## 5. Monthly cost — cloud infrastructure (no GPU needed)

| Component | Lean (MVP) | Expected (prod) | High (HA / scale) |
|---|---|---|---|
| App compute (Cloud Run / Fargate, autoscaled) | $50 | $120 | $250 |
| Managed PostgreSQL 15 + pgvector | $120 | $250 | $450 |
| Redis / queue (jobs, cache, rate-limit) | $0–30 | $40 | $80 |
| Object storage (reports, uploads) | $10 | $20 | $40 |
| Load balancer + networking + egress | $30 | $70 | $150 |
| Monitoring / logging | $20 | $60 | $150 |
| Backups / secrets / misc | $20 | $40 | $80 |
| **Cloud total** | **~$260** | **~$600** | **~$1,200** |

*(Excludes the MiHealth front-end hosting, OCR/parsing pipeline, and staff/dev costs.)*

---

## 6. All-in monthly estimate (≈30,000 plans)

| Scenario | Claude (Sonnet, optimized) | Cloud | **Total / month** | **Per plan** |
|---|---|---|---|---|
| Lean (concise reports) | ~$880 | ~$260 | **~$1,150** | **~$0.04** |
| Expected (mixed length) | ~$1,500 | ~$600 | **~$2,100** | **~$0.07** |
| High (full reports + HA) | ~$2,100 | ~$1,200 | **~$3,300** | **~$0.11** |

**Bottom line: roughly $1,200–$3,300/month** to serve ~1,000 plans/day, i.e. **~$0.04–$0.11 per
treatment plan** — dominated by Claude tokens, which the Batch API and prompt caching cut by up to
~95% combined.

### Why not self-host the LLM (Ollama)?
At this volume it's **not** worth it: a single capable GPU instance runs ~$700–$2,500/month *by
itself*, plus ops burden, and quality/safety for clinical narrative is lower. Claude API at
~$900–$2,100/month is cheaper, higher quality, and zero GPU ops. Revisit self-hosting only at far
higher volume or strict on-prem data rules.

---

## 7. Rollout checklist
1. Containerize `tspi_ai_brain`; deploy to Cloud Run/Fargate behind a gateway.
2. Managed Postgres + pgvector; load the official axes/domains/severity data; add PgBouncer.
3. Add Redis + worker for **async batch** plan generation.
4. Wire Claude via **Bedrock/Vertex** (BAA) with **prompt caching** + **Batch API**; tiered model routing.
5. De-identification + consent gating already in the engine — verify before any LLM call.
6. Token/cost telemetry, autoscaling limits, alerts; load-test to ~3× peak.
7. Doctor-validation step in front of patient delivery (CDSS, physician has final authority).

---

### Sources (Claude API pricing, June 2026)
- [Claude API Pricing — Anthropic docs](https://platform.claude.com/docs/en/about-claude/pricing)
- [Prompt caching — Anthropic docs](https://platform.claude.com/docs/en/build-with-claude/prompt-caching)
- [Batch processing — Anthropic docs](https://platform.claude.com/docs/en/build-with-claude/batch-processing)
- [Anthropic API Pricing 2026 — Finout](https://www.finout.io/blog/anthropic-api-pricing)
- [Claude API Pricing 2026: Opus 4.8, Sonnet 4.6, Haiku 4.5 — MetaCTO](https://www.metacto.com/blogs/anthropic-api-pricing-a-full-breakdown-of-costs-and-integration)
- [Claude Cost Optimization: Batch (50% off) & Caching (90% off) — PE Collective](https://pecollective.com/tools/claude-pricing-guide/)

*Costs are estimates for planning; validate against your cloud provider's calculator and your actual
average token counts once the report template is final.*
