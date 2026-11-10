import { defineConfig, defineWidget, field, Icon, useEntities, useEntity, Widget, type EntityView, type Infer, type WidgetManifest } from "@glasshome/widget-sdk";
import { For, Show } from "solid-js";

import { compactNumber, nonnegative, percent } from "../format";
import manifest from "./manifest.json";
import "../tile.css";
import "./raid.css";

const configSchema = defineConfig({
  title: field.title(),
  usage: field.entity("sensor", { title: "RAID usage percentage" }),
  problem: field.entity("binary_sensor", { title: "RAID problem" }),
  degraded: field.entity("binary_sensor", { title: "RAID degraded (optional)" }),
  drives: field.entities("binary_sensor", {
    title: "Individual drive problem sensors",
    description: "Select one problem sensor for each physical drive in this array.",
  }),
});

type Config = Infer<typeof configSchema>;
type Health = { label: string; tone: "good" | "warn" | "unknown" };

function health(state: string | undefined): Health {
  if (state === "on") return { label: "Problem", tone: "warn" };
  if (state === "off") return { label: "Healthy", tone: "good" };
  return { label: "Unknown", tone: "unknown" };
}

function Status(props: { health: Health }) {
  return <span class="nas-status" data-tone={props.health.tone}>{props.health.label}</span>;
}

function driveCapacity(bytes: unknown): string {
  const size = nonnegative(bytes);
  if (!size) return "—";
  return size >= 1e12 ? `${compactNumber(size / 1e12)} TB` : `${compactNumber(size / 1e9)} GB`;
}

function Drive(props: { entity: EntityView | undefined; id: string }) {
  const name = () => {
    const label: unknown = props.entity?.attributes.drive_name;
    return typeof label === "string" && label ? label : props.entity?.friendlyName || props.id;
  };
  return (
    <li class="nas-row nas-drive">
      <div class="nas-drive-name">
        <Icon icon="mdi:harddisk" width={17} />
        <span title={name()}>{name()}</span>
      </div>
      <span class="nas-number nas-muted">{driveCapacity(props.entity?.attributes.capacity_bytes)}</span>
      <Status health={health(props.entity?.state)} />
    </li>
  );
}

function Raid(props: { config: Config }) {
  const usage = useEntity(() => props.config.usage?.[0] ?? "");
  const problem = useEntity(() => props.config.problem?.[0] ?? "");
  const degraded = useEntity(() => props.config.degraded?.[0] ?? "");
  const driveIds = () => [...new Set(props.config.drives ?? [])];
  const drives = useEntities(driveIds);
  const arrayHealth = (): Health => degraded()?.state === "on"
    ? { label: "Degraded", tone: "warn" }
    : health(problem()?.state);
  const used = () => percent(usage()?.state);
  const capacity = () => {
    if (used() === undefined) return undefined;
    const usedGiB = nonnegative(usage()?.attributes.used_gb);
    const totalGiB = nonnegative(usage()?.attributes.total_gb);
    return usedGiB !== undefined && totalGiB !== undefined
      ? `${compactNumber(usedGiB)} / ${compactNumber(totalGiB)} GiB`
      : undefined;
  };

  return (
    <Widget variant="classic-glass" tone={arrayHealth().tone === "warn" ? "warning" : "neutral"}>
      <Widget.Content class="nas-tile">
        <header class="nas-heading">
          <h2>{props.config.title || "NAS RAID & Drives"}</h2>
          <Icon icon="mdi:harddisk" width={22} />
        </header>
        <section class="nas-section">
          <div class="nas-section-title">
            <h3>{String(usage()?.attributes.raid_level || "RAID Array")}</h3>
            <Status health={arrayHealth()} />
          </div>
          <Show when={used() !== undefined} fallback={<p class="nas-muted">Array usage unavailable</p>}>
            <div class="nas-row nas-number">
              <strong>{compactNumber(used())}% used</strong>
              <span class="nas-muted">{capacity()}</span>
            </div>
            <progress class="nas-capacity" value={used()} max={100} aria-label="RAID space used" />
          </Show>
        </section>
        <section class="nas-section">
          <div class="nas-section-title">
            <h3>Physical Drives</h3><span class="nas-muted">{driveIds().length}</span>
          </div>
          <Show when={driveIds().length} fallback={<p class="nas-muted">Select drive problem sensors in widget settings.</p>}>
            <ul class="nas-drives">
              <For each={driveIds()}>
                {(id) => <Drive id={id} entity={drives().find((item) => item.id === id)} />}
              </For>
            </ul>
          </Show>
        </section>
      </Widget.Content>
    </Widget>
  );
}

export default defineWidget<Config>({ manifest: manifest as WidgetManifest<Config>, configSchema, component: Raid });
