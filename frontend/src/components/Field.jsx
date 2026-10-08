import { useId } from "react";
import EstimateBadge from "./EstimateBadge.jsx";
import styles from "./Field.module.css";

/**
 * Labeled input with an inline error. kind: "number" | "text" | "date".
 * Numbers use type="text" + inputMode="decimal": iPhones show the number pad,
 * and the value isn't silently mangled the way type="number" can be.
 */
export default function Field({
  label,
  value,
  onChange,
  kind = "number",
  unit,
  placeholder,
  error,
  hint,
  estimate = false,
  className,
}) {
  const id = useId();
  const errorId = `${id}-err`;
  const hintId = `${id}-hint`;
  const describedBy = [error && errorId, hint && hintId].filter(Boolean).join(" ") || undefined;

  return (
    <div className={[styles.field, className].filter(Boolean).join(" ")}>
      <label htmlFor={id} className={styles.label}>
        {label}
        {unit && <span className={styles.unit}> ({unit})</span>}
      </label>
      <input
        id={id}
        type={kind === "date" ? "date" : "text"}
        inputMode={kind === "number" ? "decimal" : undefined}
        autoComplete="off"
        className={kind === "number" ? "num" : undefined}
        value={value ?? ""}
        placeholder={placeholder}
        aria-invalid={error ? "true" : undefined}
        aria-describedby={describedBy}
        onChange={(e) => onChange(e.target.value)}
      />
      {estimate && !error && (
        <p className={styles.hint}>
          <EstimateBadge />
        </p>
      )}
      {hint && !error && !estimate && (
        <p id={hintId} className={styles.hint}>
          {hint}
        </p>
      )}
      {error && (
        <p id={errorId} className={styles.error} role="alert">
          {error}
        </p>
      )}
    </div>
  );
}
