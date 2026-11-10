import {
  defineConfig, defineWidget, field, Icon, trackEntityHistory, untrackEntityHistory,
  useEntity, useEntityHistory, Widget, type Infer, type WidgetManifest,
} from "@glasshome/widget-sdk";
import { createEffect, createMemo, createSignal, onCleanup, onMount, Show, type Accessor } from "solid-js";

import { compactNumber, nonnegative, percent } from "../format";
import manifest from "./manifest.json";
import { historyPoints, line, type Point } from "./history";
import "../tile.css";
import "./performance.css";

const HOURS = 6;
const WINDOW = HOURS * 3600;

const configSchema = defineConfig({
  title: field.title(),
  cpu: field.entity("sensor", { title: "CPU usage" }),
  memory: field.entity("sensor", { title: "Memory usage" }),
  rx: field.entity("sensor", { title: "Network RX bytes" }),
  tx: field.entity("sensor", { title: "Network TX bytes" }),
});

type Config = Infer<typeof configSchema>;

function series(id: Accessor<string>, start: Accessor<number>, counter = false) {
  const current = useEntity(id);
  const history = useEntityHistory(id);
  createEffect(() => {
    const selected = id();
    if (!selected) return;
    void trackEntityHistory(selected, {
      startTime: new Date((Date.now() / 1000 - WINDOW) * 1000),
      includeStartTimeState: true,
      significantChangesOnly: false,
      minimalResponse: true,
      noAttributes: true,
    }).catch(() => undefined);
    onCleanup(() => untrackEntityHistory(selected));
  });
  return { current, points: createMemo(() => historyPoints(history()?.timeline ?? [], start(), counter)) };
}

function chartStats(points: Point[]) {
  const values = points.flatMap(({ value }) => value === undefined ? [] : [value]);
  if (!values.length) return undefined;
  return {
    min: Math.min(...values),
    average: values.reduce((sum, value) => sum + value, 0) / values.length,
    max: Math.max(...values),
  };
}

function Throughput(props: { points: Point[]; color: string; label: string; available: boolean }) {
  const value = () => props.available ? props.points.at(-1)?.value : undefined;
  const formatted = () => {
    const rate = value();
    if (rate === undefined) return "—";
    if (rate >= 1e6) return `${compactNumber(rate / 1e6)} MB/s`;
    if (rate >= 1e3) return `${compactNumber(rate / 1e3)} kB/s`;
    return `${compactNumber(rate)} B/s`;
  };
  return <span class="nas-series"><i style={{ background: props.color }} />{props.label} <b>{formatted()}</b></span>;
}

function PercentReading(props: { value: number | undefined; color: string; label: string }) {
  return (
    <span class="nas-series">
      <i style={{ background: props.color }} />{props.label}
      <b>{props.value === undefined ? "—" : `${compactNumber(props.value)}%`}</b>
    </span>
  );
}

function Chart(props: {
  label: string;
  start: number;
  end: number;
  max: number;
  primary: Point[];
  secondary: Point[];
}) {
  return (
    <Show
      when={[props.primary, props.secondary].some((points) => points.some(({ value }) => value !== undefined))}
      fallback={<div class="nas-chart nas-chart-empty">Waiting for history</div>}
    >
      <svg class="nas-chart" viewBox="0 0 300 52" preserveAspectRatio="none" role="img" aria-label={props.label}>
        <path class="nas-grid" d="M0,2 H300 M0,26 H300 M0,50 H300" />
        <path class="nas-trace nas-primary" d={line(props.primary, props.start, props.end, props.max)} />
        <path class="nas-trace nas-secondary" d={line(props.secondary, props.start, props.end, props.max)} />
      </svg>
    </Show>
  );
}

function Performance(props: { config: Config }) {
  const [now, setNow] = createSignal(Date.now() / 1000);
  const start = () => now() - WINDOW;
  onMount(() => {
    const timer = setInterval(() => setNow(Date.now() / 1000), 30_000);
    onCleanup(() => clearInterval(timer));
  });

  const cpu = series(() => props.config.cpu?.[0] ?? "", start);
  const memory = series(() => props.config.memory?.[0] ?? "", start);
  const rx = series(() => props.config.rx?.[0] ?? "", start, true);
  const tx = series(() => props.config.tx?.[0] ?? "", start, true);
  const stats = createMemo(() => chartStats(cpu.points()));
  const chartEnd = () => Math.max(
    now(),
    cpu.points().at(-1)?.time ?? 0,
    memory.points().at(-1)?.time ?? 0,
    rx.points().at(-1)?.time ?? 0,
    tx.points().at(-1)?.time ?? 0,
  );
  const rateScale = createMemo(() => Math.max(1, ...rx.points().map((p) => p.value ?? 0), ...tx.points().map((p) => p.value ?? 0)));
  const hasProcessor = () => !!(props.config.cpu?.[0] || props.config.memory?.[0]);
  const hasNetwork = () => !!(props.config.rx?.[0] || props.config.tx?.[0]);

  return (
    <Widget variant="classic-glass" tone="neutral">
      <Widget.Content class="nas-tile">
        <header class="nas-heading">
          <h2>{props.config.title || "NAS Performance"}</h2>
          <Icon icon="mdi:chart-line" width={22} />
        </header>
        <section class="nas-section">
          <div class="nas-section-title"><h3>CPU &amp; Memory</h3><span class="nas-muted">Last {HOURS} h</span></div>
          <Show when={hasProcessor()} fallback={<p class="nas-muted">Select CPU and memory sensors in widget settings.</p>}>
            <div class="nas-legend">
              <PercentReading label="CPU" color="var(--nas-primary)" value={percent(cpu.current()?.state)} />
              <PercentReading label="RAM" color="var(--nas-secondary)" value={percent(memory.current()?.state)} />
            </div>
            <Chart label="CPU and memory utilization history" start={start()} end={chartEnd()} max={100} primary={cpu.points()} secondary={memory.points()} />
            <Show when={stats()}>
              {(summary) => <div class="nas-row nas-muted nas-number">
                <span>CPU min {compactNumber(summary().min)}%</span>
                <span>Avg {compactNumber(summary().average)}%</span>
                <span>Max {compactNumber(summary().max)}%</span>
              </div>}
            </Show>
          </Show>
        </section>
        <section class="nas-section">
          <div class="nas-section-title"><h3>Network Throughput</h3><span class="nas-muted">Latest sample</span></div>
          <Show when={hasNetwork()} fallback={<p class="nas-muted">Select the RX and TX byte sensors for your active LAN port.</p>}>
            <div class="nas-legend">
              <Throughput label="RX" color="var(--nas-primary)" points={rx.points()} available={nonnegative(rx.current()?.state) !== undefined} />
              <Throughput label="TX" color="var(--nas-secondary)" points={tx.points()} available={nonnegative(tx.current()?.state) !== undefined} />
            </div>
            <Chart label="Receive and transmit throughput history" start={start()} end={chartEnd()} max={rateScale()} primary={rx.points()} secondary={tx.points()} />
          </Show>
        </section>
      </Widget.Content>
    </Widget>
  );
}

export default defineWidget<Config>({ manifest: manifest as WidgetManifest<Config>, configSchema, component: Performance });
