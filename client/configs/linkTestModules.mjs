// The tests live in ../tests and import react, vitest, ... : give them this folder's node_modules.
import { existsSync, lstatSync, rmSync, symlinkSync } from "node:fs";
import { fileURLToPath } from "node:url";

const link = fileURLToPath(new URL("../../tests/node_modules", import.meta.url));
const target = fileURLToPath(new URL("../node_modules", import.meta.url));

if (existsSync(link) || lstatSync(link, { throwIfNoEntry: false })) rmSync(link, { recursive: true, force: true });
symlinkSync(target, link, "junction");
