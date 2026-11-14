<p align="center">
  <img src="images/icon.png" width="120" alt="Buffalo TeraStation NAS">
</p>

# Buffalo TeraStation NAS for Home Assistant

Monitor a Buffalo TeraStation directly from Home Assistant through its local web API.

- CPU and memory utilization
- Used space, total capacity, usage percentage and health for each RAID array
- Health for each SATA drive
- Receive and transmit byte counters and transfer speeds for each reported network interface
- Active NAS errors and a count of informational events when the firmware exposes them

## Install and connect

Use Home Assistant 2024.12 or later. Add this repository as a custom integration repository in HACS, or copy the `buffalo_nas` folder into `<config>/custom_components/`. Restart Home Assistant, then open **Settings → Devices & services → Add integration → Buffalo TeraStation NAS**.

Enter the address you use to open the NAS web interface and the credentials for an account that can read the dashboard. Use the full URL for HTTP, for example `http://192.168.1.10`. A bare IP or hostname uses HTTPS. HTTPS certificate verification defaults to enabled for new installations. If your NAS uses HTTP, its credentials and telemetry travel in clear text over the local network.

Use **Configure** to change the independent polling intervals. CPU and memory default to 10 seconds, network to 1 second, and storage and alerts to 60 seconds. Existing storage interval settings carry over. Network transfer speeds use the actual elapsed time between counter readings and become available after two successful polls. A counter reset or polling failure clears the rate baseline.

Use **Reconfigure** in the integration's menu to change its address, credentials or TLS settings. Home Assistant prompts for credentials when the NAS rejects the login.

## Upgrade from 1.x

Install the new files and restart Home Assistant. The integration migrates existing entity IDs as their source devices are discovered. The old single RAID entities attach to the first array returned by the NAS, and each additional array receives its own entities. Existing connections initially retain their previous TLS behavior. Use **Reconfigure** if you need to switch from HTTPS to HTTP or enable certificate verification.

The `used_gb` and `total_gb` attributes retain their names for existing dashboard cards. Their values now use the same KiB conversion as Buffalo's dashboard. The separate capacity sensors report GiB. RAID Degraded now follows the firmware's degraded status. RAID Problem still reports any non-healthy RAID status. Missing values and temporarily failed telemetry sources show as unavailable.

## Firmware coverage

The NAS inspected was a TeraStation TS3410D with firmware 5.00-0.07, four SATA disks and RAID 6. Other models using the same JSON-RPC API may work. See [the API inventory](API.md) for the methods and fields found in the firmware. The integration uses the monitoring endpoints and opens and closes its own login session.

## Dashboard examples

The [GlassHome widget project](glasshome/README.md) includes a Performance tile with CPU, memory, and network history, and a RAID & Drives tile with array usage and per-drive health and capacity.

The example cards use 1.x entity IDs. For a fresh installation, replace those references with the entities created for your NAS. [GUI Cards folder](GUI%20Cards/)

<img width="1376" height="1048" alt="Example NAS dashboard" src="https://github.com/user-attachments/assets/fa10b39a-f31e-4ee1-9658-27e777379876" />
