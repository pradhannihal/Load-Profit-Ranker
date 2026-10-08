// Lazy-loaded (see Results.jsx): Vega is large, so it isn't in the first download.
import { useMemo } from "react";
import { daysSpec, moneySpec, perMileSpec, profitPerDaySpec } from "../charts/specs.js";
import { useThemeColors } from "../charts/theme.js";
import VegaChart from "./VegaChart.jsx";

export default function Charts({ which, results, target }) {
  const colors = useThemeColors();
  const specs = useMemo(
    () =>
      which === "profit"
        ? [["Profit per day", profitPerDaySpec(results, colors, target)]]
        : [
            ["Where the money goes", moneySpec(results, colors)],
            ["Board rate vs what you keep", perMileSpec(results, colors)],
            ["Days the truck is tied up", daysSpec(results, colors)],
          ],
    [which, results, colors, target],
  );
  return specs.map(([title, spec]) => <VegaChart key={title} title={title} spec={spec} />);
}
