import { useState } from "react";
import Field from "../components/Field.jsx";
import { DEFAULT_SETTINGS, ESTIMATES, FIXED_COST_ITEMS } from "../lib/defaults.js";
import { money } from "../lib/format.js";
import styles from "./Settings.module.css";

const isEstimate = (settings, path) => {
  const value = path.startsWith("advanced.") ? settings.advanced[path.slice(9)] : settings[path];
  return value === ESTIMATES[path];
};

export default function Settings({ settings, setSettings, regions, fixedTotal, errors }) {
  const set = (key) => (value) => setSettings({ ...settings, [key]: value });
  const setFixed = (key) => (value) => setSettings({ ...settings, fixedCosts: { ...settings.fixedCosts, [key]: value } });
  const setAdv = (key) => (value) => setSettings({ ...settings, advanced: { ...settings.advanced, [key]: value } });
  const err = (path) => errors[`truckSettings.${path}`];
  const est = (path) => isEstimate(settings, path);

  return (
    <div className={styles.screen}>
      <p className={styles.intro}>
        Set these once. They stay on this phone. Yellow <strong>estimate</strong> tags mark placeholder numbers;
        replace them with yours.
      </p>

      <section className={styles.card}>
        <h2>Monthly fixed costs ($ per month)</h2>
        <div className={styles.grid2}>
          {FIXED_COST_ITEMS.map(([key, label]) => (
            <Field key={key} label={label} value={settings.fixedCosts[key]} onChange={setFixed(key)}
              placeholder="0" />
          ))}
        </div>
        <p className={`${styles.total} num`} aria-live="polite">
          Total: <strong>{money(fixedTotal)}</strong> / month
        </p>
        {err("monthlyFixedCosts") && <p className={styles.error}>{err("monthlyFixedCosts")}</p>}
      </section>

      <section className={styles.card}>
        <h2>Your truck</h2>
        <div className={styles.grid2}>
          <div className={styles.full}>
            <label htmlFor="fuel-region">Fuel region (EIA)</label>
            <select id="fuel-region" value={settings.fuelRegion} onChange={(e) => set("fuelRegion")(e.target.value)}>
              {regions.map((r) => (
                <option key={r.code} value={r.code}>
                  {r.name}
                </option>
              ))}
            </select>
          </div>
          <Field label="MPG" value={settings.mpg} onChange={set("mpg")} estimate={est("mpg")} error={err("mpg")} />
          <Field label="Your share" unit="%" value={settings.payoutPercent}
            onChange={set("payoutPercent")} hint="100 if you run your own authority" error={err("payoutPercent")} />
          <Field label="Maintenance" unit="$/mi" value={settings.maintenanceCpm} onChange={set("maintenanceCpm")}
            estimate={est("maintenanceCpm")} error={err("maintenanceCpm")} />
          <Field label="Tires" unit="$/mi" value={settings.tiresCpm} onChange={set("tiresCpm")}
            estimate={est("tiresCpm")} error={err("tiresCpm")} />
          <Field label="Other" unit="$/mi" value={settings.otherCpm} onChange={set("otherCpm")}
            error={err("otherCpm")} />
        </div>
      </section>

      <section className={styles.card}>
        <h2>Your rules</h2>
        <Field label="Lowest profit per day you'd take" unit="$/day" value={settings.targetProfitPerDay}
          onChange={set("targetProfitPerDay")} placeholder="Optional" error={err("targetProfitPerDay")} />
        <fieldset className={styles.fieldset}>
          <legend>When you finish a load midday…</legend>
          <label className={styles.radio}>
            <input type="radio" name="rounding" checked={settings.daysRoundingMode === "fractional"}
              onChange={() => set("daysRoundingMode")("fractional")} />
            <span>
              <strong>I keep rolling.</strong> Count part-days (1.2 days).
            </span>
          </label>
          <label className={styles.radio}>
            <input type="radio" name="rounding" checked={settings.daysRoundingMode === "whole"}
              onChange={() => set("daysRoundingMode")("whole")} />
            <span>
              <strong>The day is done.</strong> Round up to whole days (2 days).
            </span>
          </label>
        </fieldset>
      </section>

      <details className={styles.card}>
        <summary>Advanced</summary>
        <div className={styles.grid2}>
          <Field label="Average speed" unit="mph" value={settings.advanced.avgSpeedMph} onChange={setAdv("avgSpeedMph")}
            estimate={est("advanced.avgSpeedMph")} error={err("advanced.avgSpeedMph")} hint="Including stops" />
          <Field label="Buffer per load" unit="h" value={settings.advanced.bufferHours} onChange={setAdv("bufferHours")}
            estimate={est("advanced.bufferHours")} error={err("advanced.bufferHours")} hint="Pre-trip, fuel, loading" />
          <Field label="Days worked/mo" value={settings.advanced.workingDaysPerMonth}
            onChange={setAdv("workingDaysPerMonth")} estimate={est("advanced.workingDaysPerMonth")}
            error={err("advanced.workingDaysPerMonth")} />
          <div>
            <label htmlFor="cycle">Hours-of-service cycle</label>
            <select id="cycle" value={settings.advanced.maxCycleHours}
              onChange={(e) => setAdv("maxCycleHours")(e.target.value)}>
              <option value="70">70 hours / 8 days</option>
              <option value="60">60 hours / 7 days</option>
            </select>
          </div>
        </div>
      </details>

      <Backup settings={settings} setSettings={setSettings} />
    </div>
  );
}

function Backup({ settings, setSettings }) {
  const [text, setText] = useState("");
  const [message, setMessage] = useState("");

  async function copy() {
    const json = JSON.stringify(settings);
    try {
      await navigator.clipboard.writeText(json);
      setMessage("Copied. Paste it into Notes or a text to yourself.");
    } catch {
      setText(json);
      setMessage("Couldn't copy automatically. Select the text below and copy it.");
    }
  }

  function restore() {
    try {
      const parsed = JSON.parse(text);
      if (typeof parsed !== "object" || parsed === null || !parsed.fixedCosts) throw new Error("bad");
      setSettings({
        ...DEFAULT_SETTINGS,
        ...parsed,
        fixedCosts: { ...DEFAULT_SETTINGS.fixedCosts, ...parsed.fixedCosts },
        advanced: { ...DEFAULT_SETTINGS.advanced, ...parsed.advanced },
      });
      setMessage("Settings restored.");
      setText("");
    } catch {
      setMessage("That doesn't look like a Haul Math settings backup.");
    }
  }

  return (
    <section className={styles.card}>
      <h2>Backup</h2>
      <p className={styles.small}>
        iPhone Safari can clear saved data. Keep a copy, or add Haul Math to your home screen.
      </p>
      <div className={styles.buttons}>
        <button type="button" className={styles.button} onClick={copy}>
          Copy my settings
        </button>
      </div>
      <label htmlFor="restore">Paste a backup to restore</label>
      <textarea id="restore" rows={3} value={text} onChange={(e) => setText(e.target.value)} />
      <div className={styles.buttons}>
        <button type="button" className={styles.button} onClick={restore} disabled={!text.trim()}>
          Restore settings
        </button>
      </div>
      {message && (
        <p className={styles.small} role="status">
          {message}
        </p>
      )}
    </section>
  );
}
