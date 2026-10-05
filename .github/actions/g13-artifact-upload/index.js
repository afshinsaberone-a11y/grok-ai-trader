import { execFileSync } from "node:child_process";
import { existsSync, readdirSync, statSync } from "node:fs";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const actionRoot = path.dirname(fileURLToPath(import.meta.url));
const nodeModules = path.join(actionRoot, "node_modules");

function unique(values) {
  return [...new Set(values.filter(Boolean))];
}

function findWindowsNpm() {
  const candidates = [];

  for (const dir of (process.env.PATH || "").split(path.delimiter)) {
    if (dir) candidates.push(path.join(dir, "npm.cmd"));
  }

  for (const root of unique([
    process.env.ProgramW6432,
    process.env.ProgramFiles,
    process.env["ProgramFiles(x86)"]
  ])) {
    candidates.push(path.join(root, "nodejs", "npm.cmd"));
  }

  if (process.env.NVM_HOME) {
    candidates.push(path.join(process.env.NVM_HOME, "npm.cmd"));
    candidates.push(path.join(process.env.NVM_HOME, "nodejs", "npm.cmd"));
  }

  const runnerToolCache = process.env.RUNNER_TOOL_CACHE;
  if (runnerToolCache) {
    const nodeRoot = path.join(runnerToolCache, "node");
    try {
      for (const version of readdirSync(nodeRoot)) {
        const versionRoot = path.join(nodeRoot, version);
        for (const arch of ["x64", "x86"]) {
          candidates.push(path.join(versionRoot, arch, "bin", "npm.cmd"));
          candidates.push(path.join(versionRoot, arch, "npm.cmd"));
        }
      }
    } catch {
      // The runner tool cache is optional; keep searching known system paths.
    }
  }

  const resolved = unique(candidates).find((candidate) => {
    try { return statSync(candidate).isFile(); } catch { return false; }
  });

  if (!resolved) {
    throw new Error(
      "G13_LOCAL_ARTIFACT_UPLOAD requires npm to install its runtime dependencies, " +
      "but npm.cmd was not found in PATH or known Windows Node.js locations. " +
      "Install Node.js with npm for the self-hosted runner service account, or expose npm.cmd in that account's PATH."
    );
  }

  return resolved;
}

function windowsCommandLine(npmPath, command) {
  const escapedArgs = command.map((arg) => `"${String(arg).replace(/"/g, '""')}"`).join(" ");
  return `call "${npmPath.replace(/"/g, '""')}" ${escapedArgs}`;
}

async function loadDependencies() {
  const requiredFiles = [
    "@actions/artifact/lib/artifact.js",
    "@actions/glob/lib/glob.js",
    "@actions/core/lib/core.js"
  ];
  const ready = requiredFiles.every((relative) => existsSync(path.join(nodeModules, relative)));
  if (!ready) {
    const command = [
      "install",
      "--no-audit",
      "--no-fund",
      "--no-package-lock",
      "--no-save",
      "@actions/artifact@6.2.1",
      "@actions/glob@0.7.0",
      "@actions/core@3.0.1"
    ];

    if (process.platform === "win32") {
      const npmPath = findWindowsNpm();
      const execTarget = process.env.ComSpec || "C:\\Windows\\System32\\cmd.exe";
      execFileSync(
        execTarget,
        ["/d", "/s", "/c", windowsCommandLine(npmPath, command)],
        { cwd: actionRoot, stdio: "inherit", windowsHide: true }
      );
    } else {
      execFileSync(
        "npm",
        command,
        { cwd: actionRoot, stdio: "inherit", windowsHide: true }
      );
    }
  }

  const stillMissing = requiredFiles.filter((relative) => !existsSync(path.join(nodeModules, relative)));
  if (stillMissing.length) {
    throw new Error(`G13_LOCAL_ARTIFACT_UPLOAD dependency install completed but required modules are still missing: ${stillMissing.join(", ")}`);
  }

  return {
    core: await import(pathToFileURL(path.join(nodeModules, "@actions/core/lib/core.js")).href),
    glob: await import(pathToFileURL(path.join(nodeModules, "@actions/glob/lib/glob.js")).href),
    artifact: await import(pathToFileURL(path.join(nodeModules, "@actions/artifact/lib/artifact.js")).href)
  };
}

function patternsFromInput(value) {
  return value.split(/\r?\n/).map((x) => x.trim()).filter(Boolean);
}

function noFilesMode(value) {
  const mode = (value || "warn").toLowerCase();
  if (!["error", "warn", "ignore"].includes(mode)) {
    throw new Error("if-no-files-found must be error, warn, or ignore");
  }
  return mode;
}

async function main() {
  const { core, glob, artifact } = await loadDependencies();
  const name = core.getInput("name", { required: true });
  const patterns = patternsFromInput(core.getInput("path", { required: true }));
  const mode = noFilesMode(core.getInput("if-no-files-found"));

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
