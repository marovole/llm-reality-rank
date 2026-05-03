import { defineConfig } from 'astro/config';

export default defineConfig({
  output: 'static',
  site: 'https://llm-reality-rank.pages.dev',
  trailingSlash: 'always',
  build: {
    format: 'directory'
  }
});
