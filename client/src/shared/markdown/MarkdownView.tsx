import FormatListBulletedIcon from "@mui/icons-material/FormatListBulleted";
import { Box } from "@mui/material";
import { useMemo, useRef, useState } from "react";
import { IconAction } from "../IconAction";
import { sharedTestIds } from "../testIds";
import { OutlineList } from "./OutlineList";
import { extractHeadings, renderMarkdown } from "./renderMarkdown";

interface MarkdownViewProps {
	source: string;
	/** Accessible name of the outline. Given, a document with several headings gets an icon at the left that shows or hides the outline. */
	outlineLabel?: string;
}

/** Markdown as formatted text; the HTML is cleaned before it is put into the page. */
export function MarkdownView({ source, outlineLabel }: MarkdownViewProps) {
	const html = useMemo(() => renderMarkdown(source), [source]);
	const headings = useMemo(() => (outlineLabel ? extractHeadings(source) : []), [source, outlineLabel]);
	const contentRef = useRef<HTMLDivElement>(null);
	const [open, setOpen] = useState(false);
	const hasOutline = outlineLabel !== undefined && headings.length > 1;
	// Look inside this view only: the same document may be shown elsewhere on the page with the same heading ids.
	const jumpTo = (slug: string) => contentRef.current?.querySelector(`[id="${slug}"]`)?.scrollIntoView({ block: "start" });
	return (
		<Box>
			{hasOutline && <IconAction label={outlineLabel} icon={FormatListBulletedIcon} onClick={() => setOpen((value) => !value)} testId={sharedTestIds.outlineButton} />}
			<Box sx={{ display: "flex", alignItems: "flex-start", gap: 1 }}>
				{hasOutline && open && (
					<OutlineList
						headings={headings}
						label={outlineLabel}
						onJump={jumpTo}
						testId={sharedTestIds.outline}
						itemTestId={sharedTestIds.outlineItem}
						sx={{ width: 200, flexShrink: 0, position: "sticky", top: 0, maxHeight: "70vh", overflowY: "auto", borderRight: 1, borderColor: "divider" }}
					/>
				)}
				<Box
					ref={contentRef}
					data-testid={sharedTestIds.markdownView}
					sx={{
						flexGrow: 1,
						minWidth: 0,
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
		</Box>
	);
}
