/**
 * Bundle script using esbuild.
 * Creates a single bundled JS file with content hash for cache busting.
 */

import * as esbuild from "esbuild";
import * as fs from "fs";
import * as path from "path";
import * as crypto from "crypto";

const BUNDLE_DIR = "bundle";
const ENTRY_POINT = "dist/io/autostart.js";
const INDEX_HTML = "index.html";

/** Generate short hash from content. */
function hashContent(content) {
  return crypto.createHash("md5").update(content).digest("hex").slice(0, 8);
}

/** Clean old bundles. */
function cleanBundles() {
  if (fs.existsSync(BUNDLE_DIR)) {
    const files = fs.readdirSync(BUNDLE_DIR);
    for (const file of files) {
      if (file.startsWith("app.") && file.endsWith(".js")) {
        fs.unlinkSync(path.join(BUNDLE_DIR, file));
      }
    }
  } else {
    fs.mkdirSync(BUNDLE_DIR, { recursive: true });
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
  let html = fs.readFileSync(INDEX_HTML, "utf8");
  html = html.replace(
    /src="\.\/(?:bundle\/app\.[a-f0-9]+\.js|dist\/io\/autostart\.js)"/,
    `src="./bundle/${bundleFilename}"`
  );
  fs.writeFileSync(INDEX_HTML, html);
  console.log(`Updated: ${INDEX_HTML}`);
}

async function main() {
  cleanBundles();
  const filename = await bundle();
  updateIndexHtml(filename);
}

main().catch(console.error);
