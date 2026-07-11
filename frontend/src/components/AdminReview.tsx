import { FormEvent, MouseEvent, useState } from "react";

import { API_BASE_URL } from "../api";
import type { Language } from "../copy";

type Feedback = {
  reason: string;
  comment?: string | null;
};

type ReviewRow = {
  id: string;
  source_text: string;
  translation: string;
  corrected_text: string | null;
  risk_tier: string;
  status: string;
  feedback: Feedback[];
};

type ReviewResponse = {
  items: ReviewRow[];
  total: number;
};

type Filters = {
  risk: string;
  flagged: boolean;
  low_confidence: boolean;
  escalated: boolean;
};

const initialFilters: Filters = {
  risk: "",
  flagged: false,
  low_confidence: false,
  escalated: false,
};

function reviewUrl(filters: Filters, format = "json") {
  const params = new URLSearchParams({ format });
  if (filters.risk) {
    params.set("risk", filters.risk);
  }
  if (filters.flagged) {
    params.set("flagged", "1");
  }
  if (filters.low_confidence) {
    params.set("low_confidence", "1");
  }
  if (filters.escalated) {
    params.set("escalated", "1");
  }
  return `${API_BASE_URL}/api/admin/review?${params.toString()}`;
}

export function AdminReview({ language = "vi" }: { language?: Language }) {
  const [token, setToken] = useState("");
  const [filters, setFilters] = useState<Filters>(initialFilters);
  const [rows, setRows] = useState<ReviewRow[]>([]);
  const [total, setTotal] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function loadReview(event?: FormEvent<HTMLFormElement>) {
    event?.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(reviewUrl(filters), {
        headers: { "X-Admin-Token": token },
      });
      if (!response.ok) {
        throw new Error(`review request failed: ${response.status}`);
      }
      const payload = (await response.json()) as ReviewResponse;
      setRows(payload.items);
      setTotal(payload.total);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "review request failed");
    } finally {
      setLoading(false);
    }
  }

  async function downloadCsv(event: MouseEvent<HTMLAnchorElement>) {
    event.preventDefault();
    setError(null);
    try {
      const response = await fetch(reviewUrl(filters, "csv"), {
        headers: { "X-Admin-Token": token },
      });
      if (!response.ok) {
        throw new Error(`CSV request failed: ${response.status}`);
      }
      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = "carepath-review.csv";
      link.click();
      URL.revokeObjectURL(url);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "CSV request failed");
    }
  }

  return (
    <main className="workspace admin-review" lang={language}>
      <header className="topbar">
        <div>
          <p className="eyebrow">Admin review</p>
          <h1>Translation review</h1>
        </div>
        <a href="#" onClick={(event) => void downloadCsv(event)}>
          Download CSV
        </a>
      </header>
      <form className="admin-filters" onSubmit={(event) => void loadReview(event)}>
        <label>
          Admin token
          <input
            type="password"
            value={token}
            onChange={(event) => setToken(event.target.value)}
          />
        </label>
        <label>
          Risk
          <select
            value={filters.risk}
            onChange={(event) => setFilters((current) => ({ ...current, risk: event.target.value }))}
          >
            <option value="">Any</option>
            <option value="low">Low</option>
            <option value="medium">Medium</option>
            <option value="high">High</option>
            <option value="critical">Critical</option>
          </select>
        </label>
        <label>
          <input
            checked={filters.flagged}
            type="checkbox"
            onChange={(event) =>
              setFilters((current) => ({ ...current, flagged: event.target.checked }))
            }
          />
          Flagged
        </label>
        <label>
          <input
            checked={filters.low_confidence}
            type="checkbox"
            onChange={(event) =>
              setFilters((current) => ({ ...current, low_confidence: event.target.checked }))
            }
          />
          Low confidence
        </label>
        <label>
          <input
            checked={filters.escalated}
            type="checkbox"
            onChange={(event) =>
              setFilters((current) => ({ ...current, escalated: event.target.checked }))
            }
          />
          Escalated
        </label>
        <button disabled={loading} type="submit">
          {loading ? "Loading..." : "Load review"}
        </button>
      </form>
      {error ? (
        <p className="error" role="alert">
          {error}
        </p>
      ) : null}
      <section className="admin-table" aria-label="Review results">
        <p className="meta">{total} turns</p>
        <table>
          <thead>
            <tr>
              <th>Source</th>
              <th>Translation</th>
              <th>Correction</th>
              <th>Risk tier</th>
              <th>Status</th>
              <th>Feedback</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={row.id}>
                <td>{row.source_text}</td>
                <td>{row.translation}</td>
                <td>{row.corrected_text || ""}</td>
                <td>{row.risk_tier}</td>
                <td>{row.status}</td>
                <td>{row.feedback.map((item) => item.reason).join(", ")}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </main>
  );
}
