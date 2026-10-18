import CheckIcon from "@mui/icons-material/Check";
import ContentCopyIcon from "@mui/icons-material/ContentCopy";
import { Alert, AlertTitle, Box, Button, Dialog, DialogActions, DialogContent } from "@mui/material";
import { useEffect, useId, useState } from "react";
import { useTranslation } from "react-i18next";
import { IconAction } from "../../shared";
import { coreTestIds } from "../testIds";
import { ExpandArrow } from "./ExpandArrow";
import { translateText } from "./text";
import type { AlertRequest, DetailRow } from "./types";

const COPIED_MS = 2000;

interface AlertModalProps {
	request: AlertRequest;
	onClose: () => void;
}

/** Alert with severity, title, message and collapsed technical details. */
export function AlertModal({ request, onClose }: AlertModalProps) {
	const { t } = useTranslation("core");
	const titleId = useId();
	const severity = request.severity ?? "info";
	const title = request.title ? translateText(t, request.title) : t(`modals.severity.${severity}`);

	return (
		<Dialog
			open
			onClose={onClose}
			fullWidth
			maxWidth={request.maxWidth ?? "sm"}
			aria-labelledby={titleId}
			data-testid={coreTestIds.modal}
		>
			<DialogContent>
				<Alert severity={severity}>
					<AlertTitle id={titleId} data-testid={coreTestIds.modalTitle}>
						{title}
					</AlertTitle>
					{request.message !== undefined && (
						<Box data-testid={coreTestIds.modalMessage} sx={{ whiteSpace: "pre-line" }}>
							{translateText(t, request.message)}
						</Box>
					)}
				</Alert>
				{request.details && request.details.length > 0 && <Details rows={request.details} />}
			</DialogContent>
			<DialogActions>
				<Button onClick={onClose} data-testid={coreTestIds.modalClose}>
					{t("modals.close")}
				</Button>
			</DialogActions>
		</Dialog>
	);
}

function Details({ rows }: { rows: DetailRow[] }) {
	const { t } = useTranslation("core");
	const [open, setOpen] = useState(false);
	const [copied, setCopied] = useState(false);
	const lines = rows.map((row) => ({ label: translateText(t, row.label), value: row.value }));
	const canCopy = typeof navigator !== "undefined" && Boolean(navigator.clipboard);

	useEffect(() => {
		if (!copied) return;
		const timer = setTimeout(() => setCopied(false), COPIED_MS);
		return () => clearTimeout(timer);
	}, [copied]);

	const copy = async () => {
		await navigator.clipboard.writeText(lines.map((line) => `${line.label}: ${line.value}`).join("\n"));
		setCopied(true);
	};

	return (
		<Box sx={{ mt: 2 }}>
			<Button
				size="small"
				onClick={() => setOpen((current) => !current)}
				aria-expanded={open}
				endIcon={<ExpandArrow open={open} />}
				data-testid={coreTestIds.modalDetailsToggle}
			>
				{t("modals.technicalDetails")}
			</Button>
			{open && (
				<Box data-testid={coreTestIds.modalDetails} sx={{ mt: 1 }}>
					{lines.map((line, index) => (
						<Box key={index} sx={{ mb: 1 }}>
							<Box component="span" sx={{ fontWeight: "bold" }}>
								{line.label}
							</Box>
							<Box
								component="pre"
								sx={{ m: 0, whiteSpace: "pre-wrap", wordBreak: "break-word", userSelect: "text", fontFamily: "monospace" }}
							>
								{line.value}
							</Box>
						</Box>
					))}
					{canCopy && (
						<IconAction label={copied ? t("modals.copied") : t("modals.copy")} icon={copied ? CheckIcon : ContentCopyIcon} onClick={() => void copy()} testId={coreTestIds.modalDetailsCopy} />
					)}
				</Box>
			)}
		</Box>
	);
}
