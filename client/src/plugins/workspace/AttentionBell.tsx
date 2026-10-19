import NotificationsIcon from "@mui/icons-material/Notifications";
import { Badge, IconButton, Popover, Tooltip } from "@mui/material";
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { AttentionList } from "./AttentionList";
import { useAttention } from "./attentionContext";
import { workspaceTestIds } from "./testIds";

/**
 * A bell with the number of due things (nothing while there are none). Without `projectUid` it counts all projects
 * and puts the number into the title of the browser tab; with it, only that project. A click lists them.
 */
export function AttentionBell({ projectUid }: { projectUid?: string }) {
	const { t } = useTranslation("workspace");
	const entries = useAttention(projectUid);
	const [anchor, setAnchor] = useState<HTMLElement | null>(null);
	const count = entries.length;
	const global = projectUid === undefined;

	useEffect(() => {
		if (!global) return;
		const base = document.title.replace(/^\(\d+\) /, "");
		document.title = count > 0 ? `(${count}) ${base}` : base;
		return () => {
			document.title = base;
		};
	}, [count, global]);

	if (count === 0) return null;
	const label = t("attention.label", { count });
	return (
		<>
			<Tooltip title={label}>
				<IconButton
					size="small"
					aria-label={label}
					onClick={(event) => setAnchor(event.currentTarget)}
					data-testid={global ? workspaceTestIds.attentionBell : workspaceTestIds.attentionProjectBell(projectUid)}
				>
					<Badge badgeContent={count} color="warning" max={99}>
						<NotificationsIcon fontSize="small" />
					</Badge>
				</IconButton>
			</Tooltip>
			<Popover open={anchor !== null} anchorEl={anchor} onClose={() => setAnchor(null)}>
				{anchor && <AttentionList entries={entries} onOpened={() => setAnchor(null)} />}
			</Popover>
		</>
	);
}
