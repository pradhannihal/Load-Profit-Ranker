// Defaults mirror backend/core/config.py (docs/formula.md §3c, §3d).
// Form values are kept as strings while editing; request.js converts them.

export const FIXED_COST_ITEMS = [
  ["truckPayment", "Truck payment"],
  ["insurance", "Insurance"],
  ["permits", "Permits & plates"],
  ["eld", "ELD"],
  ["phone", "Phone"],
  ["parking", "Parking"],
  ["other", "Other"],
];

export const DEFAULT_SETTINGS = {
  mpg: "6.5",
  fuelRegion: "R1Z",
  maintenanceCpm: "0.215",
  tiresCpm: "0.05",
  otherCpm: "0",
  payoutPercent: "100",
  daysRoundingMode: "fractional",
  targetProfitPerDay: "",
  fixedCosts: Object.fromEntries(FIXED_COST_ITEMS.map(([key]) => [key, ""])),
  advanced: {
    avgSpeedMph: "50",
    bufferHours: "2",
    workingDaysPerMonth: "30",
    maxCycleHours: "70",
  },
};

// Placeholder values that aren't Dad's real numbers yet. Shown with an "estimate" badge
// while the value still equals the placeholder.
export const ESTIMATES = {
  mpg: "6.5",
  maintenanceCpm: "0.215",
  tiresCpm: "0.05",
  "advanced.avgSpeedMph": "50",
  "advanced.bufferHours": "2",
  "advanced.workingDaysPerMonth": "30",
};

export const DEFAULT_DOCK_WAIT = "2";
export const MAX_LOADS = 3;
export const LETTERS = ["A", "B", "C"];

export function todayISO() {
  // Local date, not UTC: at 9 p.m. in Virginia, UTC is already tomorrow.
  const d = new Date();
  const pad = (n) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
}

export function defaultTrip() {
  return { currentLocation: "", availableDate: todayISO(), cycleHoursRemaining: "", dieselOverride: "" };
}

let nextId = 1;
export function emptyLoad() {
  return {
    id: `load-${Date.now()}-${nextId++}`,
    nickname: "",
    postedRate: "",
    loadedMiles: "",
    deadheadMiles: "",
    pickupDate: "",
    deliveryDate: "",
    dockWaitHours: "",
    tolls: "",
  };
}
