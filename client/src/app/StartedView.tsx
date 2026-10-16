import { AppRouter, PluginRegistryProvider, RootLayout, StoreProvider } from "../core";
import type { StartResult } from "./startApp";

interface StartedViewProps {
	/** `undefined` while `startApp` is still running, for example while it waits for the backend. */
	started: StartResult | undefined;
}

/**
 * Shows what `startApp` made of the start, always inside the `RootLayout` so that the app bar is there in
 * every state: the application when it started (the router brings its own frame), and an empty main area
 * while the start is still running (the banner tells why it takes long) or when it has stopped (the reason
 * has been reported to the user as a dialog). The providers for language, theme, and dialogs sit above it,
 * in `main.tsx`.
 */
export function StartedView({ started }: StartedViewProps) {
	if (!started || started.kind === "stopped") return <RootLayout />;

	return (
		<PluginRegistryProvider registry={started.registry}>
			<StoreProvider store={started.store}>
				<AppRouter router={started.router} />
			</StoreProvider>
		</PluginRegistryProvider>
	);
}
