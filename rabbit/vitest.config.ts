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
        // Generated frame data: `export const frames = [...]`. No branches,
        // nothing to exercise, and 50+ files of string literals would swamp
        // the report.
        "src/sprites/**",
        // Pure re-exports. Verified: every index.ts declares nothing.
        "src/**/index.ts",
        // The bundle entry point, and the only file excluded for a reason
        // other than "it contains nothing to run". Its whole body is the
        // invocation that starts the program; importing it from a test would
        // start the engine, which is what its own environment guard exists to
        // prevent. The decision it delegates to lives in bootstrap.ts and is
        // tested there. Named individually rather than as `src/io/**`, which
        // is how 340 lines of untested loader logic used to hide.
        "src/io/autostart.ts",
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
