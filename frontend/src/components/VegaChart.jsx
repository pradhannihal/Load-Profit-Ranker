import { useEffect, useRef } from "react";
import embed from "vega-embed";
import styles from "./VegaChart.module.css";

/** Renders one Vega-Lite spec. Re-renders when the spec object changes. */
export default function VegaChart({ spec, title }) {
  const ref = useRef(null);

  useEffect(() => {
    let result = null;
    let cancelled = false;
    embed(ref.current, spec, { actions: false, renderer: "svg" })
      .then((r) => {
        if (cancelled) r.finalize();
        else result = r;
      })
      .catch((e) => console.error("Chart failed", e));
    return () => {
      cancelled = true;
      result?.finalize();
    };
  }, [spec]);

  return (
    <figure className={styles.figure}>
      <figcaption className={styles.title}>{title}</figcaption>
      <div ref={ref} className={styles.chart} />
    </figure>
  );
}
