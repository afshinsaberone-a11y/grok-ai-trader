import { readFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

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

const encoded = Buffer.from(source, "utf8").toString("base64");
await import("data:text/javascript;base64," + encoded);
