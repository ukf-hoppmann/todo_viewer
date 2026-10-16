import CloseIcon from "@mui/icons-material/Close";
import { Box, Dialog, IconButton, List, ListItemButton, ListItemText, Typography } from "@mui/material";
import { useMemo } from "react";
import { sharedTestIds } from "../testIds";
import { MarkdownView } from "./MarkdownView";
import { extractHeadings } from "./renderMarkdown";

interface LargeViewProps {
	open: boolean;
	onClose: () => void;
	title: string;
	markdown: string;
	/** Accessible name of the close button. */
	closeLabel: string;
	/** Accessible name of the table of contents. */
	tocLabel: string;
}

/** An almost full-screen view of a document, with a table of contents built from its headings. */
export function LargeView({ open, onClose, title, markdown, closeLabel, tocLabel }: LargeViewProps) {
	const headings = useMemo(() => extractHeadings(markdown), [markdown]);
	return (
		<Dialog open={open} onClose={onClose} maxWidth={false} slotProps={{ paper: { sx: { width: "95vw", height: "95vh" }, "data-testid": sharedTestIds.largeView } as never }}>
			<Box sx={{ display: "flex", alignItems: "center", p: 1.5, borderBottom: 1, borderColor: "divider" }}>
				<Typography variant="h6" component="h2" sx={{ flexGrow: 1 }}>
					{title}
				</Typography>
				<IconButton aria-label={closeLabel} onClick={onClose} data-testid={sharedTestIds.largeViewClose}>
					<CloseIcon />
				</IconButton>
			</Box>
			<Box sx={{ display: "flex", flexGrow: 1, minHeight: 0 }}>
				{headings.length > 0 && (
					<List component="nav" aria-label={tocLabel} dense data-testid={sharedTestIds.largeViewToc} sx={{ width: 260, flexShrink: 0, overflowY: "auto", borderRight: 1, borderColor: "divider" }}>
						{headings.map((heading) => (
							<ListItemButton
								key={heading.slug}
								data-testid={sharedTestIds.largeViewTocItem(heading.slug)}
								sx={{ pl: 1 + (heading.depth - 1) * 2 }}
								onClick={() => document.getElementById(heading.slug)?.scrollIntoView({ block: "start" })}
							>
								<ListItemText primary={heading.text} slotProps={{ primary: { noWrap: true } }} />
							</ListItemButton>
						))}
					</List>
				)}
				<Box sx={{ flexGrow: 1, minWidth: 0, overflowY: "auto", p: 3 }}>
					<MarkdownView source={markdown} />
				</Box>
			</Box>
		</Dialog>
	);
}
