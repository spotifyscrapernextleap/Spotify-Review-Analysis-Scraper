import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// Static SPA. Reads the committed REVIEW_DATA snapshot; no backend.
export default defineConfig({
  plugins: [react()],
  base: './',
});
