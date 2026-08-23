# Why the System Report ≠ the Doctor Report — Root-Cause Analysis

*Comparing the **system-generated** `MiHealth Portal.pdf` against the **doctor-written**
`case Fibroids Mrs Virishali sing…pdf`, for the same patient.*

## TL;DR
The gap is **not** the embedding model and **not** the LLM. The system report is thin because the
**patient's lab data and full symptom list were never sent to the engine** — the `/report` call
contained essentially only `symptoms: "stress"`. The engine behaved correctly for the input it
got. When I re-ran the engine with the **actual labs**, it produced a doctor-aligned result.

---

## 1. Side-by-side

| | **System report (MiHealth Portal, 2 pp)** | **Doctor report (42 pp)** |
|---|---|---|
| Inputs used | **only "stress"** — *"No other symptoms, labs, or imaging are reported."* (its own words) | full labs + symptoms (CRP 21.57, HbA1c 6.5, Hb 10.8/MCV 67.2, TSH 0.416, IgE, Vit D, fibroid, HTN, bleeding) |
| Axes found | **1** — A34 (stress) | **~7 core + amplifiers** — inflammation, glucose, hematopoiesis, hormone, vascular, thyroid, autonomic |
| Severity | NSS 40 / Level 2 | "system unstable → foundation reset" (high-severity) |
| Modules | **1** — KS | KS · Kerra+Minoza+IM6 · ZAMINZYME · Blood-Nourishing + lifestyle |
| Plan | single step | 3-step staged plan + monitoring + cautions |

## 2. The root cause (proven, not guessed)

I fed the deployed engine the **exact minimal input** and it reproduced the MiHealth PDF *to the
number*:

- Input `symptoms="stress"`, no labs → **A34 only, NSS 40, Level 2, KS only** ✅ (identical to the PDF)

Then I fed it the **real patient data** (CRP 21.57, HbA1c 6.5, Hb 10.8, MCV 67.2, TSH 0.416,
Vit D 27.6 + the full symptom list):

- → **7 axes** (A1, A5, A26, A33, A8, A15, A34), **NSS 97 / Level 3**, **8 modules**, root-cause
  chain `A34→A8→A15→A1→A5→A26→A33` — i.e. the inflammation/metabolic/anemia/hormone/thyroid network
  the **doctor** described.

**Conclusion:** the engine is sound; it was **starved of input**. The MiHealth front end (or the
caller) sent only the chief complaint ("stress"), not the parsed lab report. Garbage-in → thin-out.

## 3. So is it the embeddings or the LLM? No.

- **Embeddings (bge-m3):** only used for *semantic fallback on unrecognized labs*. With **zero
  labs** sent, embeddings were never exercised — they had no effect on this report. Not the cause.
- **LLM (DeepSeek):** it wrote the narrative **faithfully from the structured analysis** — it even
  correctly stated "no other labs reported." A bigger/better LLM would produce the **same thin
  report**, because the structured input was thin. The LLM is not the bottleneck here.
- **The cause is missing data** at the input boundary (and, secondarily, clinical depth — see §5).

## 4. Why your earlier in-chat report looked right

When we drafted the sample report **inside this Claude chat**, *I* had the **entire lab PDF** and
reasoned over every value manually (CRP→A1, HbA1c→A5, Hb/MCV→A26, TSH→A33, IgE→A2, fibroid→A31…),
then wrote the full multi-section report. So it matched the doctor because it used **complete
inputs + full clinical reasoning**. The deployed pipeline got neither the full inputs (this call)
nor the full official clinical rules yet (Phase 1 still provisional).

## 5. Two real gaps to fix

**Gap A — INPUT (the big one, fixed by integration):**
The `/report` payload must carry the **parsed labs, all symptoms, imaging, meds, conditions** — not
just the chief complaint. In the MiHealth architecture, the **Intelligence Layer (OCR + medical
parser)** is supposed to turn the uploaded lab PDF into structured `labs:[...]` before calling
TSPI. That step was skipped/empty here. **This single fix moves the system report from 1 axis to 7.**

**Gap B — CLINICAL DEPTH (needs the official inputs we listed):**
Even with full labs, the engine won't yet equal the doctor's 42-page depth because Phase 1 is still
**placeholder**:
- Lab→axis dictionary covers ~12 common markers (so an unlisted lab is missed unless RAG catches it).
- Severity thresholds + the **NSS formula** are heuristics (pending official rules).
- **module→axis map** is provisional (pending the official map).
- The narrative is a concise 7-section CDSS report by design — not a 42-page treatise (the prompt
  can be expanded if you want deeper mechanism chapters).
These are exactly the items in `TSPI_Official_Inputs_Needed_Checklist.md`.

## 6. What to do

1. **Fix the input contract (highest impact, do first):** ensure MiHealth's OCR/parser fills
   `labs`, `symptoms`, `imaging`, `medications`, `conditions` before calling `/report`. Add a guard
   in TSPI that **flags low-information inputs** (e.g. "0 labs received") so a near-empty call is
   obvious instead of silently producing a 1-axis report.
2. **Load the official Phase-1 data** (lab→axis dictionary, severity thresholds, NSS formula,
   module→axis map) to deepen accuracy.
3. **(Optional) richer narrative:** expand the report-composer prompt to add per-axis mechanism
   detail if you want output closer to the doctor's length.

> Bottom line: the model choices are fine. **Send the engine the same data the doctor had** (labs +
> full symptoms), then layer in the official clinical rules — and the system report converges on the
> doctor's.
