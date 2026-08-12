/**
 * Shared plumbing for the public demo endpoints.
 *
 * Importers must write `from "../_demo.js"`, with the extension, even though
 * this file is TypeScript. Vercel compiles each api/ file separately and emits
 * ESM, and Node's ESM resolver does not add extensions — an extensionless
 * import deploys fine and then fails at runtime with ERR_MODULE_NOT_FOUND on
 * the first request. Nothing in the local build catches it, because Vite and
 * vitest both resolve extensionless specifiers happily.
 *
 * These functions exist for one reason: quota and size limits on anonymous
 * traffic. They deliberately do NOT read documents or translate anything.
 * Re-implementing either here would produce patient-visible output that never
 * passed the normalizer, the glossary, the risk engine or the clinician gate,
 * which is exactly what safety invariants 2 and 6 in AGENTS.md forbid. One AI
 * path, one gate: this layer forwards to it. See DEC-0021.
 */

export interface Req {
  method?: string;
  url?: string;
  headers: Record<string, string | string[] | undefined>;
  on(event: string, listener: (chunk?: unknown) => void): void;
}

export interface Res {
  statusCode: number;
  setHeader(name: string, value: string): void;
  end(body?: string): void;
}

/** Where the real API lives. Server-side only, so the host is not in the bundle. */
export const API_BASE = (
  process.env.DEMO_API_BASE ?? "https://tranth3truong-carepath-api.hf.space"
).replace(/\/$/, "");

export const DAILY_LIMIT = Number(process.env.DEMO_DAILY_LIMIT ?? 5);
export const MAX_IMAGE_BYTES = 4 * 1024 * 1024;

/**
 * Per-IP daily counter.
 *
 * ponytail: in-memory, so it resets on cold start and counts per instance
 * rather than globally. That is deliberate and sufficient — the real backstop
 * is that the sample path runs the scripted provider and costs nothing, so the
 * worst case of an undercount is wasted CPU. Move to Vercel KV only if real
 * abuse shows up in the logs.
 */
const hits = new Map<string, { day: string; count: number }>();

export function clientIp(req: Req): string {
  const forwarded = req.headers["x-forwarded-for"];
  const value = Array.isArray(forwarded) ? forwarded[0] : forwarded;
  return (value ?? "").split(",")[0].trim() || "unknown";
}

export interface Quota {
  ok: boolean;
  remaining: number;
  retryAfter: number;
}

export function takeQuota(ip: string): Quota {
  const day = new Date().toISOString().slice(0, 10);
  const entry = hits.get(ip);
  const count = entry && entry.day === day ? entry.count : 0;

  if (count >= DAILY_LIMIT) {
    const midnight = Date.UTC(
      new Date().getUTCFullYear(),
      new Date().getUTCMonth(),
      new Date().getUTCDate() + 1,
    );
    return {
      ok: false,
      remaining: 0,
      retryAfter: Math.max(1, Math.ceil((midnight - Date.now()) / 1000)),
    };
  }

  hits.set(ip, { day, count: count + 1 });
  return { ok: true, remaining: DAILY_LIMIT - count - 1, retryAfter: 0 };
}

/** Read the raw body, refusing anything over `limit` without buffering it all. */
export function readBody(req: Req, limit: number): Promise<Buffer> {
  return new Promise((resolve, reject) => {
    const chunks: Buffer[] = [];
    let size = 0;
    req.on("data", (chunk) => {
      const buffer = chunk as Buffer;
      size += buffer.length;
      if (size > limit) {
        reject(new Error("TOO_LARGE"));
        return;
      }
      chunks.push(buffer);
    });
    req.on("end", () => resolve(Buffer.concat(chunks)));
    req.on("error", reject);
  });
}

export function json(res: Res, status: number, body: unknown): void {
  res.statusCode = status;
  res.setHeader("Content-Type", "application/json; charset=utf-8");
  // Nothing here is cacheable: quota state and demo output are per-request.
  res.setHeader("Cache-Control", "no-store");
  res.end(JSON.stringify(body));
}

/** Vietnamese-first errors. The demo is the product's first impression. */
export const MESSAGES = {
  quota: "Bạn đã dùng hết lượt thử hôm nay. Mời quay lại vào ngày mai.",
  tooLarge: "Ảnh quá lớn. Chọn ảnh dưới 4 MB.",
  notImage: "Hãy tải lên ảnh chụp giấy tờ.",
  unreadable: "Không đọc được giấy tờ này. Thử chụp rõ và đủ sáng hơn.",
  upstream: "Máy chủ đang bận. Thử lại sau ít phút.",
  method: "Phương thức không được hỗ trợ.",
} as const;

/** Open a visit session on the real API so demo turns run the normal pipeline. */
export async function createSession(): Promise<string | null> {
  const response = await fetch(`${API_BASE}/api/sessions`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      consent: { recorded: true, method: "public-demo", locale: "vi" },
    }),
  });
  if (!response.ok) return null;
  const body = (await response.json()) as { session_id?: string };
  return body.session_id ?? null;
}
