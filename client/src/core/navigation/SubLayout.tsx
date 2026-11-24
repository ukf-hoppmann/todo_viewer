import { Box } from "@mui/material";
import { useMemo, useState, type ReactNode } from "react";
import { useTranslation } from "react-i18next";
import { ErrorBoundary } from "../errors/ErrorBoundary";
import type { MainLayout } from "../plugins/types";
import { useSlot } from "../plugins/useSlot";
import { coreTestIds } from "../testIds";
import { usePersistentState } from "../ui-state/usePersistentState";
import { Splitter } from "../../shared";
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

const MIN_DETAIL_WIDTH = 260;
/** At most this share of the window; the rest stays for the content. */
const MAX_DETAIL_SHARE = 0.7;

/** The detail column with a splitter at its left edge; the width is kept per owner in the UI state of the core. */
function ResizableDetail({ ownerId, basicWidth, children }: { ownerId: string; basicWidth: number; children: ReactNode }) {
	const { t } = useTranslation("core");
	const [stored, setStored] = usePersistentState<number | null>("core", `detailWidth.${ownerId}`, null);
	const [live, setLive] = useState<number>();
	const width = live ?? stored ?? basicWidth;
	return (
		<>
			<Splitter
				id="detail"
				label={t("layout.resizeDetail")}
				resetLabel={t("layout.resetDetail")}
				width={width}
				min={MIN_DETAIL_WIDTH}
				max={Math.max(MIN_DETAIL_WIDTH, Math.round(window.innerWidth * MAX_DETAIL_SHARE))}
				panel="after"
				onLive={setLive}
				onCommit={(next) => {
					setLive(undefined);
					setStored(next);
				}}
				canReset={width !== basicWidth}
				onReset={() => {
					setLive(undefined);
					setStored(null);
				}}
			/>
			<Box
				component="section"
				aria-label={t("layout.detail")}
				data-testid={coreTestIds.detail}
				sx={{ flex: `0 0 ${width}px`, minWidth: 0, minHeight: 0, overflowY: "auto", py: 2, pr: 2 }}
			>
				{children}
			</Box>
		</>
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
	const detailWidth = layout?.detailWidth;
	const detailBody = <ErrorBoundary origin={ownerId}>{detailContent}</ErrorBoundary>;

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
					<Box data-testid={coreTestIds.content} sx={{ flex: detailWidth === undefined ? "1 1 50%" : "1 1 0", minWidth: 0, minHeight: 0, display: "flex", flexDirection: "column", overflowY: "auto" }}>
						{children}
					</Box>
					{showDetail && detailWidth !== undefined && (
						<ResizableDetail ownerId={ownerId} basicWidth={detailWidth}>
							{detailBody}
						</ResizableDetail>
					)}
					{showDetail && detailWidth === undefined && (
						<Box
							component="section"
							aria-label={t("layout.detail")}
							data-testid={coreTestIds.detail}
							sx={{ flex: "1 1 50%", minWidth: 0, minHeight: 0, overflowY: "auto", py: 2, pr: 2 }}
						>
							{detailBody}
						</Box>
					)}
				</Box>
			</PageDetailContext>
		</PageHeaderContext>
	);
}
