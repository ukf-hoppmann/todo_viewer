import { Box } from "@mui/material";
import { useSyncExternalStore } from "react";
import type { UnhandledErrors } from "../errors/createUnhandledErrors";
import { unhandledErrors } from "../errors/unhandledErrors";
import { coreTestIds } from "../testIds";
import { banners as defaultBanners } from "./banners";
import { BannerView } from "./BannerView";
import type { Banners } from "./types";

interface BannerHostProps {
	/** Banner list to show; the standard `banners` object by default. */
	banners?: Banners;
	/** Where the error of a button is reported; the central handling of unhandled errors by default. */
	unhandled?: UnhandledErrors;
}

/**
 * Shows the banners one below the other, the oldest on top. It stands once in the `RootLayout`,
 * directly under the app bar, and takes no room while there is no banner.
 */
export function BannerHost({ banners = defaultBanners, unhandled = unhandledErrors }: BannerHostProps) {
	const shown = useSyncExternalStore(banners.subscribe, banners.getSnapshot);

	if (shown.length === 0) return null;
	return (
		<Box data-testid={coreTestIds.bannerHost} sx={{ display: "flex", flexDirection: "column" }}>
			{shown.map((banner) => (
				<BannerView key={banner.id} banner={banner} unhandled={unhandled} />
			))}
		</Box>
	);
}
