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

for (const python of ["python3", "python"]) {
  const result = spawnSync(python, [installer, ...argumentsForInstaller], {
    stdio: "inherit",
  });
  if (result.error?.code === "ENOENT") continue;
  if (result.error) {
    process.stderr.write(`Unable to run ${python}: ${result.error.message}\n`);
    process.exit(1);
  }
  process.exit(result.status ?? 1);
}

process.stderr.write("Orchi requires Python 3.11 or newer (python3 or python on PATH).\n");
process.exit(1);
