import styles from "./Header.module.css";

function TruckIcon() {
  return (
    <svg className={styles.icon} viewBox="0 0 64 40" aria-hidden="true">
      <rect x="2" y="4" width="34" height="24" rx="2" fill="currentColor" />
      <path d="M38 11h11c2 0 3.5 1 4.5 2.5L59 22c.6 1 1 2 1 3v3H38z" fill="currentColor" />
      <circle cx="14" cy="32" r="6" fill="currentColor" stroke="var(--sign-green)" strokeWidth="3" />
      <circle cx="50" cy="32" r="6" fill="currentColor" stroke="var(--sign-green)" strokeWidth="3" />
    </svg>
  );
}

export default function Header({ screen, onNavigate }) {
  const onSettings = screen === "settings";
  return (
    <header className={styles.header}>
      <div className={styles.sign}>
        <TruckIcon />
        <h1 className={styles.title}>Haul Math</h1>
        <button
          type="button"
          className={styles.navButton}
          onClick={() => onNavigate(onSettings ? "compare" : "settings")}
        >
          {onSettings ? "Done" : "Settings"}
        </button>
      </div>
    </header>
  );
}
