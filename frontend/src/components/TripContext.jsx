import Field from "./Field.jsx";
import styles from "./TripContext.module.css";

export default function TripContext({ trip, onChange, errors, maxCycleHours }) {
  const set = (key) => (value) => onChange({ ...trip, [key]: value });
  return (
    <section className={styles.card} aria-labelledby="trip-heading">
      <h2 id="trip-heading" className={styles.heading}>
        Your truck right now
      </h2>
      <Field
        label="Where are you?"
        kind="text"
        value={trip.currentLocation}
        onChange={set("currentLocation")}
        placeholder="Richmond, VA"
        error={errors["tripContext.currentLocation"]}
      />
      <div className={styles.row}>
        <Field
          label="Available"
          kind="date"
          value={trip.availableDate}
          onChange={set("availableDate")}
          error={errors["tripContext.availableDate"]}
        />
        <Field
          label="Cycle hours left"
          unit="ELD"
          value={trip.cycleHoursRemaining}
          onChange={set("cycleHoursRemaining")}
          placeholder={maxCycleHours}
          error={errors["tripContext.cycleHoursRemaining"]}
        />
      </div>
    </section>
  );
}
