import { FormEvent, useEffect, useState } from "react";
import { getIntake, Intake, saveIntake } from "../api/patients";

const toList = (s: string) => s.split(",").map((x) => x.trim()).filter(Boolean);
const fromList = (a: string[]) => (a || []).join(", ");

export default function IntakeForm({ patientId, readOnly = false, onChange }: { patientId: string; readOnly?: boolean; onChange?: () => void }) {
  const [symptoms, setSymptoms] = useState("");
  const [conditions, setConditions] = useState("");
  const [medications, setMedications] = useState("");
  const [sleep, setSleep] = useState("");
  const [diet, setDiet] = useState("");
  const [msg, setMsg] = useState("");

  useEffect(() => {
    getIntake(patientId).then((i: Intake | null) => {
      if (!i) return;
      setSymptoms(i.symptoms_text || "");
      setConditions(fromList(i.conditions));
      setMedications(fromList(i.medications));
      setSleep(i.lifestyle?.sleep || "");
      setDiet(i.lifestyle?.diet || "");
    });
  }, [patientId]);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setMsg("");
    await saveIntake(patientId, {
      symptoms_text: symptoms,
      conditions: toList(conditions),
      medications: toList(medications),
      lifestyle: { sleep, diet },
    });
    setMsg("Saved");
    onChange?.();
  }

  return (
    <form className="card" style={{ marginBottom: 16 }} onSubmit={onSubmit}>
      <h2>Symptoms &amp; history</h2>
      <label>Symptoms</label>
      <input value={symptoms} onChange={(e) => setSymptoms(e.target.value)} disabled={readOnly}
        placeholder="e.g. fibroid, hypertension, inflammation, stress" />
      <div className="row">
        <div>
          <label>Conditions (comma-separated)</label>
          <input value={conditions} onChange={(e) => setConditions(e.target.value)} disabled={readOnly} />
        </div>
        <div>
          <label>Medications (comma-separated)</label>
          <input value={medications} onChange={(e) => setMedications(e.target.value)} disabled={readOnly} />
        </div>
      </div>
      <div className="row">
        <div>
          <label>Sleep</label>
          <input value={sleep} onChange={(e) => setSleep(e.target.value)} disabled={readOnly} placeholder="e.g. poor" />
        </div>
        <div>
          <label>Diet</label>
          <input value={diet} onChange={(e) => setDiet(e.target.value)} disabled={readOnly} placeholder="e.g. vegetarian" />
        </div>
      </div>
      {msg && <div className="ok">{msg}</div>}
      {!readOnly && <button>Save intake</button>}
    </form>
  );
}
