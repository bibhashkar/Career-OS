/**
 * Semantic Status Badge Color Token Mapper.
 *
 * Normalizes status strings across admin observability tables,
 * ingestion runs, task statuses, and provenance indicators.
 */
export function getStatusBadgeClass(status) {
  const s = String(status || "")
    .toLowerCase()
    .trim();

  // 1. Positive / Successful
  if (
    [
      "success",
      "completed",
      "succeeded",
      "healthy",
      "active",
      "verified",
      "closed",
      "resolved",
    ].includes(s)
  ) {
    return "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20";
  }

  // 2. In-Progress / Running
  if (
    [
      "running",
      "in_progress",
      "pending",
      "syncing",
      "evaluating",
      "started",
    ].includes(s)
  ) {
    return "bg-sky-500/10 text-sky-400 border border-sky-500/20";
  }

  // 3. Warning / Tripped / Degraded
  if (
    [
      "warning",
      "degraded",
      "tripped",
      "discrepancy",
      "caution",
      "uncertain",
    ].includes(s)
  ) {
    return "bg-amber-500/10 text-amber-400 border border-amber-500/20";
  }

  // 4. Negative / Failed / Suspended
  if (
    [
      "failed",
      "error",
      "crashed",
      "dead",
      "aborted",
      "suspended",
      "rejected",
      "inactive",
      "unhealthy",
    ].includes(s)
  ) {
    return "bg-rose-500/10 text-rose-400 border border-rose-500/20";
  }

  return "bg-slate-800 text-slate-300 border border-slate-700";
}
