import { defineConfig } from "vite";

export default defineConfig({
  build: {
    lib: {
      entry: "src/librus-messages-card.ts",
      formats: ["es"],
      fileName: () => "librus-messages-card.js",
    },
    outDir: "../dist",
    emptyOutDir: false,
    minify: "esbuild",
    rollupOptions: {
      external: [],
    },
  },
});
