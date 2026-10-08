import { lazy, Suspense } from "react";
import Breakdown from "./Breakdown.jsx";
import ResultCard from "./ResultCard.jsx";
import styles from "./Results.module.css";

const Charts = lazy(() => import("./Charts.jsx"));

export default function Results({ data, target, usingEstimates, stale }) {
  const { results, ranked, winner, whyItWon } = data;
  const runnerUp = ranked ? results[1] : null;
  const chartFallback = <p className={styles.loading}>Loading chart…</p>;

  return (
    <section aria-labelledby="results-heading" className={`${styles.results} ${stale ? styles.stale : ""}`}>
      <h2 id="results-heading">{ranked ? "Ranked by profit per day" : "Your load"}</h2>
      {stale && <p className={styles.staleNote}>You changed something. Tap Re-rank to update.</p>}

      <div className={styles.cards}>
        {results.map((r) => (
          <ResultCard
            key={r.label}
            result={r}
            isWinner={ranked && r.label === winner}
            why={whyItWon}
            runnerUp={runnerUp}
            hasTarget={target != null}
          />
        ))}
      </div>

      <Suspense fallback={chartFallback}>
        <Charts which="profit" results={results} target={target} />
      </Suspense>

      <details className={styles.more}>
        <summary>See the numbers (3 charts + full breakdown)</summary>
        <div className={styles.moreBody}>
          <Suspense fallback={chartFallback}>
            <Charts which="more" results={results} />
          </Suspense>
          <Breakdown results={results} />
        </div>
      </details>

      <p className={styles.disclaimer}>
        Estimates from the numbers you entered, not financial advice. Check the rate con before you book.
        {usingEstimates && " Some settings are still placeholder estimates. Replace them in Settings."}
      </p>
    </section>
  );
}
