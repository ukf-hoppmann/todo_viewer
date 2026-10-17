import { List, ListItem, ListItemButton, ListItemIcon, ListItemText, Paper, Tooltip } from "@mui/material";
import { useTranslation } from "react-i18next";
import { Link, useLocation } from "react-router";
import { coreTestIds } from "../testIds";
import { viewPath } from "./paths";
import type { SidebarEntry } from "./types";

interface SidebarProps {
	/** The main route that opens the sidebar. */
	host: { ownerId: string; name: string };
	/** The entries in their order. */
	entries: readonly SidebarEntry[];
}

/**
 * The second navigation level: one card per entry with icon and text, drawn
 * the same way for every entry, as in the old application. Every entry is a
 * link with its own address. The selected entry is highlighted with the
 * secondary color of the theme and announced as the current page.
 */
export function Sidebar({ host, entries }: SidebarProps) {
	const { t } = useTranslation("core");
	const { pathname } = useLocation();
	const current = pathname.replace(/\/$/, "");

	return (
		<List
			component="nav"
			aria-label={t("navigation.sidebar")}
			data-testid={coreTestIds.sidebar}
			sx={{ flex: "0 0 16.666%", minWidth: 200, p: 0 }}
		>
			{entries.map(({ ownerId, name, slot, contribution }) => {
				const Icon = contribution.icon;
				const path = viewPath(ownerId, name, host);
				const selected = current === path;
				const label = t(contribution.title, { ns: ownerId });

				return (
					<ListItem key={`${ownerId}/${name}`} disablePadding sx={{ p: 0.5 }}>
						<Paper
							sx={{
								width: "100%",
								bgcolor: selected ? "secondary.main" : "inherit",
								color: selected ? "secondary.contrastText" : "inherit",
							}}
						>
							<Tooltip title={label} placement="right" enterDelay={500}>
								<ListItemButton
									component={Link}
									to={path}
									aria-current={selected ? "page" : undefined}
									data-testid={coreTestIds.sidebarItem(slot, ownerId, name)}
								>
									<ListItemIcon sx={{ color: "inherit" }}>
										<Icon />
									</ListItemIcon>
									<ListItemText primary={label} slotProps={{ primary: { noWrap: true } }} />
								</ListItemButton>
							</Tooltip>
						</Paper>
					</ListItem>
				);
			})}
		</List>
	);
}
