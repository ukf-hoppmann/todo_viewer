import FormatListBulletedIcon from "@mui/icons-material/FormatListBulleted";
import { Box, Menu, MenuItem } from "@mui/material";
import { useMemo, useRef, useState } from "react";
import { IconAction } from "../IconAction";
import { sharedTestIds } from "../testIds";
import { extractHeadings, renderMarkdown } from "./renderMarkdown";

interface MarkdownViewProps {
	source: string;
	/** Accessible name of the outline. Given, a document with several headings gets an outline button that jumps to a heading. */
	outlineLabel?: string;
}

/** Markdown as formatted text; the HTML is cleaned before it is put into the page. */
export function MarkdownView({ source, outlineLabel }: MarkdownViewProps) {
	const html = useMemo(() => renderMarkdown(source), [source]);
	const headings = useMemo(() => (outlineLabel ? extractHeadings(source) : []), [source, outlineLabel]);
	const contentRef = useRef<HTMLDivElement>(null);
	const [anchor, setAnchor] = useState<HTMLElement | null>(null);
	// Look inside this view only: the same document may be shown elsewhere on the page with the same heading ids.
	const jumpTo = (slug: string) => {
		setAnchor(null);
		contentRef.current?.querySelector(`[id="${slug}"]`)?.scrollIntoView({ block: "start" });
	};
	return (
		<Box>
			{outlineLabel && headings.length > 1 && (
				<Box sx={{ display: "flex", justifyContent: "flex-end" }}>
					<IconAction label={outlineLabel} icon={FormatListBulletedIcon} onClick={(event) => setAnchor(event.currentTarget)} testId={sharedTestIds.outlineButton} />
				</Box>
			)}
			<Menu open={anchor !== null} anchorEl={anchor} onClose={() => setAnchor(null)} slotProps={{ list: { "aria-label": outlineLabel, dense: true, "data-testid": sharedTestIds.outline } as never }}>
				{headings.map((heading) => (
					<MenuItem key={heading.slug} data-testid={sharedTestIds.outlineItem(heading.slug)} sx={{ pl: 1.5 + (heading.depth - 1) * 2 }} onClick={() => jumpTo(heading.slug)}>
						{heading.text}
					</MenuItem>
				))}
			</Menu>
			<Box
				ref={contentRef}
				data-testid={sharedTestIds.markdownView}
				sx={{
					wordBreak: "break-word",
					"& pre": { overflowX: "auto", p: 1, bgcolor: "action.hover", borderRadius: 1 },
					"& code": { fontFamily: "monospace" },
					"& table": { borderCollapse: "collapse" },
					"& th, & td": { border: 1, borderColor: "divider", px: 1 },
					"& h1, & h2, & h3": { mt: 2, mb: 1 },
				}}
				// cleaned by DOMPurify in renderMarkdown
				dangerouslySetInnerHTML={{ __html: html }}
			/>
		</Box>
	);
}
