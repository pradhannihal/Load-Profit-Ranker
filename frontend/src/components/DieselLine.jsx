import { useState } from "react";
import { todayISO } from "../lib/defaults.js";
import { daysBetween, shortDate } from "../lib/format.js";
import Field from "./Field.jsx";
import styles from "./DieselLine.module.css";

export default function DieselLine({ fuel, regionName, override, onOverride, error }) {
  const [editing, setEditing] = useState(Boolean(override));
  const usingOverride = override !== "";

  let status = null;
  if (!fuel) status = "Getting this week's diesel price…";
  else if (fuel.error) status = `Couldn't reach the server for diesel prices. ${fuel.error}`;
  else if (fuel.source === "fallback") status = `Couldn't get this week's EIA price. Using $${fuel.price} until it loads.`;
  else if (fuel.stale) status = `This price is ${daysBetween(fuel.asOf, todayISO())} days old.`;

  return (
    <section className={styles.line} aria-label="Diesel price">
      <div className={styles.main}>
        <span className={styles.label}>Diesel</span>
        {usingOverride ? (
          <span className={`${styles.price} num`}>${override} – your price</span>
        ) : fuel && !fuel.error ? (
          <span className={styles.price}>
            <span className="num">${fuel.price.toFixed(3)}</span>
            <span className={styles.meta}>
              {" "}
              – {regionName}
              {fuel.asOf && `, as of ${shortDate(fuel.asOf)}`}
            </span>
          </span>
        ) : (
          <span className={styles.price}>—</span>
        )}
        <button
          type="button"
          className={styles.change}
          onClick={() => {
            if (editing) onOverride("");
            setEditing(!editing);
          }}
        >
          {editing ? "Use EIA" : "Change"}
        </button>
      </div>
      {editing && (
        <Field
          label="Your price for this trip (fuel card or pump)"
          unit="$/gal"
          value={override}
          onChange={onOverride}
          placeholder={fuel?.price?.toFixed(3)}
          error={error}
        />
      )}
      {status && !usingOverride && <p className={styles.status}>{status}</p>}
    </section>
  );
}
