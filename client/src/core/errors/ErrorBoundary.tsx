import { Alert, Button } from "@mui/material";
import { Component, type ReactNode } from "react";
import { Trans } from "react-i18next";
import { LoggerOriginProvider } from "../logging/LoggerOriginProvider";
import { coreTestIds } from "../testIds";

export interface ErrorBoundaryProps {
	/** `core` or the id of the plugin the area belongs to. */
	origin: string;
	/** `app` for the topmost boundary: the whole application is replaced and can only be reloaded. */
	variant?: "area" | "app";
	/** Called when the user tries again, before the area is rendered again; lets the owner reset what failed. */
	onRetry?: () => void;
	children: ReactNode;
}

interface ErrorBoundaryState {
	failed: boolean;
}

/**
 * Replaces an area that failed while rendering by a fallback, so that the rest
 * of the application keeps working. It neither logs nor opens a dialog:
 * React reports the error to `onCaughtError` of `createRoot`
 * (see `createRootErrorHandlers`), which reads `origin` from here.
 */
export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
	state: ErrorBoundaryState = { failed: false };

	static getDerivedStateFromError(): ErrorBoundaryState {
		return { failed: true };
	}

	private retry = () => {
		this.props.onRetry?.();
		this.setState({ failed: false });
	};

	private reload = () => window.location.reload();

	render() {
		const { origin, variant = "area", children } = this.props;
		if (!this.state.failed) {
			return <LoggerOriginProvider origin={origin}>{children}</LoggerOriginProvider>;
		}

		const isApp = variant === "app";
		return (
			<Alert
				severity="error"
				data-testid={coreTestIds.errorFallback}
				action={
					isApp ? (
						<Button color="inherit" size="small" onClick={this.reload} data-testid={coreTestIds.errorFallbackReload}>
							<Trans i18nKey="errors.fallback.reload" ns="core" />
						</Button>
					) : (
						<Button color="inherit" size="small" onClick={this.retry} data-testid={coreTestIds.errorFallbackRetry}>
							<Trans i18nKey="errors.fallback.retry" ns="core" />
						</Button>
					)
				}
			>
				<Trans i18nKey={isApp ? "errors.fallback.app" : "errors.fallback.area"} ns="core" />
			</Alert>
		);
	}
}
