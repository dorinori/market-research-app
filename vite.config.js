import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  root: path.resolve(__dirname, 'client/src'), // Points to src
  build: {
    outDir: path.resolve(__dirname, 'dist'), // Outputs to root/dist
    emptyOutDir: true, // Clears dist folder before build
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, 'client/src') // Optional but recommended
    }
  }
});