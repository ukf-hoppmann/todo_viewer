import { AppRouter, AuthProvider, LoginPage, PluginRegistryProvider, RootLayout, StoreProvider } from "../core";
import type { StartResult } from "./startApp";

interface StartedViewProps {
	/** `undefined` while `startApp` is still running, for example while it waits for the backend. */
	started: StartResult | undefined;
}

/**
 * Shows what `startApp` made of the start, always inside the `RootLayout` so that the app bar with
 * the switches for language and color scheme is there in every state: the application when the user
 * is logged in (the router brings its own `RootLayout` with the tabs), the login page when not, and
 * an empty main area while the start is still running (the banner tells why it takes long) or when it
 * has stopped (the reason has been reported to the user as a dialog).
 * The providers for language, theme, and dialogs sit above it, in `main.tsx`.
 */
export function StartedView({ started }: StartedViewProps) {
	if (!started || started.kind === "stopped") return <RootLayout />;

	return (
		<AuthProvider auth={started.auth}>
			{started.kind === "login" ? (
				<LoginPage />
			) : (
				<PluginRegistryProvider registry={started.registry}>
					<StoreProvider store={started.store}>
						<AppRouter router={started.router} />
					</StoreProvider>
				</PluginRegistryProvider>
			)}
		</AuthProvider>
	);
}
