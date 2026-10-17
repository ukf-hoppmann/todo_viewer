import { createBanners } from "./createBanners";

/**
 * The central banner list of the application; callable from anywhere, also
 * outside React components. `BannerHost` shows its banners.
 */
export const banners = createBanners();
