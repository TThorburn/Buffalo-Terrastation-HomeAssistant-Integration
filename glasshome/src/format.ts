export function nonnegative(value: unknown): number | undefined {
  if (typeof value !== "number" && (typeof value !== "string" || !value.trim())) {
    return undefined;
  }
  const parsed = Number(value);
  return Number.isFinite(parsed) && parsed >= 0 ? parsed : undefined;
}

export function percent(value: unknown): number | undefined {
  const parsed = nonnegative(value);
  return parsed !== undefined && parsed <= 100 ? parsed : undefined;
}

export function compactNumber(value: number | undefined): string {
  return value === undefined ? "—" : value.toLocaleString(undefined, { maximumFractionDigits: 1 });
}
