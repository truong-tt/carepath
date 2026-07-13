/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_LEAD_ENDPOINT?: string;
  readonly VITE_LEAD_EMAIL?: string;
  readonly VITE_LEAD_PHONE?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
