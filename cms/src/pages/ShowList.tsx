import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api, ApiError } from "../api/client";
import type { Show } from "../types";

const SECTIONS = ["featured", "series", "minisodes", "songs"];

export default function ShowList() {
  const navigate = useNavigate();
  const qc = useQueryClient();
  const [q, setQ] = useState("");
  const [section, setSection] = useState("");
  const [status, setStatus] = useState("");
  const [page, setPage] = useState(1);
  const pageSize = 15;

  const query = useQuery({
    queryKey: ["shows", q, section, status, page],
    queryFn: () => {
      const params = new URLSearchParams();
      if (q) params.set("q", q);
      if (section) params.set("section", section);
      if (status) params.set("status", status);
      params.set("page", String(page));
      params.set("page_size", String(pageSize));
      return api<Show[]>(`/admin/shows?${params.toString()}`);
    },
  });

  const createShow = useMutation({
    mutationFn: () =>
      api<Show>("/admin/shows", {
        method: "POST",
        body: JSON.stringify({ title: "Untitled show", categories: ["stories"] }),
      }),
    onSuccess: (show) => {
      qc.invalidateQueries({ queryKey: ["shows"] });
      navigate(`/shows/${show.id}`);
    },
  });

  if (query.error instanceof ApiError && query.error.status === 403) {
    return (
      <div className="empty-state">
        <h2>You don't have access to this</h2>
        <p>Your role can't view the shows list. Ask an admin for access.</p>
      </div>
    );
  }

  return (
    <div>
      <h1 className="page-title">Shows</h1>
      <p className="page-sub">Search, filter, and jump into a show to edit its seasons, episodes, and artwork.</p>

      <div className="toolbar">
        <input
          className="input"
          placeholder="Search by title..."
          value={q}
          onChange={(e) => { setQ(e.target.value); setPage(1); }}
        />
        <select className="input" value={section} onChange={(e) => { setSection(e.target.value); setPage(1); }}>
          <option value="">All sections</option>
          {SECTIONS.map((s) => <option key={s} value={s}>{s}</option>)}
        </select>
        <select className="input" value={status} onChange={(e) => { setStatus(e.target.value); setPage(1); }}>
          <option value="">All statuses</option>
          <option value="draft">Draft</option>
          <option value="published">Published</option>
        </select>
        <button className="btn btn-primary" onClick={() => createShow.mutate()} disabled={createShow.isPending}>
          + New show
        </button>
      </div>

      {query.isLoading && <div className="spinner-text">Loading shows...</div>}
      {query.isError && !(query.error instanceof ApiError && query.error.status === 403) && (
        <div className="callout callout-error">Couldn't load shows: {(query.error as Error).message}</div>
      )}

      {query.data && query.data.length === 0 && (
        <div className="empty-state">
          <h3>No shows match your filters</h3>
          <p>Try clearing search or filters, or create a new show.</p>
        </div>
      )}

      {query.data && query.data.length > 0 && (
        <div className="panel" style={{ padding: 0 }}>
          <table>
            <thead>
              <tr>
                <th>Title</th>
                <th>Categories</th>
                <th>Section</th>
                <th>Status</th>
                <th>Updated</th>
              </tr>
            </thead>
            <tbody>
              {query.data.map((show) => (
                <tr key={show.id} style={{ cursor: "pointer" }} onClick={() => navigate(`/shows/${show.id}`)}>
                  <td>{show.title}</td>
                  <td>{show.categories.join(", ")}</td>
                  <td>{show.section || "—"}</td>
                  <td><span className={`badge badge-${show.status}`}>{show.status}</span></td>
                  <td>{new Date(show.updated_at).toLocaleDateString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <div className="toolbar">
        <button className="btn" onClick={() => setPage((p) => Math.max(1, p - 1))} disabled={page === 1}>
          ← Previous
        </button>
        <span>Page {page}</span>
        <button className="btn" onClick={() => setPage((p) => p + 1)} disabled={!query.data || query.data.length < pageSize}>
          Next →
        </button>
      </div>
    </div>
  );
}
