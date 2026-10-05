import { execFileSync } from "node:child_process";
import { existsSync, statSync } from "node:fs";
import path from "node:path";
import { pathToFileURL } from "node:url";

const actionRoot = path.dirname(new URL(import.meta.url).pathname);
const moduleRoot = process.platform === "win32" ? decodeURIComponent(actionRoot.replace(/^\//, "")) : actionRoot;

async function loadDependencies() {
  const nodeModules = path.join(moduleRoot, "node_modules");
  if (!existsSync(nodeModules)) {
    const npm = process.platform === "win32" ? "npm.cmd" : "npm";
    execFileSync(
      npm,
      [
        "install",
        "--no-audit",
        "--no-fund",
        "--no-package-lock",
        "--no-save",
        "@actions/artifact@6.2.1",
        "@actions/glob@0.7.0",
        "@actions/core@3.0.1"
      ],
      { cwd: moduleRoot, stdio: "inherit" }
    );
  }
  return {
    core: await import(pathToFileURL(path.join(nodeModules, "@actions/core/lib/core.js")).href),
    glob: await import(pathToFileURL(path.join(nodeModules, "@actions/glob/lib/glob.js")).href),
    artifact: await import(pathToFileURL(path.join(nodeModules, "@actions/artifact/lib/artifact.js")).href)
  };
}

function normalizePatterns(value) {
  return value
    .split(/\r?\n/)
    .map((x) => x.trim())
    .filter(Boolean);
}

function toFailureMode(value) {
  const mode = (value || "warn").toLowerCase();
  if (!["error", "warn", "ignore"].includes(mode)) {
    throw new Error("if-no-files-found must be error, warn, or ignore");
  }
  return mode;
}

async function main() {
  const { core, glob, artifact } = await loadDependencies();
  const name = core.getInput("name", { required: true });
  const patterns = normalizePatterns(core.getInput("path", { required: true }));
  const mode = toFailureMode(core.getInput("if-no-files-found"));
  const globber = await glob.create(patterns.join("\n"), { followSymbolicLinks: false });
  const matches = await globber.glob();
  const files = matches.filter((p) => {
    try { return statSync(p).isFile(); } catch { return false; }
  });

  if (files.length === 0) {
    const message = `No files matched artifact path for "${name}". Patterns: ${patterns.join(", ")}`;
    if (mode === "error") throw new Error(message);
    if (mode === "warn") core.warning(message);
    return;
  }

  const rootDirectory = process.env.GITHUB_WORKSPACE || process.cwd();
  const client = new artifact.DefaultArtifactClient();
  const result = await client.uploadArtifact(name, files, rootDirectory, { compressionLevel: 6 });

  if (!result?.id) throw new Error(`Artifact upload returned no artifact id for ${name}`);

  core.setOutput("artifact-id", String(result.id));
  core.setOutput("artifact-url", `https://github.com/${process.env.GITHUB_REPOSITORY}/actions/runs/${process.env.GITHUB_RUN_ID}/artifacts/${result.id}`);
  if (result.digest) core.setOutput("artifact-digest", result.digest);

  core.info(`G13_LOCAL_ARTIFACT_UPLOAD_OK name=${name} id=${result.id} digest=${result.digest || "unknown"} files=${files.length}`);
}

main().catch((error) => {
  console.error(error?.stack || error);
  process.exitCode = 1;
});
