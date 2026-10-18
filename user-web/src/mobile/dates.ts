// Database datetimes are UTC; the school operates in Asia/Shanghai.
function utcDate(value: string) {
  if (!value) return new Date(NaN);
  const normalized = value.replace(" ", "T");
  return new Date(
    /(?:Z|[+-]\d\d:\d\d)$/.test(normalized) ? normalized : normalized + "Z",
  );
}
export function formatDate(value: string, time = true) {
  const date = utcDate(value);
  if (!Number.isFinite(date.getTime())) return "—";
  return date.toLocaleString("zh-CN", {
    timeZone: "Asia/Shanghai",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    ...(time ? ({ hour: "2-digit", minute: "2-digit" } as const) : {}),
  });
}
export function formatTime(value: string) {
  const date = utcDate(value);
  return Number.isFinite(date.getTime())
    ? date.toLocaleTimeString("zh-CN", {
        timeZone: "Asia/Shanghai",
        hour: "2-digit",
        minute: "2-digit",
      })
    : "—";
}
