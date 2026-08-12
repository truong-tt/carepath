import {
  API_BASE,
  DAILY_LIMIT,
  MESSAGES,
  type Req,
  type Res,
  clientIp,
  createSession,
  json,
  takeQuota,
} from "../_demo.js";

/**
 * Open a visit session for the two-way consultation demo.
 *
 * The conversation itself runs over the websocket, which a serverless function
 * cannot proxy, so the quota is charged here at the one point every demo
 * conversation has to pass through.
 */
export default async function handler(req: Req, res: Res): Promise<void> {
  if (req.method !== "POST") {
    json(res, 405, { error: MESSAGES.method });
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

  json(res, 200, {
    visitId,
    wsBase: API_BASE,
    remaining: quota.remaining,
    limit: DAILY_LIMIT,
  });
}
