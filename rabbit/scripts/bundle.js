/**
 * Bundle script using esbuild.
 *
 * Emits a content-hashed bundle plus a manifest naming it. The page reads the
 * manifest at load with a cache-busting query rather than hard-coding the
 * filename, because index.html is itself served with max-age=600: a hash
 * written into the document is only as fresh as the document, which left
 * returning visitors on the previous build for ten minutes after a deploy.
 */

import * as esbuild from "esbuild";
import * as fs from "fs";
import * as path from "path";
import * as crypto from "crypto";

const BUNDLE_DIR = "bundle";
const ENTRY_POINT = "dist/io/autostart.js";
const MANIFEST = "manifest.json";

/** Generate short hash from content. */
function hashContent(content) {
  return crypto.createHash("md5").update(content).digest("hex").slice(0, 8);
}

/** Remove previous bundles so only the current hash is served. */
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

  return { filename, hash };
}

/**
 * Write the manifest the page reads to find the current bundle.
 *
 * `built` is the build's own version stamp: the repo declares versions in
 * package.json and pyproject.toml that disagree and are never surfaced, so the
 * content hash plus this timestamp is the only honest answer to "which build
 * is this?" — and it is inspectable at bundle/manifest.json in production.
 */
function writeManifest(bundleFilename, hash) {
  const manifest = {
    entry: bundleFilename,
    hash,
    built: new Date().toISOString(),
  };
  const target = path.join(BUNDLE_DIR, MANIFEST);
  fs.writeFileSync(target, `${JSON.stringify(manifest, null, 2)}
`);
  console.log(`Wrote: ${target}`);
}

async function main() {
  cleanBundles();
  const { filename, hash } = await bundle();
  writeManifest(filename, hash);
}

main().catch(console.error);
