import { cpSync, existsSync } from "node:fs";
import { spawn } from "node:child_process";

const standalone = ".next/standalone";
if (!existsSync(`${standalone}/server.js`)) {
  throw new Error("Production bundle is missing. Run `npm run build` first.");
}

cpSync(".next/static", `${standalone}/.next/static`, { recursive: true });
if (existsSync("public")) {
  cpSync("public", `${standalone}/public`, { recursive: true });
}

const server = spawn(process.execPath, [`${standalone}/server.js`], {
  env: process.env,
  stdio: "inherit",
});
server.on("exit", (code) => process.exit(code ?? 1));
