import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react-swc'
import { viteSingleFile } from "vite-plugin-singlefile"
import path from 'path'
import { globSync } from 'fs'

const htmlPaths = globSync(path.resolve(__dirname, 'src/**/*.html'))
const inputEntries = htmlPaths.map(htmlPath => {
  const stem = path.basename(htmlPath, '.html')
  const distName = stem === 'index' ? path.basename(path.dirname(htmlPath)) : stem
  return [distName, htmlPath]
})
const input = Object.fromEntries(inputEntries)

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), viteSingleFile({ useRecommendedBuildConfig: false })],

  root: path.resolve(__dirname, 'src'),
  publicDir: path.resolve(__dirname, 'public'),

  build: {
    outDir: path.resolve(__dirname, 'dist'),

    // Force to empty dist outside project
    emptyOutDir: true,

    rollupOptions: {
      input,
    },
  },
})
