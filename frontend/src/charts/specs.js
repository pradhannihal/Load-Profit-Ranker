// Vega-Lite specs for the results. Each takes the API results (best first) and theme colors.
import { baseConfig } from "./theme.js";

const name = (r) => (r.nickname ? `${r.label} – ${r.nickname}` : r.label);
const BAR_ROW = 52;

/** Domain from 0 (or the most negative value) to the max, with room for the value labels. */
function labelDomain(nums) {
  return [Math.min(0, ...nums) * 1.35, Math.max(0, ...nums) * 1.4 || 1];
}

function frame(c, rows, description, body) {
  return {
    $schema: "https://vega.github.io/schema/vega-lite/v6.json",
    description,
    width: "container",
    height: Math.max(rows, 1) * BAR_ROW,
    autosize: { type: "fit-x", contains: "padding" },
    config: baseConfig(c),
    ...body,
  };
}

const yLoad = (order) => ({
  field: "name",
  type: "nominal",
  sort: order,
  title: null,
  axis: { labelFontWeight: 800, labelFontSize: 15, labelLimit: 120 },
});

/** 1. Profit per day by load, with the target as a dashed line. */
export function profitPerDaySpec(results, c, target) {
  const values = results.map((r) => ({ name: name(r), value: r.profitPerDay, loses: r.losesMoney }));
  const x = {
    field: "value",
    type: "quantitative",
    title: "Profit per day of truck time",
    axis: { format: "$,.0f", tickCount: 3 },
    scale: { domain: labelDomain([...values.map((v) => v.value), target ?? 0]), nice: false },
  };
  const y = yLoad(values.map((v) => v.name));
  // x/y live on each layer, not the top level, so the target rule doesn't inherit the load axis.
  const layers = [
    {
      data: { values },
      mark: { type: "bar", cornerRadiusEnd: 4 },
      encoding: {
        x,
        y,
        color: { condition: { test: "datum.loses", value: c.loss }, value: c.profit },
        tooltip: [
          { field: "name", title: "Load" },
          { field: "value", title: "Profit / day", format: "$,.2f" },
        ],
      },
    },
    {
      data: { values },
      mark: { type: "text", align: "left", dx: 6, baseline: "middle" },
      encoding: { x, y, text: { field: "value", format: "$,.2f" } },
    },
  ];
  if (target != null) {
    const tx = { datum: target, type: "quantitative" };
    // Drawn under the value labels. One empty row each, or Vega has nothing to draw.
    layers.splice(
      1,
      0,
      { data: { values: [{}] }, mark: { type: "rule", strokeDash: [6, 4], strokeWidth: 2, color: c.ink }, encoding: { x: tx } },
      {
        data: { values: [{}] },
        mark: { type: "text", align: "center", dy: -8, baseline: "bottom", color: c.ink, fontWeight: 800 },
        encoding: { x: tx, y: { value: 0 }, text: { value: `target $${target}` } },
      },
    );
  }
  return frame(c, values.length, "Profit per day for each load, best first", { layer: layers });
}

/** 2. Where the money goes: the rate split into costs and what's left. */
export function moneySpec(results, c) {
  const segments = [
    ["Fuel", (r) => r.lines.fuelCost, c["c-fuel"]],
    ["Maintenance + tires", (r) => r.lines.perMileCost, c["c-wear"]],
    ["Tolls", (r) => r.lines.tolls, c["c-tolls"]],
    ["Fixed costs", (r) => r.lines.fixedCost, c["c-fixed"]],
    ["Profit", (r) => Math.max(r.netProfit, 0), c["c-profit"]],
  ];
  const values = results.flatMap((r) =>
    segments.map(([segment, get], i) => ({ name: name(r), segment, order: i, value: get(r) })),
  );
  const revenue = results.map((r) => ({ name: name(r), revenue: r.lines.grossRevenue }));
  return frame(c, results.length, "Each load's rate split into fuel, wear, tolls, fixed costs and profit", {
    encoding: { y: yLoad(results.map(name)) },
    layer: [
      {
        data: { values },
        mark: { type: "bar" },
        encoding: {
          x: { field: "value", type: "quantitative", stack: "zero", title: "Dollars", axis: { format: "$,.0f", tickCount: 4 } },
          color: {
            field: "segment",
            type: "nominal",
            scale: { domain: segments.map((s) => s[0]), range: segments.map((s) => s[2]) },
          },
          order: { field: "order" },
          tooltip: [
            { field: "name", title: "Load" },
            { field: "segment", title: "Line" },
            { field: "value", title: "Amount", format: "$,.2f" },
          ],
        },
      },
      {
        data: { values: revenue },
        mark: { type: "tick", orient: "vertical", thickness: 3, color: c.ink, size: 40 },
        encoding: {
          x: { field: "revenue", type: "quantitative" },
          tooltip: [{ field: "revenue", title: "Your pay for the load", format: "$,.2f" }],
        },
      },
    ],
  });
}

/** 3. Board rate (what the load board shows) vs what's actually left per mile. */
export function perMileSpec(results, c) {
  const metrics = [
    ["Board rate (loaded miles)", (r) => r.boardRate, c["c-board"]],
    ["You keep (all miles)", (r) => r.profitPerMile, c["c-profit"]],
  ];
  const values = results.flatMap((r) => metrics.map(([metric, get]) => ({ name: name(r), metric, value: get(r) })));
  return frame(c, results.length * 1.4, "Board rate per loaded mile versus true profit per mile for each load", {
    data: { values },
    encoding: {
      y: yLoad(results.map(name)),
      yOffset: { field: "metric", sort: metrics.map((m) => m[0]) },
      x: { field: "value", type: "quantitative", title: "Dollars per mile", axis: { format: "$.2f", tickCount: 3 }, scale: { domain: labelDomain(values.map((v) => v.value)), nice: false } },
    },
    layer: [
      {
        mark: { type: "bar", cornerRadiusEnd: 3 },
        encoding: {
          color: {
            field: "metric",
            type: "nominal",
            scale: { domain: metrics.map((m) => m[0]), range: metrics.map((m) => m[2]) },
          },
          tooltip: [
            { field: "name", title: "Load" },
            { field: "metric", title: "Measure" },
            { field: "value", title: "$/mi", format: "$.2f" },
          ],
        },
      },
      {
        mark: { type: "text", align: "left", dx: 4, baseline: "middle", fontSize: 12 },
        encoding: { text: { field: "value", format: "$.2f" } },
      },
    ],
  });
}

/** 4. Days the truck is tied up: driving/duty, 34-hr restart, waiting on the appointment. */
export function daysSpec(results, c) {
  const segments = [
    ["Driving & duty", (r) => r.hosDays - r.restartDays, c["c-fixed"]],
    ["34-hr restart", (r) => r.restartDays, c["c-restart"]],
    ["Waiting on appointment", (r) => Math.max(r.daysUsed - r.hosDays, 0), c["c-schedule"]],
  ];
  const values = results.flatMap((r) =>
    segments.map(([segment, get], i) => ({ name: name(r), segment, order: i, value: get(r) })),
  );
  return frame(c, results.length, "Days each load ties up the truck, split by driving, restart and waiting", {
    data: { values },
    encoding: { y: yLoad(results.map(name)) },
    layer: [
      {
        mark: { type: "bar" },
        encoding: {
          x: { field: "value", type: "quantitative", stack: "zero", title: "Days of truck time", axis: { tickCount: 4 } },
          color: {
            field: "segment",
            type: "nominal",
            scale: { domain: segments.map((s) => s[0]), range: segments.map((s) => s[2]) },
          },
          order: { field: "order" },
          tooltip: [
            { field: "name", title: "Load" },
            { field: "segment", title: "Part" },
            { field: "value", title: "Days", format: ".2f" },
          ],
        },
      },
    ],
  });
}
