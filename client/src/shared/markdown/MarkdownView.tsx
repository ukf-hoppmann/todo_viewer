import { Box } from "@mui/material";
import { useMemo } from "react";
import { sharedTestIds } from "../testIds";
import { renderMarkdown } from "./renderMarkdown";

/** Markdown as formatted text; the HTML is cleaned before it is put into the page. */
export function MarkdownView({ source }: { source: string }) {
	const html = useMemo(() => renderMarkdown(source), [source]);
	return (
		<Box
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
	);
}
