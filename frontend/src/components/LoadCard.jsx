import { useState } from "react";
import { DEFAULT_DOCK_WAIT } from "../lib/defaults.js";
import Field from "./Field.jsx";
import styles from "./LoadCard.module.css";

export default function LoadCard({ letter, index, load, onChange, onRemove, errors }) {
  const hasExtras = Boolean(load.pickupDate || load.deliveryDate || load.dockWaitHours || load.tolls);
  const p = `loads[${index}]`;
  const extrasHaveError = ["pickupDate", "deliveryDate", "dockWaitHours", "tolls"].some((k) => errors[`${p}.${k}`]);
  const [showMore, setShowMore] = useState(hasExtras);
  const set = (key) => (value) => onChange({ ...load, [key]: value });
  const err = (key) => errors[`${p}.${key}`];

  return (
    <section className={styles.card} aria-label={`Load ${letter}`}>
      <div className={styles.top}>
        <span className={styles.letter} aria-hidden="true">
          {letter}
        </span>
        <Field
          className={styles.nickname}
          label={`Load ${letter} name (optional)`}
          kind="text"
          value={load.nickname}
          onChange={set("nickname")}
          placeholder="Broker or lane"
        />
        {onRemove && (
          <button type="button" className={styles.remove} onClick={onRemove} aria-label={`Remove load ${letter}`}>
            ✕
          </button>
        )}
      </div>

      <div className={styles.main}>
        <Field label="Rate" unit="$" value={load.postedRate} onChange={set("postedRate")} placeholder="2400"
          error={err("postedRate")} />
        <Field label="Loaded" unit="mi" value={load.loadedMiles} onChange={set("loadedMiles")} placeholder="650"
          error={err("loadedMiles")} />
        <Field label="Deadhead" unit="mi" value={load.deadheadMiles} onChange={set("deadheadMiles")}
          placeholder="15" error={err("deadheadMiles")} />
      </div>

      {showMore || extrasHaveError ? (
        <div className={styles.more}>
          <Field label="Pickup date" kind="date" value={load.pickupDate} onChange={set("pickupDate")}
            error={err("pickupDate")} />
          <Field label="Delivery date" kind="date" value={load.deliveryDate} onChange={set("deliveryDate")}
            error={err("deliveryDate")} />
          <Field label="Dock wait" unit="h" value={load.dockWaitHours} onChange={set("dockWaitHours")}
            placeholder={DEFAULT_DOCK_WAIT} error={err("dockWaitHours")} estimate={load.dockWaitHours === ""} />
          <Field label="Tolls" unit="$" value={load.tolls} onChange={set("tolls")} placeholder="0"
            error={err("tolls")} />
        </div>
      ) : (
        <button type="button" className={styles.moreButton} onClick={() => setShowMore(true)}>
          + Dates, dock wait, tolls
        </button>
      )}
    </section>
  );
}
