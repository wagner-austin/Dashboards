import { defineConfig } from "vitest/config";

export default defineConfig({
  test: {
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
