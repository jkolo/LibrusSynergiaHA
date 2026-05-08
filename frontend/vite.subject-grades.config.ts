import { defineConfig } from "vite";

export default defineConfig({
  build: {
    lib: {
      entry: "src/librus-subject-grades-card.ts",
      formats: ["es"],
      fileName: () => "librus-subject-grades-card.js",
    },
    outDir: "../custom_components/librus_apix/www",
    emptyOutDir: false,
    minify: "esbuild",
    rollupOptions: {
      external: [],
    },
  },
});
