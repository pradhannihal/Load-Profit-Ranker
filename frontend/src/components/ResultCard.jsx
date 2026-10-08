import { days, money, perMile } from "../lib/format.js";
import styles from "./ResultCard.module.css";

const WHY_TEXT = {
  grossRevenue: (x) => `earns ${money(x)} more per day of truck time`,
  fuelCost: (x) => `${money(x)}/day less fuel`,
  perMileCost: (x) => `${money(x)}/day less maintenance and tires`,
  tolls: (x) => `${money(x)}/day less in tolls`,
  fixedCost: (x) => `${money(x)}/day less fixed cost`,
};

function daysText(r) {
  if (r.daysBoundBy === "schedule") return `${days(r.daysUsed)}, waiting on the delivery appointment`;
  return `${days(r.daysUsed)} of driving and duty time`;
}

function loadName(r) {
  return r.nickname ? `Load ${r.label} – ${r.nickname}` : `Load ${r.label}`;
}

export default function ResultCard({ result: r, isWinner, why, runnerUp, hasTarget }) {
  const tone = r.losesMoney ? styles.loss : isWinner ? styles.winner : "";
  return (
    <article className={`${styles.card} ${tone}`} aria-label={`${loadName(r)} result`}>
      <header className={styles.head}>
        {r.rank != null && <span className={styles.rank}>#{r.rank}</span>}
        <h3 className={styles.name}>{loadName(r)}</h3>
        {isWinner && !r.losesMoney && <span className={styles.best}>Best load</span>}
      </header>

      <p className={`${styles.perDay} num`}>
        {money(r.profitPerDay)} <span className={styles.perDayUnit}>/ day</span>
      </p>

      <div className={styles.badges}>
        {r.losesMoney && <span className={styles.badgeLoss}>Loses money</span>}
        {hasTarget && r.meetsTarget === true && <span className={styles.badgeOk}>✓ Meets target</span>}
        {hasTarget && r.meetsTarget === false && <span className={styles.badgeMiss}>✗ Below target</span>}
      </div>

      <p className={styles.sub}>
        Net <strong className="num">{money(r.netProfit)}</strong> over {daysText(r)}
      </p>
      <p className={styles.sub}>
        Board rate <span className="num">{perMile(r.boardRate)}</span> → you keep{" "}
        <strong className="num">{perMile(r.profitPerMile)}</strong> (all {Math.round(r.totalMiles)} mi)
      </p>

      {r.warnings.length > 0 && (
        <ul className={styles.warnings}>
          {r.warnings.map((w) => (
            <li key={w.code}>⚠ {w.message}</li>
          ))}
        </ul>
      )}

      {isWinner && why?.length > 0 && runnerUp && (
        <div className={styles.why}>
          <strong>Why it beats Load {runnerUp.label}:</strong>{" "}
          {why.map((w) => WHY_TEXT[w.line](w.advantagePerDay)).join("; ")}.
        </div>
      )}
    </article>
  );
}
