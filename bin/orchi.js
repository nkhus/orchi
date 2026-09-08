#!/usr/bin/env node

import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";

const installer = fileURLToPath(new URL("../tools/install.py", import.meta.url));
const supplied = process.argv.slice(2);
const hasProject = supplied.some(
  (argument) => argument === "--project" || argument.startsWith("--project="),
);
const argumentsForInstaller = hasProject
  ? supplied
  : ["--project", process.cwd(), ...supplied];

const result = spawnSync(
  "uv",
  ["run", "--no-project", "--python", ">=3.11", installer, ...argumentsForInstaller],
  { stdio: "inherit" },
);
if (result.error?.code === "ENOENT") {
  process.stderr.write("Orchi installation requires uv on PATH.\n");
  process.exit(1);
}
if (result.error) {
  process.stderr.write(`Unable to run uv: ${result.error.message}\n`);
  process.exit(1);
}
process.exit(result.status ?? 1);
