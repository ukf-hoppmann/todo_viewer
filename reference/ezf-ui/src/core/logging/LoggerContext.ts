import { createContext } from "react";
import { logging } from "./logging";
import type { Logger } from "./types";

/** Logger for components; without a provider it has the origin `core`. */
export const LoggerContext = createContext<Logger>(logging.forOrigin("core"));
