interface ImportMetaEnv {
  /** Base URL of the Rastrojo API (without /api/v1). Empty: offline demo with fixtures. */
  readonly VITE_API_URL?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
