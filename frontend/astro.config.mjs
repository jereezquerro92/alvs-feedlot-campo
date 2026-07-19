import { defineConfig } from "astro/config";
import svelte from "@astrojs/svelte";
import node from "@astrojs/node";
import tailwindcss from "@tailwindcss/vite";
import { defaultLocale, locales } from "./src/i18n/config";


export default defineConfig({
  output: "server",
  adapter: node({ mode: "standalone" }),
  integrations: [svelte()],
  i18n: {
    defaultLocale,
    locales: [...locales],
  },
  devToolbar: {
    enabled: false,
  },
  server: {
    host: process.env.HOST ?? "0.0.0.0",
    port: Number(process.env.PORT ?? 4321),
  },
  vite: {
    plugins: [tailwindcss()],
  },
});
