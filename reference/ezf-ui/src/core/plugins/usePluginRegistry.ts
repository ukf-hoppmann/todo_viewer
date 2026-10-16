import { useContext } from "react";
import { PluginRegistryContext } from "./PluginRegistryContext";
import type { PluginRegistry } from "./types";

/** The registry of the nearest `PluginRegistryProvider`; throws without one. */
export function usePluginRegistry(): PluginRegistry {
	const registry = useContext(PluginRegistryContext);
	if (!registry) throw new Error("usePluginRegistry must be used inside a PluginRegistryProvider");
	return registry;
}
