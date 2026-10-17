import { CssBaseline, ThemeProvider } from "@mui/material";
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { I18nextProvider } from "react-i18next";
import { createRootErrorHandlers, ErrorBoundary, initI18n, installGlobalErrorHandlers, ModalHost, theme } from "../core";
import { coreContributions } from "./coreContributions";
import { syncDocumentLanguage } from "./documentLanguage";
import { catalogue } from "./plugins/catalogue";
import { startApp, type StartResult } from "./startApp";
import { StartedView } from "./StartedView";

// Composition root: prepares the core and renders the application.
const i18n = await initI18n();
// The page names the language it is shown in, not the fixed one of index.html.
syncDocumentLanguage(i18n);
// Before the first render, so that errors during start-up are reported as well.
installGlobalErrorHandlers();

const container = document.getElementById("root")!;
const root = createRoot(container, createRootErrorHandlers({ i18n, container }));

const render = (started: StartResult | undefined) =>
	root.render(
		<StrictMode>
			<I18nextProvider i18n={i18n}>
				<ThemeProvider theme={theme}>
					<CssBaseline />
					{/* Above everything else, so dialogs work before the plugins load. */}
					<ModalHost />
					{/* Outside of the boundary, so that the hint still appears when the application failed. */}
					<ErrorBoundary origin="core" variant="app">
						<StartedView started={started} />
					</ErrorBoundary>
				</ThemeProvider>
			</I18nextProvider>
		</StrictMode>,
	);

// The layout stands before the start, so that a backend that does not answer shows the banner in a page
// and not a blank one while `startApp` waits for it.
render(undefined);

// Once per start, in a fixed order; a problem is reported as a dialog and the application stays away.
render(await startApp({ i18n, catalogue, coreContributions, devRoutes: [] }));
