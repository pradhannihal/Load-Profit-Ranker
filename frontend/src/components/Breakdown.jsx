import { miles, money, perMile } from "../lib/format.js";
import styles from "./Breakdown.module.css";

const cost = (n) => (n > 0 ? `−${money(n)}` : money(0));

const ROWS = [
  ["Total miles", (r) => miles(r.totalMiles)],
  ["Drive hours", (r) => `${r.driveHours.toFixed(1)} h`],
  ["Duty hours", (r) => `${r.dutyHours.toFixed(1)} h`],
  ["34-hr restart", (r) => (r.restartNeeded ? "Yes" : "No")],
  ["Days used", (r) => `${Math.round(r.daysUsed * 100) / 100} ${r.daysBoundBy === "schedule" ? "appt" : "HOS"}`],
  ["Revenue", (r) => money(r.lines.grossRevenue)],
  ["Fuel", (r) => cost(r.lines.fuelCost)],
  ["Maint. + tires", (r) => cost(r.lines.perMileCost)],
  ["Tolls", (r) => cost(r.lines.tolls)],
  ["Fixed costs", (r) => cost(r.lines.fixedCost)],
  ["Net profit", (r) => money(r.netProfit), true],
  ["Profit / day", (r) => money(r.profitPerDay), true],
  ["Profit / mile", (r) => perMile(r.profitPerMile)],
  ["Board rate", (r) => perMile(r.boardRate)],
];

export default function Breakdown({ results }) {
  return (
    <div className={styles.wrap}>
      <table className={`${styles.table} num`}>
        <caption className="visually-hidden">Full cost breakdown per load</caption>
        <thead>
          <tr>
            <th scope="col">
              <span className="visually-hidden">Line</span>
            </th>
            {results.map((r) => (
              <th scope="col" key={r.label}>
                {r.label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {ROWS.map(([label, value, strong]) => (
            <tr key={label} className={strong ? styles.strong : undefined}>
              <th scope="row">{label}</th>
              {results.map((r) => (
                <td key={r.label}>{value(r)}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
