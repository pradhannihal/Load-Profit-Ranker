import { useEffect, useState } from "react";

const VARS = [
  "ink", "ink-2", "line", "profit", "loss",
  "c-fuel", "c-wear", "c-tolls", "c-fixed", "c-profit", "c-board", "c-restart", "c-schedule",
];

function readColors() {
  const css = getComputedStyle(document.documentElement);
  return Object.fromEntries(VARS.map((v) => [v, css.getPropertyValue(`--${v}`).trim()]));
}

/** CSS token colors, re-read when the phone switches light/dark. */
export function useThemeColors() {
  const [colors, setColors] = useState(readColors);
  useEffect(() => {
    const mq = window.matchMedia("(prefers-color-scheme: dark)");
    const update = () => setColors(readColors());
    mq.addEventListener("change", update);
    return () => mq.removeEventListener("change", update);
  }, []);
  return colors;
}

export function baseConfig(c) {
  return {
    background: null,
    font: "Overpass, system-ui, sans-serif",
    view: { stroke: null },
    axis: {
      labelColor: c["ink-2"],
      titleColor: c["ink-2"],
      gridColor: c.line,
      domainColor: c.line,
      tickColor: c.line,
      labelFontSize: 13,
      titleFontSize: 12,
      titleFontWeight: 700,
    },
    legend: {
      orient: "bottom",
      direction: "horizontal",
      columns: 2,
      labelColor: c.ink,
      titleColor: c["ink-2"],
      labelFontSize: 13,
      symbolType: "square",
      title: null,
      labelLimit: 220,
    },
    text: { color: c.ink, fontSize: 13, fontWeight: 700 },
  };
}
