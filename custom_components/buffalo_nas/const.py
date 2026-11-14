"""Constants for the Buffalo TeraStation integration."""

DOMAIN = "buffalo_nas"

DEFAULT_SCAN_INTERVAL = 60
DEFAULT_CPU_SCAN_INTERVAL = 10
DEFAULT_NETWORK_SCAN_INTERVAL = 1
MIN_SCAN_INTERVAL = 10
MAX_SCAN_INTERVAL = 3600

NASAPI_PATH = "/nasapi/"
CONF_SCAN_INTERVAL = "scan_interval"
CONF_CPU_SCAN_INTERVAL = "cpu_scan_interval"
CONF_NETWORK_SCAN_INTERVAL = "network_scan_interval"
CONF_DEVICE_IDENTIFIER = "device_identifier"
