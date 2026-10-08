const usd = new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" });

/** $1,104.70 (always cents, per Nihal's choice). */
export function money(n) {
  return n == null || Number.isNaN(n) ? "—" : usd.format(n);
}

/** +$567.20 / −$12.00 */
export function signedMoney(n) {
  return `${n >= 0 ? "+" : "−"}${usd.format(Math.abs(n))}`;
}

export function perMile(n) {
  return `${money(n)}/mi`;
}

export function days(n) {
  const v = Math.round(n * 100) / 100;
  return `${v} ${v === 1 ? "day" : "days"}`;
}

export function miles(n) {
  return `${Math.round(n).toLocaleString("en-US")} mi`;
}

export function shortDate(iso) {
  if (!iso) return "";
  const [y, m, d] = iso.split("-").map(Number);
  return new Date(y, m - 1, d).toLocaleDateString("en-US", { month: "short", day: "numeric" });
}

export function daysBetween(fromIso, toIso) {
  const a = new Date(`${fromIso}T00:00:00`);
  const b = new Date(`${toIso}T00:00:00`);
  return Math.round((b - a) / 86400000);
}
