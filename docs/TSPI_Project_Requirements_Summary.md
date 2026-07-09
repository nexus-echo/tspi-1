# TSPI — Project Requirements & System Summary

*Prepared from the full project folder: architecture docs, the 39-axes & 200-modules data, the
product sheets, the de-identified reference patient case, the framework images, the MiHealth
front-end docs, and the stakeholder
chat. This is the shared reference that the Master Prompt and the Report-Generation Methodology
both build on.*

---

## 1. What TSPI is (in one paragraph)

TSPI (**The Standardized Network Phytochemicals Intelligence Platform**) is an **AI Diagnostic
Intelligence Platform** built under **TCHI** (Thailand Health Community Intelligence Institute).
It is the **back-end "brain"** that powers **MiHealth**, the consumer/clinician/admin-facing
front end (see §1a). TSPI treats chronic, multi-system illness as a single **network disease**
rather than a list of separate diagnoses. It ingests a patient's full picture — symptoms,
history, and **any** lab types, imaging, medications, wearables, and multi-omics — translates it
into biological signals, maps those signals onto a fixed model of the human body, finds the
root-cause chain, and produces a **TSPI Case Report**: a sequenced, multi-target plan of
phytochemical modules and lifestyle changes aimed at restoring the body's natural balanced
state, **Prakati (ปกติสภาวะ)**. A doctor validates every recommendation, and outcomes feed back
so the system learns. **TSPI is generic by design** — it must handle any patient and any
condition; the fibroid case in this folder is an illustrative *reference example only*.

## 1a. The MiHealth ↔ TSPI ecosystem (face vs brain)

**MiHealth is the face; TSPI is the brain.** MiHealth AI is the consumer-facing Personal Health
Intelligence Platform ("My Data. My Intelligence. Anywhere."); TSPI is the deep biological
intelligence engine behind it. Users only ever see MiHealth. The architecture is four layers:

1. **Layer 1 — MiHealth AI (consumer platform):** accounts, health memory, lifelong health
   timeline, dashboard/health score, AI Health Advisor chat, secure doctor sharing, drug-safety
   checker, notifications. Upload via LINE OA, Telegram, mobile app, web — PDF/image/voice/video.
2. **Layer 2 — MiHealth Intelligence Layer (orchestration):** OCR engine, medical parser
   (unstructured → structured records), timeline engine, symptom-intake engine, drug-safety
   engine, health-advisor engine.
3. **Layer 3 — TSPI Intelligence Engine (the brain, behind the scenes):** Fundamental-Medicine
   engine (maps all data to **3 Keys / 9 Steps / 12 Domains / 39 Axes**), root-cause analysis,
   biological-intelligence integration (symptoms + labs + imaging + meds + genome + microbiome +
   proteomics + metabolomics), risk-prediction engine, precision-health engine.
4. **Layer 4 — TSPI Intervention Layer (consent-gated):** activated only on explicit user
   authorization — precision nutrition/lifestyle/microbiome/genome programs, clinical protocols,
   health coaching, and connection to healthcare professionals (Samutthan Clinic).

**Roles & business model:** MiHealth = Platform Layer (mass adoption; free Basic, AI Pro
999 THB/yr, Founder Lifetime 2,990 THB, precision-omics add-ons); TSPI = Intervention & Revenue
Layer. Its most valuable asset is the lifelong, trusted health-data relationship — not
subscriptions.

**Governance (non-negotiable):** user-owned data; modular/granular, revocable consent (AI
analysis · doctor sharing · research · TSPI connection · precision services each toggled
separately); identity by phone/email + internal UUID (avoid national-ID as primary key); MiHealth
positions as a Health Intelligence Assistant — it explains/flags/educates but **does not diagnose
definitively, prescribe, or instruct medication changes**; all AI outputs carry safety messaging
and "consult a qualified professional." TSPI's clinician-validation layer sits on top of this.

---

## 2. The biological framework (the heart of the system)

TSPI maps the human body through a fixed four-level hierarchy. Everything the AI does ties back
to this structure.

### 2.1 The 3 Keys of Health (top-level pillars)
| Key | Focus |
|---|---|
| **A. Metabolic Energy** | mitochondria, ATP / energy production, metabolic flexibility |
| **B. Biological Dynamics** | adaptability, nervous system, hormonal signaling, circadian rhythm, stress adaptation |
| **C. Biointegrity** | DNA stability, tissue resilience, microbiome integrity, cellular structure |

### 2.2 The 12 Domains + 39 Biological Axes (the analytical map)
The body is decomposed into **12 domains**, subdivided into **39 mechanistic axes (A1–A39)**,
each with sub-axes (A/B/C…). An axis is a *functional dimension of stability*, not an organ or a
disease. Each axis is rated on a spectrum — **Optimal → Subclinical imbalance → Functional
impairment → Pathological dysfunction** — which lets TSPI catch early drift before overt disease.
Axes are interdependent: dysfunction in one propagates across the network ("network collapse").

Representative domain groupings (per the data files): Immune–Infection Governance ·
Metabolic–Energy Core · Genomic–Longevity Programming · Detox–Digestive–Gut Ecosystem ·
Vascular–Circulation–Stroke Prevention · Repair–Fibrosis–Regeneration · Musculoskeletal &
Structural Integrity · Endocrine Network · Neuro–Sleep–Stress · Organ Resilience · Oncology ·
Cognitive–Emotional Loop.

### 2.3 The 9 Steps of Wellness (the therapeutic ladder to Prakati)
Treatment climbs these in order; foundational steps are never skipped to chase a manifestation:
1. Detoxification → 2. Microbiome Restoration → 3. Immune Regulation → 4. Redox Balance →
5. Metabolic & Mitochondrial Recovery → 6. Autophagy & Cellular Clearance → 7. Genomic Stability
→ 8. Genomic Regulation → 9. **Prakati** (optimal biological balance).

### 2.4 Modules (the therapeutic units)
A **module** is a single TSPI **product** (a polyherbal formulation) that modulates several axes at
once (network pharmacology). Per the domain experts, **1 module = 1 product** — a module is *not* a
bundle/combination of products, and there are no sub-modules. Each module maps: product →
ingredients → mechanisms → active compounds (LC-MS) → **target 39-axes** → safety/contraindications
→ dosage → therapeutic focus, and is keyed by **H-Code** (PhytoCore Code is the long-term scientific
ID). Target catalog size ≈ **200 modules**. *(Ref: `TSPI_Module_Registry_Questions_For_Experts.md`.)*

---

## 3. The reasoning pipeline (how a patient becomes a plan)

From the System Explanation doc, distilled into 9 stages:

1. **Patient enters data** — symptoms, history, lifestyle, diet, sleep, stress, labs, scans,
   meds, (future) wearables.
2. **Symptom → biological signal** — e.g. fatigue→mitochondria, high sugar→insulin resistance,
   inflammation→immune activation, stress→cortisol imbalance.
3. **Multiomic reasoning** — combine systems (metabolism + inflammation + hormones + gut +
   liver + immune) instead of "one symptom = one disease."
4. **Biological pathway analysis** ("the brain") — which pathways are damaged, which organs
   stressed, which systems connected → the root-cause chain.
5. **Phytochemical intelligence** — match herbs/compounds to the damaged pathways
   (pathway-based herbal intelligence, not random herbal advice).
6. **AI recommendation engine** — produce conditions, biological explanation, staged treatment,
   herbal + food + lifestyle advice, further tests, risk alerts.
7. **Doctor validation layer** — AI suggestion → doctor review → approval/correction → final.
8. **Patient monitoring** — track labs, symptoms, response, side effects.
9. **Learning loop** — learn which treatment worked, for which biological pattern, for which
   patient type; get smarter over time.

---

## 4. Technical architecture (current recommended MVP)

A containerized, decoupled clinical-AI stack (from `SYSTEM ARCHITECTURE.docx` /
`system_architecture_report.md`):

- **Client / Ingress — Next.js 14** (`tspi_frontend`, port 3000): clinical dashboard for
  doctors + patient portal + LINE LIFF; also acts as the API gateway/reverse proxy.
- **Core Backend — Django REST Framework** (`tspi_core_backend`, port 8000): master data &
  EMR; clinical taxonomy models — `ClinicalDomain` (12), `ClinicalAxis` (39),
  `ClinicalSubAxis` (~114), `ClinicalModule`, `ClinicalModuleMapping` (module↔axis relevance);
  `AIValidationWorkflow` (doctor sign-off) and `OutcomeRecord` (feedback learning).
- **AI Engine — FastAPI** (`tspi_ai_engine`, port 8001): scoring + a **directed graph
  (NetworkX)** of axis dependencies with score propagation and **PageRank-style root-cause**
  discovery; a rules/registry engine with safety overrides; a **RAG** layer over ChromaDB
  collections (`clinical_axes`, `modules_kb`, `herbal_kb`); longitudinal feedback / weight
  calibration.
- **LLM layer — Ollama (local `qwen2.5:14b`)** with cloud fallbacks (Claude, DeepSeek, Groq).
- **Data — Supabase PostgreSQL 15** (relational EMR) + **Supabase Storage** (patient uploads) +
  **ChromaDB** persistent vector store.

The LLM is explicitly framed as only the **communication layer**; the real system is the
biological-reasoning + pathway + phytochemical + learning infrastructure.

---

## 5. Data assets in this folder (inventory)

| Asset | Location | Role |
|---|---|---|
| 39-axes definitions (JSON) | `39-axes/tspi_39_axes_final.json` | axes, sub-axes, suggested modules |
| 39-axes definitions (Markdown) | `39-axes/axes/axis_01…axis_39.md` | one clean file per axis (39 files) |
| Domain/axes summary decks | `39-axes/*.pdf` | Thai-language summary of 39 axes / 12 domains / 3 keys |
| Modules dataset (JSON) | `200 modules/tspi_200_modules_v1.json` | product→mechanism→target axes→dosage |
| Modules dataset (Excel) | `200 modules/200 module tspi 2 …xlsx` | source spreadsheet |
| Product sheets | `products/product_*.md` | per-product detail sheets |
| Framework posters | `keys-domains/*.jpg/.jpeg` | 3 Keys, 9 Steps, 12 Domains, product research |
| Patient inputs | reference patient folder: `symptons.txt`, `Report-1.pdf`, scan images | case input (handle as PII) |
| **Reference case report** | reference patient folder: `case Fibroids …pdf` | de-identified style/structure template only |
| System explanation | `TSPI_System_Explanation.pdf` | plain-language pipeline |
| Architecture | `SYSTEM ARCHITECTURE.docx`, `system_architecture_report.md`, `TSPI Current Recommended Hybrid Architecture (Practical MVP).pdf` | tech stack |
| Institute context | `TCHI …pdf`, `keys-domains/IMG-…WA0000.jpg` | TCHI org, mission, network |
| Stakeholder chat | `WhatsApp Chat with Jiten Bhakhda.txt` | framework decisions & rationale |
| MiHealth front-end | `mihealth/MiHealth System Architecture.txt`, `mihealth-ai scope.pdf` | 4-layer ecosystem, data sources, channels |
| MiHealth business model | `mihealth/MiHealth AI Business Model & Membership Strategy.txt` | freemium tiers, platform vs intervention layer |
| MiHealth privacy/governance | `mihealth/MiHealth Data Privacy, Health Data Governance & Regulatory Strategy.txt` | consent, ownership, ToS |
| MiHealth posters | `mihealth/WhatsApp Image 2026-06-16 …jpeg` | Fundamental Medicine Architecture; Reductionism vs Network Pharmacology |

---

## 6. Functional requirements (what the system must do)

1. **Ingest** structured + unstructured patient data of **any kind** (text, routine + functional
   labs, hormones, tumor markers, imaging PDFs/images, medications, wearables, multi-omics; via
   MiHealth: PDF/image/voice/video, LINE OA, Telegram, app, web) — never limited to a fixed lab
   panel.
2. **Normalize** any symptoms and lab parameters into standardized biological signals (via the
   MiHealth OCR + medical-parser layer), tolerant of unfamiliar tests and units.
3. **Map** signals onto the 39 axes with a 4-level severity score per axis.
4. **Compute** the root-cause chain and rank driver vs amplifier axes (graph + PageRank).
5. **Match** modules to dysfunctional axes via the module↔axis mapping, honoring safety rules.
6. **Sequence** interventions across phases (Foundation → Functional → Structural/Endocrine).
7. **Generate** three output tiers: (a) short clinical protocol, (b) full case report,
   (c) monitoring plan with phase-specific target trajectories.
8. **Route** every output through doctor validation before patient delivery.
9. **Monitor** longitudinally and **learn** from outcomes (adjust axis weights).
10. **Enforce safety**: contraindication filtering, "for clinician review" framing, no
    aggressive structural/endocrine action before foundation is stable.
11. **Stay generic**: support any condition and any lab/omics inputs; never hard-code logic to a
    single disease example (the fibroid case is reference-only).
12. **De-identify outputs**: TSPI Case Reports and all reusable templates must exclude PII (name,
    address, phone, email, ID numbers, exact DOB, facility identifiers) — patient referenced by a
    case ID + minimal demographics (age band, sex).
13. **Integrate with MiHealth**: consume structured records + consent flags from MiHealth's
    intelligence layer; return reports/insights to MiHealth; honor consent and audit logging.

---

## 7. Data-integrity gaps & open questions (please confirm)

While reviewing the data files I found mismatches between the **stated framework** and the
**actual data files**. These should be resolved before the AI is wired to them, because the AI
will only be as correct as the catalog it reads:

1. **Domain count:** the framework says **12 domains**, but `tspi_39_axes_final.json` contains
   **10** domain objects. Two domains (e.g. Oncology and Cognitive–Emotional Loop appear folded
   into "Organ Axis + Oncology"). → *Which is canonical — 12 split domains, or 10 grouped?*
2. **Axis counts per domain look malformed:** Domain 10 ("Organ Axis + Oncology") parses with a
   very large/duplicated axis list, pushing the JSON's total above 39. The clean, one-file-per-axis
   set in `39-axes/axes/` is exactly **39** and looks authoritative. → *Treat the `axes/*.md`
   folder as the source of truth and regenerate the JSON from it?*
3. **"200 modules" vs reality:** ✅ **Resolved (domain experts):** **1 module = 1 product**; the
   varying counts (65 JSON / 276 md / 282 xlsx) are duplicates + partial exports. Official target
   ≈ **200 modules**; the exact **active count** arrives with the updated master registry file.
4. **Module naming:** the 39-axes JSON references modules by short names (KS, Beta, IM6,
   Minoza, Kerra…), but product sheets use long names/IDs. → *A single ID map (short name ↔
   product ID ↔ TSPI ID) is needed so axis→module lookups resolve cleanly.*
5. **Reference report modules vs catalog:** the reference report prescribes "ZAMINZYME" and a
   generic "Blood Nourishing Module" — confirm these resolve to specific catalog products with
   defined target axes and dosing.

Resolving these five items would let the report generator (next doc) pull modules
deterministically instead of guessing.

---

## 8. The reference case (fibroid example) — a STYLE template only

One de-identified case (a 46-year-old woman: fibroids + hypertension + high CRP + diabetic-range
HbA1c + microcytic anemia + elevated T3/suppressed TSH + elevated IgE + post-menopausal
stress-triggered bleeding) is included **only to demonstrate report structure and voice** — not
as a clinical default. Its value is showing how TSPI reframes many "separate" diagnoses as one
network disease (microbiome/nutrient dysfunction → inflammation → hormonal/metabolic/vascular
cascades), maps them to axes, and prescribes a **staged plan** (Foundation Reset → targeted
correction → fine-tuning → Prakati) with doses, lifestyle, monitoring, and explicit safety gates.

**Important:** every real patient is different. The generator must adapt the *structure* to
whatever conditions and lab types the actual patient presents, and all outputs/templates must be
**de-identified** (no name or other PII). The companion *TSPI Report-Generation Methodology*
turns this structure into a repeatable, condition-agnostic recipe.
