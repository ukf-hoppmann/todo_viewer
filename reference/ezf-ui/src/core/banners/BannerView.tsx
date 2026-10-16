import CloseIcon from "@mui/icons-material/Close";
import { Alert, AlertTitle, Box, Button, IconButton } from "@mui/material";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import type { UnhandledErrors } from "../errors/createUnhandledErrors";
import { translateText } from "../modals/text";
import { coreTestIds } from "../testIds";
import type { BannerAction, VisibleBanner } from "./types";

interface BannerViewProps {
	banner: VisibleBanner;
	/** Where the error of a button is reported. */
	unhandled: UnhandledErrors;
}

/** One banner: a band with the severity color, optional title, the message, the buttons, and the X. */
export function BannerView({ banner: { request, handle }, unhandled }: BannerViewProps) {
	const { t } = useTranslation("core");
	const [busy, setBusy] = useState(false);
	const severity = request.severity ?? "info";
	const actions = request.actions ?? [];

	/** Runs the function of a button; the banner closes afterwards unless the button keeps it open. */
	const run = async (action: BannerAction) => {
		setBusy(true);
		try {
			await action.onClick(handle);
			if (!action.keepOpen) handle.close();
		} catch (error) {
			// The banner stays, so that the user can try again; the error is not swallowed.
			unhandled.report(error, { action: "banner-action" });
		} finally {
			setBusy(false);
		}
	};

	const dismissible = request.dismissible !== false;

	return (
		<Alert
			severity={severity}
			data-testid={coreTestIds.banner}
			data-severity={severity}
			sx={{ borderRadius: 0 }}
			action={
				actions.length === 0 && !dismissible ? undefined : (
					<Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
						{actions.map((action, index) => (
							<Button
								key={index}
								color="inherit"
								size="small"
								disabled={busy}
								onClick={() => void run(action)}
								data-testid={coreTestIds.bannerAction(index)}
							>
								{translateText(t, action.label)}
							</Button>
						))}
						{dismissible && (
							<IconButton size="small" color="inherit" aria-label={t("banners.close")} onClick={handle.close} data-testid={coreTestIds.bannerClose}>
								<CloseIcon fontSize="small" />
							</IconButton>
						)}
					</Box>
				)
			}
		>
			{request.title !== undefined && <AlertTitle data-testid={coreTestIds.bannerTitle}>{translateText(t, request.title)}</AlertTitle>}
			<Box data-testid={coreTestIds.bannerMessage} sx={{ whiteSpace: "pre-line" }}>
				{translateText(t, request.message)}
			</Box>
		</Alert>
	);
}
