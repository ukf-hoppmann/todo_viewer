import { Box } from "@mui/material";
import { useMemo } from "react";
import { useTranslation } from "react-i18next";
import { useSlot } from "../../core";
import { DetailPanel } from "../../shared";
import { LinksSection } from "./LinksSection";
import { ShownElementState, type ShownElement } from "./shownElement";
import { workspaceTestIds } from "./testIds";

interface ElementDetailProps extends ShownElement {
	/** For the plain view when no plugin shows this kind. */
	label?: string;
	title?: string;
}

/**
 * The detail of any element: the view that the owner of its kind hangs into `workspace.element-detail` (the
 * widget's `name` is the kind). So a plugin shows elements of other plugins without requiring them. Without such
 * a view, a plain one shows label, title and links.
 */
export function ElementDetail({ uid, kind, onClose, onSelect, label, title }: ElementDetailProps) {
	const { t } = useTranslation("workspace");
	const views = useSlot("workspace.element-detail");
	const shown = useMemo(() => ({ uid, kind, onClose, onSelect }), [uid, kind, onClose, onSelect]);
	const View = views.find((entry) => entry.name === kind)?.component;

	if (View) {
		return (
			<ShownElementState.Provider value={shown}>
				<View />
			</ShownElementState.Provider>
		);
	}
	return (
		<Box data-testid={workspaceTestIds.elementDetailPlain}>
			<DetailPanel title={[label, title].filter(Boolean).join(" — ") || uid} subtitle={kind} onClose={onClose} closeLabel={t("detail.close")}>
				<LinksSection elementUid={uid} readOnly />
			</DetailPanel>
		</Box>
	);
}
