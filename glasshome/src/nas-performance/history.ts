import { nonnegative, percent } from "../format";

export type Sample = { timestamp: number; state: string; rate?: number };
export type Point = { time: number; value: number | undefined };

export function mergeSamples(samples: Sample[], since: number): Sample[] {
  const ordered = [...new Map(samples.filter((item) => Number.isFinite(item.timestamp))
    .map((item) => [item.timestamp, item])).values()]
    .sort((a, b) => a.timestamp - b.timestamp);
  const first = ordered.findIndex((item) => item.timestamp >= since);
  // Keep the preceding reading for a flat percentage or first counter interval.
  return ordered.slice(first < 0 ? -1 : Math.max(0, first - 1));
}

export function historyPoints(
  samples: Sample[], since: number, counter = false, until?: number,
): Point[] {
  const ordered = mergeSamples(samples, since);
  const points = ordered.flatMap((item, index) => {
    if (counter) {
      if (item.timestamp < since) return [];
      if ("rate" in item) return [{ time: item.timestamp, value: item.rate }];
      const previous = ordered[index - 1];
      const from = nonnegative(previous?.state);
      const to = nonnegative(item.state);
      const seconds = item.timestamp - (previous?.timestamp ?? item.timestamp);
      // A reset, wrap or unavailable reading leaves a break in the line.
      const value = seconds > 0 && from !== undefined && to !== undefined && to >= from
        ? (to - from) / seconds
        : undefined;
      return [{ time: item.timestamp, value }];
    }
    return [{ time: Math.max(since, item.timestamp), value: percent(item.state) }];
  });
  const last = points.at(-1);
  if (!counter && until !== undefined && last && last.time < until) {
    points.push({ time: until, value: last.value });
  }
  return points;
}

export function byteScale(unit: string | null | undefined): number | undefined {
  const units: Record<string, number> = {
    B: 1, kB: 1000, MB: 1e6, GB: 1e9, TB: 1e12,
    KiB: 1024, MiB: 1024 ** 2, GiB: 1024 ** 3, TiB: 1024 ** 4,
    bit: 1 / 8, kbit: 1000 / 8, Mbit: 1e6 / 8, Gbit: 1e9 / 8,
  };
  return units[(unit ?? "B").replace(/\/s$/, "")];
}

export function chartStart(series: Point[][], earliest: number, end: number): number {
  const times = series.flatMap((points) => points.map((point) => point.time));
  return Math.max(earliest, Math.min(end - 60, ...times));
}

export function line(points: Point[], start: number, end: number, ceiling: number): string {
  let drawing = false;
  const commands: string[] = [];
  for (const point of points) {
    if (point.value === undefined) {
      drawing = false;
      continue;
    }
    const x = ((point.time - start) / Math.max(1, end - start)) * 300;
    const y = 50 - Math.min(1, point.value / ceiling) * 48;
    commands.push(`${drawing ? "L" : "M"}${x.toFixed(2)},${y.toFixed(2)}`);
    drawing = true;
  }
  return commands.join(" ");
}
