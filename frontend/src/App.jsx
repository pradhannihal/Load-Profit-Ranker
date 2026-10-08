import { useEffect, useMemo, useState } from "react";
import Header from "./components/Header.jsx";
import { fetchFuel, fetchRegions, rankLoads } from "./lib/api.js";
import { DEFAULT_SETTINGS, ESTIMATES, defaultTrip, emptyLoad, todayISO } from "./lib/defaults.js";
import { buildRankRequest, errorsByField, fixedCostTotal } from "./lib/request.js";
import * as storage from "./lib/storage.js";
import Compare from "./screens/Compare.jsx";
import Settings from "./screens/Settings.jsx";
import styles from "./App.module.css";

const FALLBACK_REGIONS = [{ code: "R1Z", name: "Lower Atlantic (PADD 1C)" }];

function initialSettings() {
  const saved = storage.load("settings", {});
  return {
    ...DEFAULT_SETTINGS,
    ...saved,
    fixedCosts: { ...DEFAULT_SETTINGS.fixedCosts, ...saved.fixedCosts },
    advanced: { ...DEFAULT_SETTINGS.advanced, ...saved.advanced },
  };
}

function initialTrip() {
  // Remember location, cycle hours and fuel price; the date always starts at today.
  return { ...defaultTrip(), ...storage.load("trip", {}), availableDate: todayISO() };
}

function initialLoads() {
  const saved = storage.load("loads", null);
  return Array.isArray(saved) && saved.length ? saved : [emptyLoad(), emptyLoad()];
}

export default function App() {
  const [screen, setScreen] = useState("compare");
  const [settings, setSettings] = useState(initialSettings);
  const [trip, setTrip] = useState(initialTrip);
  const [loads, setLoads] = useState(initialLoads);
  const [regions, setRegions] = useState(FALLBACK_REGIONS);
  const [fuel, setFuel] = useState(null);
  const [response, setResponse] = useState(null);
  const [rankedBody, setRankedBody] = useState(null);
  const [errors, setErrors] = useState({});
  const [serverError, setServerError] = useState("");
  const [busy, setBusy] = useState(false);
  const [rankCount, setRankCount] = useState(0);

  useEffect(() => storage.save("settings", settings), [settings]);
  useEffect(() => storage.save("trip", trip), [trip]);
  useEffect(() => storage.save("loads", loads), [loads]);

  useEffect(() => {
    fetchRegions()
      .then((r) => Array.isArray(r) && r.length && setRegions(r))
      .catch(() => {});
  }, []);

  useEffect(() => {
    let current = true;
    fetchFuel(settings.fuelRegion)
      .then((f) => current && setFuel(f))
      .catch((e) => current && setFuel({ error: e.message }));
    return () => {
      current = false;
    };
  }, [settings.fuelRegion]);

  const fixedTotal = fixedCostTotal(settings.fixedCosts);
  const body = useMemo(() => buildRankRequest(settings, trip, loads), [settings, trip, loads]);
  const stale = response != null && JSON.stringify(body) !== rankedBody;
  const usingEstimates = Object.keys(ESTIMATES).some((path) => {
    const value = path.startsWith("advanced.") ? settings.advanced[path.slice(9)] : settings[path];
    return value === ESTIMATES[path];
  });
  const regionName = regions.find((r) => r.code === settings.fuelRegion)?.name ?? settings.fuelRegion;

  async function rank() {
    setBusy(true);
    setServerError("");
    try {
      const data = await rankLoads(body);
      if (data.errors?.length) {
        setErrors(errorsByField(data.errors));
        return false;
      }
      setErrors({});
      setResponse(data);
      setRankedBody(JSON.stringify(body));
      setRankCount((n) => n + 1);
      return true;
    } catch (e) {
      setServerError(e.message);
      return false;
    } finally {
      setBusy(false);
    }
  }

  function newComparison() {
    setLoads([emptyLoad(), emptyLoad()]);
    setResponse(null);
    setErrors({});
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  function navigate(next) {
    setScreen(next);
    window.scrollTo({ top: 0 });
  }

  return (
    <>
      <Header screen={screen} onNavigate={navigate} />
      <main className={styles.main}>
        {screen === "settings" ? (
          <Settings settings={settings} setSettings={setSettings} regions={regions} fixedTotal={fixedTotal}
            errors={errors} />
        ) : (
          <Compare
            settings={settings}
            trip={trip}
            setTrip={setTrip}
            loads={loads}
            setLoads={setLoads}
            fuel={fuel}
            regionName={regionName}
            response={response}
            rankCount={rankCount}
            errors={errors}
            stale={stale}
            busy={busy}
            fixedTotal={fixedTotal}
            usingEstimates={usingEstimates}
            serverError={serverError}
            onRank={rank}
            onNewComparison={newComparison}
            onOpenSettings={() => navigate("settings")}
          />
        )}
      </main>
    </>
  );
}
