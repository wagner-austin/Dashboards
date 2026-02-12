/**
 * Bundle script using esbuild.
 * Creates a single bundled JS file with content hash for cache busting.
 */

import * as esbuild from "esbuild";
import * as fs from "fs";
import * as path from "path";
import * as crypto from "crypto";

const DIST_DIR = "dist";
const BUNDLE_DIR = "bundle";
const ENTRY_POINT = "dist/io/autostart.js";
const INDEX_HTML = "index.html";

/** Generate short hash from content. */
function hashContent(content) {
  return crypto.createHash("md5").update(content).digest("hex").slice(0, 8);
}

/** Clean old bundles. */
function cleanBundles() {
  const bundlePath = path.join(BUNDLE_DIR);
  if (fs.existsSync(bundlePath)) {
    const files = fs.readdirSync(bundlePath);
    for (const file of files) {
      if (file.startsWith("app.") && file.endsWith(".js")) {
        fs.unlinkSync(path.join(bundlePath, file));
      }
    }
  } else {
    fs.mkdirSync(bundlePath, { recursive: true });
  }
}

/** Bundle with esbuild. */
async function bundle() {
  const result = await esbuild.build({
    entryPoints: [ENTRY_POINT],
    bundle: true,
    format: "esm",
    minify: true,
    sourcemap: false,
    write: false,
    target: ["es2020"],
  });

  const code = result.outputFiles[0].text;
  const hash = hashContent(code);
  const filename = `app.${hash}.js`;
  const outputPath = path.join(BUNDLE_DIR, filename);

  fs.writeFileSync(outputPath, code);
  console.log(`Created: ${outputPath}`);

  return filename;
}

/** Update index.html with new bundle filename. */
function updateIndexHtml(bundleFilename) {
  let html = fs.readFileSync(INDEX_HTML, "utf-8");

  // Replace any script tag (with or without attributes)
  const oldScriptPattern = /<script[^>]*>[\s\S]*?<\/script>/;
  const newScript = `<script type="module" src="./${BUNDLE_DIR}/${bundleFilename}"></script>`;

  html = html.replace(oldScriptPattern, newScript);
  fs.writeFileSync(INDEX_HTML, html);
  console.log(`Updated: ${INDEX_HTML}`);
}

async function main() {
  console.log("Cleaning old bundles...");
  cleanBundles();

  console.log("Bundling...");
  const filename = await bundle();

  console.log("Updating index.html...");
  updateIndexHtml(filename);

  console.log("Done!");
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
