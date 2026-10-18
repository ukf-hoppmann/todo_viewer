import { Box } from "@mui/material";
import { useMemo, useState, type ReactNode } from "react";
import { useTranslation } from "react-i18next";
import { ErrorBoundary } from "../errors/ErrorBoundary";
import type { MainLayout } from "../plugins/types";
import { useSlot } from "../plugins/useSlot";
import { coreTestIds } from "../testIds";
import { PageDetailContext } from "./PageDetailContext";
import { PageHeaderContext } from "./PageHeaderContext";

interface SubLayoutProps {
	/** `core` or the plugin the page belongs to; the origin of errors in the detail column. */
	ownerId: string;
	/** The areas the main route asks for (`layout`); without it there is only the content. */
	layout?: MainLayout;
	/** The page of the main route. */
	children: ReactNode;
}

/** The sections of the slot `core.sidebar-sections` that belong to the open main route (`when`). */
function SidebarSections() {
	const { t } = useTranslation("core");
	const sections = useSlot("core.sidebar-sections");
	if (sections.length === 0) return null;
	return (
		<Box
			component="aside"
			aria-label={t("layout.sidebar")}
			data-testid={coreTestIds.sidebar}
			sx={{ width: 260, flexShrink: 0, p: 2, overflowY: "auto", bgcolor: "background.paper", borderRight: 1, borderColor: "divider" }}
		>
			{sections.map(({ ownerId, name, component: Section }) => (
				<Box key={`${ownerId}/${name}`} data-testid={coreTestIds.sidebarSection(ownerId, name)} sx={{ mb: 2 }}>
					<Section />
				</Box>
			))}
		</Box>
	);
}

/**
 * The frame below the tabs, the same for every main route: a header area, a sidebar at the left and a detail
 * column at the right if the main route asks for them (`layout`), and the content in the middle. The areas are
 * empty frames: the header and the detail column are filled by the page (`usePageHeader`, `usePageDetail`),
 * the sidebar by the plugins (slot `core.sidebar-sections`). The header area exists as soon as the layout does,
 * so the content does not jump while the page is still loading; the detail column shows only while it has content.
 */
export function SubLayout({ ownerId, layout, children }: SubLayoutProps) {
	const { t } = useTranslation("core");
	const header = layout?.header === true;
	const detail = layout?.detail === true;
	const [headerContent, setHeaderContent] = useState<ReactNode>();
	const [detailContent, setDetailContent] = useState<ReactNode>();
	const headerContext = useMemo(() => ({ enabled: header, set: setHeaderContent }), [header]);
	const detailContext = useMemo(() => ({ enabled: detail, set: setDetailContent }), [detail]);
	const showDetail = detail && detailContent !== undefined;

	return (
		<PageHeaderContext value={headerContext}>
			<PageDetailContext value={detailContext}>
				{header && (
					<Box data-testid={coreTestIds.pageHeader} sx={{ minHeight: 64, bgcolor: "action.hover", borderBottom: 1, borderColor: "divider" }}>
						{headerContent}
					</Box>
				)}
				<Box sx={{ display: "flex", flexGrow: 1, minHeight: 0 }}>
					{layout?.sidebar === true && <SidebarSections />}
					<Box data-testid={coreTestIds.content} sx={{ flex: "1 1 50%", minWidth: 0, minHeight: 0, display: "flex", flexDirection: "column", overflowY: "auto" }}>
						{children}
					</Box>
					{showDetail && (
						<Box
							component="section"
							aria-label={t("layout.detail")}
							data-testid={coreTestIds.detail}
							sx={{ flex: "1 1 50%", minWidth: 0, minHeight: 0, overflowY: "auto", py: 2, pr: 2 }}
						>
							<ErrorBoundary origin={ownerId}>{detailContent}</ErrorBoundary>
						</Box>
					)}
				</Box>
			</PageDetailContext>
		</PageHeaderContext>
	);
}
