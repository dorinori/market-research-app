import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  root: path.resolve(__dirname, 'src'), // Sets root to client/src
  build: {
    outDir: path.resolve(__dirname, 'dist'), // Outputs to client/dist
    emptyOutDir: true,
  }
})