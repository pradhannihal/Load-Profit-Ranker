import { DEFAULT_SETTINGS, FIXED_COST_ITEMS, LETTERS } from "./defaults.js";

/** "$2,400" -> 2400, "" -> null. Returns NaN for junk so the server reports it. */
export function toNumber(value) {
  if (value == null) return null;
  const cleaned = String(value).replace(/[$,\s]/g, "");
  if (cleaned === "") return null;
  const n = Number(cleaned);
  return Number.isFinite(n) ? n : NaN;
}

export function fixedCostTotal(fixedCosts) {
  return FIXED_COST_ITEMS.reduce((sum, [key]) => {
    const n = toNumber(fixedCosts?.[key]);
    return sum + (Number.isFinite(n) ? n : 0);
  }, 0);
}

// JSON can't carry NaN; send a string so the server answers "Must be a number."
const num = (v) => {
  const n = toNumber(v);
  return Number.isNaN(n) ? String(v) : n;
};

/** Build the POST /api/rank body (API names match docs/formula.md). */
export function buildRankRequest(settings, trip, loads) {
  const s = { ...DEFAULT_SETTINGS, ...settings };
  const adv = { ...DEFAULT_SETTINGS.advanced, ...s.advanced };
  const truckSettings = {
    mpg: num(s.mpg),
    fuelRegion: s.fuelRegion,
    maintenanceCpm: num(s.maintenanceCpm),
    tiresCpm: num(s.tiresCpm),
    otherCpm: num(s.otherCpm),
    payoutPercent: num(s.payoutPercent),
    daysRoundingMode: s.daysRoundingMode,
    targetProfitPerDay: num(s.targetProfitPerDay),
    monthlyFixedCosts: fixedCostTotal(s.fixedCosts) || null,
    advanced: {
      avgSpeedMph: num(adv.avgSpeedMph),
      bufferHours: num(adv.bufferHours),
      workingDaysPerMonth: num(adv.workingDaysPerMonth),
      maxCycleHours: num(adv.maxCycleHours),
    },
  };
  // Only an override is sent; otherwise the server uses its cached EIA price.
  const override = num(trip.dieselOverride);
  if (override != null) truckSettings.dieselPrice = override;

  return {
    tripContext: {
      availableDate: trip.availableDate,
      cycleHoursRemaining: num(trip.cycleHoursRemaining),
      currentLocation: trip.currentLocation,
    },
    truckSettings,
    loads: loads.map((l, i) => ({
      label: LETTERS[i],
      nickname: l.nickname,
      postedRate: num(l.postedRate),
      loadedMiles: num(l.loadedMiles),
      deadheadMiles: num(l.deadheadMiles),
      pickupDate: l.pickupDate || null,
      deliveryDate: l.deliveryDate || null,
      dockWaitHours: num(l.dockWaitHours),
      tolls: num(l.tolls),
    })),
  };
}

/** Group server errors by field path: { "loads[0].loadedMiles": "Loaded miles must be more than 0." } */
export function errorsByField(errors = []) {
  const map = {};
  for (const e of errors) if (!(e.field in map)) map[e.field] = e.message;
  return map;
}
