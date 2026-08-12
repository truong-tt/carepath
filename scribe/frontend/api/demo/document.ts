import {
  API_BASE,
  DAILY_LIMIT,
  MAX_IMAGE_BYTES,
  MESSAGES,
  type Req,
  type Res,
  clientIp,
  createSession,
  json,
  readBody,
  takeQuota,
} from "../_demo";

// Raw body: the upload is forwarded verbatim to the real endpoint, so there is
// nothing to parse here and nothing gained by buffering it twice.
export const config = { api: { bodyParser: false } };

/**
 * Read a Vietnamese medical document for an anonymous visitor.
 *
 * `?sample=1` replays the scripted prescription the page publishes as its
 * example: instant, free, and honest because the page labels it. Anything else
 * is the visitor's own photo and goes to the real reader, which costs tokens
 * and takes roughly 10-15 seconds per line — hence the quota.
 *
 * The scripted path is never used as a fallback for a failed real read. A
 * visitor who uploads their own prescription and is shown someone else's,
 * presented as theirs, has been lied to about the one thing this product does.
 */
export default async function handler(req: Req, res: Res): Promise<void> {
  if (req.method !== "POST") {
    json(res, 405, { error: MESSAGES.method });
    return;
  }

  const contentType = String(req.headers["content-type"] ?? "");
  if (!contentType.startsWith("multipart/form-data")) {
    json(res, 400, { error: MESSAGES.notImage });
    return;
  }

  const sample = new URL(req.url ?? "/", "http://localhost").searchParams.get("sample") === "1";

  // Size is checked BEFORE quota on purpose. Charging a visitor one of five
  // daily runs for picking a 10 MB photo, and then telling them "you are out of
  // runs" instead of "that image is too big", is two wrong answers for the
  // price of one. Reading is bounded by MAX_IMAGE_BYTES, so this stays cheap.
  const declared = Number(req.headers["content-length"] ?? 0);
  if (declared > MAX_IMAGE_BYTES) {
    json(res, 413, { error: MESSAGES.tooLarge });
    return;
  }

  let body: Buffer;
  try {
    body = await readBody(req, MAX_IMAGE_BYTES);
  } catch {
    json(res, 413, { error: MESSAGES.tooLarge });
    return;
  }

  const quota = takeQuota(clientIp(req));
  if (!quota.ok) {
    res.setHeader("Retry-After", String(quota.retryAfter));
    json(res, 429, { error: MESSAGES.quota, limit: DAILY_LIMIT, retryAfter: quota.retryAfter });
    return;
  }

  const visitId = await createSession();
  if (!visitId) {
    json(res, 502, { error: MESSAGES.upstream });
    return;
  }

  const headers: Record<string, string> = { "Content-Type": contentType };
  if (sample) headers["X-CarePath-Sample"] = "1";

  let upstream: Response;
  try {
    upstream = await fetch(`${API_BASE}/api/v1/visits/${visitId}/documents`, {
      method: "POST",
      headers,
      body: new Uint8Array(body),
    });
  } catch {
    json(res, 502, { error: MESSAGES.upstream });
    return;
  }

  if (!upstream.ok) {
    // 502 from the reader means it could not make sense of the image. Say that,
    // rather than leaking the upstream body, which can carry provider detail.
    json(res, upstream.status === 502 ? 422 : 502, {
      error: upstream.status === 502 ? MESSAGES.unreadable : MESSAGES.upstream,
    });
    return;
  }

  const turns = await upstream.json();
  json(res, 200, { turns, sample, remaining: quota.remaining, limit: DAILY_LIMIT });
}
