import { useEffect, useRef } from "react";
import DieselLine from "../components/DieselLine.jsx";
import LoadCard from "../components/LoadCard.jsx";
import Results from "../components/Results.jsx";
import TripContext from "../components/TripContext.jsx";
import { LETTERS, MAX_LOADS, emptyLoad } from "../lib/defaults.js";
import styles from "./Compare.module.css";

export default function Compare({
  settings,
  trip,
  setTrip,
  loads,
  setLoads,
  fuel,
  regionName,
  response,
  rankCount,
  errors,
  stale,
  busy,
  fixedTotal,
  usingEstimates,
  serverError,
  onRank,
  onNewComparison,
  onOpenSettings,
}) {
  const resultsRef = useRef(null);
  const settingsErrors = Object.entries(errors).filter(([f]) => f.startsWith("truckSettings."));
  const generalErrors = Object.entries(errors).filter(([f]) => f === "loads" || f === "");
  const target = settings.targetProfitPerDay === "" ? null : Number(settings.targetProfitPerDay);

  // Scroll to the results after each successful rank (rankCount changes only then).
  useEffect(() => {
    if (rankCount > 0) resultsRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
  }, [rankCount]);

  return (
    <div className={styles.screen}>
      <TripContext trip={trip} onChange={setTrip} errors={errors} maxCycleHours={settings.advanced.maxCycleHours} />
      <DieselLine
        fuel={fuel}
        regionName={regionName}
        override={trip.dieselOverride}
        onOverride={(v) => setTrip({ ...trip, dieselOverride: v })}
        error={errors["truckSettings.dieselPrice"]}
      />

      <h2 className={styles.loadsHeading}>Load offers</h2>
      {loads.map((load, i) => (
        <LoadCard
          key={load.id}
          letter={LETTERS[i]}
          index={i}
          load={load}
          errors={errors}
          onChange={(next) => setLoads(loads.map((l) => (l.id === load.id ? next : l)))}
          onRemove={loads.length > 1 ? () => setLoads(loads.filter((l) => l.id !== load.id)) : null}
        />
      ))}
      {loads.length < MAX_LOADS && (
        <button type="button" className={styles.addButton} onClick={() => setLoads([...loads, emptyLoad()])}>
          + Add load {LETTERS[loads.length]}
        </button>
      )}

      {fixedTotal <= 0 && (
        <div className={styles.callout} role="status">
          <strong>Enter your monthly fixed costs first.</strong> Truck payment, insurance and so on. Profit per day
          means nothing without them.
          <button type="button" className={styles.calloutButton} onClick={onOpenSettings}>
            Open Settings
          </button>
        </div>
      )}

      {(settingsErrors.length > 0 || generalErrors.length > 0 || serverError) && (
        <div className={styles.errorBox} role="alert">
          {serverError && <p>{serverError}</p>}
          {generalErrors.map(([f, m]) => (
            <p key={f}>{m}</p>
          ))}
          {settingsErrors.map(([f, m]) => (
            <p key={f}>Settings: {m}</p>
          ))}
          {settingsErrors.length > 0 && (
            <button type="button" className={styles.calloutButton} onClick={onOpenSettings}>
              Fix in Settings
            </button>
          )}
        </div>
      )}

      <div className={styles.actions}>
        <button type="button" className={styles.rank} onClick={onRank} disabled={busy || fixedTotal <= 0}>
          {busy ? "Ranking…" : stale ? "Re-rank" : loads.length > 1 ? "Rank loads" : "Check load"}
        </button>
        {response && (
          <button type="button" className={styles.newButton} onClick={onNewComparison}>
            New comparison
          </button>
        )}
      </div>

      <div ref={resultsRef} className={styles.resultsAnchor}>
        {response && <Results data={response} target={target} usingEstimates={usingEstimates} stale={stale} />}
      </div>
    </div>
  );
}
