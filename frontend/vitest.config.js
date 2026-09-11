import { defineConfig, mergeConfig } from "vitest/config";

import viteConfig from "./vite.config.js";

export default mergeConfig(
  viteConfig,
  defineConfig({
    test: {
      environment: "jsdom",
      globals: true,
      setupFiles: ["./src/test/setup.js"],
      css: false,

      exclude: ["**/node_modules/**", "**/dist/**", "e2e/**"],
      restoreMocks: true,
    },
  }),
);
