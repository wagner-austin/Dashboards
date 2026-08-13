import { defineConfig } from "vitest/config";

export default defineConfig({
  test: {
    // Source tests only. Without this, compiled copies under dist/ are
    // collected as well, so a stale build silently reruns old tests.
    include: ["src/**/*.test.ts"],
    coverage: {
      provider: "v8",
      include: ["src/**/*.ts"],
      exclude: [
        "src/**/*.test.ts",
        "src/sprites/**",
        "src/types.ts", // Type definitions only - no executable code
        "src/io/**", // I/O boundary code - tested through dependency injection
        "src/**/index.ts", // Re-export files - no executable logic
      ],
      thresholds: {
        lines: 100,
        functions: 100,
        branches: 100,
        statements: 100,
      },
    },
  },
});
