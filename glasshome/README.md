# Buffalo NAS widgets for GlassHome

**NAS Performance** shows current CPU and RAM usage, a six-hour chart for both, and CPU sample minimum, average, and maximum. The network chart shows average receive and transmit rates between recorded byte-counter samples. A reset, wrap, or unavailable reading leaves a gap.

**NAS RAID & Drives** shows the array’s health, usage, and capacity. Each selected drive has its own row with health and capacity. Add one widget per array if your NAS has multiple arrays.

## Try the widgets on your GlassHome dashboard

1. Install Buffalo TeraStation NAS integration **2.1.0** in Home Assistant and restart it. The per-drive capacity comes from the new `capacity_bytes` attribute on the existing drive problem sensor.
2. Use GlassHome Dash **1.4.5** or later with a compatible 1.x widget SDK. From this `glasshome` directory in PowerShell, run the commands below. Replace the URL with your **GlassHome Dash** address. The example assumes its default port.
3. Follow the browser approval prompt from the CLI. In Dash, enter dashboard edit mode, add the two widgets, and hold each tile to open its settings. Keep the command running during this local preview. Stopping it unregisters the test widgets.

```powershell
npm.cmd ci
npm.cmd exec --yes --package=bun -- bun run widget connect http://homeassistant.local:3123
```

### Select entities

| Tile | Home Assistant entities to select |
| --- | --- |
| NAS Performance | CPU Usage, Memory Usage, and RX Bytes and TX Bytes for the active network port. On the inspected NAS this is `eth1` (LAN 2). |
| NAS RAID & Drives | RAID Usage and RAID Problem for the same array, optionally RAID Degraded, then the individual SATA drive Problem entities. On the inspected NAS the array is `md10`. |

Keep these sensors in Home Assistant Recorder to populate the charts. Network throughput needs at least two valid counter samples. Individual drive capacities display in decimal GB or TB, while array usage displays in GiB.

## Build and validate locally

```powershell
npm.cmd ci
npm.cmd run typecheck
npm.cmd run build
npm.cmd exec --yes --package=bun -- bun run widget validate
```

The build writes both bundles and `registry.json` to `dist`. The tiles read Home Assistant entities through GlassHome's SDK using read-only capabilities. For the local connection and publishing workflows, see the [GlassHome developer guide](https://glasshome.app/docs/widgets/widget-development).
