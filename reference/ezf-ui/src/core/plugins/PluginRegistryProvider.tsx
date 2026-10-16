import type { ReactNode } from "react";
import { PluginRegistryContext } from "./PluginRegistryContext";
import type { PluginRegistry } from "./types";

interface PluginRegistryProviderProps {
	registry: PluginRegistry;
	children: ReactNode;
}

/** Provides the registry created by `src/app` to the components below. */
export function PluginRegistryProvider({ registry, children }: PluginRegistryProviderProps) {
	return <PluginRegistryContext.Provider value={registry}>{children}</PluginRegistryContext.Provider>;
}
