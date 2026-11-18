import fs from 'node:fs';
import { fileURLToPath } from 'node:url';
import react from '@vitejs/plugin-react';
import { defineConfig, loadEnv, type Plugin } from 'vite';

// Reuse the approved prototype without maintaining a second copy.
// Both development and production builds expose the same self-contained HTML.
function approvedPrototype(): Plugin {
  const source = fileURLToPath(new URL('../edurag-p0.html', import.meta.url));
  return {
    name: 'approved-edurag-prototype',
    configureServer(server) {
      server.middlewares.use('/prototype.html', (_req, res) => {
        res.setHeader('Content-Type', 'text/html; charset=utf-8');
        res.end(fs.readFileSync(source, 'utf8'));
      });
    },
    generateBundle() {
      this.emitFile({ type: 'asset', fileName: 'prototype.html', source: fs.readFileSync(source) });
    },
  };
}

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '');
  return {
    plugins: [react(), approvedPrototype()],
    server: {
      port: 5173,
      strictPort: true,
      proxy: { '/api': { target: env.API_PROXY_TARGET || 'http://127.0.0.1:8000' } },
    },
    preview: {
      port: 4173,
      strictPort: true,
      proxy: { '/api': { target: env.API_PROXY_TARGET || 'http://127.0.0.1:8000' } },
    },
  };
});
