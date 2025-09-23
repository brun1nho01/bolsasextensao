import { defineConfig } from "vite";
import react from "@vitejs/plugin-react-swc";
import path from "path";
import { componentTagger } from "lovable-tagger";

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  // Expõe a versão do package.json para o código do frontend
  define: {
    "import.meta.env.PACKAGE_VERSION": JSON.stringify(
      process.env.npm_package_version
    ),
  },
});
