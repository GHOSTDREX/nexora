// Backend timestamps (SensorReading.timestamp, CameraSnapshot.timestamp, etc.)
// are always UTC (see app/db/models.py's utcnow()), but the DB column is
// timezone-naive, so FastAPI serializes them without a "Z"/offset suffix
// (e.g. "2026-09-07T22:21:28" instead of "...Z"). A bare date-time string
// like that is parsed as LOCAL time by `new Date(...)`, silently shifting
// every displayed time by the viewer's UTC offset (e.g. off by 5:30 in
// India) — this appends "Z" when it's missing so parsing is always UTC.
const HAS_TZ = /Z$|[+-]\d{2}:\d{2}$/

export function parseUtc(isoTimestamp: string): Date {
  return new Date(HAS_TZ.test(isoTimestamp) ? isoTimestamp : `${isoTimestamp}Z`)
}
