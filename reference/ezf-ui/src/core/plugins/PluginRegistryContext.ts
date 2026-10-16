import { createContext } from "react";
import type { PluginRegistry } from "./types";

/** The registry of this start; without a provider there is none. */
export const PluginRegistryContext = createContext<PluginRegistry | undefined>(undefined);
