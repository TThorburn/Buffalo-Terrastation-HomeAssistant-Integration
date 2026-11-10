import { nonnegative, percent } from "../format";

type Sample = { timestamp: number; state: string };
export type Point = { time: number; value: number | undefined };

export function historyPoints(samples: Sample[], since: number, counter = false): Point[] {
  const points = [...new Map(samples.filter((item) => Number.isFinite(item.timestamp))
    .map((item) => [item.timestamp, item])).values()]
    .sort((a, b) => a.timestamp - b.timestamp);
  return points.flatMap((item, index) => {
    if (item.timestamp < since) return [];
    if (!counter) return [{ time: item.timestamp, value: percent(item.state) }];

    const previous = points[index - 1];
    const from = nonnegative(previous?.state);
    const to = nonnegative(item.state);
    const seconds = item.timestamp - (previous?.timestamp ?? item.timestamp);
    // A reset or wrap makes this interval ambiguous. Leave a break in the line.
    const value = seconds > 0 && from !== undefined && to !== undefined && to >= from
      ? (to - from) / seconds
      : undefined;
    return [{ time: item.timestamp, value }];
  });
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
