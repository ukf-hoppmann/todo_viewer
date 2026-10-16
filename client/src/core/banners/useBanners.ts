import { banners } from "./banners";
import type { Banners } from "./types";

/** The central banner list `banners`, for use in components. */
export function useBanners(): Banners {
	return banners;
}
