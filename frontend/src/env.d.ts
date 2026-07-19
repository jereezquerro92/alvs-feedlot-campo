

interface ImportMetaEnv {
  readonly PUBLIC_SITE_URL: string;
  readonly PUBLIC_API_URL: string;
  readonly PUBLIC_BACKEND_URL: string;
  readonly PUBLIC_PROJECT_SLUG: string;
  readonly BACKEND_API_URL: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
