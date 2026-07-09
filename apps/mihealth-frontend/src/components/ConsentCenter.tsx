import { useEffect, useState } from "react";
import { CONSENT_SCOPES, Consent, getConsents, setConsent } from "../api/patients";

// Consent toggles. Read-only when the viewer is staff looking at someone else.
export default function ConsentCenter({ patientId, readOnly = false, onChange }: { patientId: string; readOnly?: boolean; onChange?: () => void }) {
  const [map, setMap] = useState<Record<string, boolean>>({});
  const [busy, setBusy] = useState<string | null>(null);

  async function load() {
    const rows: Consent[] = await getConsents(patientId);
    const m: Record<string, boolean> = {};
    rows.forEach((r) => (m[r.scope] = r.granted));
    setMap(m);
  }
  useEffect(() => {
    load();
  }, [patientId]);

  async function toggle(scope: string, granted: boolean) {
    setBusy(scope);
    try {
      await setConsent(patientId, scope, granted);
      setMap((m) => ({ ...m, [scope]: granted }));
      onChange?.();
    } finally {
      setBusy(null);
    }
  }

  return (
    <div className="card" style={{ marginBottom: 16 }}>
      <h2>Consent</h2>
      <p className="muted">Granular consent — each scope is independently required where relevant.</p>
      {CONSENT_SCOPES.map((s) => (
        <div key={s.scope} className="row" style={{ alignItems: "center", marginTop: 10 }}>
          <div style={{ flex: 3 }}>
            <strong>{s.label}</strong>
            {s.scope === "ai_analysis" && <span className="badge" style={{ marginLeft: 8 }}>required</span>}
            <div className="muted">{s.help}</div>
          </div>
          <div style={{ flex: 1, textAlign: "right" }}>
            <label style={{ display: "inline-flex", gap: 8, alignItems: "center", margin: 0 }}>
              <input
                type="checkbox"
                style={{ width: "auto" }}
                checked={!!map[s.scope]}
                disabled={readOnly || busy === s.scope}
                onChange={(e) => toggle(s.scope, e.target.checked)}
              />
              {map[s.scope] ? "Granted" : "Not granted"}
            </label>
          </div>
        </div>
      ))}
    </div>
  );
}
