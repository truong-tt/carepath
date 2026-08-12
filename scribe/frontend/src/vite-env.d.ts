/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_LEAD_ENDPOINT?: string;
  readonly VITE_LEAD_EMAIL?: string;
  readonly VITE_LEAD_PHONE?: string;
  /** Empty on Vercel: /api/* is rewritten same-origin (DEC-0021). */
  readonly VITE_API_BASE?: string;
  /** Websocket origin. A rewrite cannot proxy the upgrade, so /ws/* goes direct. */
  readonly VITE_WS_BASE?: string;
  readonly VITE_TEAM_CODE?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
