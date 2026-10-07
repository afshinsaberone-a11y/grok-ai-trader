import { readFile, mkdtemp, rm, writeFile } from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const root = path.dirname(fileURLToPath(import.meta.url));
const partDir = path.join(root, "dist-upload");
const partNames = [
  "part-01.js",
  "part-02.js",
  "part-03.js",
  "part-04.js",
  "part-05.js",
  "part-06.js",
  "part-07.js",
  "part-08.js",
  "part-09.js",
  "part-10.js"
];

const source = (await Promise.all(
  partNames.map((name) => readFile(path.join(partDir, name), "utf8"))
)).join("");

const tempDir = await mkdtemp(path.join(os.tmpdir(), "g13-artifact-upload-"));
const bundlePath = path.join(tempDir, "index.mjs");

try {
  // Execute the ncc bundle from a real file URL. The bundled
  // @actions/artifact runtime resolves resources relative to import.meta.url;
  // importing from a data: URL makes new URL(".", import.meta.url) invalid.
  await writeFile(bundlePath, source, "utf8");
  await import(pathToFileURL(bundlePath).href);
} finally {
  await rm(tempDir, { recursive: true, force: true });
}
