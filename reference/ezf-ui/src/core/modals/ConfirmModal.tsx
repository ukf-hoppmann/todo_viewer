import { Box, Button, Dialog, DialogActions, DialogContent, DialogTitle } from "@mui/material";
import { Component, useId, useRef, useState, type ReactNode } from "react";
import { useTranslation } from "react-i18next";
import { coreTestIds } from "../testIds";
import { translateText } from "./text";
import type { ConfirmBodyProps, ConfirmRequest, ConfirmWithBodyRequest } from "./types";

interface ConfirmModalProps {
	request: ConfirmRequest | ConfirmWithBodyRequest<unknown>;
	onAnswer: (confirmed: boolean, data: unknown) => void;
}

/**
 * Confirmation, with or without content of its own. It closes only through
 * its buttons: Escape and a click outside do nothing, so a decision is always
 * explicit and input in the content is not lost by a misclick.
 */
export function ConfirmModal({ request, onAnswer }: ConfirmModalProps) {
	const { t } = useTranslation("core");
	const titleId = useId();
	const withBody = "body" in request;
	const [data, setState] = useState<unknown>(withBody ? request.initialData : undefined);
	// Latest data, also for several updates within one event and for the error case.
	const latest = useRef(data);

	const setData = (next: unknown) => {
		latest.current = next;
		setState(next);
	};
	const bodyProps: ConfirmBodyProps<unknown> = {
		data,
		setData,
		updateData: (patch) => setData({ ...(latest.current as object), ...(patch as object) }),
	};

	return (
		<Dialog
			open
			fullWidth
			maxWidth={request.maxWidth ?? "sm"}
			aria-labelledby={titleId}
			data-testid={coreTestIds.modal}
		>
			<DialogTitle id={titleId} data-testid={coreTestIds.modalTitle}>
				{request.title ? translateText(t, request.title) : t("modals.confirmationRequired")}
			</DialogTitle>
			<DialogContent>
				{request.message !== undefined && (
					<Box data-testid={coreTestIds.modalMessage} sx={{ whiteSpace: "pre-line" }}>
						{translateText(t, request.message)}
					</Box>
				)}
				{withBody && (
					<Box data-testid={coreTestIds.modalBody} sx={{ mt: request.message !== undefined ? 2 : 0 }}>
						<BodyBoundary onError={() => onAnswer(false, latest.current)}>
							<Body render={request.body} props={bodyProps} />
						</BodyBoundary>
					</Box>
				)}
			</DialogContent>
			<DialogActions sx={{ justifyContent: "space-between" }}>
				<Button onClick={() => onAnswer(false, latest.current)} data-testid={coreTestIds.modalCancel}>
					{request.cancelText ? translateText(t, request.cancelText) : t("modals.cancel")}
				</Button>
				<Button variant="contained" onClick={() => onAnswer(true, latest.current)} data-testid={coreTestIds.modalConfirm}>
					{request.confirmText ? translateText(t, request.confirmText) : t("modals.confirm")}
				</Button>
			</DialogActions>
		</Dialog>
	);
}

/** Calls the render function of the caller inside the error boundary. */
function Body({
	render,
	props,
}: {
	render: (props: ConfirmBodyProps<unknown>) => ReactNode;
	props: ConfirmBodyProps<unknown>;
}) {
	return <>{render(props)}</>;
}

/**
 * Catches a render error of the content: the request is answered with
 * `confirmed: false` and the queue goes on. Logging is done centrally
 * through `onCaughtError` of the root (TASK-011), not here.
 */
class BodyBoundary extends Component<{ onError: () => void; children: ReactNode }, { failed: boolean }> {
	state = { failed: false };

	static getDerivedStateFromError() {
		return { failed: true };
	}

	componentDidCatch() {
		this.props.onError();
	}

	render() {
		return this.state.failed ? null : this.props.children;
	}
}
