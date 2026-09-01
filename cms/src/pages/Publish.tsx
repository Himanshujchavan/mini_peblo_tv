import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api, ApiError } from "../api/client";
import type { PublishRun, ValidationReport } from "../types";
import { useAuth } from "../auth";

export default function Publish() {
  const { role } = useAuth();
  const qc = useQueryClient();

  const reportQuery = useQuery({
    queryKey: ["validation-report"],
    queryFn: () => api<ValidationReport>("/admin/validation-report"),
    refetchInterval: 15000,
  });

  const runsQuery = useQuery({
    queryKey: ["publish-runs"],
    queryFn: () => api<PublishRun[]>("/admin/publish-runs"),
  });

  const publish = useMutation({
    mutationFn: () => api<PublishRun>("/admin/catalog/publish", { method: "POST" }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["publish-runs"] });
      qc.invalidateQueries({ queryKey: ["validation-report"] });
    },
  });

  const canPublish = reportQuery.data?.can_publish ?? false;
  const isAdmin = role === "admin";

  return (
    <div>
      <h1 className="page-title">Publish</h1>
      <p className="page-sub">Fix everything below before you can publish. Only admins can trigger a publish.</p>

      {reportQuery.isLoading && <div className="spinner-text">Checking for issues...</div>}

      {reportQuery.data && reportQuery.data.groups.length === 0 && (
        <div className="callout callout-success">✅ Nothing is blocking publish right now.</div>
      )}

      {reportQuery.data?.groups.map((group) => (
        <div className="report-group" key={group.rule}>
          <div className="report-group-header">
            {group.rule.replaceAll("_", " ")} ({group.count})
          </div>
          {group.issues.map((issue, i) => (
            <div className="report-issue" key={i}>
              <b>{issue.entity_label}</b>
              {issue.issue}
            </div>
          ))}
        </div>
      ))}

      <div className="panel">
        <button
          className="btn btn-primary"
          disabled={!canPublish || !isAdmin || publish.isPending}
          onClick={() => publish.mutate()}
        >
          {publish.isPending ? "Publishing..." : "Publish catalogue"}
        </button>
        {!isAdmin && <p className="hint" style={{ marginTop: 8 }}>Only admins can publish. Ask an admin to run this.</p>}
        {isAdmin && !canPublish && <p className="hint" style={{ marginTop: 8 }}>Resolve the issues above first.</p>}
        {publish.isError && (
          <div className="callout callout-error" style={{ marginTop: 12 }}>
            {publish.error instanceof ApiError ? publish.error.message : "Publish failed"}
          </div>
        )}
        {publish.isSuccess && (
          <div className="callout callout-success" style={{ marginTop: 12 }}>
            Published {publish.data.show_count} shows / {publish.data.episode_count} episode-language rows.
          </div>
        )}
      </div>

      <div className="panel">
        <h3 style={{ marginTop: 0 }}>Run history</h3>
        {runsQuery.data && runsQuery.data.length === 0 && <p className="page-sub">No publishes yet.</p>}
        {runsQuery.data && runsQuery.data.length > 0 && (
          <table>
            <thead>
              <tr><th>Started</th><th>By</th><th>Outcome</th><th>Shows</th><th>Episodes</th></tr>
            </thead>
            <tbody>
              {runsQuery.data.map((run) => (
                <tr key={run.id}>
                  <td>{new Date(run.started_at).toLocaleString()}</td>
                  <td>{run.triggered_by}</td>
                  <td><span className={`badge badge-${run.outcome === "success" ? "published" : "draft"}`}>{run.outcome}</span></td>
                  <td>{run.show_count}</td>
                  <td>{run.episode_count}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
