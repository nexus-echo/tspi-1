# TSPI Case Report — Common Template

*Derived from three physician-authored TSPI reports (Pradyumn Singh · Mr. Hole · Mrs. Virishali).
Those reports vary in order and dosing style, but share the same building blocks. This is the
**single canonical template** the engine renders from its Analysis Object.*

## How this template is used
- **Structured first, narrative second.** Every section is filled from the deterministic **Analysis
  Object** (axes, modules, safety, NSS…). The LLM only **translates/expands** already-computed content —
  it never invents scores, modules, or values.
- **PII is a placeholder.** The LLM prompt and the engine's brain see only `{{PATIENT}}` tokens +
  de-identified data. Real identity is substituted **after** the LLM, at render time (the re-id step on
  the engine API side). Tokens: `{{patient.full_name}}`, `{{patient.age}}`, `{{patient.sex}}`,
  `{{patient.case_id}}`, `{{report.date}}`.
- **Bilingual.** `report_language = th | en`. Section **labels** and **narrative** localise; canonical
  identifiers (axis codes, module names, marker names, units) stay stable in both.
- **Status.** Draft carries the watermark; patient version is produced only after physician approval.

Section legend — data source: **[E]** engine/deterministic · **[L]** LLM narrative (de-identified) ·
**[T]** template-static guidance · **[R]** re-id/render-time (PII).

---

## 0 · Header  [E][R]
```
TSPI Integrative Case Report
Patient: {{patient.full_name}}   ·   {{patient.age}} y   ·   {{patient.sex}}      [R]
Case: {{patient.case_id}}   ·   Date: {{report.date}}   ·   Language: {{report.language}}
Report ID: {{report.id}}   ·   Algorithm: NSS {{versions.nss}} / Match {{versions.module_match}}
STATUS: {{report.status_banner}}      # e.g. "AI-GENERATED DRAFT — PENDING PHYSICIAN REVIEW — NOT FOR PATIENT RELEASE"
{{pilot_watermark_if_any}}            # "PILOT — PROVISIONAL, NOT CLINICALLY VALIDATED"
```

## 1 · Patient Clinical Summary  [E][L]
- **Presenting picture:** {{summary.presentation}}  *(chief concerns + relevant history)*
- **Key diagnoses / conditions:** {{summary.conditions}}
- **Current medications:** {{summary.medications}}
- **Key findings (measured):** loop {{summary.key_findings}} → `marker: value unit (flag)`
- **Assessment:** Network Severity **{{analysis.nss}}/100** ({{analysis.severity_name}}) ·
  Assessment status **{{nss.assessment_status}}** · Coverage {{nss.coverage}}% ·
  Confidence {{nss.confidence_label}} · Biological uncertainty {{nss.uncertainty_label}}

## 2 · Clinical Overview — a Network Disorder  [L]
One paragraph in the TSPI voice: this is **not a single disease but a multi-system network
dysregulation**; name the central driving axis (usually **A1 Systemic Inflammatory Load** when CRP/hs-CRP
elevated) and the systems involved. Grounded strictly in §3's assessed axes — no new claims.

## 3 · Biological Systems / Axis Analysis  [E][L]
The core diagnostic section. **Loop over each ASSESSED axis** (highest severity first):
```
{{axis.code}} — {{axis.name}}   ({{axis.domain}})        severity: {{axis.severity}}   status: {{axis.status}}
  Key findings:      {{axis.evidence}}                    # measured markers / symptoms behind it
  Interpretation:    {{axis.interpretation}}   [L]        # what it means, de-identified
  Clinical impact:   {{axis.impact}}           [L]
  Evidence:          status {{axis.evidence_status}} · grade {{axis.evidence_grade}} · confidence {{axis.confidence}}
```
Then list **Not-assessed axes** explicitly (`NOT_ASSESSED — reason`) — never shown as "normal".
Then **Relatively normal systems** {{axes.normal}} (measured and unremarkable).

## 4 · Integrated Pathophysiological Model  [E][L]
Render the **root-cause / network chain** as a self-reinforcing loop, e.g.
`{{root_cause_chain}}` → "Hypothyroidism → ↓metabolism → ↑fat → ↑inflammation → brain → insomnia → ↑cortisol → worsens insulin resistance". Names the candidate **root driver(s)** with confidence
({{root_drivers}}); network-level detail only when network data is assessed, else omit.

## 5 · Therapeutic Objectives  [E][L]
Numbered goals derived from the top axes + restoration steps, e.g. *Reduce systemic inflammation ·
Restore microbiome & gut barrier · Restore metabolic energy · Rebuild blood · Normalise autonomic tone*.
Maps to the **9 Restoration Steps** engaged: {{restoration_steps}}.

## 6 · Treatment Protocol — Module Plan  [E][L]
The recommended TSPI modules. Support **two render styles** (choose per case / clinician):

**6a. By phase/step** (foundation-first cases): loop {{steps}} →
```
Step {{step.n}} — {{step.name}} ({{step.phase_window}})     e.g. "Foundation Reset (0–8/12 weeks)"
  {{module.code}} — {{module.name}}
     Dose: {{module.dose}}                                  # e.g. "1–2 caps before breakfast & before sleep"
     Primary target axes: {{module.target_axes}}
     Mechanisms: {{module.mechanisms}}     [L]
     Clinical role: {{module.role}}         [L]
     Safety: {{module.safety_outcome}}      # PASS / PASS_WITH_MONITORING / …
```
**6b. By time-of-day** (stable maintenance cases): Morning / Midday / Evening / Night blocks, each with
its modules + a one-line **Goal**. Same per-module fields as above.

> Every module line carries `reason_selected`; excluded/contraindicated modules are listed separately
> with `reason_not_selected` (matching ≠ prescribing). Provisional modules flagged in PILOT_MODE.

## 7 · Lifestyle Prescription  [E-guided][T]
- **Medication strategy:** {{medication_strategy}} — *continue current; taper only under physician
  supervision; never stop abruptly* (patient-specific meds from §1).
- **Nutrition / Diet:** {{nutrition}} — pattern (e.g. 2 meals, IF window), composition (whole grains,
  plant protein, fibre diversity), hydration (mineral water, TDS/quality note).
- **Exercise:** {{exercise}} — aerobic (duration/intensity) + resistance; tie to axes (fat metabolism
  A6, insulin sensitivity A5, mitochondria A8, inflammation A1).
- **Behavioural & Sleep:** {{sleep_behaviour}} — screen hygiene, consistent timing, environment.

## 8 · Expected Functional Markers (timeline)  [T][L]
```
Weeks 1–2:  {{expected.wk1_2}}      # e.g. improved bowel movement, slight calming
Weeks 3–6:  {{expected.wk3_6}}
Weeks 6–8:  {{expected.wk6_8}}
```

## 9 · Follow-up Monitoring  [E][T]
- **Repeat labs (after ~2 months):** {{followup.labs}} — grouped (Metabolic · Inflammation · Thyroid ·
  Nutritional/Cellular · Optional) from the markers implicated in §3.
- **Clinical (non-lab) tracking:** {{followup.clinical}} — sleep quality, anxiety/energy, bowel
  regularity, weight/waist, symptom-specific outcomes.

## 10 · Final Clinical Principle  [E][T]
Restate in the **3 Keys** frame — which key each core module restores:
**Metabolic Energy (Key A)** · **Biological Dynamics (Key B)** · **Biointegrity (Key C)**.
Ultimate goal: **not symptom control, but return to Prakati (biological balance).**

## 11 · Safety, Provenance & Approval  [E]
- **Red flags / critical alerts:** {{safety.red_flags}} (always shown, even at low NSS).
- **Safety notes per module:** {{safety.module_notes}}.
- **Provenance:** registries + versions used ({{versions.all}}); every claim traces to patient evidence
  + an approved (or PILOT-provisional) registry entry.
- **Disclaimer:** *TSPI is decision-support; the physician has final authority. Not a prescription until
  approved.*
- **Approval block** (physician report): reason_selected/not_selected summary · physician edits ·
  `{{approval.physician}} · {{approval.datetime}} · {{approval.signature}}`.

---

## Two audiences (same Analysis Object, differ only in language/detail)
- **Physician report:** all sections, full evidence chain, provenance, reason_selected/not_selected.
- **Patient report (post-approval only):** friendly language; sections → **Confirmed · Probable · Not
  yet known · Suggested next tests · Your approved plan (modules + lifestyle) · Safety warnings**. No
  raw scores, no unapproved modules, no hypotheses stated as fact.
- **Multi-Omics:** only if real omics exist; otherwise an "Omics Readiness" note (no simulated values).

## Analysis Object → template field map (build reference)
| Template section | Analysis Object source |
|---|---|
| §1 summary/NSS | `analysis.nss`, `nss_detail`, `axis_scores`, patient meds/conditions |
| §3 axis analysis | `axis_scores[]` (severity, status, evidence_*, confidence) + `not_assessed[]` |
| §4 network model | `root_cause_chain`, `root_drivers`, network validation status |
| §5 objectives / §6 steps | `restoration_steps`, selected `modules[]` |
| §6 module plan | `modules[]` (code, name, dose, target_axes, safety_outcome, reason_*), `considered_modules[]` |
| §9 monitoring | markers implicated in `axis_scores` + `marker_registry` |
| §11 safety/approval | `safety_alerts`, `red_flags`, `versions`, validation record |

*Sections 7 (lifestyle) and 8 (timeline) are partly template-static today (the engine doesn't yet
generate diet/exercise text); mark them as guidance and let the physician edit. A future phase can add
axis-driven lifestyle rules.*
